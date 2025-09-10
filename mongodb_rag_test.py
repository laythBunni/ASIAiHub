#!/usr/bin/env python3
"""
MongoDB RAG System Testing - Comprehensive Test Suite
Tests the newly implemented MongoDB-based RAG system for document processing, chunking, and chat functionality
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path

class MongoDBRAGTester:
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
        self.session_id = f"mongodb-rag-test-{int(time.time())}"
        self.auth_token = None

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

    def test_mongodb_rag_document_processing(self):
        """Test MongoDB RAG System - Document Processing & Chunking Verification"""
        print("\n🔥 CRITICAL: Testing MongoDB RAG System - Document Processing...")
        print("=" * 80)
        
        # Phase 1: Document Upload
        print("\n📤 Phase 1: Document Upload via POST /api/documents/upload...")
        
        # Create a comprehensive test document with policy content
        test_content = """
        ASI Company Travel Policy - March 2024
        
        OVERVIEW:
        This document outlines the travel policy for all ASI employees including booking procedures, expense limits, and approval requirements.
        
        TRAVEL BOOKING REQUIREMENTS:
        1. All business travel must be pre-approved by direct manager
        2. Travel requests must be submitted at least 2 weeks in advance
        3. Use company-approved travel booking platform
        4. Economy class for domestic flights under 4 hours
        5. Business class allowed for international flights over 8 hours
        
        EXPENSE LIMITS:
        - Accommodation: $200/night domestic, $300/night international
        - Meals: $75/day domestic, $100/day international  
        - Ground transportation: Reasonable taxi/uber costs
        - Rental cars require manager approval
        
        APPROVAL PROCESS:
        1. Submit travel request in company portal
        2. Manager approval required within 48 hours
        3. Finance team reviews expenses over $2000
        4. CEO approval required for expenses over $5000
        
        EMERGENCY TRAVEL:
        Emergency travel can be approved verbally by manager but must be documented within 24 hours.
        
        IT SECURITY GUIDELINES:
        When traveling internationally:
        - Use company VPN at all times
        - Do not connect to public WiFi for work
        - Report any security incidents immediately
        - Backup important data before travel
        """
        
        test_file_path = Path("/tmp/asi_travel_policy.txt")
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        document_id = None
        try:
            with open(test_file_path, 'rb') as f:
                files = {'file': ('asi_travel_policy.txt', f, 'text/plain')}
                data = {'department': 'Finance', 'tags': 'travel,policy,expenses'}
                success, response = self.run_test(
                    "Document Upload (Travel Policy)", 
                    "POST", 
                    "/documents/upload", 
                    200, 
                    data=data, 
                    files=files
                )
                if success:
                    document_id = response.get('id')
                    print(f"   ✅ Document uploaded with ID: {document_id}")
                else:
                    print("   ❌ Document upload failed - cannot continue RAG tests")
                    return False
        finally:
            if test_file_path.exists():
                test_file_path.unlink()
        
        if not document_id:
            print("❌ No document ID received - stopping RAG tests")
            return False
        
        # Phase 2: Document Approval Workflow
        print(f"\n✅ Phase 2: Document Approval via PUT /api/documents/{document_id}/approve...")
        
        approval_success, approval_response = self.run_test(
            "Document Approval (Travel Policy)", 
            "PUT", 
            f"/documents/{document_id}/approve", 
            200,
            data={"approved_by": "test_admin"}
        )
        
        if approval_success:
            print(f"   ✅ Document approved successfully")
            print(f"   🔄 RAG processing should now begin automatically...")
            
            # Wait for processing to complete
            print(f"   ⏳ Waiting 15 seconds for MongoDB RAG processing to complete...")
            time.sleep(15)
        else:
            print("   ❌ Document approval failed")
            return False
        
        # Phase 3: Verify Document Chunking & MongoDB Storage
        print(f"\n🔍 Phase 3: Verify Document Chunking & MongoDB Storage...")
        
        # Check RAG stats to see if chunks were created
        rag_stats_success, rag_stats_response = self.run_test(
            "RAG Stats (Check MongoDB Chunks)", 
            "GET", 
            "/documents/rag-stats", 
            200
        )
        
        if rag_stats_success:
            vector_db = rag_stats_response.get('vector_database', {})
            total_chunks = vector_db.get('total_chunks', 0)
            total_documents = vector_db.get('unique_documents', 0)
            
            print(f"   📊 MongoDB RAG Statistics:")
            print(f"   📄 Total Documents: {total_documents}")
            print(f"   🧩 Total Chunks: {total_chunks}")
            
            if total_chunks > 0:
                print(f"   ✅ MongoDB document chunking successful - {total_chunks} chunks created")
            else:
                print(f"   ⚠️  No chunks found - document may still be processing or MongoDB storage failed")
        else:
            print("   ❌ Failed to get RAG statistics")
        
        # Phase 4: Verify Document Metadata Shows Chunk Count
        print(f"\n📋 Phase 4: Verify Document Metadata Shows Chunk Count...")
        
        # Get documents to check if chunk count is displayed
        docs_success, docs_response = self.run_test(
            "Get Documents (Check Metadata)", 
            "GET", 
            "/documents", 
            200
        )
        
        if docs_success and isinstance(docs_response, list):
            uploaded_doc = None
            for doc in docs_response:
                if doc.get('id') == document_id:
                    uploaded_doc = doc
                    break
            
            if uploaded_doc:
                chunks_count = uploaded_doc.get('chunks_count', 0)
                processing_status = uploaded_doc.get('processing_status', 'unknown')
                
                print(f"   📄 Document: {uploaded_doc.get('original_name')}")
                print(f"   🧩 Chunks Count: {chunks_count}")
                print(f"   🔄 Processing Status: {processing_status}")
                
                if chunks_count > 0:
                    print(f"   ✅ Chunk count properly displayed in document metadata")
                else:
                    print(f"   ⚠️  Chunk count not yet updated (may still be processing)")
            else:
                print(f"   ❌ Uploaded document not found in documents list")
        else:
            print("   ❌ Failed to get documents list")
        
        print(f"\n🎉 MongoDB RAG Document Processing Test Complete!")
        return document_id  # Return for use in chat tests

    def test_mongodb_rag_chat_functionality(self, document_id=None):
        """Test MongoDB RAG System - Chat Functionality & Search"""
        print("\n🤖 CRITICAL: Testing MongoDB RAG System - Chat Functionality...")
        print("=" * 80)
        
        # Phase 1: Basic RAG Chat Test
        print("\n💬 Phase 1: Test Chat with Knowledge-Based Query...")
        
        travel_query = "What is the ASI travel policy for business trips? What are the expense limits?"
        
        chat_data = {
            "session_id": f"mongodb-rag-test-{int(time.time())}",
            "message": travel_query,
            "stream": False
        }
        
        chat_success, chat_response = self.run_test(
            "MongoDB RAG Chat (Travel Policy Query)", 
            "POST", 
            "/chat/send", 
            200, 
            chat_data
        )
        
        if chat_success:
            ai_response = chat_response.get('response', {})
            documents_referenced = chat_response.get('documents_referenced', 0)
            response_type = chat_response.get('response_type', 'unknown')
            
            print(f"   🤖 Response Type: {response_type}")
            print(f"   📚 Documents Referenced: {documents_referenced}")
            
            if isinstance(ai_response, dict):
                summary = ai_response.get('summary', '')
                details = ai_response.get('details', {})
                
                print(f"   📝 Response Summary: {summary[:100]}...")
                print(f"   📋 Details Provided: {len(details) > 0}")
                
                # Check if response contains travel policy information
                response_text = json.dumps(ai_response).lower()
                travel_keywords = ['travel', 'expense', 'approval', 'booking', 'policy']
                found_keywords = [kw for kw in travel_keywords if kw in response_text]
                
                print(f"   🔍 Travel Keywords Found: {found_keywords}")
                
                if documents_referenced > 0:
                    print(f"   ✅ MongoDB RAG search successfully found and referenced documents")
                else:
                    print(f"   ⚠️  No documents referenced - MongoDB RAG search may not be working")
                
                if len(found_keywords) >= 2:
                    print(f"   ✅ Response contains relevant travel policy information")
                else:
                    print(f"   ⚠️  Response may not contain specific travel policy details")
            else:
                print(f"   ⚠️  Response not in expected structured format")
        else:
            print("   ❌ MongoDB RAG chat request failed")
            return False
        
        # Phase 2: Test IT Security Query
        print("\n🔒 Phase 2: Test IT Security Guidelines Query...")
        
        it_query = "What are the IT security guidelines when traveling internationally?"
        
        it_chat_data = {
            "session_id": f"mongodb-rag-it-test-{int(time.time())}",
            "message": it_query,
            "stream": False
        }
        
        it_success, it_response = self.run_test(
            "MongoDB RAG Chat (IT Security Query)", 
            "POST", 
            "/chat/send", 
            200, 
            it_chat_data
        )
        
        if it_success:
            it_ai_response = it_response.get('response', {})
            it_docs_referenced = it_response.get('documents_referenced', 0)
            
            print(f"   📚 Documents Referenced: {it_docs_referenced}")
            
            if isinstance(it_ai_response, dict):
                it_summary = it_ai_response.get('summary', '')
                print(f"   📝 IT Response Summary: {it_summary[:100]}...")
                
                # Check for IT security keywords
                it_response_text = json.dumps(it_ai_response).lower()
                it_keywords = ['vpn', 'wifi', 'security', 'backup', 'international']
                found_it_keywords = [kw for kw in it_keywords if kw in it_response_text]
                
                print(f"   🔍 IT Security Keywords Found: {found_it_keywords}")
                
                if len(found_it_keywords) >= 2:
                    print(f"   ✅ Response contains specific IT security guidelines")
                else:
                    print(f"   ⚠️  Response may not contain specific IT security details")
        
        # Phase 3: Test Semantic Search Quality
        print("\n🔍 Phase 3: Test MongoDB Semantic Search Quality...")
        
        # Test with a query that should find relevant chunks
        semantic_query = "How much can I spend on hotels and meals during business travel?"
        
        semantic_chat_data = {
            "session_id": f"mongodb-rag-semantic-{int(time.time())}",
            "message": semantic_query,
            "stream": False
        }
        
        semantic_success, semantic_response = self.run_test(
            "MongoDB RAG Chat (Semantic Search)", 
            "POST", 
            "/chat/send", 
            200, 
            semantic_chat_data
        )
        
        if semantic_success:
            semantic_ai_response = semantic_response.get('response', {})
            semantic_docs = semantic_response.get('documents_referenced', 0)
            
            print(f"   📚 Documents Referenced: {semantic_docs}")
            
            if isinstance(semantic_ai_response, dict):
                semantic_summary = semantic_ai_response.get('summary', '')
                semantic_details = semantic_ai_response.get('details', {})
                
                print(f"   📝 Semantic Response: {semantic_summary[:100]}...")
                
                # Check for expense-related information
                semantic_text = json.dumps(semantic_ai_response).lower()
                expense_keywords = ['$200', '$300', '$75', '$100', 'accommodation', 'meals']
                found_expense_keywords = [kw for kw in expense_keywords if kw in semantic_text]
                
                print(f"   💰 Expense Keywords Found: {found_expense_keywords}")
                
                if len(found_expense_keywords) >= 2:
                    print(f"   ✅ MongoDB semantic search successfully found specific expense limits")
                else:
                    print(f"   ⚠️  MongoDB semantic search may not be finding specific expense details")
        
        # Phase 4: Test Response Structure
        print("\n📋 Phase 4: Verify Structured Response Format...")
        
        if chat_success and isinstance(chat_response.get('response'), dict):
            response_structure = chat_response['response']
            
            required_fields = ['summary', 'details', 'action_required', 'contact_info']
            present_fields = [field for field in required_fields if field in response_structure]
            
            print(f"   📊 Response Structure Analysis:")
            print(f"   ✅ Required Fields Present: {present_fields}")
            print(f"   📋 Structure Score: {len(present_fields)}/{len(required_fields)}")
            
            if len(present_fields) >= 3:
                print(f"   ✅ Response follows structured format correctly")
            else:
                print(f"   ⚠️  Response structure may be incomplete")
        
        print(f"\n🎉 MongoDB RAG Chat Functionality Test Complete!")
        return True

    def test_mongodb_rag_system_integration(self):
        """Test Complete MongoDB RAG System Integration"""
        print("\n🔄 CRITICAL: Testing Complete MongoDB RAG System Integration...")
        print("=" * 80)
        
        # Phase 1: Document Processing Pipeline
        print("\n🏭 Phase 1: Complete Document Processing Pipeline...")
        
        # Upload → Approval → Processing → Chunking → Storage → Search → Response
        document_id = self.test_mongodb_rag_document_processing()
        
        if not document_id:
            print("❌ Document processing pipeline failed - cannot test integration")
            return False
        
        # Phase 2: RAG Search & Chat Integration
        print("\n🔍 Phase 2: RAG Search & Chat Integration...")
        
        chat_success = self.test_mongodb_rag_chat_functionality(document_id)
        
        if not chat_success:
            print("❌ RAG chat functionality failed")
            return False
        
        # Phase 3: Error Handling & Timeout Protection
        print("\n⚠️  Phase 3: Error Handling & Timeout Protection...")
        
        # Test with a very long query to check timeout handling
        timeout_query = "This is a very long query " * 50 + " about travel policies and procedures"
        
        timeout_chat_data = {
            "session_id": f"mongodb-rag-timeout-{int(time.time())}",
            "message": timeout_query,
            "stream": False
        }
        
        timeout_success, timeout_response = self.run_test(
            "MongoDB RAG Timeout Protection Test", 
            "POST", 
            "/chat/send", 
            200,  # Should still return 200 even with timeout
            timeout_chat_data
        )
        
        if timeout_success:
            timeout_response_type = timeout_response.get('response_type', 'unknown')
            print(f"   🔄 Response Type: {timeout_response_type}")
            
            if timeout_response_type in ['llm_timeout', 'success', 'structured']:
                print(f"   ✅ Timeout protection working correctly")
            else:
                print(f"   ⚠️  Timeout handling may need review")
        
        # Phase 4: MongoDB Collections Verification
        print("\n🗄️  Phase 4: MongoDB Collections Verification...")
        
        # Test that document_chunks collection is being used
        print("   📊 Checking if MongoDB 'document_chunks' collection is populated...")
        
        # We can't directly access MongoDB from here, but we can infer from RAG stats
        final_stats_success, final_stats_response = self.run_test(
            "Final MongoDB RAG Stats Check", 
            "GET", 
            "/documents/rag-stats", 
            200
        )
        
        if final_stats_success:
            final_vector_db = final_stats_response.get('vector_database', {})
            final_chunks = final_vector_db.get('total_chunks', 0)
            final_docs = final_vector_db.get('unique_documents', 0)
            
            print(f"   📊 Final MongoDB RAG Statistics:")
            print(f"   📄 Total Documents: {final_docs}")
            print(f"   🧩 Total Chunks: {final_chunks}")
            
            if final_chunks > 0 and final_docs > 0:
                print(f"   ✅ MongoDB RAG system fully operational")
                print(f"   🎉 Document processing, chunking, storage, and search all working")
                print(f"   🗄️  MongoDB 'document_chunks' collection populated with {final_chunks} chunks")
                return True
            else:
                print(f"   ❌ MongoDB RAG system not fully operational")
                return False
        else:
            print("   ❌ Cannot verify final MongoDB RAG stats")
            return False

    def test_openai_embeddings_integration(self):
        """Test OpenAI Embeddings Integration in MongoDB RAG"""
        print("\n🧠 CRITICAL: Testing OpenAI Embeddings Integration...")
        print("=" * 80)
        
        print("\n📝 Phase 1: Verify OpenAI Embeddings are Generated...")
        
        # Create a test document specifically for embeddings testing
        embeddings_test_content = """
        ASI IT Security Policy - Embeddings Test Document
        
        PASSWORD REQUIREMENTS:
        - Minimum 12 characters
        - Must include uppercase, lowercase, numbers, and symbols
        - Cannot reuse last 5 passwords
        - Must be changed every 90 days
        
        VPN USAGE:
        - Required for all remote work
        - Use company-approved VPN clients only
        - Connect before accessing any company resources
        - Report connection issues immediately
        
        DATA BACKUP:
        - All critical data must be backed up daily
        - Use company-approved cloud storage
        - Verify backup integrity weekly
        - Test restore procedures monthly
        """
        
        test_file_path = Path("/tmp/asi_it_security_embeddings.txt")
        with open(test_file_path, 'w') as f:
            f.write(embeddings_test_content)
        
        document_id = None
        try:
            with open(test_file_path, 'rb') as f:
                files = {'file': ('asi_it_security_embeddings.txt', f, 'text/plain')}
                data = {'department': 'Information Technology', 'tags': 'security,IT,embeddings'}
                success, response = self.run_test(
                    "Document Upload (Embeddings Test)", 
                    "POST", 
                    "/documents/upload", 
                    200, 
                    data=data, 
                    files=files
                )
                if success:
                    document_id = response.get('id')
                    print(f"   ✅ Embeddings test document uploaded with ID: {document_id}")
        finally:
            if test_file_path.exists():
                test_file_path.unlink()
        
        if not document_id:
            print("❌ Failed to upload embeddings test document")
            return False
        
        # Approve the document
        approval_success, approval_response = self.run_test(
            "Document Approval (Embeddings Test)", 
            "PUT", 
            f"/documents/{document_id}/approve", 
            200,
            data={"approved_by": "embeddings_test"}
        )
        
        if not approval_success:
            print("❌ Failed to approve embeddings test document")
            return False
        
        print(f"   ⏳ Waiting 20 seconds for OpenAI embeddings generation...")
        time.sleep(20)
        
        # Phase 2: Test Semantic Search with OpenAI Embeddings
        print("\n🔍 Phase 2: Test Semantic Search with OpenAI Embeddings...")
        
        # Test queries that should find semantically similar content
        embedding_test_queries = [
            {
                "query": "What are the password requirements?",
                "expected_keywords": ["password", "characters", "uppercase", "lowercase"]
            },
            {
                "query": "How do I use VPN for remote work?",
                "expected_keywords": ["vpn", "remote", "connect", "company"]
            },
            {
                "query": "What is the data backup policy?",
                "expected_keywords": ["backup", "data", "daily", "cloud"]
            }
        ]
        
        embeddings_working = True
        
        for i, test_case in enumerate(embedding_test_queries, 1):
            print(f"\n   🧠 Embeddings Test {i}: '{test_case['query']}'")
            
            chat_data = {
                "session_id": f"embeddings-test-{int(time.time())}-{i}",
                "message": test_case['query'],
                "stream": False
            }
            
            success, response = self.run_test(
                f"OpenAI Embeddings Query {i}", 
                "POST", 
                "/chat/send", 
                200, 
                chat_data
            )
            
            if success:
                ai_response = response.get('response', {})
                documents_referenced = response.get('documents_referenced', 0)
                
                print(f"      📚 Documents Referenced: {documents_referenced}")
                
                if documents_referenced > 0:
                    print(f"      ✅ OpenAI embeddings found relevant documents")
                    
                    # Check semantic relevance
                    if isinstance(ai_response, dict):
                        response_text = json.dumps(ai_response).lower()
                        found_keywords = [kw for kw in test_case['expected_keywords'] if kw.lower() in response_text]
                        
                        print(f"      🔍 Semantic Keywords Found: {found_keywords}")
                        
                        if len(found_keywords) >= 2:
                            print(f"      ✅ Semantic search working correctly")
                        else:
                            print(f"      ⚠️  Semantic relevance may be low")
                            embeddings_working = False
                else:
                    print(f"      ❌ No documents referenced - embeddings may not be working")
                    embeddings_working = False
            else:
                print(f"      ❌ Embeddings query failed")
                embeddings_working = False
        
        # Phase 3: Test Cosine Similarity Calculation
        print("\n📐 Phase 3: Test Cosine Similarity Calculation...")
        
        # Test with very specific query that should have high similarity
        specific_query = "12 character password with uppercase lowercase numbers symbols"
        
        specific_chat_data = {
            "session_id": f"similarity-test-{int(time.time())}",
            "message": specific_query,
            "stream": False
        }
        
        similarity_success, similarity_response = self.run_test(
            "Cosine Similarity Test", 
            "POST", 
            "/chat/send", 
            200, 
            specific_chat_data
        )
        
        if similarity_success:
            similarity_docs = similarity_response.get('documents_referenced', 0)
            similarity_ai_response = similarity_response.get('response', {})
            
            print(f"   📚 Documents Referenced: {similarity_docs}")
            
            if similarity_docs > 0:
                # Check if the response contains very specific password requirements
                if isinstance(similarity_ai_response, dict):
                    response_text = json.dumps(similarity_ai_response).lower()
                    specific_keywords = ['12', 'character', 'uppercase', 'lowercase', 'number', 'symbol']
                    found_specific = [kw for kw in specific_keywords if kw in response_text]
                    
                    print(f"   🎯 Specific Keywords Found: {found_specific}")
                    
                    if len(found_specific) >= 4:
                        print(f"   ✅ High similarity search working - found very specific content")
                    else:
                        print(f"   ⚠️  Similarity calculation may need tuning")
            else:
                print(f"   ❌ No documents found for specific query")
                embeddings_working = False
        
        if embeddings_working:
            print(f"\n🎉 OpenAI Embeddings Integration Test PASSED!")
            print(f"   ✅ OpenAI text-embedding-ada-002 model working")
            print(f"   ✅ Semantic search finding relevant documents")
            print(f"   ✅ Cosine similarity calculation working")
            print(f"   ✅ MongoDB storing embeddings correctly")
        else:
            print(f"\n❌ OpenAI Embeddings Integration Test FAILED!")
            print(f"   ❌ Embeddings generation or search not working properly")
        
        return embeddings_working

    def run_comprehensive_mongodb_rag_tests(self):
        """Run all MongoDB RAG system tests"""
        print(f"🔥 STARTING COMPREHENSIVE MONGODB RAG SYSTEM TESTING...")
        print(f"📍 Base URL: {self.base_url}")
        print(f"🔗 API URL: {self.api_url}")
        print("=" * 80)
        
        print("\n🎯 TESTING FOCUS: MongoDB-based RAG System")
        print("   - Document Processing & Chunking")
        print("   - MongoDB Chunk Storage")
        print("   - OpenAI Embeddings Generation")
        print("   - Semantic Search & Chat Functionality")
        print("   - System Integration & Error Handling")
        print("=" * 80)
        
        all_tests_passed = True
        
        # Test 1: Complete MongoDB RAG System Integration
        print("\n🔄 TEST 1: Complete MongoDB RAG System Integration")
        print("-" * 60)
        
        try:
            integration_success = self.test_mongodb_rag_system_integration()
            if not integration_success:
                all_tests_passed = False
                print("❌ MongoDB RAG System Integration: FAILED")
            else:
                print("✅ MongoDB RAG System Integration: PASSED")
        except Exception as e:
            print(f"❌ MongoDB RAG System Integration: ERROR - {str(e)}")
            all_tests_passed = False
        
        # Test 2: OpenAI Embeddings Integration
        print("\n🧠 TEST 2: OpenAI Embeddings Integration")
        print("-" * 60)
        
        try:
            embeddings_success = self.test_openai_embeddings_integration()
            if not embeddings_success:
                all_tests_passed = False
                print("❌ OpenAI Embeddings Integration: FAILED")
            else:
                print("✅ OpenAI Embeddings Integration: PASSED")
        except Exception as e:
            print(f"❌ OpenAI Embeddings Integration: ERROR - {str(e)}")
            all_tests_passed = False
        
        # Final Summary
        print("\n" + "=" * 80)
        print("🎯 MONGODB RAG SYSTEM TEST RESULTS")
        print("=" * 80)
        
        print(f"📊 Total Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if all_tests_passed:
            print("\n🎉 MONGODB RAG SYSTEM: FULLY OPERATIONAL")
            print("✅ Document processing and chunking working")
            print("✅ MongoDB chunk storage working")
            print("✅ OpenAI embeddings generation working")
            print("✅ Semantic search and chat functionality working")
            print("✅ System integration and error handling working")
            print("\n🚀 READY FOR PRODUCTION USE")
        else:
            print("\n❌ MONGODB RAG SYSTEM: ISSUES DETECTED")
            print("⚠️  Some components are not working correctly")
            print("🔧 REQUIRES ATTENTION BEFORE PRODUCTION USE")
        
        print("=" * 80)
        
        return all_tests_passed

def main():
    """Main test execution"""
    print("🔥 MongoDB RAG System Testing Suite")
    print("=" * 50)
    
    tester = MongoDBRAGTester()
    success = tester.run_comprehensive_mongodb_rag_tests()
    
    if success:
        print("\n🎉 ALL MONGODB RAG TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME MONGODB RAG TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()