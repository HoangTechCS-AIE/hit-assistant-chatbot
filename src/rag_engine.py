"""
HaUI Chatbot - RAG Engine with Conversation Memory
Handles document ingestion, retrieval, and question answering.
"""
import json
import os
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
    JSON_DATA_PATH, CHROMA_DB_PATH, SYSTEM_PROMPT
)

load_dotenv()


class RAGSystem:
    """
    RAG (Retrieval-Augmented Generation) system for HaUI Chatbot.
    
    Features:
    - Document ingestion with chunking
    - Vector storage with Chroma
    - Conversation memory support
    - Source citation
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
        self.embeddings = OpenAIEmbeddings()
        self.model = ChatOpenAI(model=LLM_MODEL, temperature=0.3)
        self._vectorstore: Optional[Chroma] = None

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
            shutil.rmtree(self.db_path)
            print("🗑️ Removed old database.")

        print("💾 Storing in Chroma DB...")
        self._vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=self.db_path
        )
        print("✅ Data ingestion complete.")
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
        
        Args:
            question: User question
            chat_history: Previous conversation messages
            
        Yields:
            Answer chunks, then finally yields sources
        """
        context, sources = self.retrieve_with_sources(question)
        history_str = self.format_chat_history(chat_history or [])
        
        prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
        
        chain = prompt | self.model | StrOutputParser()
        
        for chunk in chain.stream({
            "context": context,
            "question": question,
            "chat_history": history_str
        }):
            yield {"type": "token", "content": chunk}
        
        yield {"type": "sources", "content": sources}


if __name__ == "__main__":
    rag = RAGSystem()
    # rag.ingest_data()  # Uncomment to test ingestion
