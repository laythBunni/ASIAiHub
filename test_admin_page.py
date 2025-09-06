#!/usr/bin/env python3

import requests
import json

class AdminPageTester:
    def __init__(self, base_url="https://aihub-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None

    def authenticate_as_layth(self):
        """Authenticate as Layth using Phase 2 credentials"""
        print("🔐 Authenticating as Layth with Phase 2 credentials...")
        
        login_data = {
            "email": "layth.bunni@adamsmithinternational.com",
            "personal_code": "899443"
        }
        
        try:
            response = requests.post(f"{self.api_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                user = data.get('user', {})
                
                print(f"✅ Authentication successful")
                print(f"   User: {user.get('email')}")
                print(f"   Role: {user.get('role')}")
                print(f"   Token: {self.admin_token[:20] if self.admin_token else 'None'}...")
                
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False

    def test_admin_endpoints(self):
        """Test admin endpoints that the admin page uses"""
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        print("\n📊 Testing Admin Page Endpoints...")
        
        # Test 1: /admin/users
        print("\n1️⃣ Testing GET /admin/users...")
        try:
            response = requests.get(f"{self.api_url}/admin/users", headers=headers)
            
            if response.status_code == 200:
                users = response.json()
                print(f"   ✅ Success: Retrieved {len(users)} users")
                
                # Check if users have required fields
                if users:
                    sample_user = users[0]
                    required_fields = ['id', 'email', 'name', 'role']
                    missing_fields = [field for field in required_fields if field not in sample_user]
                    
                    if missing_fields:
                        print(f"   ⚠️  Missing fields in user data: {missing_fields}")
                    else:
                        print(f"   ✅ User data structure looks good")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
        
        # Test 2: /admin/stats
        print("\n2️⃣ Testing GET /admin/stats...")
        try:
            response = requests.get(f"{self.api_url}/admin/stats", headers=headers)
            
            if response.status_code == 200:
                stats = response.json()
                print(f"   ✅ Success: Retrieved system stats")
                print(f"   📊 Stats: {json.dumps(stats, indent=2)}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
                # This might not exist, let's check fallback endpoints
                print("   🔄 Testing fallback endpoints...")
                
                # Test boost tickets
                tickets_response = requests.get(f"{self.api_url}/boost/tickets", headers=headers)
                if tickets_response.status_code == 200:
                    tickets = tickets_response.json()
                    print(f"   ✅ Fallback: Retrieved {len(tickets)} tickets")
                else:
                    print(f"   ❌ Fallback tickets failed: {tickets_response.status_code}")
                
                # Test documents
                docs_response = requests.get(f"{self.api_url}/documents?show_all=true", headers=headers)
                if docs_response.status_code == 200:
                    docs = docs_response.json()
                    print(f"   ✅ Fallback: Retrieved {len(docs)} documents")
                else:
                    print(f"   ❌ Fallback documents failed: {docs_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        # Test 3: /boost/business-units
        print("\n3️⃣ Testing GET /boost/business-units...")
        try:
            response = requests.get(f"{self.api_url}/boost/business-units", headers=headers)
            
            if response.status_code == 200:
                units = response.json()
                print(f"   ✅ Success: Retrieved {len(units)} business units")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        return True

    def test_admin_page_functionality(self):
        """Test complete admin page functionality"""
        print("\n🔍 TESTING ADMIN PAGE FUNCTIONALITY")
        print("=" * 50)
        
        # Step 1: Authenticate
        if not self.authenticate_as_layth():
            return False
        
        # Step 2: Test endpoints
        if not self.test_admin_endpoints():
            return False
        
        print("\n✅ Admin page endpoints testing completed")
        return True

def main():
    tester = AdminPageTester()
    
    success = tester.test_admin_page_functionality()
    
    if success:
        print("\n🎉 Admin page testing completed successfully!")
        print("✅ No critical errors found in admin endpoints")
    else:
        print("\n❌ Admin page testing failed!")
        print("⚠️  Issues found that may cause admin page errors")

if __name__ == "__main__":
    main()