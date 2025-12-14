"""
Query Rewriter for HaUI Chatbot
Improves query understanding by rewriting ambiguous queries.
Uses LLM to clarify user intent and add context for better retrieval.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RewriteResult:
    """Result of query rewriting."""
    original: str
    rewritten: str
    intent_clarification: str
    keywords_added: List[str]
    was_modified: bool


class QueryRewriter:
    """
    Rewrite queries to improve retrieval precision.
    
    Features:
    - Clarify ambiguous references (e.g., "nó", "cái đó")
    - Add context from conversation history
    - Expand implicit constraints (e.g., "do trường tổ chức")
    - Handle follow-up questions
    """
    
    # === CONTEXT PATTERNS ===
    # Patterns that indicate specific constraints
    CONSTRAINT_PATTERNS = {
        # Ownership/organization constraints
        r'(do|của)\s+(trường|sict|haui|khoa)\s+(tổ chức|đứng ra|chủ trì)': 
            'sự kiện/hoạt động NỘI BỘ do SICT/HaUI tổ chức',
        r'trường\s+(có\s+)?(tổ chức|mở|đứng ra)':
            'hoạt động do SICT/HaUI tổ chức, KHÔNG phải tham gia cuộc thi bên ngoài',
        r'(hoạt động|sự kiện)\s+(nội bộ|trong trường)':
            'hoạt động nội bộ của SICT/HaUI',
        
        # Time constraints
        r'(gần đây|mới nhất|hôm nay|tuần này|tháng này)':
            'tin tức/sự kiện gần đây nhất',
        r'(sắp tới|upcoming|tới đây)':
            'sự kiện sắp diễn ra trong tương lai',
        
        # Comparison
        r'(khác|khác nhau|so sánh|vs|versus)':
            'so sánh sự khác biệt giữa các lựa chọn',
        
        # Recommendation
        r'(nên|nên chọn|khuyên|recommend)':
            'đề xuất/gợi ý dựa trên ưu nhược điểm',
    }
    
    # === FOLLOW-UP PATTERNS ===
    # Patterns indicating follow-up questions
    FOLLOWUP_PATTERNS = [
        r'^(còn|thế còn|vậy còn)',
        r'^(à|ừm?)\s+(thế|vậy)',
        r'^(nó|cái đó|ngành đó|trường đó)',
        r'(là gì|thế nào)\?*$',
        r'^(chi tiết|cụ thể)\s+(hơn|thêm)',
    ]
    
    # === IMPLICIT KEYWORDS ===
    # Keywords to add based on detected intent
    IMPLICIT_KEYWORDS = {
        'olympic': ['cuộc thi', 'giải thưởng', 'thành tích', 'sinh viên'],
        'contest': ['cuộc thi', 'thi đấu', 'giải thưởng'],
        'hot': ['nổi bật', 'đáng chú ý', 'quan trọng'],
        'tổ chức': ['diễn ra', 'được tổ chức', 'chủ trì'],
    }
    
    def __init__(self):
        """Initialize query rewriter."""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns."""
        self._constraint_patterns = [
            (re.compile(p, re.IGNORECASE), clarification)
            for p, clarification in self.CONSTRAINT_PATTERNS.items()
        ]
        self._followup_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.FOLLOWUP_PATTERNS
        ]
    
    def detect_constraints(self, query: str) -> List[str]:
        """
        Detect implicit constraints in the query.
        
        Args:
            query: User query
            
        Returns:
            List of detected constraints/clarifications
        """
        constraints = []
        for pattern, clarification in self._constraint_patterns:
            if pattern.search(query):
                constraints.append(clarification)
        return constraints
    
    def is_followup(self, query: str) -> bool:
        """
        Check if query is a follow-up question.
        
        Args:
            query: User query
            
        Returns:
            True if it's a follow-up
        """
        return any(p.search(query) for p in self._followup_patterns)
    
    def expand_keywords(self, query: str) -> List[str]:
        """
        Find additional keywords to help retrieval.
        
        Args:
            query: User query
            
        Returns:
            List of implicit keywords
        """
        keywords = []
        query_lower = query.lower()
        
        for trigger, additions in self.IMPLICIT_KEYWORDS.items():
            if trigger in query_lower:
                keywords.extend(additions)
        
        return list(set(keywords))
    
    def rewrite_with_context(
        self, 
        query: str, 
        chat_history: List[Dict[str, str]] = None
    ) -> RewriteResult:
        """
        Rewrite query with context and clarifications.
        
        Args:
            query: Current user query
            chat_history: Previous conversation messages
            
        Returns:
            RewriteResult with rewritten query
        """
        original = query
        rewritten = query
        intent_clarification = ""
        keywords_added = []
        was_modified = False
        
        # Step 1: Detect constraints
        constraints = self.detect_constraints(query)
        if constraints:
            intent_clarification = "; ".join(constraints)
            was_modified = True
        
        # Step 2: Handle follow-up questions
        if self.is_followup(query) and chat_history:
            # Get context from last exchange
            context_parts = []
            for msg in reversed(chat_history[-4:]):  # Last 2 exchanges
                if msg.get('role') == 'user':
                    context_parts.append(msg.get('content', '')[:100])
            
            if context_parts:
                rewritten = f"{query} (trong ngữ cảnh: {context_parts[0]})"
                was_modified = True
        
        # Step 3: Add implicit keywords
        keywords_added = self.expand_keywords(query)
        
        # Step 4: Add constraint clarification to query
        if intent_clarification:
            rewritten = f"{rewritten} [Lưu ý: {intent_clarification}]"
        
        return RewriteResult(
            original=original,
            rewritten=rewritten,
            intent_clarification=intent_clarification,
            keywords_added=keywords_added,
            was_modified=was_modified
        )
    
    def create_search_queries(self, query: str) -> List[str]:
        """
        Create multiple search queries for better recall.
        
        Args:
            query: Original query
            
        Returns:
            List of search query variations
        """
        queries = [query]
        
        # Add constraint-aware variation
        constraints = self.detect_constraints(query)
        if constraints:
            # Add a version that emphasizes the constraint
            if "nội bộ" in " ".join(constraints).lower() or "tổ chức" in " ".join(constraints).lower():
                # For queries about school-organized events
                queries.append(f"{query} SICT HaUI tổ chức nội bộ")
        
        # Add keyword variations
        keywords = self.expand_keywords(query)
        if keywords:
            queries.append(f"{query} {' '.join(keywords[:3])}")
        
        return queries


