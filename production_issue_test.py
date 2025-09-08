#!/usr/bin/env python3
"""
PRODUCTION ISSUE INVESTIGATION TEST
==================================

This test specifically investigates the two critical production issues:
1. Document Upload Issue: Files upload but don't appear in approval list
2. Chat Loading Issue: Conversations from James chat don't load into chat space

The test will identify the exact root cause of these API call issues.
"""

import requests
import json
import time
import tempfile
import os
from pathlib import Path
from datetime import datetime

class ProductionIssueInvestigator:
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
        self.session_id = f"test-session-{int(time.time())}"
        self.test_results = []
        
        print(f"🔍 PRODUCTION ISSUE INVESTIGATION")
        print(f"=" * 60)
        print(f"Backend URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print(f"Test Session ID: {self.session_id}")
        print(f"=" * 60)

    def log_result(self, test_name, success, details):
        """Log test result for final summary"""
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")

    def make_request(self, method, endpoint, data=None, files=None, headers=None):
        """Make HTTP request and return response with detailed logging"""
        url = f"{self.api_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers or {})
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, data=data, headers=headers or {})
                else:
                    response = requests.post(url, json=data, headers=headers or {'Content-Type': 'application/json'})
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers or {'Content-Type': 'application/json'})
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers or {})
            
            print(f"    {method} {url} -> {response.status_code}")
            
            try:
                response_data = response.json()
                return response.status_code, response_data
            except:
                return response.status_code, response.text
                
        except Exception as e:
            print(f"    ERROR: {str(e)}")
            return None, str(e)

    def investigate_document_upload_issue(self):
        """
        ISSUE 1: Document Upload Issue
        Files upload but don't appear in approval list
        
        Test Flow:
        1. Upload a test document via POST /documents/upload
        2. Check if document appears in GET /documents/admin (admin endpoint)
        3. Verify document database record has correct approval_status
        4. Test if admin can see pending documents for approval
        """
        print(f"\n🔍 INVESTIGATING DOCUMENT UPLOAD ISSUE")
        print(f"-" * 50)
        
        # Step 1: Create test document
        test_content = f"""
ASI Test Document - {datetime.now().isoformat()}

This is a test document uploaded to investigate the production issue
where documents upload successfully but don't appear in the admin approval list.

Document Details:
- Upload Time: {datetime.now()}
- Test Session: {self.session_id}
- Purpose: Production Issue Investigation

Content:
This document contains test policy information for verification purposes.
All employees should follow proper procedures when uploading documents.
"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            # Step 2: Upload document
            print(f"\n📤 Step 1: Uploading test document...")
            
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test_upload_document.txt', f, 'text/plain')}
                data = {
                    'department': 'Information Technology',
                    'tags': 'test,production-issue,investigation'
                }
                
                status_code, response = self.make_request('POST', '/documents/upload', data=data, files=files)
            
            if status_code == 200:
                document_id = response.get('id')
                filename = response.get('filename')
                message = response.get('message')
                
                self.log_result(
                    "Document Upload API", 
                    True, 
                    f"Document uploaded: ID={document_id}, File={filename}, Message='{message}'"
                )
                
                # Step 3: Check if document appears in admin list
                print(f"\n📋 Step 2: Checking admin document list...")
                
                admin_status, admin_response = self.make_request('GET', '/documents/admin')
                
                if admin_status == 200:
                    admin_docs = admin_response if isinstance(admin_response, list) else []
                    
                    # Look for our uploaded document
                    uploaded_doc = None
                    for doc in admin_docs:
                        if doc.get('id') == document_id:
                            uploaded_doc = doc
                            break
                    
                    if uploaded_doc:
                        approval_status = uploaded_doc.get('approval_status')
                        department = uploaded_doc.get('department')
                        file_size = uploaded_doc.get('file_size')
                        upload_date = uploaded_doc.get('uploaded_at')
                        
                        self.log_result(
                            "Document in Admin List", 
                            True, 
                            f"Found in admin list: Status={approval_status}, Dept={department}, Size={file_size}B"
                        )
                        
                        # Step 4: Verify approval status is correct
                        if approval_status == 'pending_approval':
                            self.log_result(
                                "Document Approval Status", 
                                True, 
                                "Document correctly has 'pending_approval' status"
                            )
                        else:
                            self.log_result(
                                "Document Approval Status", 
                                False, 
                                f"Expected 'pending_approval', got '{approval_status}'"
                            )
                        
                        # Step 5: Check if document appears in regular documents list (should NOT appear until approved)
                        print(f"\n📄 Step 3: Checking regular documents list (should be empty)...")
                        
                        regular_status, regular_response = self.make_request('GET', '/documents')
                        
                        if regular_status == 200:
                            regular_docs = regular_response if isinstance(regular_response, list) else []
                            
                            # Look for our document (should NOT be there)
                            doc_in_regular = any(doc.get('id') == document_id for doc in regular_docs)
                            
                            if not doc_in_regular:
                                self.log_result(
                                    "Document Not in Regular List", 
                                    True, 
                                    "Document correctly hidden from regular list until approved"
                                )
                            else:
                                self.log_result(
                                    "Document Not in Regular List", 
                                    False, 
                                    "Document incorrectly appears in regular list before approval"
                                )
                        else:
                            self.log_result(
                                "Regular Documents API", 
                                False, 
                                f"Failed to get regular documents: {regular_status}"
                            )
                        
                        # Step 6: Test document approval workflow
                        print(f"\n✅ Step 4: Testing document approval...")
                        
                        approve_status, approve_response = self.make_request(
                            'PUT', 
                            f'/documents/{document_id}/approve',
                            data={'approved_by': 'test_admin'}
                        )
                        
                        if approve_status == 200:
                            self.log_result(
                                "Document Approval", 
                                True, 
                                "Document approved successfully"
                            )
                            
                            # Verify document now appears in regular list
                            time.sleep(1)  # Brief delay for database update
                            
                            regular_status, regular_response = self.make_request('GET', '/documents')
                            
                            if regular_status == 200:
                                regular_docs = regular_response if isinstance(regular_response, list) else []
                                doc_in_regular = any(doc.get('id') == document_id for doc in regular_docs)
                                
                                if doc_in_regular:
                                    self.log_result(
                                        "Approved Document in Regular List", 
                                        True, 
                                        "Approved document correctly appears in regular list"
                                    )
                                else:
                                    self.log_result(
                                        "Approved Document in Regular List", 
                                        False, 
                                        "Approved document missing from regular list"
                                    )
                        else:
                            self.log_result(
                                "Document Approval", 
                                False, 
                                f"Failed to approve document: {approve_status}"
                            )
                    
                    else:
                        self.log_result(
                            "Document in Admin List", 
                            False, 
                            f"Document ID {document_id} NOT found in admin list of {len(admin_docs)} documents"
                        )
                        
                        # Debug: Show what documents are in the admin list
                        print(f"    DEBUG: Admin list contains {len(admin_docs)} documents:")
                        for i, doc in enumerate(admin_docs[:5]):  # Show first 5
                            print(f"      {i+1}. ID={doc.get('id')}, Name={doc.get('original_name')}, Status={doc.get('approval_status')}")
                
                else:
                    self.log_result(
                        "Admin Documents API", 
                        False, 
                        f"Failed to get admin documents: {admin_status}"
                    )
            
            else:
                self.log_result(
                    "Document Upload API", 
                    False, 
                    f"Upload failed with status {status_code}: {response}"
                )
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def investigate_chat_loading_issue(self):
        """
        ISSUE 2: Chat Loading Issue
        Conversations from James chat don't load into chat space
        
        Test Flow:
        1. Send a test message via POST /chat/send
        2. Check if session is created in GET /chat/sessions
        3. Verify messages are stored via GET /chat/sessions/{id}/messages
        4. Test if frontend can load full conversation
        """
        print(f"\n🔍 INVESTIGATING CHAT LOADING ISSUE")
        print(f"-" * 50)
        
        # Step 1: Send test message to create chat session
        print(f"\n💬 Step 1: Sending test message to create chat session...")
        
        chat_data = {
            "session_id": self.session_id,
            "message": "Hello James, I need help with company policies. Can you tell me about leave management procedures?",
            "document_ids": [],
            "stream": False
        }
        
        status_code, response = self.make_request('POST', '/chat/send', data=chat_data)
        
        if status_code == 200:
            session_id = response.get('session_id')
            ai_response = response.get('response')
            documents_referenced = response.get('documents_referenced', 0)
            response_type = response.get('response_type', 'unknown')
            
            self.log_result(
                "Chat Send API", 
                True, 
                f"Message sent: Session={session_id}, Docs={documents_referenced}, Type={response_type}"
            )
            
            # Step 2: Check if session was created
            print(f"\n📝 Step 2: Checking if chat session was created...")
            
            sessions_status, sessions_response = self.make_request('GET', '/chat/sessions')
            
            if sessions_status == 200:
                sessions = sessions_response if isinstance(sessions_response, list) else []
                
                # Look for our session
                our_session = None
                for session in sessions:
                    if session.get('id') == self.session_id:
                        our_session = session
                        break
                
                if our_session:
                    title = our_session.get('title')
                    messages_count = our_session.get('messages_count', 0)
                    created_at = our_session.get('created_at')
                    updated_at = our_session.get('updated_at')
                    
                    self.log_result(
                        "Chat Session Created", 
                        True, 
                        f"Session found: Title='{title}', Messages={messages_count}, Created={created_at}"
                    )
                    
                    # Step 3: Check if messages are stored
                    print(f"\n💾 Step 3: Checking if messages are stored...")
                    
                    messages_status, messages_response = self.make_request('GET', f'/chat/sessions/{self.session_id}/messages')
                    
                    if messages_status == 200:
                        messages = messages_response if isinstance(messages_response, list) else []
                        
                        # Analyze messages
                        user_messages = [msg for msg in messages if msg.get('role') == 'user']
                        assistant_messages = [msg for msg in messages if msg.get('role') == 'assistant']
                        
                        self.log_result(
                            "Chat Messages Stored", 
                            True, 
                            f"Found {len(messages)} total messages: {len(user_messages)} user, {len(assistant_messages)} assistant"
                        )
                        
                        # Verify message content
                        if user_messages:
                            user_msg = user_messages[0]
                            user_content = user_msg.get('content', '')
                            user_timestamp = user_msg.get('timestamp')
                            
                            if chat_data['message'] in user_content:
                                self.log_result(
                                    "User Message Content", 
                                    True, 
                                    f"User message correctly stored: '{user_content[:50]}...'"
                                )
                            else:
                                self.log_result(
                                    "User Message Content", 
                                    False, 
                                    f"User message content mismatch: Expected '{chat_data['message'][:30]}...', Got '{user_content[:30]}...'"
                                )
                        
                        if assistant_messages:
                            ai_msg = assistant_messages[0]
                            ai_content = ai_msg.get('content', '')
                            ai_timestamp = ai_msg.get('timestamp')
                            
                            # Try to parse AI response (might be JSON string)
                            try:
                                if isinstance(ai_content, str) and ai_content.startswith('{'):
                                    ai_parsed = json.loads(ai_content)
                                    ai_summary = ai_parsed.get('summary', 'No summary')
                                else:
                                    ai_summary = str(ai_content)[:100]
                                
                                self.log_result(
                                    "Assistant Message Content", 
                                    True, 
                                    f"AI response stored: '{ai_summary[:50]}...'"
                                )
                            except:
                                self.log_result(
                                    "Assistant Message Content", 
                                    True, 
                                    f"AI response stored (raw): '{str(ai_content)[:50]}...'"
                                )
                        
                        # Step 4: Send another message to test conversation continuity
                        print(f"\n🔄 Step 4: Testing conversation continuity...")
                        
                        followup_data = {
                            "session_id": self.session_id,
                            "message": "Thank you for that information. Can you also tell me about emergency leave procedures?",
                            "document_ids": [],
                            "stream": False
                        }
                        
                        followup_status, followup_response = self.make_request('POST', '/chat/send', data=followup_data)
                        
                        if followup_status == 200:
                            self.log_result(
                                "Conversation Continuity", 
                                True, 
                                "Follow-up message sent successfully"
                            )
                            
                            # Check updated message count
                            time.sleep(1)  # Brief delay for database update
                            
                            updated_messages_status, updated_messages_response = self.make_request('GET', f'/chat/sessions/{self.session_id}/messages')
                            
                            if updated_messages_status == 200:
                                updated_messages = updated_messages_response if isinstance(updated_messages_response, list) else []
                                
                                if len(updated_messages) > len(messages):
                                    self.log_result(
                                        "Message Count Update", 
                                        True, 
                                        f"Message count increased from {len(messages)} to {len(updated_messages)}"
                                    )
                                else:
                                    self.log_result(
                                        "Message Count Update", 
                                        False, 
                                        f"Message count did not increase: {len(messages)} -> {len(updated_messages)}"
                                    )
                        else:
                            self.log_result(
                                "Conversation Continuity", 
                                False, 
                                f"Follow-up message failed: {followup_status}"
                            )
                    
                    else:
                        self.log_result(
                            "Chat Messages API", 
                            False, 
                            f"Failed to get messages: {messages_status}"
                        )
                
                else:
                    self.log_result(
                        "Chat Session Created", 
                        False, 
                        f"Session {self.session_id} NOT found in {len(sessions)} sessions"
                    )
                    
                    # Debug: Show what sessions exist
                    print(f"    DEBUG: Found {len(sessions)} sessions:")
                    for i, session in enumerate(sessions[:5]):  # Show first 5
                        print(f"      {i+1}. ID={session.get('id')}, Title='{session.get('title')}', Messages={session.get('messages_count')}")
            
            else:
                self.log_result(
                    "Chat Sessions API", 
                    False, 
                    f"Failed to get sessions: {sessions_status}"
                )
        
        else:
            self.log_result(
                "Chat Send API", 
                False, 
                f"Chat send failed with status {status_code}: {response}"
            )

    def investigate_database_verification(self):
        """
        Database Verification
        Check actual database collections for uploaded files and chat data
        """
        print(f"\n🔍 DATABASE VERIFICATION")
        print(f"-" * 50)
        
        # Test database connectivity through API endpoints that show stats
        print(f"\n📊 Checking database connectivity via stats endpoints...")
        
        # Check dashboard stats
        stats_status, stats_response = self.make_request('GET', '/dashboard/stats')
        
        if stats_status == 200:
            total_documents = stats_response.get('total_documents', 0)
            total_chat_sessions = stats_response.get('total_chat_sessions', 0)
            total_tickets = stats_response.get('total_tickets', 0)
            
            self.log_result(
                "Database Connectivity", 
                True, 
                f"Stats retrieved: {total_documents} docs, {total_chat_sessions} sessions, {total_tickets} tickets"
            )
            
            # Check document processing stats
            if total_documents > 0:
                self.log_result(
                    "Documents Collection", 
                    True, 
                    f"Documents collection has {total_documents} documents"
                )
            else:
                self.log_result(
                    "Documents Collection", 
                    False, 
                    "Documents collection appears empty"
                )
            
            if total_chat_sessions > 0:
                self.log_result(
                    "Chat Sessions Collection", 
                    True, 
                    f"Chat sessions collection has {total_chat_sessions} sessions"
                )
            else:
                self.log_result(
                    "Chat Sessions Collection", 
                    False, 
                    "Chat sessions collection appears empty"
                )
        
        else:
            self.log_result(
                "Database Connectivity", 
                False, 
                f"Failed to get dashboard stats: {stats_status}"
            )
        
        # Check RAG stats for document processing
        rag_status, rag_response = self.make_request('GET', '/documents/rag-stats')
        
        if rag_status == 200:
            vector_db = rag_response.get('vector_database', {})
            processing_status = rag_response.get('processing_status', {})
            total_docs = rag_response.get('total_documents', 0)
            processed_docs = rag_response.get('processed_documents', 0)
            
            self.log_result(
                "RAG System Status", 
                True, 
                f"Total docs: {total_docs}, Processed: {processed_docs}, Vector DB: {vector_db}"
            )
            
            if processing_status:
                print(f"    Processing status breakdown:")
                for status, count in processing_status.items():
                    print(f"      {status}: {count} documents")
        
        else:
            self.log_result(
                "RAG System Status", 
                False, 
                f"Failed to get RAG stats: {rag_status}"
            )

    def run_investigation(self):
        """Run complete investigation of both production issues"""
        print(f"\n🚀 STARTING PRODUCTION ISSUE INVESTIGATION")
        print(f"Time: {datetime.now().isoformat()}")
        print(f"=" * 60)
        
        # Run all investigations
        self.investigate_document_upload_issue()
        self.investigate_chat_loading_issue()
        self.investigate_database_verification()
        
        # Generate final report
        self.generate_final_report()

    def generate_final_report(self):
        """Generate final investigation report"""
        print(f"\n📋 FINAL INVESTIGATION REPORT")
        print(f"=" * 60)
        
        passed_tests = [r for r in self.test_results if r['success']]
        failed_tests = [r for r in self.test_results if not r['success']]
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {len(passed_tests)}")
        print(f"Failed: {len(failed_tests)}")
        print(f"Success Rate: {len(passed_tests)/len(self.test_results)*100:.1f}%")
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        if passed_tests:
            print(f"\n✅ PASSED TESTS:")
            for test in passed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        # Specific issue analysis
        print(f"\n🔍 ISSUE ANALYSIS:")
        
        # Document Upload Issue Analysis
        doc_upload_tests = [r for r in self.test_results if 'Document' in r['test']]
        doc_upload_failed = [r for r in doc_upload_tests if not r['success']]
        
        if doc_upload_failed:
            print(f"\n📄 DOCUMENT UPLOAD ISSUE:")
            print(f"  Status: ❌ CONFIRMED - Issues found in document upload flow")
            for test in doc_upload_failed:
                print(f"    • {test['test']}: {test['details']}")
        else:
            print(f"\n📄 DOCUMENT UPLOAD ISSUE:")
            print(f"  Status: ✅ WORKING - Document upload flow functioning correctly")
        
        # Chat Loading Issue Analysis
        chat_tests = [r for r in self.test_results if 'Chat' in r['test']]
        chat_failed = [r for r in chat_tests if not r['success']]
        
        if chat_failed:
            print(f"\n💬 CHAT LOADING ISSUE:")
            print(f"  Status: ❌ CONFIRMED - Issues found in chat loading flow")
            for test in chat_failed:
                print(f"    • {test['test']}: {test['details']}")
        else:
            print(f"\n💬 CHAT LOADING ISSUE:")
            print(f"  Status: ✅ WORKING - Chat loading flow functioning correctly")
        
        print(f"\n🎯 RECOMMENDATIONS:")
        
        if failed_tests:
            print(f"  1. Focus on fixing the failed API endpoints identified above")
            print(f"  2. Check database connectivity and data persistence")
            print(f"  3. Verify frontend-backend integration for failed flows")
            print(f"  4. Review error logs for the specific failed operations")
        else:
            print(f"  1. All backend APIs are functioning correctly")
            print(f"  2. Issues may be frontend-specific or environment-related")
            print(f"  3. Check frontend JavaScript console for errors")
            print(f"  4. Verify network connectivity in production environment")
        
        print(f"\n" + "=" * 60)

if __name__ == "__main__":
    investigator = ProductionIssueInvestigator()
    investigator.run_investigation()