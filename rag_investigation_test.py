#!/usr/bin/env python3
"""
RAG Search Failure Investigation Test
Specifically testing the issues mentioned in the review request
"""

import requests
import json
import time
from datetime import datetime

class RAGInvestigationTester:
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
        self.session_id = f"rag-investigation-{int(time.time())}"
        self.auth_token = None
        
    def authenticate_admin(self):
        """Authenticate as admin user"""
        print("🔐 Authenticating as admin...")
        
        login_data = {
            "email": "layth.bunni@adamsmithinternational.com",
            "personal_code": "899443"
        }
        
        try:
            response = requests.post(f"{self.api_url}/auth/login", json=login_data)
            if response.status_code == 200:
                result = response.json()
                self.auth_token = result.get('access_token')
                print(f"✅ Admin authenticated successfully")
                return True
            else:
                print(f"❌ Admin authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Admin authentication error: {e}")
            return False
    
    def test_rag_collection_stats(self):
        """Test RAG collection statistics to see if documents are indexed"""
        print("\n📊 Testing RAG Collection Statistics...")
        print("-" * 50)
        
        try:
            response = requests.get(f"{self.api_url}/documents/rag-stats")
            if response.status_code == 200:
                stats = response.json()
                vector_db = stats.get('vector_database', {})
                
                print(f"✅ RAG Statistics Retrieved:")
                print(f"   📄 Total Documents in DB: {stats.get('total_documents', 0)}")
                print(f"   ✅ Processed Documents: {stats.get('processed_documents', 0)}")
                print(f"   🧩 Total Chunks in Vector DB: {vector_db.get('total_chunks', 0)}")
                print(f"   📚 Unique Documents in Vector DB: {vector_db.get('unique_documents', 0)}")
                print(f"   🏢 Departments: {vector_db.get('departments', [])}")
                print(f"   🗄️  Collection Name: {vector_db.get('collection_name', 'Unknown')}")
                
                # Check if we have enough data for search
                total_chunks = vector_db.get('total_chunks', 0)
                if total_chunks > 0:
                    print(f"   ✅ RAG system has {total_chunks} chunks ready for search")
                    return True, total_chunks
                else:
                    print(f"   ❌ RAG system has no chunks - documents not processed")
                    return False, 0
            else:
                print(f"❌ Failed to get RAG stats: {response.status_code}")
                print(f"   Response: {response.text}")
                return False, 0
                
        except Exception as e:
            print(f"❌ RAG stats error: {e}")
            return False, 0
    
    def test_direct_rag_search(self):
        """Test direct RAG search with IT security policy query"""
        print("\n🔍 Testing Direct RAG Search...")
        print("-" * 50)
        
        # Test the specific queries mentioned in the review request
        test_queries = [
            "whats the IT security policy for asi",
            "whats the travel policy",
            "What are the company leave policies?"
        ]
        
        results = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Query {i}: '{query}'")
            
            chat_data = {
                "session_id": f"{self.session_id}-search-{i}",
                "message": query,
                "stream": False
            }
            
            try:
                start_time = time.time()
                response = requests.post(f"{self.api_url}/chat/send", json=chat_data, timeout=60)
                end_time = time.time()
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract key information
                    documents_referenced = result.get('documents_referenced', 0)
                    response_type = result.get('response_type', 'unknown')
                    ai_response = result.get('response', {})
                    
                    print(f"   ✅ Response received in {end_time - start_time:.2f}s")
                    print(f"   📄 Documents referenced: {documents_referenced}")
                    print(f"   🔧 Response type: {response_type}")
                    
                    # Analyze the response content
                    if isinstance(ai_response, dict):
                        summary = ai_response.get('summary', '')
                        details = ai_response.get('details', {})
                        
                        print(f"   📋 Structured response format")
                        print(f"   📝 Summary length: {len(summary)} characters")
                        
                        # Check if it's a generic "no information" response
                        response_text = json.dumps(ai_response).lower()
                        generic_phrases = [
                            "no information",
                            "don't have information",
                            "not available in the knowledge base",
                            "cannot find information"
                        ]
                        
                        is_generic = any(phrase in response_text for phrase in generic_phrases)
                        
                        if is_generic:
                            print(f"   ❌ GENERIC RESPONSE DETECTED: {summary[:100]}...")
                            results.append(False)
                        elif documents_referenced > 0:
                            print(f"   ✅ KNOWLEDGE BASE SEARCH SUCCESSFUL")
                            print(f"   📄 Found relevant information from {documents_referenced} documents")
                            print(f"   📝 Summary: {summary[:150]}...")
                            results.append(True)
                        else:
                            print(f"   ⚠️  Response generated but no documents referenced")
                            print(f"   📝 Summary: {summary[:150]}...")
                            results.append(False)
                    else:
                        # Simple text response
                        response_text = str(ai_response).lower()
                        print(f"   📝 Text response: {str(ai_response)[:150]}...")
                        
                        generic_phrases = [
                            "no information",
                            "don't have information", 
                            "not available in the knowledge base"
                        ]
                        
                        is_generic = any(phrase in response_text for phrase in generic_phrases)
                        results.append(not is_generic and documents_referenced > 0)
                        
                else:
                    print(f"   ❌ Chat request failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    results.append(False)
                    
            except requests.exceptions.Timeout:
                print(f"   ❌ Request timed out after 60 seconds")
                results.append(False)
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append(False)
        
        return results
    
    def test_document_processing_status(self):
        """Check if approved documents are actually processed and chunked"""
        print("\n📄 Testing Document Processing Status...")
        print("-" * 50)
        
        if not self.auth_token:
            if not self.authenticate_admin():
                return False
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            # Get admin documents (includes all documents)
            response = requests.get(f"{self.api_url}/documents/admin", headers=headers)
            if response.status_code == 200:
                documents = response.json()
                
                print(f"📋 Found {len(documents)} total documents")
                
                approved_docs = [doc for doc in documents if doc.get('approval_status') == 'approved']
                processed_docs = [doc for doc in approved_docs if doc.get('processed', False)]
                
                print(f"✅ Approved documents: {len(approved_docs)}")
                print(f"✅ Processed documents: {len(processed_docs)}")
                
                print(f"\n📄 Document Details:")
                for i, doc in enumerate(approved_docs[:5], 1):  # Show first 5
                    name = doc.get('original_name', 'Unknown')
                    status = doc.get('approval_status', 'Unknown')
                    processed = doc.get('processed', False)
                    chunks = doc.get('chunks_count', 0)
                    processing_status = doc.get('processing_status', 'unknown')
                    
                    print(f"   {i}. {name}")
                    print(f"      Status: {status} | Processed: {processed} | Chunks: {chunks}")
                    print(f"      Processing Status: {processing_status}")
                
                return len(processed_docs) > 0
                
            else:
                print(f"❌ Failed to get documents: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking documents: {e}")
            return False
    
    def test_cloud_mode_rag_search(self):
        """Test if cloud mode RAG search functions correctly"""
        print("\n☁️  Testing Cloud Mode RAG Search...")
        print("-" * 50)
        
        # Test a simple search that should definitely find results if the system is working
        test_query = "company policy"
        
        chat_data = {
            "session_id": f"{self.session_id}-cloud-test",
            "message": test_query,
            "stream": False
        }
        
        try:
            print(f"🔍 Testing cloud search with query: '{test_query}'")
            
            response = requests.post(f"{self.api_url}/chat/send", json=chat_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                documents_referenced = result.get('documents_referenced', 0)
                
                print(f"✅ Cloud mode search completed")
                print(f"📄 Documents referenced: {documents_referenced}")
                
                if documents_referenced > 0:
                    print(f"✅ Cloud mode RAG search is working correctly")
                    return True
                else:
                    print(f"❌ Cloud mode RAG search not finding documents")
                    return False
            else:
                print(f"❌ Cloud mode search failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Cloud mode search error: {e}")
            return False
    
    def run_investigation(self):
        """Run complete RAG search failure investigation"""
        print("🚨 RAG SEARCH FAILURE INVESTIGATION")
        print("=" * 60)
        print("Issue: Chat queries returning generic 'no information' responses")
        print("Expected: Should search through uploaded/approved documents")
        print("=" * 60)
        
        # Test 1: RAG Collection Stats
        stats_success, chunk_count = self.test_rag_collection_stats()
        
        # Test 2: Document Processing Status  
        processing_success = self.test_document_processing_status()
        
        # Test 3: Direct RAG Search with problematic queries
        search_results = self.test_direct_rag_search()
        
        # Test 4: Cloud Mode RAG Search
        cloud_success = self.test_cloud_mode_rag_search()
        
        # Summary
        print("\n🎯 INVESTIGATION SUMMARY")
        print("=" * 60)
        
        print(f"📊 RAG Collection Stats: {'✅ PASS' if stats_success else '❌ FAIL'}")
        if stats_success:
            print(f"   - {chunk_count} chunks available for search")
        
        print(f"📄 Document Processing: {'✅ PASS' if processing_success else '❌ FAIL'}")
        
        search_success_count = sum(search_results)
        print(f"🔍 RAG Search Tests: {search_success_count}/{len(search_results)} PASSED")
        
        print(f"☁️  Cloud Mode Search: {'✅ PASS' if cloud_success else '❌ FAIL'}")
        
        # Root cause analysis
        print(f"\n🔍 ROOT CAUSE ANALYSIS:")
        
        if not stats_success:
            print("❌ CRITICAL: RAG system has no indexed documents")
            print("   → Documents are not being processed into vector database")
            print("   → Check document approval and processing pipeline")
        elif not processing_success:
            print("❌ CRITICAL: Documents not processed despite being approved")
            print("   → Document processing pipeline is broken")
            print("   → Check RAG processing background tasks")
        elif search_success_count == 0:
            print("❌ CRITICAL: RAG search not finding relevant documents")
            print("   → Vector similarity search may be failing")
            print("   → Check embedding generation and search thresholds")
        elif search_success_count < len(search_results):
            print("⚠️  PARTIAL: Some RAG searches failing")
            print("   → Inconsistent search results")
            print("   → May be query-specific or threshold issues")
        else:
            print("✅ SUCCESS: RAG system appears to be working correctly")
            print("   → Issue may be frontend-specific or user-specific")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if not stats_success or not processing_success:
            print("1. Reprocess all approved documents through RAG pipeline")
            print("2. Check document approval workflow triggers RAG processing")
            print("3. Verify ChromaDB connection and collection setup")
        elif search_success_count < len(search_results):
            print("1. Review RAG search similarity thresholds")
            print("2. Check embedding model consistency")
            print("3. Verify document chunking strategy")
        else:
            print("1. Check frontend chat integration")
            print("2. Verify user session management")
            print("3. Test with different user accounts")
        
        return {
            'stats_success': stats_success,
            'processing_success': processing_success,
            'search_results': search_results,
            'cloud_success': cloud_success,
            'overall_success': stats_success and processing_success and all(search_results) and cloud_success
        }

if __name__ == "__main__":
    tester = RAGInvestigationTester()
    results = tester.run_investigation()
    
    if results['overall_success']:
        print(f"\n🎉 RAG SYSTEM IS WORKING CORRECTLY")
        print("The reported issue may be frontend-specific or user-specific")
    else:
        print(f"\n🚨 RAG SYSTEM ISSUES DETECTED")
        print("Backend RAG search functionality needs attention")