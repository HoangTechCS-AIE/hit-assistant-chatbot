"""
Test script to validate domain filtering in HaUI Chatbot.
Tests both in-domain (should answer) and out-domain (should politely decline) questions.
"""
from src.rag_engine import RAGSystem

def test_domain_filter():
    """Test that chatbot correctly filters domain."""
    print("🧪 Testing Domain Filter")
    print("=" * 60)
    
    rag = RAGSystem()
    
    # Test cases: in-domain (should answer)
    in_domain_questions = [
        "SICT có những ngành nào?",
        "Học phí HaUI năm 2025 là bao nhiêu?",
        "Điều kiện xét tuyển vào trường?",
        "Có những học bổng nào?",
        "Địa chỉ trường ở đâu?"
    ]
    
    # Test cases: out-domain (should decline)
    out_domain_questions = [
        "Giải phương trình x² + 5x + 6 = 0",
        "Thủ đô của Việt Nam là gì?",
        "Viết code Python tính giai thừa",
        "2 + 2 bằng mấy?",
        "Ai là tổng thống Mỹ?"
    ]
    
    # Test in-domain questions
    print("\n✅ Testing IN-DOMAIN Questions (Should Answer):")
    print("-" * 60)
    
    for i, question in enumerate(in_domain_questions, 1):
        print(f"\n{i}. Q: {question}")
        try:
            answer, sources = rag.answer_with_sources(question)
            print(f"   A: {answer[:150]}...")
            
            # Check that it didn't decline
            decline_keywords = ["xin lỗi", "không thể", "ngoài phạm vi", "chuyên môn"]
            has_decline = any(kw in answer.lower() for kw in decline_keywords)
            
            if has_decline:
                print("   ⚠️  WARNING: Declined in-domain question!")
            else:
                print("   ✅ PASS: Answered correctly")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    # Test out-domain questions
    print("\n\n❌ Testing OUT-DOMAIN Questions (Should Decline):")
    print("-" * 60)
    
    for i, question in enumerate(out_domain_questions, 1):
        print(f"\n{i}. Q: {question}")
        try:
            answer, sources = rag.answer_with_sources(question)
            print(f"   A: {answer[:200]}...")
            
            # Check that it DID decline
            decline_keywords = ["xin lỗi", "không thể", "chuyên về", "phạm vi"]
            has_decline = any(kw in answer.lower() for kw in decline_keywords)
            
            if has_decline:
                print("   ✅ PASS: Politely declined")
            else:
                print("   ⚠️  WARNING: Should have declined but answered!")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Domain filter testing complete!")
    print("\nNote: Review answers above to ensure quality.")
    print("=" * 60)

if __name__ == "__main__":
    test_domain_filter()
