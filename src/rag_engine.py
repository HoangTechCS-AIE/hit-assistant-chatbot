"""
HaUI Chatbot - RAG Engine with Conversation Memory
Handles document ingestion, retrieval, and question answering.
Supports Vietnamese embedding model for improved accuracy.
"""
import json
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from src.config import (
    LLM_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVER_K,
    JSON_DATA_PATH, CHROMA_DB_PATH, SYSTEM_PROMPT,
    USE_VIETNAMESE_EMBEDDING, VIETNAMESE_EMBEDDING_MODEL, OPENAI_EMBEDDING_MODEL
)

load_dotenv()
logger = logging.getLogger(__name__)


class RAGSystem:
    """
    RAG (Retrieval-Augmented Generation) system for HaUI Chatbot.
    
    Features:
    - Document ingestion with chunking
    - Vector storage with Chroma
    - Conversation memory support
    - Source citation
    - Vietnamese embedding model support
    """
    
    def __init__(
        self, 
        db_path: str = CHROMA_DB_PATH, 
        data_path: str = JSON_DATA_PATH
    ) -> None:
        """
        Initialize RAG system.
        
        Args:
            db_path: Path to Chroma vector database
            data_path: Path to JSON data file
        """
        self.db_path = db_path
        self.data_path = data_path
        self.embeddings = self._initialize_embeddings()
        self.model = ChatOpenAI(model=LLM_MODEL, temperature=0.3)
        self._vectorstore: Optional[Chroma] = None
    
    def _initialize_embeddings(self):
        """
        Initialize embeddings - prefer Vietnamese model, fallback to OpenAI.
        """
        if USE_VIETNAMESE_EMBEDDING:
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
                print(f"🇻🇳 Loading Vietnamese embedding model: {VIETNAMESE_EMBEDDING_MODEL}")
                embeddings = HuggingFaceEmbeddings(
                    model_name=VIETNAMESE_EMBEDDING_MODEL,
                    model_kwargs={'device': 'cpu'},  # Use 'cuda' if GPU available
                    encode_kwargs={'normalize_embeddings': True}
                )
                print("✅ Vietnamese embedding model loaded successfully!")
                return embeddings
            except ImportError:
                print("⚠️ sentence-transformers not installed. Run: pip install sentence-transformers")
                print("📦 Falling back to OpenAI embeddings...")
            except Exception as e:
                print(f"⚠️ Error loading Vietnamese model: {e}")
                print("📦 Falling back to OpenAI embeddings...")
        
        # Fallback to OpenAI
        print(f"🔧 Using OpenAI embedding: {OPENAI_EMBEDDING_MODEL}")
        return OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)

    def ingest_data(self) -> int:
        """
        Load data from JSON, split into chunks, and store in vector database.
        
        Returns:
            Number of chunks created
        """
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(
                f"Data file not found at {self.data_path}. Please run scraper first."
            )

        print("📂 Loading data...")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        documents = []
        for item in data:
            content = f"Tiêu đề: {item.get('title', '')}\n\n{item.get('content', '')}"
            metadata = {
                "source": item.get('url', ''),
                "title": item.get('title', ''),
                "category": self._extract_category(item.get('url', ''))
            }
            documents.append(Document(page_content=content, metadata=metadata))

        print(f"✅ Loaded {len(documents)} documents.")

        print("✂️ Splitting text...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        splits = text_splitter.split_documents(documents)
        print(f"✅ Created {len(splits)} chunks.")

        # Remove existing database to avoid duplicates
        if os.path.exists(self.db_path):
            import shutil
            try:
                shutil.rmtree(self.db_path)
                print("🗑️ Removed old database.")
            except PermissionError:
                # Database is locked, use a new path with timestamp
                import time
                new_path = f"{self.db_path}_{int(time.time())}"
                print(f"⚠️ Old database locked, using new path: {new_path}")
                self.db_path = new_path

        print("💾 Storing in Chroma DB...")
        self._vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=self.db_path
        )
        print(f"✅ Data ingestion complete. DB path: {self.db_path}")
        return len(splits)

    def _extract_category(self, url: str) -> str:
        """Extract category from URL."""
        if '/tin-tuc/' in url:
            return 'Tin tức'
        elif '/su-kien/' in url:
            return 'Sự kiện'
        elif '/tuyen-sinh/' in url:
            return 'Tuyển sinh'
        elif '/nganh-dao-tao/' in url:
            return 'Ngành đào tạo'
        return 'Khác'

    def get_vectorstore(self) -> Chroma:
        """Get or create vectorstore instance."""
        if self._vectorstore is None:
            if not os.path.exists(self.db_path):
                raise ValueError("Vector database not found. Please run ingest_data() first.")
            self._vectorstore = Chroma(
                persist_directory=self.db_path,
                embedding_function=self.embeddings
            )
        return self._vectorstore

    def retrieve_with_sources(
        self, 
        query: str, 
        k: int = RETRIEVER_K
    ) -> Tuple[str, List[Dict[str, str]]]:
        """
        Retrieve relevant documents and return formatted context with sources.
        
        Args:
            query: User question
            k: Number of documents to retrieve
            
        Returns:
            Tuple of (formatted context, list of sources)
        """
        vectorstore = self.get_vectorstore()
        # Use MMR (Maximal Marginal Relevance) for diverse, relevant results
        docs = vectorstore.max_marginal_relevance_search(
            query, 
            k=k,
            fetch_k=k * 2  # Fetch more candidates for better diversity
        )
        
        context_parts = []
        sources = []
        seen_sources = set()
        
        for doc in docs:
            context_parts.append(doc.page_content)
            source_url = doc.metadata.get('source', '')
            if source_url and source_url not in seen_sources:
                seen_sources.add(source_url)
                sources.append({
                    'title': doc.metadata.get('title', 'Không có tiêu đề'),
                    'url': source_url,
                    'category': doc.metadata.get('category', 'Khác')
                })
        
        context = "\n\n---\n\n".join(context_parts)
        return context, sources

    def format_chat_history(self, messages: List[Dict[str, str]], max_turns: int = 3) -> str:
        """
        Format recent chat history for context.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_turns: Maximum number of recent turns to include
            
        Returns:
            Formatted chat history string
        """
        if not messages:
            return "Chưa có lịch sử hội thoại."
        
        recent = messages[-(max_turns * 2):]  # Get last N turns (user + assistant)
        formatted = []
        
        for msg in recent:
            role = "Người dùng" if msg['role'] == 'user' else "Trợ lý"
            formatted.append(f"{role}: {msg['content'][:200]}...")
        
        return "\n".join(formatted) if formatted else "Chưa có lịch sử hội thoại."

    def get_chain(self):
        """
        Create and return the RAG chain (legacy method for compatibility).
        """
        vectorstore = self.get_vectorstore()
        retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})

        template = SYSTEM_PROMPT
        prompt = ChatPromptTemplate.from_template(template)

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        chain = (
            {
                "context": retriever | format_docs, 
                "question": RunnablePassthrough(),
                "chat_history": lambda x: ""
            }
            | prompt
            | self.model
            | StrOutputParser()
        )

        return chain

    def answer_with_sources(
        self, 
        question: str, 
        chat_history: List[Dict[str, str]] = None
    ) -> Tuple[str, List[Dict[str, str]]]:
        """
        Answer a question with source citations.
        
        Args:
            question: User question
            chat_history: Previous conversation messages
            
        Returns:
            Tuple of (answer, sources)
        """
        context, sources = self.retrieve_with_sources(question)
        history_str = self.format_chat_history(chat_history or [])
        
        prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
        
        chain = prompt | self.model | StrOutputParser()
        
        answer = chain.invoke({
            "context": context,
            "question": question,
            "chat_history": history_str
        })
        
        return answer, sources

    def stream_answer_with_sources(
        self, 
        question: str, 
        chat_history: List[Dict[str, str]] = None
    ):
        """
        Stream answer with source citations.
        Enhanced with text processing, FAQ check, entity extraction, and query rewriting.
        
        Args:
            question: User question
            chat_history: Previous conversation messages
            
        Yields:
            Answer chunks, then finally yields sources and suggestions
        """
        # Import modules here to avoid circular imports
        try:
            from src.text_processor import process_query
            from src.faq_handler import check_faq, get_faq_handler
            from src.entity_extractor import extract_entities
            from src.query_rewriter import get_query_rewriter, get_context_filter
        except ImportError:
            # Fallback if modules not available
            process_query = lambda x: x
            check_faq = lambda x: type('obj', (object,), {'found': False})()
            extract_entities = lambda x: type('obj', (object,), {'has_entities': lambda: False})()
            get_faq_handler = lambda: None
            get_query_rewriter = lambda: None
            get_context_filter = lambda: None
        
        # Step 1: Process query (spell check, abbreviations)
        processed_question = process_query(question)
        logger.debug(f"Processed query: {question} -> {processed_question}")
        
        # Step 2: Check FAQ first (fast response)
        faq_result = check_faq(processed_question)
        if faq_result.found and faq_result.entry:
            # Stream FAQ answer directly
            answer = faq_result.entry.answer
            for i in range(0, len(answer), 10):
                yield {"type": "token", "content": answer[i:i+10]}
            
            yield {"type": "sources", "content": []}
            yield {"type": "suggestions", "content": faq_result.suggestions or []}
            return
        
        # Step 3: Query rewriting for better understanding
        query_for_search = processed_question
        context_hint = ""
        
        rewriter = get_query_rewriter()
        context_filter = get_context_filter()
        
        if rewriter:
            rewrite_result = rewriter.rewrite_with_context(processed_question, chat_history)
            if rewrite_result.intent_clarification:
                context_hint = f"\n\n⚠️ LƯU Ý VỀ CÂU HỎI: {rewrite_result.intent_clarification}"
                logger.debug(f"Query rewritten with hint: {context_hint}")
        
        # Step 4: Regular RAG flow  
        context, sources = self.retrieve_with_sources(query_for_search)
        history_str = self.format_chat_history(chat_history or [])
        
        # Step 5: Extract entities from context
        entities = extract_entities(context)
        
        # Enhance context with entities and hints
        enhanced_context = context
        if entities.has_entities():
            entity_info = entities.format_for_response()
            enhanced_context = f"{context}\n\n📋 THÔNG TIN TRÍCH XUẤT:\n{entity_info}"
        
        # Add context hint for LLM to understand query constraints
        if context_hint:
            enhanced_context = f"{enhanced_context}{context_hint}"
        
        prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
        chain = prompt | self.model | StrOutputParser()
        
        for chunk in chain.stream({
            "context": enhanced_context,
            "question": processed_question,
            "chat_history": history_str
        }):
            yield {"type": "token", "content": chunk}
        
        yield {"type": "sources", "content": sources}
        
        # Step 6: Generate suggestions
        try:
            faq_handler = get_faq_handler()
            if faq_handler:
                suggestions = faq_handler.get_related_questions(processed_question)
                yield {"type": "suggestions", "content": suggestions}
        except Exception:
            pass

    def answer_enhanced(
        self, 
        question: str, 
        chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Enhanced answer method with all features.
        
        Args:
            question: User question
            chat_history: Previous conversation messages
            
        Returns:
            Dict with answer, sources, entities, suggestions
        """
        try:
            from src.text_processor import process_query, get_text_processor
            from src.faq_handler import check_faq, get_faq_handler
            from src.entity_extractor import extract_entities
        except ImportError:
            return self._legacy_answer(question, chat_history)
        
        result = {
            "original_question": question,
            "processed_question": None,
            "answer": "",
            "sources": [],
            "entities": {},
            "suggestions": [],
            "intent": None,
            "from_faq": False,
        }
        
        # Process query
        processor = get_text_processor()
        processed, changes = processor.process(question)
        result["processed_question"] = processed
        
        # Check FAQ
        faq_result = check_faq(processed)
        if faq_result.found and faq_result.entry:
            result["answer"] = faq_result.entry.answer
            result["from_faq"] = True
            result["suggestions"] = faq_result.suggestions or []
            return result
        
        # Classify intent
        faq_handler = get_faq_handler()
        result["intent"] = faq_handler.classify_intent(processed).value
        
        # RAG retrieval
        context, sources = self.retrieve_with_sources(processed)
        result["sources"] = sources
        
        # Extract entities
        entities = extract_entities(context)
        result["entities"] = entities.to_dict()
        
        # Generate answer
        prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
        chain = prompt | self.model | StrOutputParser()
        
        history_str = self.format_chat_history(chat_history or [])
        result["answer"] = chain.invoke({
            "context": context,
            "question": processed,
            "chat_history": history_str
        })
        
        # Suggestions
        result["suggestions"] = faq_handler.get_related_questions(processed)
        
        return result
    
    def _legacy_answer(self, question: str, chat_history: List[Dict[str, str]] = None) -> Dict:
        """Legacy answer method without enhancements."""
        context, sources = self.retrieve_with_sources(question)
        history_str = self.format_chat_history(chat_history or [])
        
        prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
        chain = prompt | self.model | StrOutputParser()
        
        answer = chain.invoke({
            "context": context,
            "question": question,
            "chat_history": history_str
        })
        
        return {
            "original_question": question,
            "processed_question": question,
            "answer": answer,
            "sources": sources,
            "entities": {},
            "suggestions": [],
            "intent": None,
            "from_faq": False,
        }


if __name__ == "__main__":
    rag = RAGSystem()
    # rag.ingest_data()  # Uncomment to test ingestion

