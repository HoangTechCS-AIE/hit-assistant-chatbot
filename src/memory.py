"""
HaUI Chatbot - Memory System
Manages short-term (session) and long-term (persistent) conversation memory.
"""
import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import os

# Get project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_DB_PATH = os.path.join(PROJECT_ROOT, "data", "memory.db")


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class Conversation:
    """Represents a complete conversation session."""
    id: str
    title: str
    messages: List[Message]
    created_at: str
    updated_at: str
    summary: str = ""
    
    @staticmethod
    def create_new(title: str = "Cuộc trò chuyện mới") -> 'Conversation':
        now = datetime.now().isoformat()
        return Conversation(
            id=str(uuid.uuid4()),
            title=title,
            messages=[],
            created_at=now,
            updated_at=now
        )


class MemoryManager:
    """
    Manages conversation memory with:
    - Short-term: Current conversation context
    - Long-term: Persistent conversation history (SQLite)
    """
    
    def __init__(self, db_path: str = MEMORY_DB_PATH):
        self.db_path = db_path
        self._init_database()
        self.current_conversation: Optional[Conversation] = None
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                summary TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation 
            ON messages(conversation_id)
        """)
        
        conn.commit()
        conn.close()
    
    # === Short-term Memory (Current Session) ===
    
    def start_conversation(self, title: str = None) -> Conversation:
        """Start a new conversation session."""
        if title is None:
            title = f"Cuộc trò chuyện {datetime.now().strftime('%d/%m %H:%M')}"
        
        self.current_conversation = Conversation.create_new(title)
        return self.current_conversation
    
    def add_message(self, role: str, content: str) -> Message:
        """Add a message to current conversation."""
        if self.current_conversation is None:
            self.start_conversation()
        
        msg = Message(role=role, content=content)
        self.current_conversation.messages.append(msg)
        self.current_conversation.updated_at = datetime.now().isoformat()
        
        # Auto-update title from first user message
        if role == "user" and len(self.current_conversation.messages) == 1:
            self.current_conversation.title = content[:50] + ("..." if len(content) > 50 else "")
        
        return msg
    
    def get_context(self, max_turns: int = 5) -> List[Dict]:
        """Get recent conversation context for RAG."""
        if self.current_conversation is None:
            return []
        
        recent = self.current_conversation.messages[-(max_turns * 2):]
        return [{"role": m.role, "content": m.content} for m in recent]
    
    def get_context_summary(self) -> str:
        """Generate a summary of current conversation for context."""
        if not self.current_conversation or not self.current_conversation.messages:
            return "Chưa có lịch sử hội thoại."
        
        context_parts = []
        for msg in self.current_conversation.messages[-6:]:  # Last 6 messages
            role = "Người dùng" if msg.role == "user" else "Trợ lý"
            content = msg.content[:200] + ("..." if len(msg.content) > 200 else "")
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    # === Long-term Memory (Persistent Storage) ===
    
    def save_conversation(self) -> bool:
        """Save current conversation to database."""
        if not self.current_conversation or not self.current_conversation.messages:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Upsert conversation
            cursor.execute("""
                INSERT OR REPLACE INTO conversations (id, title, summary, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.current_conversation.id,
                self.current_conversation.title,
                self.current_conversation.summary,
                self.current_conversation.created_at,
                self.current_conversation.updated_at
            ))
            
            # Delete old messages and insert new ones
            cursor.execute("DELETE FROM messages WHERE conversation_id = ?", 
                          (self.current_conversation.id,))
            
            for msg in self.current_conversation.messages:
                cursor.execute("""
                    INSERT INTO messages (conversation_id, role, content, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (self.current_conversation.id, msg.role, msg.content, msg.timestamp))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error saving conversation: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get conversation
            cursor.execute(
                "SELECT id, title, summary, created_at, updated_at FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Get messages
            cursor.execute(
                "SELECT role, content, timestamp FROM messages WHERE conversation_id = ? ORDER BY id",
                (conversation_id,)
            )
            messages = [Message(role=r[0], content=r[1], timestamp=r[2]) for r in cursor.fetchall()]
            
            conversation = Conversation(
                id=row[0],
                title=row[1],
                summary=row[2],
                created_at=row[3],
                updated_at=row[4],
                messages=messages
            )
            
            self.current_conversation = conversation
            return conversation
            
        finally:
            conn.close()
    
    def get_conversation_list(self, limit: int = 20) -> List[Dict]:
        """Get list of recent conversations."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, title, created_at, updated_at,
                       (SELECT COUNT(*) FROM messages WHERE conversation_id = conversations.id) as msg_count
                FROM conversations
                ORDER BY updated_at DESC
                LIMIT ?
            """, (limit,))
            
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "created_at": row[2],
                    "updated_at": row[3],
                    "message_count": row[4]
                }
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            conn.commit()
            
            if self.current_conversation and self.current_conversation.id == conversation_id:
                self.current_conversation = None
            
            return True
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False
        finally:
            conn.close()
    
    def clear_all(self) -> bool:
        """Delete all conversations."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM messages")
            cursor.execute("DELETE FROM conversations")
            conn.commit()
            self.current_conversation = None
            return True
        except Exception as e:
            print(f"Error clearing memory: {e}")
            return False
        finally:
            conn.close()


# Singleton instance
_memory_manager: Optional[MemoryManager] = None

def get_memory_manager() -> MemoryManager:
    """Get singleton memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
