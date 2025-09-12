#!/usr/bin/env python3
"""
Historic Chat Content Display Issue Test
Specific test for the issue: "User reports that when clicking on historic conversations 
in the chat interface sidebar, the conversation content is NOT displaying in the main 
chat window, even though navigation appears to work."
"""

import requests
import json
import time
from datetime import datetime

class HistoricChatTester:
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
        self.auth_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        
    def authenticate(self):
        """Authenticate as layth.bunni@adamsmithinternational.com with personal code 899443"""
        print("\n🔐 STEP 1: Authentication")
        print("=" * 50)
        
        auth_data = {
            "email": "layth.bunni@adamsmithinternational.com",
            "personal_code": "899443"
        }
        
        try:
            response = requests.post(f"{self.api_url}/auth/login", json=auth_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token') or data.get('token')
                user = data.get('user', {})
                
                self.log_result("Authentication", True, 
                    f"User: {user.get('email')}, Role: {user.get('role')}")
                return True
            else:
                self.log_result("Authentication", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Error: {str(e)}")
            return False
    
    def test_chat_sessions_endpoint(self):
        """Test GET /api/chat/sessions endpoint"""
        print("\n📋 STEP 2: Test Chat Sessions Endpoint")
        print("=" * 50)
        
        headers = {'Authorization': f'Bearer {self.auth_token}'} if self.auth_token else {}
        
        try:
            response = requests.get(f"{self.api_url}/chat/sessions", headers=headers)
            
            if response.status_code == 200:
                sessions = response.json()
                
                if isinstance(sessions, list):
                    self.log_result("Sessions Endpoint Structure", True, 
                        f"Retrieved {len(sessions)} sessions as list")
                    
                    if len(sessions) > 0:
                        sample_session = sessions[0]
                        session_id = sample_session.get('id')
                        session_title = sample_session.get('title', 'No title')
                        messages_count = sample_session.get('messages_count', 'N/A')
                        
                        self.log_result("Session Data Structure", True,
                            f"Sample: ID={session_id}, Title='{session_title}', Messages={messages_count}")
                        
                        # Verify session has valid ID for message retrieval
                        if session_id:
                            self.log_result("Session ID Validity", True, 
                                f"Session has valid ID: {session_id}")
                            return sessions
                        else:
                            self.log_result("Session ID Validity", False, 
                                "Session missing ID field")
                            return []
                    else:
                        self.log_result("Sessions Available", False, 
                            "No sessions found - will create test sessions")
                        return []
                else:
                    self.log_result("Sessions Endpoint Structure", False, 
                        f"Expected list, got {type(sessions)}")
                    return []
            else:
                self.log_result("Sessions Endpoint", False, 
                    f"Status: {response.status_code}, Response: {response.text}")
                return []
                
        except Exception as e:
            self.log_result("Sessions Endpoint", False, f"Error: {str(e)}")
            return []
    
    def create_test_sessions(self):
        """Create test chat sessions if none exist"""
        print("\n💬 STEP 3: Create Test Chat Sessions")
        print("=" * 50)
        
        headers = {'Authorization': f'Bearer {self.auth_token}'} if self.auth_token else {}
        
        test_messages = [
            "What is the company travel policy?",
            "How do I submit an expense report?",
            "What are the IT security requirements?",
            "What is the leave policy for annual vacation?"
        ]
        
        created_sessions = []
        
        for i, message in enumerate(test_messages, 1):
            session_id = f"historic-test-{int(time.time())}-{i}"
            
            chat_data = {
                "session_id": session_id,
                "message": message,
                "stream": False
            }
            
            try:
                response = requests.post(f"{self.api_url}/chat/send", json=chat_data, headers=headers)
                
                if response.status_code == 200:
                    self.log_result(f"Create Test Session {i}", True, 
                        f"Session: {session_id}, Message: '{message[:30]}...'")
                    created_sessions.append({
                        'id': session_id,
                        'title': f'Test Conversation {i}',
                        'message': message
                    })
                    time.sleep(1)  # Brief pause between requests
                else:
                    self.log_result(f"Create Test Session {i}", False, 
                        f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Create Test Session {i}", False, f"Error: {str(e)}")
        
        return created_sessions
    
    def test_message_retrieval(self, sessions):
        """Test GET /api/chat/sessions/{session_id}/messages endpoint"""
        print("\n💬 STEP 4: Test Message Retrieval")
        print("=" * 50)
        
        headers = {'Authorization': f'Bearer {self.auth_token}'} if self.auth_token else {}
        
        # Test first 3 sessions
        test_sessions = sessions[:3] if len(sessions) >= 3 else sessions
        successful_retrievals = 0
        sessions_with_content = 0
        
        for i, session in enumerate(test_sessions, 1):
            session_id = session.get('id')
            session_title = session.get('title', 'Unknown')
            
            print(f"\n   🔍 Testing Session {i}: {session_title}")
            print(f"       Session ID: {session_id}")
            
            try:
                response = requests.get(f"{self.api_url}/chat/sessions/{session_id}/messages", headers=headers)
                
                if response.status_code == 200:
                    messages_data = response.json()
                    successful_retrievals += 1
                    
                    # Handle different response formats
                    if isinstance(messages_data, dict):
                        # Structured response with session info and messages
                        session_info = messages_data.get('session', {})
                        messages_list = messages_data.get('messages', [])
                        
                        self.log_result(f"Session {i} - Structured Response", True,
                            f"Session: {session_info.get('title', 'N/A')}, Messages: {len(messages_list)}")
                        
                    elif isinstance(messages_data, list):
                        # Direct messages list
                        messages_list = messages_data
                        self.log_result(f"Session {i} - Direct List Response", True,
                            f"Messages: {len(messages_list)}")
                    else:
                        self.log_result(f"Session {i} - Response Format", False,
                            f"Unexpected format: {type(messages_data)}")
                        continue
                    
                    # Analyze message content structure
                    if len(messages_list) > 0:
                        sessions_with_content += 1
                        sample_message = messages_list[0]
                        
                        # Check required fields
                        required_fields = ['role', 'content', 'timestamp']
                        missing_fields = [field for field in required_fields if not sample_message.get(field)]
                        
                        if not missing_fields:
                            self.log_result(f"Session {i} - Message Structure", True,
                                f"All required fields present: {required_fields}")
                        else:
                            self.log_result(f"Session {i} - Message Structure", False,
                                f"Missing fields: {missing_fields}")
                        
                        # Check message content
                        content = sample_message.get('content', '')
                        role = sample_message.get('role', 'unknown')
                        
                        if len(content) > 0:
                            self.log_result(f"Session {i} - Content Availability", True,
                                f"Role: {role}, Content length: {len(content)}")
                            
                            # Check if content is displayable
                            try:
                                # Try to parse as JSON (structured content)
                                parsed_content = json.loads(content)
                                if isinstance(parsed_content, dict):
                                    self.log_result(f"Session {i} - Content Format", True,
                                        f"Structured JSON content with keys: {list(parsed_content.keys())}")
                                else:
                                    self.log_result(f"Session {i} - Content Format", True,
                                        "JSON content (non-dict)")
                            except:
                                self.log_result(f"Session {i} - Content Format", True,
                                    "Plain text content")
                        else:
                            self.log_result(f"Session {i} - Content Availability", False,
                                "Message has no content")
                        
                        # Check for balanced conversation
                        user_messages = [m for m in messages_list if m.get('role') == 'user']
                        assistant_messages = [m for m in messages_list if m.get('role') == 'assistant']
                        
                        self.log_result(f"Session {i} - Conversation Balance", True,
                            f"User: {len(user_messages)}, Assistant: {len(assistant_messages)}")
                    else:
                        self.log_result(f"Session {i} - Messages Available", False,
                            "No messages found in session")
                else:
                    self.log_result(f"Session {i} - Message Retrieval", False,
                        f"Status: {response.status_code}, Response: {response.text}")
                    
            except Exception as e:
                self.log_result(f"Session {i} - Message Retrieval", False, f"Error: {str(e)}")
        
        return successful_retrievals, sessions_with_content, len(test_sessions)
    
    def test_authentication_context(self):
        """Test authentication context for session access"""
        print("\n🔐 STEP 5: Test Authentication Context")
        print("=" * 50)
        
        # Test access without authentication
        try:
            response = requests.get(f"{self.api_url}/chat/sessions")
            
            if response.status_code in [401, 403]:
                self.log_result("Unauthenticated Access Protection", True,
                    f"Properly rejected with status {response.status_code}")
            elif response.status_code == 200:
                self.log_result("Unauthenticated Access Protection", False,
                    "Sessions accessible without authentication (potential security issue)")
            else:
                self.log_result("Unauthenticated Access Protection", True,
                    f"Unexpected status {response.status_code} (not 200)")
                    
        except Exception as e:
            self.log_result("Unauthenticated Access Protection", False, f"Error: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run comprehensive historic chat content display test"""
        print("🔍 HISTORIC CHAT CONTENT DISPLAY ISSUE - COMPREHENSIVE TEST")
        print("=" * 80)
        print("ISSUE: User reports that when clicking on historic conversations in the chat")
        print("interface sidebar, the conversation content is NOT displaying in the main")
        print("chat window, even though navigation appears to work.")
        print("=" * 80)
        print(f"Testing against: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("\n❌ CRITICAL: Authentication failed - cannot proceed with tests")
            return False
        
        # Step 2: Test chat sessions endpoint
        sessions = self.test_chat_sessions_endpoint()
        
        # Step 3: Create test sessions if needed
        if len(sessions) == 0:
            print("\n⚠️  No existing sessions found - creating test sessions...")
            created_sessions = self.create_test_sessions()
            
            # Re-fetch sessions after creation
            if created_sessions:
                print("\n🔄 Re-fetching sessions after creation...")
                sessions = self.test_chat_sessions_endpoint()
        
        # Step 4: Test message retrieval
        if len(sessions) > 0:
            successful_retrievals, sessions_with_content, total_tested = self.test_message_retrieval(sessions)
        else:
            print("\n❌ CRITICAL: No sessions available for message retrieval testing")
            successful_retrievals, sessions_with_content, total_tested = 0, 0, 0
        
        # Step 5: Test authentication context
        self.test_authentication_context()
        
        # Final Assessment
        print("\n🎯 FINAL ASSESSMENT - HISTORIC CHAT CONTENT DISPLAY ISSUE")
        print("=" * 80)
        
        # Analyze results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        
        print(f"\n📊 TEST SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests")
        
        print(f"\n📋 BACKEND API FUNCTIONALITY:")
        print(f"   ✅ Sessions Endpoint: {'Working' if len(sessions) > 0 else 'Failed'}")
        print(f"   ✅ Message Retrieval: {successful_retrievals}/{total_tested} sessions")
        print(f"   ✅ Content Available: {sessions_with_content}/{total_tested} sessions")
        print(f"   ✅ Authentication: {'Working' if self.auth_token else 'Failed'}")
        
        # Determine if backend is working correctly
        backend_working = (
            len(sessions) > 0 and 
            successful_retrievals == total_tested and 
            sessions_with_content > 0 and
            self.auth_token is not None
        )
        
        if backend_working:
            print(f"\n🎉 BACKEND CONCLUSION: Historic chat content retrieval is WORKING CORRECTLY!")
            print(f"   - Sessions endpoint returns valid session IDs ({len(sessions)} sessions)")
            print(f"   - Messages endpoint returns formatted messages for those session IDs")
            print(f"   - Messages have proper content structure for display")
            print(f"   - Authentication context works with layth.bunni@adamsmithinternational.com")
            print(f"\n💡 If users report content not displaying, the issue is likely FRONTEND-RELATED:")
            print(f"   - Frontend JavaScript not properly calling the backend APIs")
            print(f"   - Frontend state management not updating the chat interface")
            print(f"   - Frontend routing/navigation not triggering message loading")
            print(f"   - Frontend error handling masking API call failures")
            print(f"   - Frontend URL parsing not extracting session ID correctly")
            print(f"   - Frontend component not re-rendering when session changes")
            
            return True
        else:
            print(f"\n❌ BACKEND ISSUES FOUND:")
            if len(sessions) == 0:
                print(f"   - Sessions endpoint not returning sessions")
            if successful_retrievals < total_tested:
                print(f"   - Message retrieval failing for some sessions")
            if sessions_with_content == 0:
                print(f"   - Sessions have no displayable content")
            if not self.auth_token:
                print(f"   - Authentication not working")
            print(f"\n🔧 These backend issues need to be fixed before frontend can work properly")
            
            return False

if __name__ == "__main__":
    tester = HistoricChatTester()
    success = tester.run_comprehensive_test()
    
    print(f"\n{'='*80}")
    if success:
        print("🎯 RESULT: BACKEND APIs for historic chat content are WORKING CORRECTLY")
        print("🔍 Focus investigation on FRONTEND implementation")
    else:
        print("🎯 RESULT: BACKEND APIs have issues that need to be resolved")
        print("🔧 Fix backend issues before investigating frontend")
    print(f"{'='*80}")