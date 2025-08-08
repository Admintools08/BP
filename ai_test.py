import requests
import json
from datetime import datetime, timedelta

class AIRecommendationTester:
    def __init__(self, base_url="https://b8f64771-5782-46ef-925f-ec1fb6f9f75c.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.goal_ids = []

    def create_comprehensive_user(self):
        """Create a user with comprehensive profile data"""
        user_data = {
            "full_name": "AI Test User",
            "email": f"aitest_{datetime.now().strftime('%H%M%S')}@example.com",
            "password": "TestPass123!",
            "position": "Senior Software Engineer",
            "department": "Engineering",
            "date_of_joining": "2022-03-15",
            "existing_skills": [
                "Python", "JavaScript", "React", "Node.js", "MongoDB", 
                "Docker", "AWS", "Git", "REST APIs", "SQL"
            ],
            "learning_interests": [
                "Machine Learning", "DevOps", "Leadership", "System Design",
                "Microservices", "Kubernetes", "Data Science", "AI/ML"
            ]
        }
        
        response = requests.post(f"{self.base_url}/api/register", json=user_data)
        if response.status_code == 200:
            result = response.json()
            self.token = result['access_token']
            self.user_id = result['user']['id']
            print(f"✅ Created comprehensive user: {user_data['full_name']}")
            return True
        else:
            print(f"❌ Failed to create user: {response.text}")
            return False

    def create_multiple_goals(self):
        """Create multiple learning goals"""
        goals = [
            {
                "title": "Master Machine Learning",
                "description": "Learn ML algorithms, deep learning, and practical implementation",
                "target_completion": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
            },
            {
                "title": "DevOps and Cloud Architecture",
                "description": "Master Kubernetes, CI/CD, and cloud-native development",
                "target_completion": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
            },
            {
                "title": "Leadership and Team Management",
                "description": "Develop leadership skills and team management capabilities",
                "target_completion": (datetime.now() + timedelta(days=120)).strftime("%Y-%m-%d")
            }
        ]
        
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        
        for goal in goals:
            response = requests.post(f"{self.base_url}/api/goals", json=goal, headers=headers)
            if response.status_code == 200:
                goal_id = response.json()['id']
                self.goal_ids.append(goal_id)
                print(f"✅ Created goal: {goal['title']}")
            else:
                print(f"❌ Failed to create goal: {goal['title']}")
        
        return len(self.goal_ids) > 0

    def create_multiple_milestones(self):
        """Create multiple learning milestones"""
        if not self.goal_ids:
            print("❌ No goals available for milestones")
            return False
            
        milestones = [
            {
                "goal_id": self.goal_ids[0],
                "what_learned": "Python scikit-learn basics and linear regression",
                "learning_source": "Coursera Machine Learning Course",
                "can_teach_others": True,
                "hours_invested": 8.0,
                "project_certificate_link": "https://coursera.org/certificate/ml-basics"
            },
            {
                "goal_id": self.goal_ids[0],
                "what_learned": "Neural networks and backpropagation",
                "learning_source": "Deep Learning Specialization",
                "can_teach_others": False,
                "hours_invested": 12.0,
                "project_certificate_link": "https://coursera.org/certificate/deep-learning"
            },
            {
                "goal_id": self.goal_ids[1] if len(self.goal_ids) > 1 else self.goal_ids[0],
                "what_learned": "Docker containerization and orchestration",
                "learning_source": "Docker Official Documentation",
                "can_teach_others": True,
                "hours_invested": 6.0,
                "project_certificate_link": "https://github.com/user/docker-project"
            },
            {
                "goal_id": self.goal_ids[1] if len(self.goal_ids) > 1 else self.goal_ids[0],
                "what_learned": "Kubernetes deployment and services",
                "learning_source": "Kubernetes in Action book",
                "can_teach_others": False,
                "hours_invested": 15.0
            },
            {
                "goal_id": self.goal_ids[2] if len(self.goal_ids) > 2 else self.goal_ids[0],
                "what_learned": "Agile project management and scrum methodology",
                "learning_source": "Scrum Master Certification",
                "can_teach_others": True,
                "hours_invested": 4.0,
                "project_certificate_link": "https://scrumalliance.org/certificate/123"
            }
        ]
        
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        created_count = 0
        
        for milestone in milestones:
            response = requests.post(f"{self.base_url}/api/milestones", json=milestone, headers=headers)
            if response.status_code == 200:
                created_count += 1
                print(f"✅ Created milestone: {milestone['what_learned'][:50]}...")
            else:
                print(f"❌ Failed to create milestone: {response.text}")
        
        print(f"📊 Created {created_count}/{len(milestones)} milestones")
        return created_count > 0

    def test_ai_recommendations(self):
        """Test AI recommendations with comprehensive data"""
        headers = {'Authorization': f'Bearer {self.token}'}
        
        print("\n🧠 Testing AI Recommendations...")
        response = requests.get(f"{self.base_url}/api/ai-recommendations", headers=headers)
        
        if response.status_code == 200:
            recommendations = response.json()
            print(f"✅ AI Recommendations API working - Status: {response.status_code}")
            print(f"📊 Received {len(recommendations)} recommendations")
            
            if len(recommendations) > 0:
                print("\n📋 AI Recommendations Details:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"\n{i}. {rec.get('title', 'N/A')}")
                    print(f"   Category: {rec.get('skill_category', 'N/A')}")
                    print(f"   Difficulty: {rec.get('difficulty_level', 'N/A')}")
                    print(f"   Priority: {rec.get('priority_score', 'N/A')}%")
                    print(f"   Hours: {rec.get('estimated_hours', 'N/A')}h")
                    print(f"   Description: {rec.get('description', 'N/A')[:100]}...")
                    
                    resources = rec.get('recommended_resources', [])
                    if resources:
                        print(f"   Resources: {', '.join(resources[:2])}...")
                
                # Validate structure
                sample_rec = recommendations[0]
                required_fields = ['id', 'user_id', 'title', 'description', 'skill_category', 
                                 'recommended_resources', 'difficulty_level', 'estimated_hours', 
                                 'priority_score', 'created_at']
                missing_fields = [field for field in required_fields if field not in sample_rec]
                
                if missing_fields:
                    print(f"\n⚠️  Missing required fields: {missing_fields}")
                    return False
                else:
                    print(f"\n✅ All required fields present in recommendations")
                    return True
            else:
                print("⚠️  No recommendations generated - checking fallback...")
                return False
        else:
            print(f"❌ AI Recommendations failed - Status: {response.status_code}")
            print(f"Error: {response.text}")
            return False

    def test_refresh_recommendations(self):
        """Test refreshing AI recommendations"""
        headers = {'Authorization': f'Bearer {self.token}'}
        
        print("\n🔄 Testing AI Recommendations Refresh...")
        response = requests.post(f"{self.base_url}/api/ai-recommendations/refresh", headers=headers)
        
        if response.status_code == 200:
            recommendations = response.json()
            print(f"✅ Refresh AI Recommendations API working - Status: {response.status_code}")
            print(f"📊 Refreshed {len(recommendations)} recommendations")
            return len(recommendations) > 0
        else:
            print(f"❌ Refresh failed - Status: {response.status_code}")
            print(f"Error: {response.text}")
            return False

def main():
    print("🚀 Starting Comprehensive AI Recommendations Test")
    print("=" * 60)
    
    tester = AIRecommendationTester()
    
    # Step 1: Create comprehensive user
    if not tester.create_comprehensive_user():
        print("❌ Failed to create user, stopping test")
        return 1
    
    # Step 2: Create multiple goals
    if not tester.create_multiple_goals():
        print("❌ Failed to create goals, stopping test")
        return 1
    
    # Step 3: Create multiple milestones
    if not tester.create_multiple_milestones():
        print("❌ Failed to create milestones, stopping test")
        return 1
    
    # Step 4: Test AI recommendations
    ai_success = tester.test_ai_recommendations()
    
    # Step 5: Test refresh functionality
    refresh_success = tester.test_refresh_recommendations()
    
    print("\n" + "=" * 60)
    print("📊 AI RECOMMENDATIONS TEST SUMMARY")
    print("=" * 60)
    
    results = [
        ("User Creation", True),
        ("Goals Creation", True),
        ("Milestones Creation", True),
        ("AI Recommendations", ai_success),
        ("Refresh Recommendations", refresh_success)
    ]
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n📈 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if ai_success and refresh_success:
        print("🎉 AI Recommendations feature is working correctly!")
        return 0
    else:
        print("⚠️  AI Recommendations feature needs attention.")
        return 1

if __name__ == "__main__":
    exit(main())