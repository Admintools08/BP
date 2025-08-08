import sys
import os
sys.path.append('/app/backend')

# Import the AI service to test fallback functionality
from server import LearningRecommendationService

def test_fallback_recommendations():
    """Test the fallback recommendations functionality"""
    print("🧪 Testing AI Service Fallback Functionality")
    print("=" * 50)
    
    # Create AI service instance
    ai_service = LearningRecommendationService()
    
    # Test fallback recommendations
    test_user_id = "test-user-123"
    fallback_recs = ai_service._fallback_recommendations(test_user_id)
    
    print(f"📊 Generated {len(fallback_recs)} fallback recommendations")
    
    if len(fallback_recs) > 0:
        print("\n📋 Fallback Recommendations:")
        for i, rec in enumerate(fallback_recs, 1):
            print(f"\n{i}. {rec.get('title', 'N/A')}")
            print(f"   Category: {rec.get('skill_category', 'N/A')}")
            print(f"   Difficulty: {rec.get('difficulty_level', 'N/A')}")
            print(f"   Priority: {rec.get('priority_score', 'N/A')}%")
            print(f"   Hours: {rec.get('estimated_hours', 'N/A')}h")
            print(f"   Description: {rec.get('description', 'N/A')}")
            
            resources = rec.get('recommended_resources', [])
            if resources:
                print(f"   Resources: {', '.join(resources)}")
        
        # Validate structure
        sample_rec = fallback_recs[0]
        required_fields = ['id', 'user_id', 'title', 'description', 'skill_category', 
                         'recommended_resources', 'difficulty_level', 'estimated_hours', 
                         'priority_score', 'created_at']
        missing_fields = [field for field in required_fields if field not in sample_rec]
        
        if missing_fields:
            print(f"\n⚠️  Missing required fields: {missing_fields}")
            return False
        else:
            print(f"\n✅ All required fields present in fallback recommendations")
            return True
    else:
        print("❌ No fallback recommendations generated")
        return False

def test_api_key_detection():
    """Test API key detection"""
    print("\n🔑 Testing API Key Detection")
    print("=" * 30)
    
    ai_service = LearningRecommendationService()
    
    print(f"API Key present: {'Yes' if ai_service.api_key else 'No'}")
    if ai_service.api_key:
        print(f"API Key format: {ai_service.api_key[:10]}...")
        if ai_service.api_key.startswith('sk-'):
            print("✅ Valid OpenAI API key format")
            return True
        else:
            print("❌ Invalid OpenAI API key format (should start with 'sk-')")
            return False
    else:
        print("❌ No API key found")
        return False

def main():
    print("🚀 Testing AI Service Components")
    print("=" * 60)
    
    # Test API key
    api_key_valid = test_api_key_detection()
    
    # Test fallback functionality
    fallback_works = test_fallback_recommendations()
    
    print("\n" + "=" * 60)
    print("📊 AI SERVICE TEST SUMMARY")
    print("=" * 60)
    
    results = [
        ("API Key Format", api_key_valid),
        ("Fallback Recommendations", fallback_works)
    ]
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    if not api_key_valid:
        print("\n🔍 DIAGNOSIS:")
        print("- The OpenAI API key appears to be invalid or in wrong format")
        print("- OpenAI API keys should start with 'sk-'")
        print("- Current key appears to be a Google API key format")
        print("- AI recommendations will not work until valid OpenAI key is provided")
        print("- Fallback recommendations should be used instead")
    
    return 0 if fallback_works else 1

if __name__ == "__main__":
    exit(main())