#!/usr/bin/env python3

import requests
import json
import time
from pathlib import Path

class BetaAuthTester:
    def __init__(self, base_url="https://aihub-fix.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}{endpoint}"
        if not headers:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

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

    def setup_beta_settings(self):
        """Setup beta settings for testing"""
        try:
            import pymongo
            from pymongo import MongoClient
            
            client = MongoClient("mongodb://localhost:27017")
            db = client["test_database"]
            
            # Create or update beta settings
            settings_data = {
                "registration_code": "BETA2025",
                "admin_email": "layth.bunni@adamsmithinternational.com",
                "allowed_domain": "adamsmithinternational.com",
                "max_users": 20
            }
            
            # Upsert settings
            db.beta_settings.replace_one({}, settings_data, upsert=True)
            
            # Clean up any existing test users
            db.beta_users.delete_many({"email": {"$regex": "test.*@adamsmithinternational.com"}})
            
            print("✅ Beta settings configured and test data cleaned")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup beta settings: {str(e)}")
            return False

    def test_auth_register_valid(self):
        """Test user registration with valid data"""
        register_data = {
            "email": "test.user@adamsmithinternational.com",
            "registration_code": "BETA2025",
            "personal_code": "testpass123",
            "department": "IT"
        }
        
        success, response = self.run_test("Auth Register (Valid)", "POST", "/auth/register", 200, register_data)
        
        if success:
            print(f"   User ID: {response.get('user', {}).get('id')}")
            print(f"   Email: {response.get('user', {}).get('email')}")
            print(f"   Role: {response.get('user', {}).get('role')}")
            print(f"   Token: {response.get('access_token', '')[:20]}...")
            return success, response.get('access_token'), response.get('user', {})
        
        return success, None, {}

    def test_auth_register_invalid_domain(self):
        """Test user registration with invalid email domain"""
        register_data = {
            "email": "test.user@gmail.com",
            "registration_code": "BETA2025", 
            "personal_code": "testpass123",
            "department": "IT"
        }
        
        return self.run_test("Auth Register (Invalid Domain)", "POST", "/auth/register", 400, register_data)

    def test_auth_register_invalid_code(self):
        """Test user registration with invalid registration code"""
        register_data = {
            "email": "test2.user@adamsmithinternational.com",
            "registration_code": "WRONGCODE",
            "personal_code": "testpass123",
            "department": "IT"
        }
        
        return self.run_test("Auth Register (Invalid Code)", "POST", "/auth/register", 400, register_data)

    def test_auth_register_duplicate_user(self):
        """Test user registration with existing email"""
        register_data = {
            "email": "test.user@adamsmithinternational.com",  # Same as first test
            "registration_code": "BETA2025",
            "personal_code": "testpass123",
            "department": "IT"
        }
        
        return self.run_test("Auth Register (Duplicate User)", "POST", "/auth/register", 400, register_data)

    def test_auth_login_valid(self):
        """Test user login with valid credentials"""
        login_data = {
            "email": "test.user@adamsmithinternational.com",
            "personal_code": "testpass123"
        }
        
        success, response = self.run_test("Auth Login (Valid)", "POST", "/auth/login", 200, login_data)
        
        if success:
            print(f"   User ID: {response.get('user', {}).get('id')}")
            print(f"   Email: {response.get('user', {}).get('email')}")
            print(f"   Last Login: {response.get('user', {}).get('last_login')}")
            print(f"   Token: {response.get('access_token', '')[:20]}...")
            return success, response.get('access_token')
        
        return success, None

    def test_auth_login_invalid_email(self):
        """Test user login with non-existent email"""
        login_data = {
            "email": "nonexistent@adamsmithinternational.com",
            "personal_code": "testpass123"
        }
        
        return self.run_test("Auth Login (Invalid Email)", "POST", "/auth/login", 401, login_data)

    def test_auth_login_invalid_code(self):
        """Test user login with wrong personal code"""
        login_data = {
            "email": "test.user@adamsmithinternational.com",
            "personal_code": "wrongpassword"
        }
        
        return self.run_test("Auth Login (Invalid Code)", "POST", "/auth/login", 401, login_data)

    def test_auth_me_with_token(self, token):
        """Test getting current user info with valid token"""
        if not token:
            print("⚠️  Skipping auth/me test - no token available")
            return True, {}
        
        headers = {'Authorization': f'Bearer {token}'}
        
        success, response = self.run_test("Auth Me (With Token)", "GET", "/auth/me", 200, headers=headers)
        
        if success:
            print(f"   User Email: {response.get('email')}")
            print(f"   User Role: {response.get('role')}")
            print(f"   User Department: {response.get('department')}")
        
        return success, response

    def test_auth_me_without_token(self):
        """Test getting current user info without token"""
        return self.run_test("Auth Me (No Token)", "GET", "/auth/me", 403)

def main():
    print("🔐 Beta Authentication System Testing")
    print("=" * 50)
    
    tester = BetaAuthTester()
    
    # Setup
    print("\n⚙️  Setting up test environment...")
    if not tester.setup_beta_settings():
        print("❌ Failed to setup test environment")
        return 1
    
    # Test user registration
    print("\n📝 Testing User Registration...")
    reg_success, access_token, user_data = tester.test_auth_register_valid()
    tester.test_auth_register_invalid_domain()
    tester.test_auth_register_invalid_code()
    tester.test_auth_register_duplicate_user()
    
    # Test user login
    print("\n🔑 Testing User Login...")
    login_success, login_token = tester.test_auth_login_valid()
    tester.test_auth_login_invalid_email()
    tester.test_auth_login_invalid_code()
    
    # Test authenticated endpoints
    print("\n👤 Testing Authenticated Endpoints...")
    tester.test_auth_me_with_token(login_token if login_success else access_token)
    tester.test_auth_me_without_token()
    
    # Results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All Beta Authentication tests passed!")
        return 0
    else:
        failed_tests = tester.tests_run - tester.tests_passed
        print(f"⚠️  {failed_tests} test(s) failed.")
        return 1

if __name__ == "__main__":
    exit(main())