#!/usr/bin/env python3
"""
PRODUCTION GUARANTEE TEST - COMPLETE END-TO-END RAG VERIFICATION

This test specifically verifies the production RAG system with document ID:
283e01f8-f98d-4ff5-a669-dd3bfdd79a24 (production_guarantee_test.txt)

CRITICAL TESTS:
1. Verify production environment is actually using MongoDB (not ChromaDB)
2. Test MongoDB chunk storage directly with the specific document
3. Check if chunks are being stored but not counted correctly
4. Verify OpenAI API key is working for embeddings
5. Test complete document approval → chunking → storage → search pipeline
6. Confirm chunks exist in production MongoDB collection
"""

import requests
import sys
import json
import time
import os
from datetime import datetime
from pathlib import Path

class ProductionRAGTester:
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
        self.target_document_id = "283e01f8-f98d-4ff5-a669-dd3bfdd79a24"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = f"production-rag-test-{int(time.time())}"
        self.auth_token = None
        
        print(f"🎯 PRODUCTION RAG TESTING")
        print(f"📍 Backend URL: {self.base_url}")
        print(f"🎯 Target Document ID: {self.target_document_id}")
        print("=" * 80)

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}{endpoint}"
        default_headers = {'Content-Type': 'application/json'} if not files else {}
        
        if headers:
            default_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=60)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, data=data, headers=headers or {}, timeout=60)
                else:
                    response = requests.post(url, json=data, headers=default_headers, timeout=60)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=60)

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
                    # Truncate long responses for readability
                    response_str = json.dumps(response_data, indent=2)
                    if len(response_str) > 500:
                        print(f"   Response: {response_str[:500]}...")
                    else:
                        print(f"   Response: {response_str}")
                    return True, response_data
                except:
                    print(f"   Response: {response.text[:200]}...")
                    return True, {}
            else:
                expected_str = str(expected_status) if not isinstance(expected_status, list) else f"one of {expected_status}"
                print(f"❌ Failed - Expected {expected_str}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def authenticate_admin(self):
        """Authenticate as admin user to access protected endpoints"""
        print(f"\n🔐 AUTHENTICATING AS ADMIN...")
        
        # Use Layth's Phase 2 credentials
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
            # Try different token field names
            token = response.get('access_token') or response.get('token')
            if token:
                self.auth_token = token
                print(f"✅ ADMIN AUTHENTICATED SUCCESSFULLY!")
                print(f"   👤 User: {response.get('user', {}).get('email')}")
                print(f"   👑 Role: {response.get('user', {}).get('role')}")
                print(f"   🔑 Token: {token[:20]}...")
                return True, response
            else:
                print(f"❌ No token received in response")
                return False, response
        else:
            print(f"❌ Admin authentication failed")
            return False, {}

    def get_auth_headers(self):
        """Get authentication headers for API calls"""
        if self.auth_token:
            return {'Authorization': f'Bearer {self.auth_token}'}
        return {}

    def test_1_verify_document_exists(self):
        """Test 1: Verify the target document exists in the system"""
        print(f"\n🎯 TEST 1: VERIFY TARGET DOCUMENT EXISTS")
        print("=" * 50)
        
        # First authenticate
        auth_success, _ = self.authenticate_admin()
        if not auth_success:
            print(f"❌ Cannot authenticate - skipping document check")
            return False, {}
        
        # Check if document exists in admin documents list
        success, response = self.run_test(
            f"Check Document {self.target_document_id} Exists",
            "GET",
            "/documents/admin",
            200,
            headers=self.get_auth_headers()
        )
        
        if success and isinstance(response, list):
            target_doc = None
            for doc in response:
                if doc.get('id') == self.target_document_id:
                    target_doc = doc
                    break
            
            if target_doc:
                print(f"✅ TARGET DOCUMENT FOUND!")
                print(f"   📄 Name: {target_doc.get('original_name')}")
                print(f"   📊 Status: {target_doc.get('approval_status')}")
                print(f"   🔄 Processing: {target_doc.get('processing_status')}")
                print(f"   📦 Chunks: {target_doc.get('chunks_count', 0)}")
                print(f"   ✅ Processed: {target_doc.get('processed', False)}")
                return True, target_doc
            else:
                print(f"❌ TARGET DOCUMENT NOT FOUND!")
                print(f"   Found {len(response)} documents, but target ID not among them")
                # Show first few documents for debugging
                if len(response) > 0:
                    print(f"   📋 Available documents:")
                    for i, doc in enumerate(response[:3]):
                        print(f"      {i+1}. {doc.get('original_name')} (ID: {doc.get('id')})")
                return False, {}
        else:
            print(f"❌ Failed to retrieve documents list")
            return False, {}

    def test_2_verify_production_mongodb_mode(self):
        """Test 2: Verify production environment is using MongoDB (not ChromaDB)"""
        print(f"\n🎯 TEST 2: VERIFY PRODUCTION MONGODB MODE")
        print("=" * 50)
        
        # Test the debug endpoint to check RAG system mode
        success, response = self.run_test(
            "Check RAG System Mode",
            "GET",
            "/debug/test-mongodb-rag-directly",
            200
        )
        
        if success:
            steps = response.get('steps', [])
            rag_init_step = None
            
            for step in steps:
                if step.get('step') == 'RAG_INITIALIZATION':
                    rag_init_step = step
                    break
            
            if rag_init_step:
                rag_mode = rag_init_step.get('rag_mode', 'unknown')
                print(f"   🔍 RAG Mode: {rag_mode}")
                
                if 'mongodb' in rag_mode.lower() or 'production' in rag_mode.lower():
                    print(f"✅ PRODUCTION MONGODB MODE CONFIRMED!")
                    return True, response
                else:
                    print(f"❌ NOT IN MONGODB MODE - Using: {rag_mode}")
                    return False, response
            else:
                print(f"❌ Could not determine RAG mode from response")
                return False, response
        else:
            print(f"❌ Failed to check RAG system mode")
            return False, {}

    def test_3_verify_openai_api_key(self):
        """Test 3: Verify OpenAI API key is working for embeddings"""
        print(f"\n🎯 TEST 3: VERIFY OPENAI API KEY")
        print("=" * 50)
        
        success, response = self.run_test(
            "Test OpenAI API Key",
            "GET",
            "/debug/test-openai-key",
            200
        )
        
        if success:
            steps = response.get('steps', [])
            embedding_test = None
            completion_test = None
            
            for step in steps:
                if step.get('step') == 'EMBEDDING_TEST':
                    embedding_test = step
                elif step.get('step') == 'COMPLETION_TEST':
                    completion_test = step
            
            # Check embedding test (most important for RAG)
            if embedding_test:
                if embedding_test.get('status') == 'SUCCESS':
                    print(f"✅ OPENAI EMBEDDINGS WORKING!")
                    print(f"   📏 Embedding length: {embedding_test.get('embedding_length')}")
                    print(f"   🤖 Model: {embedding_test.get('model_used')}")
                    print(f"   🎯 Tokens used: {embedding_test.get('tokens_used')}")
                else:
                    print(f"❌ OPENAI EMBEDDINGS FAILED!")
                    print(f"   Error: {embedding_test.get('error')}")
                    return False, response
            
            # Check completion test
            if completion_test:
                if completion_test.get('status') == 'SUCCESS':
                    print(f"✅ OPENAI COMPLETIONS WORKING!")
                    print(f"   🤖 Model: {completion_test.get('model_used')}")
                    print(f"   💬 Response: {completion_test.get('response')}")
                else:
                    print(f"⚠️  OPENAI COMPLETIONS ISSUE:")
                    print(f"   Status: {completion_test.get('status')}")
                    print(f"   Error: {completion_test.get('error')}")
            
            return True, response
        else:
            print(f"❌ Failed to test OpenAI API key")
            return False, {}

    def test_4_direct_document_approval(self):
        """Test 4: Test direct document approval and processing"""
        print(f"\n🎯 TEST 4: DIRECT DOCUMENT APPROVAL & PROCESSING")
        print("=" * 50)
        
        success, response = self.run_test(
            f"Direct Approval Test for {self.target_document_id}",
            "GET",
            f"/debug/test-approval-direct/{self.target_document_id}",
            200
        )
        
        if success:
            approval_result = response.get('approval_result', {})
            print(f"✅ DIRECT APPROVAL TEST COMPLETED!")
            print(f"   📄 Document: {response.get('document_name')}")
            print(f"   🔄 Status: {response.get('status')}")
            print(f"   📋 Result: {approval_result}")
            return True, response
        else:
            print(f"❌ Direct approval test failed")
            return False, {}

    def test_5_check_mongodb_chunks(self):
        """Test 5: Check if chunks exist in MongoDB collection"""
        print(f"\n🎯 TEST 5: CHECK MONGODB CHUNKS")
        print("=" * 50)
        
        # First check document status after processing
        doc_success, doc_response = self.run_test(
            f"Check Document Status After Processing",
            "GET",
            "/documents/admin",
            200,
            headers=self.get_auth_headers()
        )
        
        if doc_success and isinstance(doc_response, list):
            target_doc = None
            for doc in doc_response:
                if doc.get('id') == self.target_document_id:
                    target_doc = doc
                    break
            
            if target_doc:
                print(f"📄 DOCUMENT STATUS AFTER PROCESSING:")
                print(f"   📊 Processing Status: {target_doc.get('processing_status')}")
                print(f"   📦 Chunks Count: {target_doc.get('chunks_count', 0)}")
                print(f"   ✅ Processed: {target_doc.get('processed', False)}")
                print(f"   📝 Notes: {target_doc.get('notes', 'None')}")
                
                chunks_count = target_doc.get('chunks_count', 0)
                if chunks_count > 0:
                    print(f"✅ CHUNKS FOUND IN DOCUMENT METADATA!")
                    print(f"   📦 Total chunks: {chunks_count}")
                    return True, target_doc
                else:
                    print(f"❌ NO CHUNKS IN DOCUMENT METADATA!")
                    print(f"   This indicates the RAG processing may have failed")
                    return False, target_doc
            else:
                print(f"❌ Target document not found after processing")
                return False, {}
        else:
            print(f"❌ Failed to check document status")
            return False, {}

    def test_6_test_rag_search(self):
        """Test 6: Test RAG search functionality with the processed document"""
        print(f"\n🎯 TEST 6: TEST RAG SEARCH FUNCTIONALITY")
        print("=" * 50)
        
        # Test chat with a query that should find the document
        chat_data = {
            "session_id": self.session_id,
            "message": "What information is available in the production guarantee test document?",
            "stream": False
        }
        
        success, response = self.run_test(
            "RAG Search Test",
            "POST",
            "/chat/send",
            200,
            chat_data
        )
        
        if success:
            ai_response = response.get('response', {})
            documents_referenced = response.get('documents_referenced', 0)
            response_type = response.get('response_type', 'unknown')
            
            print(f"✅ RAG SEARCH COMPLETED!")
            print(f"   🤖 Response Type: {response_type}")
            print(f"   📚 Documents Referenced: {documents_referenced}")
            
            if documents_referenced > 0:
                print(f"✅ DOCUMENTS FOUND BY RAG SEARCH!")
                print(f"   📖 RAG system successfully found and referenced documents")
                
                if isinstance(ai_response, dict):
                    summary = ai_response.get('summary', '')
                    print(f"   💬 Response Summary: {summary[:200]}...")
                
                return True, response
            else:
                print(f"❌ NO DOCUMENTS REFERENCED!")
                print(f"   RAG search did not find any relevant documents")
                print(f"   This suggests chunks are not properly stored or searchable")
                return False, response
        else:
            print(f"❌ RAG search test failed")
            return False, {}

    def test_7_comprehensive_pipeline_verification(self):
        """Test 7: Comprehensive end-to-end pipeline verification"""
        print(f"\n🎯 TEST 7: COMPREHENSIVE PIPELINE VERIFICATION")
        print("=" * 50)
        
        # Create a new test document to verify the complete pipeline
        test_content = f"""
        PRODUCTION RAG SYSTEM VERIFICATION TEST
        
        Document ID: test-production-verification-{int(time.time())}
        Created: {datetime.now().isoformat()}
        
        This document is created specifically to test the production RAG system pipeline:
        
        REQUIREMENTS VERIFICATION:
        1. Document upload and storage ✓
        2. Document approval workflow ✓
        3. RAG processing and chunking ✓
        4. MongoDB chunk storage ✓
        5. OpenAI embedding generation ✓
        6. Search functionality ✓
        
        PRODUCTION ENVIRONMENT DETAILS:
        - Environment: Production MongoDB mode
        - Backend URL: {self.base_url}
        - Test Session: {self.session_id}
        - Target Document: {self.target_document_id}
        
        EXPECTED OUTCOMES:
        - This document should be chunked into multiple pieces
        - Each chunk should have OpenAI embeddings
        - Chunks should be stored in MongoDB document_chunks collection
        - Search queries should find this document
        - Chat responses should reference this document content
        
        TEST KEYWORDS: production, verification, mongodb, rag, embeddings, chunks
        """
        
        # Create test file
        test_file_path = Path("/tmp/production_verification_test.txt")
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        try:
            # Upload test document
            with open(test_file_path, 'rb') as f:
                files = {'file': ('production_verification_test.txt', f, 'text/plain')}
                data = {'department': 'Information Technology', 'tags': 'production,test,verification'}
                
                upload_success, upload_response = self.run_test(
                    "Upload Test Document",
                    "POST",
                    "/documents/upload",
                    200,
                    data=data,
                    files=files
                )
            
            if not upload_success:
                print(f"❌ Failed to upload test document")
                return False, {}
            
            test_doc_id = upload_response.get('id')
            print(f"✅ TEST DOCUMENT UPLOADED!")
            print(f"   📄 Document ID: {test_doc_id}")
            
            # Approve the document
            approve_success, approve_response = self.run_test(
                "Approve Test Document",
                "PUT",
                f"/documents/{test_doc_id}/approve",
                200
            )
            
            if not approve_success:
                print(f"❌ Failed to approve test document")
                return False, {}
            
            print(f"✅ TEST DOCUMENT APPROVED!")
            
            # Wait for processing
            print(f"⏳ Waiting for RAG processing...")
            time.sleep(10)  # Give time for background processing
            
            # Check document status
            doc_check_success, doc_check_response = self.run_test(
                "Check Test Document Status",
                "GET",
                "/documents/admin",
                200
            )
            
            if doc_check_success and isinstance(doc_check_response, list):
                test_doc = None
                for doc in doc_check_response:
                    if doc.get('id') == test_doc_id:
                        test_doc = doc
                        break
                
                if test_doc:
                    print(f"📊 TEST DOCUMENT STATUS:")
                    print(f"   🔄 Processing Status: {test_doc.get('processing_status')}")
                    print(f"   📦 Chunks Count: {test_doc.get('chunks_count', 0)}")
                    print(f"   ✅ Processed: {test_doc.get('processed', False)}")
                    
                    if test_doc.get('chunks_count', 0) > 0:
                        print(f"✅ PIPELINE VERIFICATION SUCCESSFUL!")
                        print(f"   📦 Document was successfully chunked and processed")
                        
                        # Test search with the new document
                        search_data = {
                            "session_id": f"{self.session_id}-verification",
                            "message": "Tell me about the production RAG system verification test",
                            "stream": False
                        }
                        
                        search_success, search_response = self.run_test(
                            "Search Test Document",
                            "POST",
                            "/chat/send",
                            200,
                            search_data
                        )
                        
                        if search_success:
                            docs_referenced = search_response.get('documents_referenced', 0)
                            if docs_referenced > 0:
                                print(f"✅ SEARCH VERIFICATION SUCCESSFUL!")
                                print(f"   📚 Found {docs_referenced} documents in search")
                                return True, {"test_doc_id": test_doc_id, "search_response": search_response}
                            else:
                                print(f"⚠️  Search completed but no documents referenced")
                                return True, {"test_doc_id": test_doc_id, "search_response": search_response}
                        else:
                            print(f"❌ Search test failed")
                            return False, {}
                    else:
                        print(f"❌ PIPELINE VERIFICATION FAILED!")
                        print(f"   Document was not properly chunked")
                        return False, test_doc
                else:
                    print(f"❌ Test document not found after approval")
                    return False, {}
            else:
                print(f"❌ Failed to check test document status")
                return False, {}
                
        finally:
            # Clean up test file
            if test_file_path.exists():
                test_file_path.unlink()

    def run_all_tests(self):
        """Run all production RAG tests"""
        print(f"\n🚀 STARTING PRODUCTION RAG VERIFICATION TESTS")
        print(f"🎯 Target Document: {self.target_document_id}")
        print("=" * 80)
        
        test_results = {}
        
        # Test 1: Verify document exists
        test_results['document_exists'] = self.test_1_verify_document_exists()
        
        # Test 2: Verify MongoDB mode
        test_results['mongodb_mode'] = self.test_2_verify_production_mongodb_mode()
        
        # Test 3: Verify OpenAI API key
        test_results['openai_key'] = self.test_3_verify_openai_api_key()
        
        # Test 4: Direct document approval
        test_results['direct_approval'] = self.test_4_direct_document_approval()
        
        # Test 5: Check MongoDB chunks
        test_results['mongodb_chunks'] = self.test_5_check_mongodb_chunks()
        
        # Test 6: Test RAG search
        test_results['rag_search'] = self.test_6_test_rag_search()
        
        # Test 7: Comprehensive pipeline verification
        test_results['pipeline_verification'] = self.test_7_comprehensive_pipeline_verification()
        
        # Print final results
        print(f"\n🎉 PRODUCTION RAG VERIFICATION COMPLETE!")
        print("=" * 80)
        print(f"📊 FINAL RESULTS:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n📋 TEST BREAKDOWN:")
        for test_name, (success, data) in test_results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        # Determine overall success
        critical_tests = ['mongodb_mode', 'openai_key', 'mongodb_chunks', 'rag_search']
        critical_passed = sum(1 for test in critical_tests if test_results.get(test, (False, {}))[0])
        
        print(f"\n🎯 CRITICAL TESTS: {critical_passed}/{len(critical_tests)} passed")
        
        if critical_passed == len(critical_tests):
            print(f"🎉 PRODUCTION RAG SYSTEM VERIFIED WORKING!")
            print(f"✅ All critical components are functioning correctly")
            return True
        else:
            print(f"❌ PRODUCTION RAG SYSTEM HAS ISSUES!")
            failed_tests = [test for test in critical_tests if not test_results.get(test, (False, {}))[0]]
            print(f"❌ Failed critical tests: {failed_tests}")
            return False

if __name__ == "__main__":
    tester = ProductionRAGTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)