#!/usr/bin/env python3
"""
Admin User Management API Testing Script
Specifically tests the endpoints mentioned in the review request:
- DELETE /api/admin/users/{user_id}
- PUT /api/admin/users/{user_id}  
- GET /api/admin/users
"""

import requests
import json
import sys
import time

class AdminUserManagementTester:
    def __init__(self, base_url="https://asi-platform.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {name}")
        if details:
            print(f"   {details}")
        self.test_results.append({"name": name, "success": success, "details": details})

    def authenticate_admin(self):
        """Authenticate as admin user (layth.bunni@adamsmithinternational.com)"""
        print("\n🔐 Step 1: Admin Authentication...")
        
        login_data = {
            "email": "layth.bunni@adamsmithinternational.com",
            "personal_code": "ASI2025"
        }
        
        try:
            response = requests.post(f"{self.api_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                user = data.get('user', {})
                
                self.log_test("Admin Authentication", True, 
                    f"Logged in as {user.get('email')} with role {user.get('role')}")
                return True
            else:
                self.log_test("Admin Authentication", False, 
                    f"Login failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Error: {str(e)}")
            return False

    def get_users_list(self):
        """Test GET /api/admin/users - Get list of users"""
        print("\n👥 Step 2: Testing GET /api/admin/users...")
        
        if not self.admin_token:
            self.log_test("Get Users List", False, "No admin token available")
            return []
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        try:
            response = requests.get(f"{self.api_url}/admin/users", headers=headers)
            
            if response.status_code == 200:
                users = response.json()
                self.log_test("Get Users List", True, 
                    f"Retrieved {len(users)} users")
                
                # Show sample user data structure
                if users:
                    sample_user = users[0]
                    print(f"   Sample user structure: {list(sample_user.keys())}")
                    print(f"   Sample user: {sample_user.get('email')} ({sample_user.get('role')})")
                
                return users
            else:
                self.log_test("Get Users List", False, 
                    f"Failed with status {response.status_code}")
                return []
                
        except Exception as e:
            self.log_test("Get Users List", False, f"Error: {str(e)}")
            return []

    def create_test_user(self):
        """Create a test user for management operations"""
        print("\n📝 Step 3: Creating Test User...")
        
        if not self.admin_token:
            self.log_test("Create Test User", False, "No admin token available")
            return None
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        test_user_data = {
            "email": "test.user.delete@example.com",
            "name": "Test User Delete",
            "role": "Agent",
            "department": "IT",
            "is_active": True
        }
        
        try:
            response = requests.post(f"{self.api_url}/admin/users", 
                                   json=test_user_data, headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                user_id = user_data.get('id') or user_data.get('user_id')
                
                self.log_test("Create Test User", True, 
                    f"Created user with ID: {user_id}")
                return user_id
            else:
                # User might already exist, try to find it
                users = self.get_users_list()
                for user in users:
                    if user.get('email') == test_user_data['email']:
                        user_id = user.get('id')
                        self.log_test("Create Test User", True, 
                            f"Found existing user with ID: {user_id}")
                        return user_id
                
                self.log_test("Create Test User", False, 
                    f"Failed with status {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("Create Test User", False, f"Error: {str(e)}")
            return None

    def test_user_role_update(self, user_id):
        """Test PUT /api/admin/users/{user_id} - Update user role"""
        print(f"\n🔄 Step 4: Testing PUT /api/admin/users/{user_id}...")
        
        if not self.admin_token or not user_id:
            self.log_test("User Role Update", False, "Missing admin token or user ID")
            return False
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Update user role from Agent to Manager
        update_data = {
            "role": "Manager",
            "department": "Management", 
            "name": "Test User Updated",
            "is_active": True
        }
        
        try:
            response = requests.put(f"{self.api_url}/admin/users/{user_id}", 
                                  json=update_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("User Role Update", True, 
                    f"Updated user role to Manager: {result}")
                return True
            else:
                self.log_test("User Role Update", False, 
                    f"Failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Role Update", False, f"Error: {str(e)}")
            return False

    def verify_role_update_persistence(self, user_id):
        """Verify the role update persisted by getting user list again"""
        print(f"\n🔍 Step 5: Verifying Role Update Persistence...")
        
        users = self.get_users_list()
        
        for user in users:
            if user.get('id') == user_id:
                current_role = user.get('role')
                if current_role == 'Manager':
                    self.log_test("Role Update Persistence", True, 
                        f"Role successfully updated to Manager")
                    return True
                else:
                    self.log_test("Role Update Persistence", False, 
                        f"Role not updated - still {current_role}")
                    return False
        
        self.log_test("Role Update Persistence", False, "User not found in updated list")
        return False

    def test_user_deletion(self, user_id):
        """Test DELETE /api/admin/users/{user_id} - Delete user"""
        print(f"\n🗑️  Step 6: Testing DELETE /api/admin/users/{user_id}...")
        
        if not self.admin_token or not user_id:
            self.log_test("User Deletion", False, "Missing admin token or user ID")
            return False
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        try:
            response = requests.delete(f"{self.api_url}/admin/users/{user_id}", 
                                     headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("User Deletion", True, 
                    f"User deleted successfully: {result}")
                return True
            else:
                self.log_test("User Deletion", False, 
                    f"Failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Deletion", False, f"Error: {str(e)}")
            return False

    def verify_user_deletion(self, user_id):
        """Verify user was deleted from database"""
        print(f"\n🔍 Step 7: Verifying User Deletion...")
        
        users = self.get_users_list()
        
        for user in users:
            if user.get('id') == user_id:
                self.log_test("User Deletion Verification", False, 
                    "User still exists in database")
                return False
        
        self.log_test("User Deletion Verification", True, 
            "User successfully removed from database")
        return True

    def test_error_cases(self):
        """Test error cases for admin endpoints"""
        print(f"\n⚠️  Step 8: Testing Error Cases...")
        
        if not self.admin_token:
            self.log_test("Error Cases", False, "No admin token available")
            return False
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test 1: Update non-existent user
        fake_user_id = "non-existent-user-12345"
        update_data = {"role": "Manager", "name": "Fake User"}
        
        try:
            response = requests.put(f"{self.api_url}/admin/users/{fake_user_id}", 
                                  json=update_data, headers=headers)
            
            if response.status_code == 404:
                self.log_test("Update Non-existent User", True, 
                    "Correctly returned 404 for non-existent user")
            else:
                self.log_test("Update Non-existent User", False, 
                    f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Update Non-existent User", False, f"Error: {str(e)}")
        
        # Test 2: Delete non-existent user
        try:
            response = requests.delete(f"{self.api_url}/admin/users/{fake_user_id}", 
                                     headers=headers)
            
            if response.status_code == 404:
                self.log_test("Delete Non-existent User", True, 
                    "Correctly returned 404 for non-existent user")
            else:
                self.log_test("Delete Non-existent User", False, 
                    f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Delete Non-existent User", False, f"Error: {str(e)}")
        
        # Test 3: Admin trying to delete themselves (should be prevented)
        # First get admin user ID
        users = self.get_users_list()
        admin_user_id = None
        
        for user in users:
            if user.get('email') == 'layth.bunni@adamsmithinternational.com':
                admin_user_id = user.get('id')
                break
        
        if admin_user_id:
            try:
                response = requests.delete(f"{self.api_url}/admin/users/{admin_user_id}", 
                                         headers=headers)
                
                if response.status_code == 400:
                    self.log_test("Admin Self-Delete Prevention", True, 
                        "Correctly prevented admin from deleting themselves")
                else:
                    self.log_test("Admin Self-Delete Prevention", False, 
                        f"Expected 400, got {response.status_code}")
            except Exception as e:
                self.log_test("Admin Self-Delete Prevention", False, f"Error: {str(e)}")
        
        return True

    def run_all_tests(self):
        """Run all admin user management tests"""
        print("🚀 ADMIN USER MANAGEMENT API TESTING")
        print("=" * 60)
        print("Testing Admin User Management endpoints as specified in review request:")
        print("1. DELETE /api/admin/users/{user_id}")
        print("2. PUT /api/admin/users/{user_id}")
        print("3. GET /api/admin/users")
        print("=" * 60)
        
        # Step 1: Authenticate as admin
        if not self.authenticate_admin():
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Step 2: Get initial users list
        initial_users = self.get_users_list()
        if not initial_users:
            print("❌ Cannot proceed without users list")
            return False
        
        # Step 3: Create test user
        test_user_id = self.create_test_user()
        if not test_user_id:
            print("❌ Cannot proceed without test user")
            return False
        
        # Step 4: Test role update
        role_update_success = self.test_user_role_update(test_user_id)
        
        # Step 5: Verify role update persistence
        role_persistence_success = self.verify_role_update_persistence(test_user_id)
        
        # Step 6: Test user deletion
        deletion_success = self.test_user_deletion(test_user_id)
        
        # Step 7: Verify deletion
        deletion_verification_success = self.verify_user_deletion(test_user_id)
        
        # Step 8: Test error cases
        error_cases_success = self.test_error_cases()
        
        # Final verification - get users list reflects changes
        print(f"\n📊 Step 9: Final Verification...")
        final_users = self.get_users_list()
        
        if final_users is not None:
            self.log_test("Final Users List", True, 
                f"Final user count: {len(final_users)}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 ADMIN USER MANAGEMENT TEST RESULTS")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.test_results if result['success'])
        total_tests = len(self.test_results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {result['name']}")
            if result['details']:
                print(f"     {result['details']}")
        
        # Overall assessment
        critical_tests = [
            "Admin Authentication",
            "Get Users List", 
            "User Role Update",
            "Role Update Persistence",
            "User Deletion",
            "User Deletion Verification"
        ]
        
        critical_passed = all(
            any(r['name'] == test and r['success'] for r in self.test_results)
            for test in critical_tests
        )
        
        if critical_passed:
            print("\n🎉 ALL CRITICAL ADMIN USER MANAGEMENT TESTS PASSED!")
            print("✅ DELETE /api/admin/users/{user_id} - WORKING")
            print("✅ PUT /api/admin/users/{user_id} - WORKING") 
            print("✅ GET /api/admin/users - WORKING")
            print("🚀 Admin User Management APIs are ready for production use!")
            return True
        else:
            print("\n⚠️  SOME CRITICAL TESTS FAILED")
            print("🔧 Admin User Management APIs need attention before production use")
            return False

def main():
    tester = AdminUserManagementTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())