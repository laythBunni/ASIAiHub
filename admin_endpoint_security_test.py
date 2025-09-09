#!/usr/bin/env python3
"""
Admin Endpoint Security Test
CRITICAL SECURITY VERIFICATION: Test admin endpoint protection fix

This test verifies the security fix for /api/documents/admin endpoint as specified in review request:
1. Test /api/documents/admin WITHOUT authentication (should get 401/403)
2. Test /api/documents/admin WITH admin authentication (should work)
3. Test /api/documents/admin WITH regular user authentication (should get 403)
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path

class AdminEndpointSecurityTester:
    def __init__(self, base_url=None):
        # Use production URL from frontend/.env for testing
        if base_url is None:
            try:
                with open('/app/frontend/.env', 'r') as f:
                    for line in f:
                        if line.startswith('REACT_APP_BACKEND_URL='):
                            base_url = line.split('=', 1)[1].strip()
                            break
                if not base_url:
                    base_url = "http://localhost:8001"  # Fallback
            except:
                base_url = "http://localhost:8001"  # Fallback
        
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None
        self.regular_token = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}{endpoint}"
        default_headers = {'Content-Type': 'application/json'} if not files else {}
        
        # Merge with provided headers
        if headers:
            default_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, data=data, headers=headers or {})
                else:
                    response = requests.post(url, json=data, headers=default_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers)

            # Handle multiple expected status codes
            if isinstance(expected_status, list):
                success = response.status_code in expected_status
            else:
                success = response.status_code == expected_status
                
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    else:
                        print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                expected_str = str(expected_status) if not isinstance(expected_status, list) else f"one of {expected_status}"
                print(f"❌ Failed - Expected {expected_str}, got {response.status_code}")
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
            "personal_code": "899443"  # Phase 2 credentials
        }
        
        success, response = self.run_test(
            "Admin Authentication", 
            "POST", 
            "/auth/login", 
            200, 
            admin_login_data
        )
        
        if success:
            self.admin_token = response.get('access_token') or response.get('token')
            user_data = response.get('user', {})
            
            print(f"   👤 Admin User: {user_data.get('email')}")
            print(f"   👑 Role: {user_data.get('role')}")
            print(f"   🔑 Token: {self.admin_token[:20] if self.admin_token else 'None'}...")
            
            return self.admin_token is not None
        
        return False

    def authenticate_regular_user(self):
        """Authenticate as regular (non-admin) user"""
        print("\n👤 Authenticating as Regular User...")
        
        # Try to create/login a regular user
        regular_login_data = {
            "email": "test.regular.user@example.com",
            "access_code": "ASI2025"  # This should create a Manager user, not Admin
        }
        
        success, response = self.run_test(
            "Regular User Authentication", 
            "POST", 
            "/auth/login", 
            200, 
            regular_login_data
        )
        
        if success:
            self.regular_token = response.get('access_token') or response.get('token')
            user_data = response.get('user', {})
            
            print(f"   👤 Regular User: {user_data.get('email')}")
            print(f"   👤 Role: {user_data.get('role')}")
            print(f"   🔑 Token: {self.regular_token[:20] if self.regular_token else 'None'}...")
            
            return self.regular_token is not None
        
        return False

    def test_unauthenticated_access(self):
        """Test 1: Access /api/documents/admin WITHOUT authentication (should get 401/403)"""
        print("\n🚫 TEST 1: Unauthenticated Access (Should be Blocked)...")
        
        success, response = self.run_test(
            "GET /api/documents/admin (No Auth)", 
            "GET", 
            "/documents/admin", 
            [401, 403]  # Should be unauthorized or forbidden
        )
        
        if success:
            print(f"   ✅ SECURITY FIX WORKING: Unauthenticated access properly blocked")
            print(f"   🚫 Endpoint correctly requires authentication")
            return True
        else:
            print(f"   ❌ CRITICAL SECURITY FLAW: Unauthenticated access allowed!")
            print(f"   ⚠️  Anyone can access admin documents without credentials")
            return False

    def test_admin_authenticated_access(self):
        """Test 2: Access /api/documents/admin WITH admin authentication (should work)"""
        print("\n👑 TEST 2: Admin Authentication (Should Work)...")
        
        if not self.admin_token:
            print("❌ No admin token available - cannot test admin access")
            return False
        
        admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        success, response = self.run_test(
            "GET /api/documents/admin (With Admin Auth)", 
            "GET", 
            "/documents/admin", 
            200,
            headers=admin_headers
        )
        
        if success:
            print(f"   ✅ ADMIN ACCESS WORKING: Admin can access documents/admin endpoint")
            
            # Verify response contains document list
            if isinstance(response, list):
                print(f"   📋 Retrieved {len(response)} documents from admin endpoint")
                
                # Show sample document info if available
                if len(response) > 0:
                    sample_doc = response[0]
                    print(f"   📄 Sample document: {sample_doc.get('original_name', 'Unknown')}")
                    print(f"   🏷️  Approval status: {sample_doc.get('approval_status', 'Unknown')}")
                    print(f"   🏢 Department: {sample_doc.get('department', 'Unknown')}")
            else:
                print(f"   ⚠️  Unexpected response format from admin endpoint")
            
            return True
        else:
            print(f"   ❌ ADMIN ACCESS FAILED: Admin cannot access documents/admin endpoint")
            return False

    def test_regular_user_access(self):
        """Test 3: Access /api/documents/admin WITH regular user authentication (should get 403)"""
        print("\n👤 TEST 3: Regular User Authentication (Should be Denied)...")
        
        if not self.regular_token:
            print("⚠️  No regular user token available - skipping regular user access test")
            return True  # Not a failure, just can't test this scenario
        
        regular_headers = {'Authorization': f'Bearer {self.regular_token}'}
        
        success, response = self.run_test(
            "GET /api/documents/admin (With Regular User Auth)", 
            "GET", 
            "/documents/admin", 
            403,  # Should be forbidden for non-admin users
            headers=regular_headers
        )
        
        if success:
            print(f"   ✅ SECURITY FIX WORKING: Regular user access properly denied (403)")
            print(f"   🚫 Non-admin users cannot access admin documents")
            return True
        else:
            print(f"   ❌ SECURITY ISSUE: Regular user can access admin documents!")
            print(f"   ⚠️  Non-admin users should not have admin access")
            return False

    def test_invalid_token_handling(self):
        """Test 4: Test with invalid/malformed tokens"""
        print("\n🔑 TEST 4: Invalid Token Handling...")
        
        invalid_tokens = [
            "Bearer invalid_token_12345",
            "Bearer ",
            "InvalidFormat token123",
            ""
        ]
        
        all_passed = True
        
        for i, invalid_token in enumerate(invalid_tokens, 1):
            if invalid_token:
                invalid_headers = {'Authorization': invalid_token}
            else:
                invalid_headers = {}  # No Authorization header
            
            success, response = self.run_test(
                f"Invalid Token Test {i}", 
                "GET", 
                "/documents/admin", 
                [401, 403],  # Should be unauthorized/forbidden
                headers=invalid_headers
            )
            
            if success:
                print(f"   ✅ Invalid token {i} properly rejected")
            else:
                print(f"   ❌ Invalid token {i} not properly rejected")
                all_passed = False
        
        return all_passed

    def test_public_endpoint_still_works(self):
        """Test 5: Verify public documents endpoint still works"""
        print("\n🌐 TEST 5: Public Documents Endpoint (Should Still Work)...")
        
        success, response = self.run_test(
            "GET /api/documents (Public Access)", 
            "GET", 
            "/documents", 
            200
        )
        
        if success:
            print(f"   ✅ Public documents endpoint working correctly")
            
            if isinstance(response, list):
                print(f"   📋 Public documents available: {len(response)}")
                
                # Verify these are only approved documents
                if len(response) > 0:
                    sample_public_doc = response[0]
                    approval_status = sample_public_doc.get('approval_status', 'Unknown')
                    print(f"   ✅ Sample public document approval status: {approval_status}")
            else:
                print(f"   ⚠️  Unexpected response format from public documents endpoint")
            
            return True
        else:
            print(f"   ❌ Public documents endpoint not working")
            return False

    def run_all_security_tests(self):
        """Run all admin endpoint security tests"""
        print("🔒 CRITICAL SECURITY TEST: Admin Endpoint Protection...")
        print("=" * 70)
        print("VERIFYING SECURITY FIX - TEST ADMIN ENDPOINT PROTECTION")
        print("=" * 70)
        
        results = []
        
        # Test 1: Unauthenticated access (should be blocked)
        results.append(self.test_unauthenticated_access())
        
        # Authenticate users for subsequent tests
        admin_auth_success = self.authenticate_admin()
        regular_auth_success = self.authenticate_regular_user()
        
        # Test 2: Admin authenticated access (should work)
        if admin_auth_success:
            results.append(self.test_admin_authenticated_access())
        else:
            print("❌ Cannot authenticate admin - skipping admin access test")
            results.append(False)
        
        # Test 3: Regular user access (should be denied)
        if regular_auth_success:
            results.append(self.test_regular_user_access())
        else:
            print("⚠️  Cannot authenticate regular user - skipping regular user test")
            results.append(True)  # Not a failure
        
        # Test 4: Invalid token handling
        results.append(self.test_invalid_token_handling())
        
        # Test 5: Public endpoint still works
        results.append(self.test_public_endpoint_still_works())
        
        return all(results)

if __name__ == "__main__":
    tester = AdminEndpointSecurityTester()
    
    print("🚀 Starting Admin Endpoint Security Test...")
    print(f"📡 Base URL: {tester.base_url}")
    print(f"🔗 API URL: {tester.api_url}")
    print("=" * 80)
    
    try:
        # Run all security tests
        all_passed = tester.run_all_security_tests()
        
        # Final Results
        print("\n" + "=" * 80)
        print("🏁 ADMIN ENDPOINT SECURITY TEST COMPLETE")
        print("=" * 80)
        print(f"📊 Tests Run: {tester.tests_run}")
        print(f"✅ Tests Passed: {tester.tests_passed}")
        print(f"❌ Tests Failed: {tester.tests_run - tester.tests_passed}")
        
        if all_passed and tester.tests_passed == tester.tests_run:
            print("\n🎉 ALL SECURITY TESTS PASSED!")
            print("✅ Unauthenticated Access: Properly blocked (401/403)")
            print("✅ Admin Access: Working correctly (200 with document list)")
            print("✅ Regular User Access: Properly denied (403)")
            print("✅ Invalid Token Handling: Properly rejected (401/403)")
            print("✅ Public Endpoint: Still accessible for approved documents")
            print("\n🔒 SECURITY FIX VERIFIED - ADMIN ENDPOINT IS PROTECTED!")
        else:
            print(f"\n⚠️  {tester.tests_run - tester.tests_passed} tests failed")
            print("❌ SECURITY ISSUES DETECTED - ADMIN ENDPOINT MAY NOT BE PROPERLY PROTECTED!")
            
            if tester.tests_run - tester.tests_passed > 0:
                print("\n🚨 CRITICAL SECURITY RECOMMENDATIONS:")
                print("1. Ensure /api/documents/admin endpoint has require_admin dependency")
                print("2. Verify authentication middleware is properly applied")
                print("3. Test with different user roles to confirm access control")
                print("4. Check that only Admin role users can access admin endpoints")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Testing failed with error: {str(e)}")
        import traceback
        traceback.print_exc()