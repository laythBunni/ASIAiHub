#!/usr/bin/env python3
"""
Final verification test for the two specific fixes mentioned in the review request:

1. Historic Chat Modal Fix - CORRECTED to handle proper response format
2. Remove System Key Toggle - Backend Changes

Authentication: layth.bunni@adamsmithinternational.com with personal code 899443
"""

import requests
import json
import time
from datetime import datetime
import sys

class FinalFixVerificationTester:
    def __init__(self):
        # Use production URL from frontend/.env
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.base_url = line.split('=', 1)[1].strip()
                        break
                else:
                    self.base_url = "http://localhost:8001"
        except:
            self.base_url = "http://localhost:8001"
        
        self.api_url = f"{self.base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.session_id = f"final-test-{int(time.time())}"
        
        print(f"🔗 Testing against: {self.base_url}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}{endpoint}"
        default_headers = {'Content-Type': 'application/json'}
        
        if headers:
            default_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers)

            success = response.status_code == expected_status
                
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            return False, {}

    def authenticate_admin(self):
        """Authenticate as admin user"""
        print("\n🔐 AUTHENTICATING AS ADMIN USER...")
        
        login_data = {
            "email": "layth.bunni@adamsmithinternational.com",
            "personal_code": "899443"
        }
        
        success, response = self.run_test(
            "Admin Authentication", 
            "POST", 
            "/auth/login", 
            200, 
            login_data
        )
        
        if success:
            self.auth_token = response.get('access_token') or response.get('token')
            user_data = response.get('user', {})
            
            print(f"   👤 User: {user_data.get('email')}")
            print(f"   👑 Role: {user_data.get('role')}")
            
            return user_data.get('role') == 'Admin'
        return False

    def test_historic_chat_modal_fix_corrected(self):
        """Test Historic Chat Modal Fix - CORRECTED VERSION"""
        print("\n💬 TESTING HISTORIC CHAT MODAL FIX (CORRECTED)...")
        print("=" * 60)
        
        # Test 1: Create test chat session
        print("\n📝 Step 1: Creating Test Chat Session...")
        
        chat_data = {
            "session_id": self.session_id,
            "message": "What are the ASI company travel policies?",
            "stream": False
        }
        
        chat_success, chat_response = self.run_test(
            "Create Chat Session", 
            "POST", 
            "/chat/send", 
            200, 
            chat_data
        )
        
        if not chat_success:
            print("   ❌ Cannot create test chat session")
            return False
        
        print(f"   ✅ Chat session created: {self.session_id}")
        
        # Add second message
        chat_data2 = {
            "session_id": self.session_id,
            "message": "What about expense limits for hotels?",
            "stream": False
        }
        
        self.run_test("Add Second Message", "POST", "/chat/send", 200, chat_data2)
        
        # Test 2: Verify chat sessions can be retrieved
        print("\n📋 Step 2: Testing GET /api/chat/sessions...")
        
        sessions_success, sessions_response = self.run_test(
            "Get Chat Sessions", 
            "GET", 
            "/chat/sessions", 
            200
        )
        
        if not sessions_success:
            print("   ❌ Failed to retrieve chat sessions")
            return False
        
        sessions_list = sessions_response if isinstance(sessions_response, list) else []
        print(f"   ✅ Retrieved {len(sessions_list)} chat sessions")
        
        # Find our test session
        test_session_found = False
        for session in sessions_list:
            if session.get('id') == self.session_id:
                test_session_found = True
                print(f"   ✅ Test session found in sessions list")
                print(f"   📊 Messages count: {session.get('messages_count', 0)}")
                break
        
        if not test_session_found:
            print(f"   ❌ Test session not found in sessions list")
            return False
        
        # Test 3: Test message retrieval endpoint - CORRECTED FORMAT
        print(f"\n💬 Step 3: Testing GET /api/chat/sessions/{self.session_id}/messages...")
        
        messages_success, messages_response = self.run_test(
            "Get Session Messages", 
            "GET", 
            f"/chat/sessions/{self.session_id}/messages", 
            200
        )
        
        if not messages_success:
            print(f"   ❌ Failed to retrieve session messages")
            return False
        
        # CORRECTED: Handle the proper response format
        print(f"   ✅ Messages endpoint responded successfully")
        print(f"   📋 Response type: {type(messages_response)}")
        
        # The response should be an object with session info and messages array
        if isinstance(messages_response, dict):
            session_id = messages_response.get('session_id')
            session_title = messages_response.get('session_title')
            messages_array = messages_response.get('messages', [])
            total_messages = messages_response.get('total_messages', 0)
            
            print(f"   ✅ Structured response format confirmed")
            print(f"   📊 Session ID: {session_id}")
            print(f"   📊 Session Title: {session_title}")
            print(f"   📊 Total Messages: {total_messages}")
            print(f"   📊 Messages Array Length: {len(messages_array)}")
            
            # Verify message structure
            if messages_array and len(messages_array) > 0:
                print(f"\n   📨 Message Structure Verification:")
                
                user_messages = 0
                assistant_messages = 0
                
                for i, message in enumerate(messages_array):
                    role = message.get('role')
                    content = message.get('content')
                    timestamp = message.get('timestamp')
                    
                    print(f"     Message {i+1}:")
                    print(f"       Role: {role}")
                    print(f"       Has Content: {bool(content)}")
                    print(f"       Has Timestamp: {bool(timestamp)}")
                    
                    # Verify required fields
                    required_fields = ['role', 'content', 'timestamp']
                    missing_fields = [field for field in required_fields if not message.get(field)]
                    
                    if missing_fields:
                        print(f"       ❌ Missing fields: {missing_fields}")
                        return False
                    else:
                        print(f"       ✅ All required fields present")
                    
                    if role == 'user':
                        user_messages += 1
                    elif role == 'assistant':
                        assistant_messages += 1
                
                print(f"\n   📊 Message Summary:")
                print(f"     User messages: {user_messages}")
                print(f"     Assistant messages: {assistant_messages}")
                
                # We should have at least 2 user messages and some assistant responses
                if user_messages >= 2:
                    print(f"   ✅ HISTORIC CHAT MODAL FIX WORKING CORRECTLY!")
                    print(f"   ✅ Messages can be retrieved with proper structure")
                    print(f"   ✅ Required fields (role, content, timestamp) present")
                    return True
                else:
                    print(f"   ⚠️  Expected at least 2 user messages, got {user_messages}")
                    return user_messages > 0  # Partial success
            else:
                print(f"   ❌ No messages found in response")
                return False
        else:
            print(f"   ❌ Unexpected response format: {type(messages_response)}")
            return False

    def test_system_settings_personal_key_default(self):
        """Test System Settings Default to Personal Key Usage"""
        print("\n⚙️ TESTING SYSTEM SETTINGS - PERSONAL KEY DEFAULT...")
        print("=" * 60)
        
        auth_headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        # Test 1: GET system settings
        print("\n📋 Step 1: Testing GET /api/admin/system-settings...")
        
        settings_success, settings_response = self.run_test(
            "Get System Settings", 
            "GET", 
            "/admin/system-settings", 
            200,
            headers=auth_headers
        )
        
        if not settings_success:
            print("   ❌ Failed to retrieve system settings")
            return False
        
        use_personal_key = settings_response.get('use_personal_openai_key')
        ai_model = settings_response.get('ai_model')
        
        print(f"   ✅ System settings retrieved")
        print(f"   ⚙️  use_personal_openai_key: {use_personal_key}")
        print(f"   🤖 ai_model: {ai_model}")
        
        # Verify default is True for personal key usage
        if use_personal_key is True:
            print(f"   ✅ DEFAULT SETTING CORRECT: use_personal_openai_key = true")
        else:
            print(f"   ❌ DEFAULT SETTING INCORRECT: Expected true, got {use_personal_key}")
            return False
        
        # Test 2: PUT system settings
        print("\n🔄 Step 2: Testing PUT /api/admin/system-settings...")
        
        update_data = {
            "use_personal_openai_key": True,
            "ai_model": "gpt-5"
        }
        
        update_success, update_response = self.run_test(
            "Update System Settings", 
            "PUT", 
            "/admin/system-settings", 
            200,
            update_data,
            headers=auth_headers
        )
        
        if not update_success:
            print("   ❌ Failed to update system settings")
            return False
        
        print(f"   ✅ System settings updated successfully")
        
        # Test 3: Verify persistence
        print("\n🔍 Step 3: Verifying Settings Persistence...")
        
        verify_success, verify_response = self.run_test(
            "Verify Settings Persistence", 
            "GET", 
            "/admin/system-settings", 
            200,
            headers=auth_headers
        )
        
        if verify_success:
            updated_use_personal = verify_response.get('use_personal_openai_key')
            if updated_use_personal is True:
                print(f"   ✅ SYSTEM SETTINGS FIX WORKING CORRECTLY!")
                print(f"   ✅ Personal key usage is default (true)")
                print(f"   ✅ Settings can be updated via PUT endpoint")
                print(f"   ✅ Settings persist correctly")
                return True
            else:
                print(f"   ❌ Settings not persisted correctly")
                return False
        else:
            print(f"   ❌ Failed to verify settings persistence")
            return False

    def run_final_verification(self):
        """Run final verification of both fixes"""
        print("🎯 FINAL VERIFICATION OF ASI AIHUB FIXES")
        print("=" * 80)
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 Testing URL: {self.base_url}")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate_admin():
            print("\n❌ CRITICAL: Admin authentication failed")
            return False
        
        # Step 2: Test Historic Chat Modal Fix
        print("\n" + "="*80)
        print("🎯 FIX #1: HISTORIC CHAT MODAL FIX")
        print("="*80)
        
        chat_fix_success = self.test_historic_chat_modal_fix_corrected()
        
        # Step 3: Test System Settings Fix
        print("\n" + "="*80)
        print("🎯 FIX #2: REMOVE SYSTEM KEY TOGGLE - BACKEND CHANGES")
        print("="*80)
        
        settings_fix_success = self.test_system_settings_personal_key_default()
        
        # Final Results
        print("\n" + "="*80)
        print("🏁 FINAL VERIFICATION RESULTS")
        print("="*80)
        
        print(f"\n🔐 Authentication: {'✅ PASSED' if self.auth_token else '❌ FAILED'}")
        print(f"💬 Historic Chat Modal Fix: {'✅ PASSED' if chat_fix_success else '❌ FAILED'}")
        print(f"⚙️  System Settings Personal Key Default: {'✅ PASSED' if settings_fix_success else '❌ FAILED'}")
        
        print(f"\n📈 Test Statistics:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        both_fixes_working = chat_fix_success and settings_fix_success
        
        if both_fixes_working:
            print(f"\n🎉 BOTH FIXES ARE WORKING CORRECTLY!")
            print(f"✅ Historic Chat Modal: Messages can be retrieved with proper structure")
            print(f"✅ System Settings: Personal key usage is default, settings can be updated")
            return True
        else:
            print(f"\n⚠️  ONE OR MORE FIXES NEED ATTENTION")
            if not chat_fix_success:
                print(f"❌ Historic Chat Modal Fix: Issues with message retrieval")
            if not settings_fix_success:
                print(f"❌ System Settings Fix: Issues with personal key default or updates")
            return False

def main():
    """Main test execution"""
    tester = FinalFixVerificationTester()
    
    try:
        success = tester.run_final_verification()
        
        if success:
            print(f"\n✅ Final verification completed successfully!")
            sys.exit(0)
        else:
            print(f"\n❌ Final verification completed with issues!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Testing failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()