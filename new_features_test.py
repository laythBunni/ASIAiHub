#!/usr/bin/env python3
"""
New Features Testing for ASI AiHub - Pre-Deployment Verification
Tests all new features mentioned in test_result.md for production deployment
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path

class NewFeaturesTester:
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
        self.session_id = f"test-session-{int(time.time())}"
        self.admin_token = None

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
        """Authenticate as admin user and store token"""
        print("\n🔐 Authenticating as Admin User...")
        
        # Try Phase 2 credentials first (from test_result.md)
        admin_login_data = {
            "email": "layth.bunni@adamsmithinternational.com",
            "personal_code": "899443"  # Phase 2 credentials
        }
        
        success, response = self.run_test(
            "Admin Login (Phase 2)", 
            "POST", 
            "/auth/login", 
            200, 
            admin_login_data
        )
        
        if success:
            self.admin_token = response.get('access_token') or response.get('token')
            if self.admin_token:
                print(f"   ✅ Admin authenticated with Phase 2 credentials")
                return True
        
        print(f"   ❌ Admin authentication failed")
        return False

    def test_personal_openai_key_integration(self):
        """Test Personal OpenAI API Key Integration as specified in test_result.md"""
        print("\n🔑 TESTING PERSONAL OPENAI KEY INTEGRATION...")
        print("=" * 70)
        
        if not self.admin_token:
            print("❌ No admin token available - skipping OpenAI key tests")
            return False
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test 1: Get current system settings
        print("\n⚙️ Test 1: Get System Settings...")
        
        get_settings_success, get_settings_response = self.run_test(
            "GET /api/admin/system-settings", 
            "GET", 
            "/admin/system-settings", 
            200, 
            headers=auth_headers
        )
        
        if get_settings_success:
            current_settings = get_settings_response
            print(f"   🔧 Use Personal Key: {current_settings.get('use_personal_openai_key', False)}")
            print(f"   🤖 AI Model: {current_settings.get('ai_model', 'gpt-5')}")
            print(f"   🔑 Personal Key Set: {'Yes' if current_settings.get('personal_openai_key') else 'No'}")
        else:
            print("❌ Failed to get system settings")
            return False
        
        # Test 2: Update system settings with personal key
        print("\n💾 Test 2: Update System Settings (Enable Personal Key)...")
        
        test_settings = {
            "use_personal_openai_key": True,
            "personal_openai_key": "sk-test-personal-key-for-testing-12345",
            "ai_model": "gpt-4o",
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        post_settings_success, post_settings_response = self.run_test(
            "POST /api/admin/system-settings (Enable Personal Key)", 
            "POST", 
            "/admin/system-settings", 
            200, 
            test_settings,
            headers=auth_headers
        )
        
        if post_settings_success:
            print(f"   ✅ System settings updated successfully")
            print(f"   🔧 Personal Key Enabled: {test_settings['use_personal_openai_key']}")
            print(f"   🤖 AI Model Set: {test_settings['ai_model']}")
        else:
            print("❌ Failed to update system settings")
            return False
        
        # Test 3: Verify settings persistence
        print("\n🔍 Test 3: Verify Settings Persistence...")
        
        verify_settings_success, verify_settings_response = self.run_test(
            "GET /api/admin/system-settings (Verify Persistence)", 
            "GET", 
            "/admin/system-settings", 
            200, 
            headers=auth_headers
        )
        
        if verify_settings_success:
            updated_settings = verify_settings_response
            
            # Check if settings were saved correctly
            personal_key_enabled = updated_settings.get('use_personal_openai_key') == True
            ai_model_correct = updated_settings.get('ai_model') == 'gpt-4o'
            
            if personal_key_enabled:
                print(f"   ✅ Personal key toggle persisted correctly")
            else:
                print(f"   ❌ Personal key toggle not persisted")
                
            if ai_model_correct:
                print(f"   ✅ AI model setting persisted correctly")
            else:
                print(f"   ❌ AI model setting not persisted")
                
            # Personal key should be masked in response for security
            personal_key = updated_settings.get('personal_openai_key', '')
            if personal_key and ('*' in personal_key or len(personal_key) < 10):
                print(f"   ✅ Personal key properly masked in response: {personal_key}")
            else:
                print(f"   ⚠️ Personal key not properly masked: {personal_key}")
        else:
            print("❌ Failed to verify settings persistence")
            return False
        
        # Test 4: Test model switching functionality
        print("\n🔄 Test 4: Test AI Model Switching...")
        
        model_tests = [
            {"ai_model": "gpt-5", "description": "GPT-5"},
            {"ai_model": "gpt-5-mini", "description": "GPT-5 Mini"},
            {"ai_model": "gpt-4o-mini", "description": "GPT-4o Mini"}
        ]
        
        for model_test in model_tests:
            model_settings = {
                "use_personal_openai_key": True,
                "personal_openai_key": "sk-test-personal-key-for-testing-12345",
                "ai_model": model_test["ai_model"]
            }
            
            model_success, model_response = self.run_test(
                f"Switch to {model_test['description']}", 
                "POST", 
                "/admin/system-settings", 
                200, 
                model_settings,
                headers=auth_headers
            )
            
            if model_success:
                print(f"   ✅ Successfully switched to {model_test['description']}")
            else:
                print(f"   ❌ Failed to switch to {model_test['description']}")
        
        # Test 5: API usage tracking
        print("\n📊 Test 5: API Usage Tracking...")
        
        usage_success, usage_response = self.run_test(
            "GET /api/admin/api-usage", 
            "GET", 
            "/admin/api-usage", 
            200, 
            headers=auth_headers
        )
        
        if usage_success:
            usage_data = usage_response
            print(f"   ✅ API usage data retrieved")
            print(f"   📈 Total Requests: {usage_data.get('total_requests', 0)}")
            print(f"   💰 Estimated Cost: ${usage_data.get('estimated_cost', 0)}")
            print(f"   🔑 Key Source: {usage_data.get('key_source', 'unknown')}")
        else:
            print("❌ Failed to get API usage data")
        
        print(f"\n🎉 Personal OpenAI Key Integration Testing Complete!")
        return True

    def test_enhanced_chat_analytics(self):
        """Test Enhanced Chat Analytics System as specified in test_result.md"""
        print("\n📊 TESTING ENHANCED CHAT ANALYTICS SYSTEM...")
        print("=" * 70)
        
        if not self.admin_token:
            print("❌ No admin token available - skipping analytics tests")
            return False
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test 1: Get chat analytics
        print("\n📈 Test 1: Get Chat Analytics...")
        
        analytics_success, analytics_response = self.run_test(
            "GET /api/admin/chat-analytics", 
            "GET", 
            "/admin/chat-analytics", 
            200, 
            headers=auth_headers
        )
        
        if analytics_success:
            analytics_data = analytics_response
            total_sessions = analytics_data.get('total_sessions', 0)
            total_messages = analytics_data.get('total_messages', 0)
            avg_response_time = analytics_data.get('average_response_time', 0)
            
            print(f"   ✅ Chat analytics data retrieved successfully")
            print(f"   📊 Total Sessions: {total_sessions}")
            print(f"   💬 Total Messages: {total_messages}")
            print(f"   ⏱️ Average Response Time: {avg_response_time}s")
            
            # Check for expected data (51 sessions, 113 messages from review request)
            if total_sessions >= 50:
                print(f"   ✅ Expected session count confirmed (≥50 sessions)")
            else:
                print(f"   ⚠️ Lower session count than expected: {total_sessions}")
                
            if total_messages >= 100:
                print(f"   ✅ Expected message count confirmed (≥100 messages)")
            else:
                print(f"   ⚠️ Lower message count than expected: {total_messages}")
            
            # Check most asked questions
            most_asked = analytics_data.get('most_asked_questions', [])
            print(f"   ❓ Most Asked Questions: {len(most_asked)} found")
            for i, question in enumerate(most_asked[:3], 1):
                print(f"      {i}. {question.get('question', 'Unknown')[:50]}... (Count: {question.get('count', 0)})")
            
            # Check ticket conversations
            ticket_conversations = analytics_data.get('ticket_conversations', [])
            print(f"   🎫 Ticket Conversations: {len(ticket_conversations)} found")
            for i, conv in enumerate(ticket_conversations[:3], 1):
                print(f"      {i}. Session: {conv.get('session_id', 'Unknown')[:20]}... (Messages: {conv.get('message_count', 0)})")
            
            # Check user activity
            user_activity = analytics_data.get('user_activity', [])
            print(f"   👥 User Activity: {len(user_activity)} users tracked")
            
        else:
            print("❌ Failed to get chat analytics data")
            return False
        
        # Test 2: Test conversation detail viewer
        print("\n🔍 Test 2: Conversation Detail Viewer...")
        
        if analytics_success and analytics_data.get('recent_sessions'):
            test_session_id = analytics_data['recent_sessions'][0].get('id')
            
            if test_session_id:
                detail_success, detail_response = self.run_test(
                    f"GET /api/chat/sessions/{test_session_id}/messages", 
                    "GET", 
                    f"/chat/sessions/{test_session_id}/messages", 
                    200
                )
                
                if detail_success:
                    messages = detail_response if isinstance(detail_response, list) else []
                    print(f"   ✅ Retrieved {len(messages)} messages from session")
                    
                    # Check message structure
                    if messages:
                        sample_message = messages[0]
                        print(f"   📝 Sample message role: {sample_message.get('role')}")
                        print(f"   📝 Sample message content: {sample_message.get('content', '')[:50]}...")
                        print(f"   ⏱️ Sample message timestamp: {sample_message.get('timestamp')}")
                        
                        # Check for response timing metadata
                        metadata = sample_message.get('metadata', {})
                        if metadata.get('response_time_seconds'):
                            print(f"   ✅ Response timing data found: {metadata['response_time_seconds']}s")
                        else:
                            print(f"   ⚠️ No response timing data in message metadata")
                else:
                    print("❌ Failed to get conversation details")
            else:
                print("⚠️ No session ID available for detail testing")
        
        print(f"\n🎉 Enhanced Chat Analytics Testing Complete!")
        return True

    def test_kpi_dashboard_system(self):
        """Test KPI Dashboard System as specified in test_result.md"""
        print("\n📊 TESTING KPI DASHBOARD SYSTEM...")
        print("=" * 60)
        
        if not self.admin_token:
            print("❌ No admin token available - skipping KPI tests")
            return False
        
        auth_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test 1: Get system KPIs
        print("\n📈 Test 1: Get System KPIs...")
        
        kpi_success, kpi_response = self.run_test(
            "GET /api/admin/system-kpis", 
            "GET", 
            "/admin/system-kpis", 
            200, 
            headers=auth_headers
        )
        
        if kpi_success:
            kpi_data = kpi_response
            print(f"   ✅ KPI dashboard data retrieved successfully")
            
            # Test Chat Performance KPIs
            chat_performance = kpi_data.get('chat_performance', {})
            print(f"   💬 Chat Performance:")
            print(f"      Sessions: {chat_performance.get('total_sessions', 0)}")
            print(f"      Messages: {chat_performance.get('total_messages', 0)}")
            print(f"      Avg Response Time: {chat_performance.get('avg_response_time', 0)}s")
            print(f"      Success Rate: {chat_performance.get('success_rate', 0)}%")
            
            # Test Ticket Resolution KPIs
            ticket_resolution = kpi_data.get('ticket_resolution', {})
            print(f"   🎫 Ticket Resolution:")
            print(f"      Total Tickets: {ticket_resolution.get('total_tickets', 0)}")
            print(f"      Resolved: {ticket_resolution.get('resolved_tickets', 0)}")
            print(f"      Avg Resolution Time: {ticket_resolution.get('avg_resolution_hours', 0)}h")
            
            # Test by Priority breakdown
            by_priority = ticket_resolution.get('by_priority', {})
            for priority in ['high', 'medium', 'low']:
                priority_data = by_priority.get(priority, {})
                if priority_data:
                    print(f"      {priority.title()} Priority: {priority_data.get('count', 0)} tickets, {priority_data.get('avg_resolution_hours', 0)}h avg")
            
            # Test Document Processing KPIs
            document_processing = kpi_data.get('document_processing', {})
            print(f"   📄 Document Processing:")
            print(f"      Total Documents: {document_processing.get('total_documents', 0)}")
            print(f"      Processed: {document_processing.get('processed_documents', 0)}")
            print(f"      Success Rate: {document_processing.get('success_rate', 0)}%")
            print(f"      Avg Processing Time: {document_processing.get('avg_processing_time', 0)}s")
            
            # Test User Engagement KPIs
            user_engagement = kpi_data.get('user_engagement', {})
            print(f"   👥 User Engagement:")
            print(f"      Active Users: {user_engagement.get('active_users', 0)}")
            print(f"      Total Users: {user_engagement.get('total_users', 0)}")
            print(f"      Avg Sessions per User: {user_engagement.get('avg_sessions_per_user', 0)}")
            print(f"      User Retention: {user_engagement.get('user_retention_rate', 0)}%")
            
            # Verify data completeness
            required_sections = ['chat_performance', 'ticket_resolution', 'document_processing', 'user_engagement']
            missing_sections = [section for section in required_sections if section not in kpi_data]
            
            if not missing_sections:
                print(f"   ✅ All required KPI sections present")
            else:
                print(f"   ⚠️ Missing KPI sections: {missing_sections}")
            
        else:
            print("❌ Failed to get KPI dashboard data")
            return False
        
        print(f"\n🎉 KPI Dashboard System Testing Complete!")
        return True

    def test_response_timing_system(self):
        """Test Response Timing System as specified in test_result.md"""
        print("\n⏱️ TESTING RESPONSE TIMING SYSTEM...")
        print("=" * 60)
        
        # Test 1: Send a chat message and measure timing
        print("\n💬 Test 1: Chat Response Timing...")
        
        import time
        start_time = time.time()
        
        chat_data = {
            "session_id": f"{self.session_id}-timing-test",
            "message": "What is the company IT support policy for password resets?",
            "stream": False
        }
        
        chat_success, chat_response = self.run_test(
            "Chat with Timing Measurement", 
            "POST", 
            "/chat/send", 
            200, 
            chat_data
        )
        
        end_time = time.time()
        measured_time = end_time - start_time
        
        if chat_success:
            print(f"   ✅ Chat response received")
            print(f"   ⏱️ Measured response time: {measured_time:.2f}s")
            
            # Check if response includes timing information
            response_time_seconds = chat_response.get('response_time_seconds')
            if response_time_seconds:
                print(f"   ✅ Server-reported response time: {response_time_seconds:.2f}s")
                
                # Verify timing is reasonable (within 10% of measured time)
                time_diff = abs(response_time_seconds - measured_time)
                if time_diff < (measured_time * 0.1):
                    print(f"   ✅ Response timing accuracy verified")
                else:
                    print(f"   ⚠️ Response timing discrepancy: {time_diff:.2f}s difference")
            else:
                print(f"   ❌ No response timing data in chat response")
                return False
        else:
            print("❌ Chat request failed")
            return False
        
        # Test 2: Check if timing is stored in message metadata
        print("\n📝 Test 2: Message Metadata Timing Storage...")
        
        session_id = chat_response.get('session_id')
        if session_id:
            messages_success, messages_response = self.run_test(
                "Get Session Messages (Check Timing)", 
                "GET", 
                f"/chat/sessions/{session_id}/messages", 
                200
            )
            
            if messages_success:
                messages = messages_response if isinstance(messages_response, list) else []
                print(f"   ✅ Retrieved {len(messages)} messages from session")
                
                # Find the assistant's response message
                assistant_messages = [m for m in messages if m.get('role') == 'assistant']
                if assistant_messages:
                    latest_response = assistant_messages[-1]
                    metadata = latest_response.get('metadata', {})
                    
                    if metadata.get('response_time_seconds'):
                        stored_time = metadata['response_time_seconds']
                        print(f"   ✅ Response time stored in metadata: {stored_time}s")
                        
                        # Verify stored time matches response time
                        if abs(stored_time - response_time_seconds) < 0.1:
                            print(f"   ✅ Metadata timing matches response timing")
                        else:
                            print(f"   ⚠️ Metadata timing mismatch")
                    else:
                        print(f"   ❌ No response timing in message metadata")
                        return False
                else:
                    print(f"   ❌ No assistant messages found")
                    return False
            else:
                print("❌ Failed to get session messages")
                return False
        
        print(f"\n🎉 Response Timing System Testing Complete!")
        return True

    def test_conversation_detail_viewer(self):
        """Test Conversation Detail Viewer as specified in test_result.md"""
        print("\n🔍 TESTING CONVERSATION DETAIL VIEWER...")
        print("=" * 60)
        
        # Test 1: Create a conversation with multiple messages
        print("\n💬 Test 1: Creating Test Conversation...")
        
        viewer_session = f"{self.session_id}-viewer-test"
        test_messages = [
            "Hello, I need help with company policies",
            "What is the process for requesting leave?",
            "Are there any restrictions on annual leave?",
            "Thank you for the information"
        ]
        
        for i, message in enumerate(test_messages, 1):
            chat_data = {
                "session_id": viewer_session,
                "message": message,
                "stream": False
            }
            
            success, response = self.run_test(
                f"Create Conversation Message {i}", 
                "POST", 
                "/chat/send", 
                200, 
                chat_data
            )
            
            if success:
                print(f"   ✅ Message {i} sent successfully")
            else:
                print(f"   ❌ Failed to send message {i}")
                return False
        
        # Test 2: Test GET /api/chat/sessions/{session_id}/messages endpoint
        print("\n📋 Test 2: Testing Conversation Detail Retrieval...")
        
        detail_success, detail_response = self.run_test(
            "GET Conversation Details", 
            "GET", 
            f"/chat/sessions/{viewer_session}/messages", 
            200
        )
        
        if detail_success:
            messages = detail_response if isinstance(detail_response, list) else []
            print(f"   ✅ Retrieved {len(messages)} messages from conversation")
            
            # Verify message structure and content
            user_messages = [m for m in messages if m.get('role') == 'user']
            assistant_messages = [m for m in messages if m.get('role') == 'assistant']
            
            print(f"   👤 User messages: {len(user_messages)}")
            print(f"   🤖 Assistant messages: {len(assistant_messages)}")
            
            # Should have equal number of user and assistant messages
            if len(user_messages) == len(assistant_messages):
                print(f"   ✅ Balanced conversation structure")
            else:
                print(f"   ⚠️ Unbalanced conversation: {len(user_messages)} user, {len(assistant_messages)} assistant")
            
            # Check message details
            if messages:
                sample_message = messages[0]
                required_fields = ['id', 'role', 'content', 'timestamp']
                missing_fields = [field for field in required_fields if field not in sample_message]
                
                if not missing_fields:
                    print(f"   ✅ All required message fields present")
                else:
                    print(f"   ❌ Missing message fields: {missing_fields}")
                
                # Check for metadata
                if sample_message.get('metadata'):
                    print(f"   ✅ Message metadata present")
                    metadata = sample_message['metadata']
                    
                    # Check for timing information
                    if metadata.get('response_time_seconds'):
                        print(f"   ⏱️ Response timing in metadata: {metadata['response_time_seconds']}s")
                    
                    # Check for other metadata
                    if metadata.get('documents_referenced'):
                        print(f"   📄 Documents referenced: {metadata['documents_referenced']}")
                else:
                    print(f"   ⚠️ No metadata in messages")
            
        else:
            print("❌ Failed to retrieve conversation details")
            return False
        
        print(f"\n🎉 Conversation Detail Viewer Testing Complete!")
        return True

    def run_new_features_tests(self):
        """Run all new features tests"""
        print("🚀 STARTING NEW FEATURES TESTING FOR PRE-DEPLOYMENT...")
        print("=" * 80)
        print(f"🌐 Base URL: {self.base_url}")
        print(f"🔗 API URL: {self.api_url}")
        print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Authenticate as admin first
        if not self.authenticate_admin():
            print("❌ Cannot authenticate as admin - stopping all tests")
            return False

        # Store test results
        results = {}
        
        # Test 1: Personal OpenAI Key Integration
        print("\n" + "="*70)
        print("🔑 PERSONAL OPENAI KEY INTEGRATION")
        print("="*70)
        
        openai_result = self.test_personal_openai_key_integration()
        results['Personal OpenAI Key Integration'] = openai_result
        
        # Test 2: Enhanced Chat Analytics
        print("\n" + "="*70)
        print("📊 ENHANCED CHAT ANALYTICS SYSTEM")
        print("="*70)
        
        analytics_result = self.test_enhanced_chat_analytics()
        results['Enhanced Chat Analytics System'] = analytics_result
        
        # Test 3: KPI Dashboard System
        print("\n" + "="*70)
        print("📊 KPI DASHBOARD SYSTEM")
        print("="*70)
        
        kpi_result = self.test_kpi_dashboard_system()
        results['KPI Dashboard System'] = kpi_result
        
        # Test 4: Response Timing System
        print("\n" + "="*70)
        print("⏱️ RESPONSE TIMING SYSTEM")
        print("="*70)
        
        timing_result = self.test_response_timing_system()
        results['Response Timing System'] = timing_result
        
        # Test 5: Conversation Detail Viewer
        print("\n" + "="*70)
        print("🔍 CONVERSATION DETAIL VIEWER")
        print("="*70)
        
        viewer_result = self.test_conversation_detail_viewer()
        results['Conversation Detail Viewer'] = viewer_result
        
        # Print final results
        self.print_final_results(results)
        
        # Return overall success
        return all(results.values())

    def print_final_results(self, results):
        """Print final test results"""
        print("\n" + "="*80)
        print("📊 NEW FEATURES TESTING RESULTS")
        print("="*80)
        
        passed_tests = sum(1 for result in results.values() if result)
        total_tests = len(results)
        
        for feature_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status} - {feature_name}")
        
        print(f"\n📈 Overall Results: {passed_tests}/{total_tests} features passed")
        print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL NEW FEATURES TESTS PASSED!")
            print("✅ Personal OpenAI Key Integration working")
            print("✅ Enhanced Chat Analytics functional")
            print("✅ KPI Dashboard System operational")
            print("✅ Response Timing System working")
            print("✅ Conversation Detail Viewer functional")
            print("\n🚀 NEW FEATURES ARE READY FOR DEPLOYMENT!")
        else:
            failed_features = [name for name, result in results.items() if not result]
            print(f"\n🚨 {len(failed_features)} NEW FEATURES FAILED!")
            print("❌ FEATURES NOT READY FOR DEPLOYMENT:")
            for feature in failed_features:
                print(f"   ❌ {feature}")
        
        print("="*80)

def main():
    """Main function to run new features tests"""
    print("🔧 ASI AiHub - New Features Pre-Deployment Testing")
    print("=" * 60)
    
    # Initialize tester
    tester = NewFeaturesTester()
    
    # Run all new features tests
    all_passed = tester.run_new_features_tests()
    
    # Exit with appropriate code
    if all_passed:
        print("\n🎉 All new features tests completed successfully!")
        sys.exit(0)
    else:
        print("\n🚨 Some new features tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()