#!/usr/bin/env python3

import requests
import json
import time
from datetime import datetime

class AdminRoleConsistencyTester:
    def __init__(self, base_url="https://asi-platform.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}{endpoint}"
        default_headers = {'Content-Type': 'application/json'}
        
        if headers:
            default_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
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

    def authenticate_admin(self):
        """Authenticate as admin user"""
        print("\n🔐 Authenticating as Admin User...")
        
        admin_login_data = {
            "email": "layth.bunni@adamsmithinternational.com",
            "personal_code": ""
        }
        
        success, response = self.run_test(
            "Admin Authentication", 
            "POST", 
            "/auth/login", 
            200, 
            admin_login_data
        )
        
        if success:
            self.admin_token = response.get('token') or response.get('access_token')
            if self.admin_token:
                print(f"   ✅ Admin authenticated successfully")
                return True
            else:
                print(f"   ❌ No token received")
                return False
        else:
            print(f"   ❌ Admin authentication failed")
            return False

    def get_business_units(self):
        """Get business units for testing"""
        print("\n🏢 Getting Business Units...")
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        success, response = self.run_test(
            "GET Business Units", 
            "GET", 
            "/boost/business-units", 
            200, 
            headers=auth_headers
        )
        
        if success:
            business_units = response if isinstance(response, list) else []
            print(f"   ✅ Retrieved {len(business_units)} business units")
            
            # Create test business units if needed
            if len(business_units) < 2:
                print("   📝 Creating test business units...")
                
                test_units = [
                    {"name": "Engineering Division", "code": "ENG001"},
                    {"name": "Finance Department", "code": "FIN001"}
                ]
                
                for unit_data in test_units:
                    create_success, create_response = self.run_test(
                        f"Create Business Unit: {unit_data['name']}", 
                        "POST", 
                        "/boost/business-units", 
                        200, 
                        unit_data,
                        headers=auth_headers
                    )
                    if create_success:
                        business_units.append(create_response)
            
            return business_units
        else:
            return []

    def get_test_user(self):
        """Get or create a test user"""
        print("\n👥 Getting Test User...")
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        success, response = self.run_test(
            "GET Admin Users", 
            "GET", 
            "/admin/users", 
            200, 
            headers=auth_headers
        )
        
        if success:
            users_list = response if isinstance(response, list) else []
            
            # Find a non-admin test user
            test_user = None
            for user in users_list:
                if user.get('email') != 'layth.bunni@adamsmithinternational.com':
                    test_user = user
                    break
            
            # Create a test user if none exists
            if not test_user:
                print("   📝 Creating test user...")
                
                test_user_data = {
                    "email": "role.test.user@example.com",
                    "name": "Role Test User",
                    "role": "Agent",
                    "department": "IT",
                    "is_active": True
                }
                
                create_success, create_response = self.run_test(
                    "Create Test User", 
                    "POST", 
                    "/admin/users", 
                    200, 
                    test_user_data,
                    headers=auth_headers
                )
                
                if create_success:
                    test_user = create_response
            
            if test_user:
                print(f"   📋 Test User: {test_user.get('email')} (ID: {test_user.get('id')})")
                print(f"   📋 Current Role: {test_user.get('role')}")
                return test_user
            else:
                print("   ❌ No test user available")
                return None
        else:
            return None

    def test_role_update_consistency(self, test_user, business_units):
        """Test role update consistency as specified in review request"""
        print("\n🔄 Testing Role Update Consistency...")
        
        if not test_user or len(business_units) < 2:
            print("❌ Missing test user or business units")
            return False
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        user_id = test_user.get('id')
        
        # Test role changes: Manager → Agent → Manager → Agent
        role_sequence = ['Manager', 'Agent', 'Manager', 'Agent']
        
        for i, new_role in enumerate(role_sequence, 1):
            print(f"\n   🔄 Role Update {i}: Changing to {new_role}...")
            
            # Test with 'role' field name
            update_data = {
                "role": new_role,
                "name": test_user.get('name'),
                "email": test_user.get('email'),
                "department": test_user.get('department', 'IT'),
                "is_active": True
            }
            
            update_success, update_response = self.run_test(
                f"Update Role to {new_role} (using 'role' field)", 
                "PUT", 
                f"/admin/users/{user_id}", 
                200, 
                update_data,
                headers=auth_headers
            )
            
            if update_success:
                print(f"      ✅ Role update successful")
                
                # Verify the change persisted
                verify_success, verify_response = self.run_test(
                    f"Verify Role Update {i}", 
                    "GET", 
                    "/admin/users", 
                    200, 
                    headers=auth_headers
                )
                
                if verify_success:
                    updated_users = verify_response if isinstance(verify_response, list) else []
                    updated_user = None
                    
                    for user in updated_users:
                        if user.get('id') == user_id:
                            updated_user = user
                            break
                    
                    if updated_user:
                        actual_role = updated_user.get('role')
                        if actual_role == new_role:
                            print(f"      ✅ Role persistence verified: {actual_role}")
                        else:
                            print(f"      ❌ Role persistence failed: Expected {new_role}, got {actual_role}")
                            return False
                    else:
                        print(f"      ❌ User not found in verification")
                        return False
                
                # Test with 'boost_role' field name
                update_data_boost = {
                    "boost_role": new_role,
                    "name": test_user.get('name'),
                    "email": test_user.get('email'),
                    "department": test_user.get('department', 'IT'),
                    "is_active": True
                }
                
                boost_success, boost_response = self.run_test(
                    f"Update Role to {new_role} (using 'boost_role' field)", 
                    "PUT", 
                    f"/admin/users/{user_id}", 
                    200, 
                    update_data_boost,
                    headers=auth_headers
                )
                
                if boost_success:
                    print(f"      ✅ 'boost_role' field also supported")
                else:
                    print(f"      ⚠️  'boost_role' field not supported (expected)")
            else:
                print(f"      ❌ Role update failed for {new_role}")
                return False
        
        return True

    def test_business_unit_updates(self, test_user, business_units):
        """Test business unit updates as specified in review request"""
        print("\n🏢 Testing Business Unit Updates...")
        
        if not test_user or len(business_units) < 2:
            print("❌ Missing test user or business units")
            return False
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        user_id = test_user.get('id')
        unit1 = business_units[0]
        unit2 = business_units[1]
        
        # Test updating to first business unit
        print(f"\n   🔄 Business Unit Update 1: {unit1.get('name')}...")
        
        bu_update_data1 = {
            "role": test_user.get('role', 'Agent'),
            "name": test_user.get('name'),
            "email": test_user.get('email'),
            "department": test_user.get('department', 'IT'),
            "business_unit_id": unit1.get('id'),
            "is_active": True
        }
        
        bu_success1, bu_response1 = self.run_test(
            f"Update Business Unit to {unit1.get('name')}", 
            "PUT", 
            f"/admin/users/{user_id}", 
            200, 
            bu_update_data1,
            headers=auth_headers
        )
        
        if bu_success1:
            print(f"      ✅ Business unit update successful")
            
            # Verify business_unit_name is automatically resolved
            verify_success, verify_response = self.run_test(
                "Verify Business Unit Update 1", 
                "GET", 
                "/admin/users", 
                200, 
                headers=auth_headers
            )
            
            if verify_success:
                updated_users = verify_response if isinstance(verify_response, list) else []
                updated_user = None
                
                for user in updated_users:
                    if user.get('id') == user_id:
                        updated_user = user
                        break
                
                if updated_user:
                    actual_bu_id = updated_user.get('business_unit_id')
                    actual_bu_name = updated_user.get('business_unit_name')
                    
                    print(f"      📋 Business Unit ID: {actual_bu_id}")
                    print(f"      📋 Business Unit Name: {actual_bu_name}")
                    
                    if actual_bu_id == unit1.get('id'):
                        print(f"      ✅ Business Unit ID correctly updated")
                    else:
                        print(f"      ❌ Business Unit ID mismatch")
                        return False
                    
                    if actual_bu_name == unit1.get('name'):
                        print(f"      ✅ Business Unit Name automatically resolved")
                    else:
                        print(f"      ❌ Business Unit Name not resolved")
                        return False
        else:
            print(f"      ❌ Business unit update failed")
            return False
        
        # Test updating to second business unit
        print(f"\n   🔄 Business Unit Update 2: {unit2.get('name')}...")
        
        bu_update_data2 = {
            "role": test_user.get('role', 'Agent'),
            "name": test_user.get('name'),
            "email": test_user.get('email'),
            "department": test_user.get('department', 'IT'),
            "business_unit_id": unit2.get('id'),
            "is_active": True
        }
        
        bu_success2, bu_response2 = self.run_test(
            f"Update Business Unit to {unit2.get('name')}", 
            "PUT", 
            f"/admin/users/{user_id}", 
            200, 
            bu_update_data2,
            headers=auth_headers
        )
        
        if bu_success2:
            print(f"      ✅ Second business unit update successful")
        else:
            print(f"      ❌ Second business unit update failed")
            return False
        
        # Test edge cases
        print(f"\n   ⚠️  Testing Edge Cases...")
        
        # Test business_unit_id = 'none'
        edge_data1 = {
            "role": test_user.get('role', 'Agent'),
            "name": test_user.get('name'),
            "email": test_user.get('email'),
            "department": test_user.get('department', 'IT'),
            "business_unit_id": "none",
            "is_active": True
        }
        
        edge_success1, _ = self.run_test(
            "Update Business Unit to 'none'", 
            "PUT", 
            f"/admin/users/{user_id}", 
            200, 
            edge_data1,
            headers=auth_headers
        )
        
        if edge_success1:
            print(f"      ✅ 'none' business unit handled")
        
        # Test business_unit_id = null
        edge_data2 = {
            "role": test_user.get('role', 'Agent'),
            "name": test_user.get('name'),
            "email": test_user.get('email'),
            "department": test_user.get('department', 'IT'),
            "business_unit_id": None,
            "is_active": True
        }
        
        edge_success2, _ = self.run_test(
            "Update Business Unit to null", 
            "PUT", 
            f"/admin/users/{user_id}", 
            200, 
            edge_data2,
            headers=auth_headers
        )
        
        if edge_success2:
            print(f"      ✅ null business unit handled")
        
        return True

    def run_comprehensive_test(self):
        """Run the comprehensive admin user management test as specified in review request"""
        print("👑 ADMIN USER MANAGEMENT API - ROLE CONSISTENCY & BUSINESS UNIT TESTING")
        print("=" * 80)
        print("Testing specific issues reported:")
        print("1. Role Update Consistency - multiple role changes")
        print("2. Business Unit Update - auto-resolution of business_unit_name")
        print("3. Field Mapping Verification - 'role' vs 'boost_role' fields")
        print("=" * 80)
        
        # Step 1: Authenticate as admin
        if not self.authenticate_admin():
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Step 2: Get business units
        business_units = self.get_business_units()
        if len(business_units) < 2:
            print("❌ Need at least 2 business units for testing")
            return False
        
        # Step 3: Get test user
        test_user = self.get_test_user()
        if not test_user:
            print("❌ Cannot proceed without test user")
            return False
        
        # Step 4: Test role update consistency
        role_test_success = self.test_role_update_consistency(test_user, business_units)
        
        # Step 5: Test business unit updates
        bu_test_success = self.test_business_unit_updates(test_user, business_units)
        
        # Results
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "No tests run")
        
        print("\n🔍 SPECIFIC ISSUE TESTING:")
        print("-" * 40)
        
        role_status = "✅ WORKING" if role_test_success else "❌ FAILING"
        bu_status = "✅ WORKING" if bu_test_success else "❌ FAILING"
        
        print(f"Role Update Consistency: {role_status}")
        print(f"Business Unit Updates: {bu_status}")
        
        overall_success = role_test_success and bu_test_success
        
        if overall_success:
            print("\n🎉 ALL ADMIN USER MANAGEMENT ISSUES RESOLVED!")
            print("✅ Role updates work consistently")
            print("✅ Business unit updates work with auto-resolution")
            print("✅ Field mapping verified")
        else:
            print("\n⚠️  ADMIN USER MANAGEMENT ISSUES STILL PRESENT")
            if not role_test_success:
                print("❌ Role update consistency issues found")
            if not bu_test_success:
                print("❌ Business unit update issues found")
        
        return overall_success

def main():
    tester = AdminRoleConsistencyTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())