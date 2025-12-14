"""
Script to rebuild ChromaDB with correct embedding dimensions.
Fixes: "Collection expecting embedding with dimension of 1024, got 1536"
"""
import os
import shutil
from dotenv import load_dotenv
from src.rag_engine import RAGSystem
from src.config import CHROMA_DB_PATH

load_dotenv()

def rebuild_database():
    """Remove old database and create new one with current embedding model."""
    print("🔧 ChromaDB Rebuild Script")
    print("=" * 50)
    
    # Step 1: Remove old database
    if os.path.exists(CHROMA_DB_PATH):
        print(f"\n🗑️  Removing old database at: {CHROMA_DB_PATH}")
        try:
            shutil.rmtree(CHROMA_DB_PATH)
            print("✅ Old database removed successfully")
        except PermissionError:
            print("⚠️  Database is locked. Please close any apps using it.")
            return False
        except Exception as e:
            print(f"❌ Error removing database: {e}")
            return False
    else:
        print(f"\n📂 No existing database found at: {CHROMA_DB_PATH}")
    
    # Step 2: Create new database
    print("\n📊 Creating new database with current embedding model...")
    try:
        rag = RAGSystem()
        print(f"   Using embedding: {type(rag.embeddings).__name__}")
        
        num_chunks = rag.ingest_data()
        
        print(f"\n✅ Database rebuilt successfully!")
        print(f"   📈 Total chunks: {num_chunks}")
        print(f"   💾 Location: {CHROMA_DB_PATH}")
        
        # Step 3: Test the database
        print("\n🧪 Testing database connection...")
        vectorstore = rag.get_vectorstore()
        test_results = vectorstore.similarity_search("HaUI", k=2)
        print(f"✅ Database test successful! Found {len(test_results)} results.")
        
        return True
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("💡 Make sure you have run the scraper first to generate data.")
        print("   Run: python -m src.scraper")
        return False
    except Exception as e:
        print(f"\n❌ Error creating database: {e}")
        return False

if __name__ == "__main__":
    success = rebuild_database()
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 Database rebuild complete!")
        print("\nNext steps:")
        print("  1. Restart your Streamlit app")
        print("  2. Try asking a question")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ Database rebuild failed. Please fix the errors above.")
        print("=" * 50)
