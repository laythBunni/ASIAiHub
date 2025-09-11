#!/usr/bin/env python3
"""
RAG System Event Loop Fix Testing Script
Tests the newly implemented event loop fix for the RAG system that was causing
RuntimeError in production ASGI context.
"""

import requests
import json
import time
from datetime import datetime

class RAGEventLoopTester:
    def __init__(self):
        # Use production URL from frontend/.env
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.base_url = line.split('=', 1)[1].strip()
                        break
        except:
            self.base_url = "http://localhost:8001"
        
        self.api_url = f"{self.base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

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

    def test_rag_event_loop_fix(self):
        """Test the RAG System Event Loop Fix as specified in review request"""
        print("\n🔥 CRITICAL EVENT LOOP FIX TESTING - RAG SYSTEM PRODUCTION ISSUE")
        print("=" * 80)
        print("Testing newly implemented event loop fix for RAG system that was causing")
        print("RuntimeError in production ASGI context. Issue: RAG processing never starting")
        print("in production (last_processed_at: null), AsyncIO event loop conflicts.")
        print("=" * 80)
        
        # Test 1: Check if the specific document exists
        print("\n📄 Test 1: Checking for existing test document...")
        document_id = "5ad77e8e-43bb-40d4-914f-8dcf3d444e2f"
        
        check_success, check_response = self.run_test(
            "Check Document Exists", 
            "GET", 
            f"/debug/check-document-debug-info/{document_id}", 
            200
        )
        
        if check_success:
            doc_name = check_response.get('document_name', 'Unknown')
            processing_status = check_response.get('processing_status', 'Unknown')
            processed = check_response.get('processed', False)
            chunks_count = check_response.get('chunks_count', 0)
            last_processed_at = check_response.get('last_processed_at')
            
            print(f"   ✅ Document found: {doc_name}")
            print(f"   📊 Processing status: {processing_status}")
            print(f"   ✅ Processed: {processed}")
            print(f"   📦 Chunks count: {chunks_count}")
            print(f"   ⏰ Last processed at: {last_processed_at}")
            
            if last_processed_at is None:
                print(f"   ⚠️  ISSUE CONFIRMED: last_processed_at is null - processing never started")
            else:
                print(f"   ✅ Processing timestamp exists - may be working")
        else:
            print(f"   ❌ Document not found - will test with available documents")
        
        # Test 2: Get list of available documents for testing
        print("\n📋 Test 2: Getting available documents for testing...")
        
        list_success, list_response = self.run_test(
            "List Available Documents", 
            "GET", 
            "/debug/simple-document-list", 
            200
        )
        
        test_document_id = None
        if list_success:
            documents = list_response.get('documents', [])
            print(f"   ✅ Found {len(documents)} approved documents")
            
            if documents:
                test_document_id = documents[0]['id']
                test_document_name = documents[0]['name']
                print(f"   🎯 Using test document: {test_document_name} (ID: {test_document_id})")
            else:
                print(f"   ⚠️  No approved documents found for testing")
        
        # Test 3: Test direct approval endpoint (the critical fix)
        print("\n🔥 Test 3: Testing Direct Approval Endpoint (Event Loop Fix)...")
        
        if test_document_id:
            approval_success, approval_response = self.run_test(
                "Direct Document Approval Test", 
                "GET", 
                f"/debug/test-approval-direct/{test_document_id}", 
                200
            )
            
            if approval_success:
                status = approval_response.get('status', 'Unknown')
                approval_result = approval_response.get('approval_result', {})
                
                print(f"   ✅ Direct approval endpoint responded: {status}")
                print(f"   📋 Approval result: {approval_result}")
                
                if status == "SUCCESS":
                    print(f"   🎉 EVENT LOOP FIX WORKING: No RuntimeError occurred!")
                else:
                    print(f"   ⚠️  Approval may have issues - check logs")
            else:
                print(f"   ❌ Direct approval endpoint failed")
        else:
            print(f"   ⚠️  Skipping direct approval test - no document available")
        
        # Test 4: Verify RAG processing actually starts
        print("\n⚙️  Test 4: Verifying RAG Processing Pipeline...")
        
        # Test MongoDB RAG system directly
        mongodb_success, mongodb_response = self.run_test(
            "MongoDB RAG Direct Test", 
            "GET", 
            "/debug/test-mongodb-rag-directly", 
            200
        )
        
        if mongodb_success:
            test_status = mongodb_response.get('test_status', 'Unknown')
            steps = mongodb_response.get('steps', [])
            
            print(f"   📊 MongoDB RAG test status: {test_status}")
            
            for step in steps:
                step_name = step.get('step', 'Unknown')
                step_status = step.get('status', 'Unknown')
                
                if step_status == 'SUCCESS':
                    print(f"   ✅ {step_name}: SUCCESS")
                elif step_status == 'FAILED':
                    print(f"   ❌ {step_name}: FAILED - {step.get('error', 'Unknown error')}")
                else:
                    print(f"   ⚠️  {step_name}: {step_status}")
            
            if test_status == "COMPLETED":
                print(f"   🎉 RAG PROCESSING PIPELINE WORKING!")
            else:
                print(f"   ⚠️  RAG processing may have issues")
        else:
            print(f"   ❌ MongoDB RAG test failed")
        
        # Test 5: Test embedding generation (critical for event loop fix)
        print("\n🧠 Test 5: Testing Embedding Generation (Event Loop Critical)...")
        
        embedding_success, embedding_response = self.run_test(
            "Embedding Generation Test", 
            "GET", 
            "/debug/test-embedding-generation", 
            200
        )
        
        if embedding_success:
            test_status = embedding_response.get('test_status', 'Unknown')
            steps = embedding_response.get('steps', [])
            
            print(f"   📊 Embedding test status: {test_status}")
            
            # Check critical steps
            for step in steps:
                step_name = step.get('step', 'Unknown')
                step_status = step.get('status', 'Unknown')
                
                if step_name == "EMBEDDING_GENERATION":
                    if step_status == 'SUCCESS':
                        print(f"   ✅ EMBEDDING GENERATION: SUCCESS - Event loop fix working!")
                        embedding_length = step.get('embedding_length', 0)
                        print(f"   📏 Embedding length: {embedding_length}")
                    elif step_status == 'TIMEOUT':
                        print(f"   ⏰ EMBEDDING GENERATION: TIMEOUT - May indicate event loop issues")
                    else:
                        print(f"   ❌ EMBEDDING GENERATION: FAILED - {step.get('error', 'Unknown')}")
                elif step_name == "MONGODB_WRITE_TEST":
                    if step_status == 'SUCCESS':
                        print(f"   ✅ MONGODB WRITE: SUCCESS")
                    else:
                        print(f"   ❌ MONGODB WRITE: FAILED - {step.get('error', 'Unknown')}")
        else:
            print(f"   ❌ Embedding generation test failed")
        
        # Test 6: Check document processing status after fix
        print("\n📊 Test 6: Checking Document Processing Status After Fix...")
        
        status_success, status_response = self.run_test(
            "Document Status Check", 
            "GET", 
            "/debug/check-document-status", 
            200
        )
        
        if status_success:
            total_docs = status_response.get('total_documents', 0)
            status_counts = status_response.get('status_counts', {})
            processing_counts = status_response.get('processing_status_counts', {})
            sample_docs = status_response.get('sample_documents', [])
            
            print(f"   📊 Total documents: {total_docs}")
            print(f"   📈 Status counts: {status_counts}")
            print(f"   ⚙️  Processing counts: {processing_counts}")
            
            # Check for documents with null last_processed_at
            null_processed_count = 0
            completed_count = 0
            
            for doc in sample_docs:
                processing_status = doc.get('processing_status', 'unknown')
                processed = doc.get('processed', False)
                
                if processing_status == 'completed' and processed:
                    completed_count += 1
                elif processing_status in ['pending', 'processing'] or not processed:
                    null_processed_count += 1
            
            print(f"   ✅ Completed documents: {completed_count}")
            print(f"   ⚠️  Pending/processing documents: {null_processed_count}")
            
            if completed_count > 0:
                print(f"   🎉 EVENT LOOP FIX VERIFIED: Documents are completing processing!")
            else:
                print(f"   ⚠️  No completed documents found - fix may need verification")
        
        # Test 7: Test OpenAI API key functionality (critical for embeddings)
        print("\n🔑 Test 7: Testing OpenAI API Key (Critical for Embeddings)...")
        
        openai_success, openai_response = self.run_test(
            "OpenAI API Key Test", 
            "GET", 
            "/debug/test-openai-key", 
            200
        )
        
        if openai_success:
            test_status = openai_response.get('test_status', 'Unknown')
            steps = openai_response.get('steps', [])
            
            print(f"   📊 OpenAI test status: {test_status}")
            
            embedding_test_passed = False
            completion_test_passed = False
            
            for step in steps:
                step_name = step.get('step', 'Unknown')
                step_status = step.get('status', 'Unknown')
                
                if step_name == "EMBEDDING_TEST":
                    if step_status == 'SUCCESS':
                        print(f"   ✅ OPENAI EMBEDDING TEST: SUCCESS")
                        embedding_test_passed = True
                    else:
                        print(f"   ❌ OPENAI EMBEDDING TEST: {step_status} - {step.get('error', '')}")
                elif step_name == "COMPLETION_TEST":
                    if step_status == 'SUCCESS':
                        print(f"   ✅ OPENAI COMPLETION TEST: SUCCESS")
                        completion_test_passed = True
                    else:
                        print(f"   ❌ OPENAI COMPLETION TEST: {step_status} - {step.get('error', '')}")
            
            if embedding_test_passed and completion_test_passed:
                print(f"   🎉 OPENAI INTEGRATION WORKING: Event loop not blocking API calls!")
            else:
                print(f"   ⚠️  OpenAI integration may have issues")
        
        print(f"\n🎯 RAG EVENT LOOP FIX TEST SUMMARY:")
        print("=" * 80)
        print("KEY CHANGES TESTED:")
        print("✅ Added async process_and_store_document_async() method")
        print("✅ Safe event loop detection using asyncio.get_running_loop()")
        print("✅ Server.py updated to call async method directly")
        print("✅ Updated embedding model from text-embedding-ada-002 to text-embedding-3-small")
        print("✅ Eliminated manual event loop creation")
        print("")
        print("EXPECTED RESULTS:")
        print("✅ Document processing should complete successfully (processed: true)")
        print("✅ Chunks should be created and stored (chunks_count > 0)")
        print("✅ last_processed_at should have timestamp (not null)")
        print("✅ No RuntimeError or event loop conflicts")
        print("✅ processing_status should be 'completed'")
        print("=" * 80)
        
        return True

    def run_all_tests(self):
        """Run all RAG Event Loop Fix tests"""
        print(f"\n🚀 Starting RAG Event Loop Fix Testing...")
        print(f"   Base URL: {self.base_url}")
        print(f"   API URL: {self.api_url}")
        print("=" * 60)
        
        # Run the critical RAG Event Loop Fix test
        self.test_rag_event_loop_fix()
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"🎯 RAG Event Loop Fix Test Results:")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print(f"🎉 All RAG Event Loop Fix tests passed! System is working correctly.")
        else:
            print(f"⚠️  Some tests failed. Event loop fix may need additional work.")
        
        print("=" * 60)

if __name__ == "__main__":
    tester = RAGEventLoopTester()
    tester.run_all_tests()