class ContextAwareFilter:
    """
    Filter and re-rank retrieved documents based on query context.
    """
    
    # Keywords indicating external events (not organized by school)
    EXTERNAL_EVENT_INDICATORS = [
        'toàn quốc', 'quốc gia', 'quốc tế', 'việt nam',
        'hội tin học', 'bộ giáo dục', 'olympic tin học sinh viên việt nam',
        'icpc', 'acm', 'oi', 'ioi',
    ]
    
    # Keywords indicating internal events (organized by school)
    INTERNAL_EVENT_INDICATORS = [
        'sict tổ chức', 'haui tổ chức', 'trường tổ chức',
        'nội bộ', 'sinh viên trường', 'trong trường',
        'câu lạc bộ', 'khoa tổ chức', 'liên chi đoàn',
    ]
    
    def is_internal_event_query(self, query: str) -> bool:
        """Check if query is asking for school-organized events."""
        query_lower = query.lower()
        patterns = [
            r'trường\s+(có\s+)?(tổ chức|mở)',
            r'(do|của)\s+(trường|sict|haui)',
            r'(nội bộ|trong trường)',
        ]
        return any(re.search(p, query_lower) for p in patterns)
    
    def score_document_relevance(
        self, 
        query: str, 
        doc_content: str, 
        is_internal_query: bool
    ) -> float:
        """
        Score a document's relevance considering context.
        
        Args:
            query: User query
            doc_content: Document content
            is_internal_query: Whether query is asking for internal events
            
        Returns:
            Score adjustment (-1.0 to 1.0)
        """
        doc_lower = doc_content.lower()
        score = 0.0
        
        if is_internal_query:
            # Boost internal event indicators
            for indicator in self.INTERNAL_EVENT_INDICATORS:
                if indicator in doc_lower:
                    score += 0.2
            
            # Penalize external event indicators
            for indicator in self.EXTERNAL_EVENT_INDICATORS:
                if indicator in doc_lower:
                    score -= 0.15
        
        return max(-1.0, min(1.0, score))
    
    def filter_documents(
        self, 
        query: str, 
        documents: List[Dict], 
        threshold: float = -0.3
    ) -> List[Dict]:
        """
        Filter documents based on context relevance.
        
        Args:
            query: User query
            documents: Retrieved documents
            threshold: Minimum score to keep
            
        Returns:
            Filtered and re-ranked documents
        """
        is_internal = self.is_internal_event_query(query)
        
        if not is_internal:
            return documents  # No filtering needed
        
        scored_docs = []
        for doc in documents:
            content = doc.get('page_content', '') or doc.get('content', '')
            score = self.score_document_relevance(query, content, is_internal)
            scored_docs.append((doc, score))
        
        # Filter and sort
        filtered = [(doc, score) for doc, score in scored_docs if score >= threshold]
        filtered.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in filtered]


# === SINGLETON INSTANCES ===
_rewriter_instance: Optional[QueryRewriter] = None
_filter_instance: Optional[ContextAwareFilter] = None

def get_query_rewriter() -> QueryRewriter:
    """Get or create the singleton query rewriter instance."""
    global _rewriter_instance
    if _rewriter_instance is None:
        _rewriter_instance = QueryRewriter()
    return _rewriter_instance

def get_context_filter() -> ContextAwareFilter:
    """Get or create the singleton context filter instance."""
    global _filter_instance
    if _filter_instance is None:
        _filter_instance = ContextAwareFilter()
    return _filter_instance


def rewrite_query(query: str, chat_history: List[Dict] = None) -> str:
    """
    Convenient function to rewrite a query.
    
    Args:
        query: User query
        chat_history: Previous messages
        
    Returns:
        Rewritten query
    """
    rewriter = get_query_rewriter()
    result = rewriter.rewrite_with_context(query, chat_history)
    return result.rewritten


# === TEST ===
if __name__ == "__main__":
    rewriter = QueryRewriter()
    context_filter = ContextAwareFilter()
    
    test_queries = [
        "Trường có tổ chức contest olympic nào hot ko ạ?",
        "SICT có những ngành nào?",
        "Còn ngành ATTT thì sao?",
        "So sánh CNTT và KHMT",
        "Sự kiện nội bộ gần đây của trường?",
    ]
    
    print("=" * 60)
    print("Query Rewriter - Test Cases")
    print("=" * 60)
    
    for query in test_queries:
        result = rewriter.rewrite_with_context(query)
        is_internal = context_filter.is_internal_event_query(query)
        
        print(f"\n📝 Original: {query}")
        print(f"✅ Rewritten: {result.rewritten}")
        print(f"🎯 Intent: {result.intent_clarification or 'General'}")
        print(f"🏠 Internal query: {is_internal}")
        print(f"🔑 Keywords: {result.keywords_added}")
