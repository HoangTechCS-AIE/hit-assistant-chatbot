"""
Test script to verify embedding consistency between RAG system and database viewer.
"""
import sys
from src.rag_engine import RAGSystem
from src.config import USE_VIETNAMESE_EMBEDDING

def test_embedding_consistency():
    """Test that embeddings are consistent."""
    print("🧪 Testing Embedding Consistency...")
    print("=" * 50)
    
    try:
        # Initialize RAG system
        rag = RAGSystem()
        print(f"✅ RAG system initialized")
        
        # Check embedding type
        embedding_type = type(rag.embeddings).__name__
        print(f"📊 Embedding type: {embedding_type}")
        print(f"⚙️  Config USE_VIETNAMESE_EMBEDDING: {USE_VIETNAMESE_EMBEDDING}")
        
        # Test embedding dimension
        print("\n🔍 Testing embedding dimension...")
        test_text = "Đại học Công nghiệp Hà Nội"
        test_vector = rag.embeddings.embed_query(test_text)
        actual_dim = len(test_vector)
        
        print(f"📏 Actual dimension: {actual_dim}")
        
        # Validate
        if USE_VIETNAMESE_EMBEDDING:
            expected_dim = 1024
            if "HuggingFace" not in embedding_type:
                print(f"⚠️  WARNING: Config says Vietnamese but using {embedding_type}")
        else:
            expected_dim = 1536
            if "OpenAI" not in embedding_type:
                print(f"⚠️  WARNING: Config says OpenAI but using {embedding_type}")
        
        if actual_dim == expected_dim:
            print(f"✅ PASS: Dimension matches expected {expected_dim}")
        else:
            print(f"❌ FAIL: Expected {expected_dim} but got {actual_dim}")
            return False
        
        # Test vectorstore connection
        print("\n🗄️  Testing vector database connection...")
        try:
            vectorstore = rag.get_vectorstore()
            collection = vectorstore._collection
            count = collection.count()
            print(f"✅ Connected to database: {count} documents")
            
            # Test search
            print("\n🔎 Testing search functionality...")
            results = vectorstore.similarity_search("HaUI", k=2)
            print(f"✅ Search returned {len(results)} results")
            
            if results:
                print(f"   Sample result: {results[0].metadata.get('title', 'N/A')[:50]}...")
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            print("💡 Run: python rebuild_db.py")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_embedding_consistency()
    sys.exit(0 if success else 1)
