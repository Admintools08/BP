import requests
import sys
import json
from datetime import datetime, timedelta

class LearningTrackerAPITester:
    def __init__(self, base_url="https://b8f64771-5782-46ef-925f-ec1fb6f9f75c.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_goal_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test user registration"""
        test_user_data = {
            "full_name": "Test User",
            "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
            "password": "TestPass123!",
            "position": "Software Developer",
            "department": "Engineering",
            "date_of_joining": "2024-01-15",
            "existing_skills": ["Python", "JavaScript", "React"],
            "learning_interests": ["Machine Learning", "DevOps", "Leadership"]
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "api/register",
            200,
            data=test_user_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_user_login(self):
        """Test user login with existing credentials"""
        login_data = {
            "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "User Login",
            "POST", 
            "api/login",
            200,
            data=login_data
        )
        return success

    def test_get_profile(self):
        """Test getting user profile"""
        success, response = self.run_test(
            "Get User Profile",
            "GET",
            "api/profile",
            200
        )
        return success

    def test_create_goal(self):
        """Test creating a learning goal"""
        goal_data = {
            "title": "Master React Hooks",
            "description": "Learn advanced React concepts including custom hooks and performance optimization",
            "target_completion": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        }
        
        success, response = self.run_test(
            "Create Learning Goal",
            "POST",
            "api/goals",
            200,
            data=goal_data
        )
        
        if success and 'id' in response:
            self.created_goal_id = response['id']
            print(f"   Goal ID: {self.created_goal_id}")
            return True
        return False

    def test_get_goals(self):
        """Test getting user goals"""
        success, response = self.run_test(
            "Get User Goals",
            "GET",
            "api/goals",
            200
        )
        return success

    def test_create_milestone(self):
        """Test creating a learning milestone"""
        if not self.created_goal_id:
            print("❌ Cannot create milestone - no goal ID available")
            return False
            
        milestone_data = {
            "goal_id": self.created_goal_id,
            "what_learned": "React useState and useEffect hooks",
            "learning_source": "React Documentation",
            "can_teach_others": True,
            "hours_invested": 3.5,
            "project_certificate_link": "https://example.com/certificate"
        }
        
        success, response = self.run_test(
            "Create Learning Milestone",
            "POST",
            "api/milestones",
            200,
            data=milestone_data
        )
        return success

    def test_get_current_month_progress(self):
        """Test getting current month progress"""
        success, response = self.run_test(
            "Get Current Month Progress",
            "GET",
            "api/milestones/current-month",
            200
        )
        
        if success:
            print(f"   Progress: {response.get('progress_percentage', 0):.1f}%")
            print(f"   Hours: {response.get('total_hours', 0)}/{response.get('target_hours', 6)}")
        
        return success

    def test_get_dashboard_stats(self):
        """Test getting dashboard statistics"""
        success, response = self.run_test(
            "Get Dashboard Stats",
            "GET",
            "api/dashboard/stats",
            200
        )
        
        if success:
            print(f"   Active Goals: {response.get('active_goals', 0)}")
            print(f"   Total Milestones: {response.get('total_milestones', 0)}")
            print(f"   Total Hours: {response.get('total_hours', 0)}")
        
        return success

    def test_get_resources(self):
        """Test getting auto-generated resources"""
        success, response = self.run_test(
            "Get Learning Resources",
            "GET",
            "api/resources",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} resources")
        
        return success

def main():
    print("🚀 Starting Learning Tracker API Tests")
    print("=" * 50)
    
    tester = LearningTrackerAPITester()
    
    # Test sequence
    test_results = []
    
    # Authentication tests
    test_results.append(("User Registration", tester.test_user_registration()))
    
    if not tester.token:
        print("\n❌ Registration failed, cannot continue with authenticated tests")
        return 1
    
    test_results.append(("Get Profile", tester.test_get_profile()))
    
    # Goals tests
    test_results.append(("Create Goal", tester.test_create_goal()))
    test_results.append(("Get Goals", tester.test_get_goals()))
    
    # Milestones tests
    test_results.append(("Create Milestone", tester.test_create_milestone()))
    test_results.append(("Current Month Progress", tester.test_get_current_month_progress()))
    
    # Dashboard and resources tests
    test_results.append(("Dashboard Stats", tester.test_get_dashboard_stats()))
    test_results.append(("Learning Resources", tester.test_get_resources()))
    
    # Print final results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"\n📈 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the API implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())