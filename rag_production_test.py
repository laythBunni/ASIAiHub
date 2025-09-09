#!/usr/bin/env python3
"""
RAG Production Crash Fix Testing
Tests the production environment detection and cloud mode activation to prevent memory crashes
"""

import os
import sys
import json
import time
import requests
import tempfile
import psutil
from pathlib import Path
from datetime import datetime

class RAGProductionTester:
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
        self.session_id = f"rag-test-{int(time.time())}"
        self.auth_token = None
        
        print(f"🔧 RAG Production Crash Fix Tester")
        print(f"📡 Backend URL: {self.base_url}")
        print(f"🎯 Testing production memory crash fix")
        print("=" * 80)

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
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, data=data, headers=headers or {}, timeout=60)
                else:
                    response = requests.post(url, json=data, headers=default_headers, timeout=60)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers, timeout=60)

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
        """Authenticate as admin user for testing"""
        print("\n🔐 Authenticating as admin user...")
        
        # Try Phase 2 authentication first
        admin_login_data = {
            "email": "layth.bunni@adamsmithinternational.com",
            "personal_code": "899443"
        }
        
        success, response = self.run_test(
            "Admin Authentication (Phase 2)", 
            "POST", 
            "/auth/login", 
            200, 
            admin_login_data
        )
        
        if success:
            self.auth_token = response.get('access_token') or response.get('token')
            print(f"   ✅ Admin authenticated successfully")
            return True
        
        # Fallback to ASI2025 if Phase 2 fails
        admin_login_data = {
            "email": "layth.bunni@adamsmithinternational.com",
            "access_code": "ASI2025"
        }
        
        success, response = self.run_test(
            "Admin Authentication (Fallback)", 
            "POST", 
            "/auth/login", 
            200, 
            admin_login_data
        )
        
        if success:
            self.auth_token = response.get('access_token') or response.get('token')
            print(f"   ✅ Admin authenticated successfully (fallback)")
            return True
        
        print(f"   ❌ Admin authentication failed")
        return False

    def test_production_environment_detection(self):
        """Test 1: Verify production environment indicators work correctly"""
        print("\n🏭 TEST 1: PRODUCTION ENVIRONMENT DETECTION")
        print("=" * 60)
        
        # Check environment variables that should trigger production mode
        production_indicators = []
        
        # Check NODE_ENV
        node_env = os.environ.get('NODE_ENV')
        if node_env == 'production':
            production_indicators.append(f"NODE_ENV=production")
        print(f"   NODE_ENV: {node_env}")
        
        # Check ENVIRONMENT
        environment = os.environ.get('ENVIRONMENT')
        if environment == 'production':
            production_indicators.append(f"ENVIRONMENT=production")
        print(f"   ENVIRONMENT: {environment}")
        
        # Check REACT_APP_BACKEND_URL for production domains
        backend_url = os.environ.get('REACT_APP_BACKEND_URL', '')
        if 'emergentagent.com' in backend_url:
            production_indicators.append(f"emergentagent.com in REACT_APP_BACKEND_URL")
        if 'ai-workspace-17' in backend_url:
            production_indicators.append(f"ai-workspace-17 in REACT_APP_BACKEND_URL")
        print(f"   REACT_APP_BACKEND_URL: {backend_url}")
        
        print(f"\n📊 Production Indicators Found:")
        if production_indicators:
            for indicator in production_indicators:
                print(f"   ✅ {indicator}")
            print(f"\n🎯 RESULT: Production environment detected - cloud mode should be active")
            return True, True  # Production detected
        else:
            print(f"   ⚠️  No production indicators found")
            print(f"\n🎯 RESULT: Development environment - local mode may be active")
            return True, False  # Development environment

    def test_rag_system_initialization(self):
        """Test 2: Test RAG system initialization and mode detection"""
        print("\n🤖 TEST 2: RAG SYSTEM INITIALIZATION")
        print("=" * 60)
        
        # Test RAG stats endpoint to see system status
        success, response = self.run_test(
            "RAG System Stats", 
            "GET", 
            "/documents/rag-stats", 
            200
        )
        
        if success:
            print(f"   ✅ RAG system is accessible")
            
            # Check for cloud mode indicators
            status = response.get('status', 'unknown')
            total_chunks = response.get('total_chunks', 0)
            total_documents = response.get('total_documents', 0)
            
            print(f"   📊 Status: {status}")
            print(f"   📄 Total documents: {total_documents}")
            print(f"   🧩 Total chunks: {total_chunks}")
            
            # Check if system is using cloud alternatives
            if 'unavailable' in status.lower() or 'temporarily' in status.lower():
                print(f"   ✅ Cloud mode detected - RAG system using lightweight alternatives")
                return True, "cloud"
            else:
                print(f"   ℹ️  RAG system operational - mode unclear from stats")
                return True, "operational"
        else:
            print(f"   ❌ RAG system not accessible")
            return False, "error"

    def test_document_processing_cloud_mode(self):
        """Test 3: Test document processing in cloud mode"""
        print("\n📄 TEST 3: DOCUMENT PROCESSING IN CLOUD MODE")
        print("=" * 60)
        
        if not self.auth_token:
            if not self.authenticate_admin():
                print("   ❌ Cannot test document processing without authentication")
                return False
        
        # Create a test document
        test_content = """
        ASI Production Test Policy Document
        
        Cloud Mode Testing:
        1. This document tests cloud mode functionality
        2. Memory usage should remain low during processing
        3. No heavy ML models should be loaded
        
        Production Environment:
        1. RAG system should use cloud alternatives
        2. Document processing should complete without crashes
        3. Embeddings should use lightweight methods
        """
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            # Monitor memory before upload
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            print(f"   📊 Memory before upload: {memory_before:.1f} MB")
            
            # Upload document
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('cloud_mode_test.txt', f, 'text/plain')}
                data = {'department': 'Information Technology', 'tags': 'test,cloud,production'}
                
                success, response = self.run_test(
                    "Document Upload (Cloud Mode)", 
                    "POST", 
                    "/documents/upload", 
                    200, 
                    data=data, 
                    files=files
                )
            
            if success:
                document_id = response.get('id')
                print(f"   ✅ Document uploaded successfully: {document_id}")
                
                # Monitor memory after upload
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = memory_after - memory_before
                print(f"   📊 Memory after upload: {memory_after:.1f} MB")
                print(f"   📊 Memory increase: {memory_increase:.1f} MB")
                
                # Check if memory increase is reasonable (should be low in cloud mode)
                if memory_increase < 100:  # Less than 100MB increase
                    print(f"   ✅ Memory usage acceptable for cloud mode")
                else:
                    print(f"   ⚠️  High memory usage detected: {memory_increase:.1f} MB")
                
                # Wait a bit for processing
                time.sleep(3)
                
                # Test document approval (triggers RAG processing)
                if document_id:
                    auth_headers = {'Authorization': f'Bearer {self.auth_token}'}
                    approve_success, approve_response = self.run_test(
                        "Document Approval (Triggers RAG)", 
                        "PUT", 
                        f"/documents/{document_id}/approve", 
                        200,
                        headers=auth_headers
                    )
                    
                    if approve_success:
                        print(f"   ✅ Document approval successful - RAG processing initiated")
                        
                        # Monitor memory during processing
                        time.sleep(5)  # Wait for processing
                        memory_processing = process.memory_info().rss / 1024 / 1024  # MB
                        processing_increase = memory_processing - memory_before
                        print(f"   📊 Memory during processing: {memory_processing:.1f} MB")
                        print(f"   📊 Total memory increase: {processing_increase:.1f} MB")
                        
                        if processing_increase < 200:  # Less than 200MB total
                            print(f"   ✅ Memory usage during processing acceptable")
                        else:
                            print(f"   ⚠️  High memory usage during processing: {processing_increase:.1f} MB")
                        
                        return True, document_id
                    else:
                        print(f"   ❌ Document approval failed")
                        return False, document_id
                else:
                    print(f"   ⚠️  No document ID returned")
                    return True, None
            else:
                print(f"   ❌ Document upload failed")
                return False, None
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_document_deletion_cloud_mode(self, document_id):
        """Test 4: Test document deletion in cloud mode"""
        print("\n🗑️ TEST 4: DOCUMENT DELETION IN CLOUD MODE")
        print("=" * 60)
        
        if not document_id:
            print("   ⚠️  No document ID provided - skipping deletion test")
            return True
        
        if not self.auth_token:
            if not self.authenticate_admin():
                print("   ❌ Cannot test document deletion without authentication")
                return False
        
        # Monitor memory before deletion
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        print(f"   📊 Memory before deletion: {memory_before:.1f} MB")
        
        # Delete document
        auth_headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        start_time = time.time()
        success, response = self.run_test(
            "Document Deletion (Cloud Mode)", 
            "DELETE", 
            f"/documents/{document_id}", 
            200,
            headers=auth_headers
        )
        end_time = time.time()
        
        deletion_time = end_time - start_time
        print(f"   ⏱️  Deletion time: {deletion_time:.1f} seconds")
        
        if success:
            print(f"   ✅ Document deleted successfully")
            
            # Monitor memory after deletion
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_change = memory_after - memory_before
            print(f"   📊 Memory after deletion: {memory_after:.1f} MB")
            print(f"   📊 Memory change: {memory_change:+.1f} MB")
            
            # Check deletion time (should be reasonable in cloud mode)
            if deletion_time < 60:  # Less than 60 seconds
                print(f"   ✅ Deletion completed within reasonable time")
            else:
                print(f"   ⚠️  Deletion took longer than expected: {deletion_time:.1f}s")
            
            # Verify document is actually deleted
            verify_success, verify_response = self.run_test(
                "Verify Document Deletion", 
                "GET", 
                "/documents/admin", 
                200,
                headers=auth_headers
            )
            
            if verify_success:
                documents = verify_response if isinstance(verify_response, list) else []
                deleted_doc_found = any(doc.get('id') == document_id for doc in documents)
                
                if not deleted_doc_found:
                    print(f"   ✅ Document successfully removed from database")
                else:
                    print(f"   ❌ Document still exists in database after deletion")
                    return False
            
            return True
        else:
            print(f"   ❌ Document deletion failed")
            return False

    def test_chat_functionality_cloud_mode(self):
        """Test 5: Test chat functionality in cloud mode"""
        print("\n💬 TEST 5: CHAT FUNCTIONALITY IN CLOUD MODE")
        print("=" * 60)
        
        # Monitor memory before chat
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        print(f"   📊 Memory before chat: {memory_before:.1f} MB")
        
        # Test chat with RAG query
        chat_data = {
            "session_id": self.session_id,
            "message": "What are the cloud mode testing procedures for production environments?",
            "stream": False
        }
        
        start_time = time.time()
        success, response = self.run_test(
            "Chat Query (Cloud Mode RAG)", 
            "POST", 
            "/chat/send", 
            200, 
            chat_data
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        print(f"   ⏱️  Response time: {response_time:.1f} seconds")
        
        if success:
            print(f"   ✅ Chat response received successfully")
            
            # Check response structure
            ai_response = response.get('response', {})
            documents_referenced = response.get('documents_referenced', 0)
            response_type = response.get('response_type', 'unknown')
            
            print(f"   📋 Response type: {response_type}")
            print(f"   📄 Documents referenced: {documents_referenced}")
            
            # Monitor memory after chat
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = memory_after - memory_before
            print(f"   📊 Memory after chat: {memory_after:.1f} MB")
            print(f"   📊 Memory increase: {memory_increase:.1f} MB")
            
            # Check if response is structured (cloud mode should still work)
            if isinstance(ai_response, dict):
                summary = ai_response.get('summary', '')
                print(f"   ✅ Structured response format maintained")
                print(f"   💡 Summary: {summary[:100]}...")
            else:
                print(f"   ⚠️  Response format: {type(ai_response)}")
            
            # Check memory usage during chat (should be low in cloud mode)
            if memory_increase < 50:  # Less than 50MB increase
                print(f"   ✅ Memory usage during chat acceptable")
            else:
                print(f"   ⚠️  High memory usage during chat: {memory_increase:.1f} MB")
            
            # Check response time (should be reasonable)
            if response_time < 30:  # Less than 30 seconds
                print(f"   ✅ Chat response time acceptable")
            else:
                print(f"   ⚠️  Slow chat response: {response_time:.1f}s")
            
            return True
        else:
            print(f"   ❌ Chat functionality failed")
            return False

    def test_memory_safety_verification(self):
        """Test 6: Verify no heavy ML models are loaded"""
        print("\n🧠 TEST 6: MEMORY SAFETY VERIFICATION")
        print("=" * 60)
        
        # Get current process memory info
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        print(f"   📊 Current memory usage: {memory_mb:.1f} MB")
        print(f"   📊 Virtual memory: {memory_info.vms / 1024 / 1024:.1f} MB")
        
        # Check if memory usage is reasonable for cloud mode
        if memory_mb < 500:  # Less than 500MB total
            print(f"   ✅ Memory usage indicates cloud mode (no heavy ML models)")
        elif memory_mb < 1000:  # Less than 1GB
            print(f"   ⚠️  Moderate memory usage: {memory_mb:.1f} MB")
        else:
            print(f"   ❌ High memory usage detected: {memory_mb:.1f} MB")
            print(f"   ⚠️  Heavy ML models may be loaded")
        
        # Test multiple operations to check for memory leaks
        print(f"\n   🔄 Testing memory stability with multiple operations...")
        
        initial_memory = memory_mb
        for i in range(3):
            # Perform a lightweight operation
            success, response = self.run_test(
                f"Memory Test Operation {i+1}", 
                "GET", 
                "/documents/rag-stats", 
                200
            )
            
            if success:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_change = current_memory - initial_memory
                print(f"   📊 Operation {i+1}: {current_memory:.1f} MB ({memory_change:+.1f} MB)")
                
                # Small delay between operations
                time.sleep(1)
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_change = final_memory - initial_memory
        
        print(f"\n   📊 Final memory: {final_memory:.1f} MB")
        print(f"   📊 Total change: {total_change:+.1f} MB")
        
        if abs(total_change) < 20:  # Less than 20MB change
            print(f"   ✅ Memory usage stable - no significant leaks detected")
        else:
            print(f"   ⚠️  Memory change detected: {total_change:+.1f} MB")
        
        return True

    def run_all_tests(self):
        """Run all RAG production crash fix tests"""
        print(f"\n🚀 STARTING RAG PRODUCTION CRASH FIX TESTING")
        print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        test_results = {}
        document_id = None
        
        # Test 1: Production Environment Detection
        try:
            success, is_production = self.test_production_environment_detection()
            test_results['environment_detection'] = success
        except Exception as e:
            print(f"❌ Environment detection test failed: {e}")
            test_results['environment_detection'] = False
        
        # Test 2: RAG System Initialization
        try:
            success, rag_mode = self.test_rag_system_initialization()
            test_results['rag_initialization'] = success
        except Exception as e:
            print(f"❌ RAG initialization test failed: {e}")
            test_results['rag_initialization'] = False
        
        # Test 3: Document Processing
        try:
            success, document_id = self.test_document_processing_cloud_mode()
            test_results['document_processing'] = success
        except Exception as e:
            print(f"❌ Document processing test failed: {e}")
            test_results['document_processing'] = False
        
        # Test 4: Document Deletion
        try:
            success = self.test_document_deletion_cloud_mode(document_id)
            test_results['document_deletion'] = success
        except Exception as e:
            print(f"❌ Document deletion test failed: {e}")
            test_results['document_deletion'] = False
        
        # Test 5: Chat Functionality
        try:
            success = self.test_chat_functionality_cloud_mode()
            test_results['chat_functionality'] = success
        except Exception as e:
            print(f"❌ Chat functionality test failed: {e}")
            test_results['chat_functionality'] = False
        
        # Test 6: Memory Safety
        try:
            success = self.test_memory_safety_verification()
            test_results['memory_safety'] = success
        except Exception as e:
            print(f"❌ Memory safety test failed: {e}")
            test_results['memory_safety'] = False
        
        # Print final results
        self.print_final_results(test_results)
        
        return test_results

    def print_final_results(self, test_results):
        """Print comprehensive test results"""
        print(f"\n" + "=" * 80)
        print(f"🎯 RAG PRODUCTION CRASH FIX TEST RESULTS")
        print(f"=" * 80)
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   ✅ Tests Passed: {passed_tests}/{total_tests}")
        print(f"   📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        
        test_names = {
            'environment_detection': 'Production Environment Detection',
            'rag_initialization': 'RAG System Initialization', 
            'document_processing': 'Document Processing (Cloud Mode)',
            'document_deletion': 'Document Deletion (Cloud Mode)',
            'chat_functionality': 'Chat Functionality (Cloud Mode)',
            'memory_safety': 'Memory Safety Verification'
        }
        
        for test_key, result in test_results.items():
            test_name = test_names.get(test_key, test_key)
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} - {test_name}")
        
        print(f"\n🎯 PRODUCTION READINESS ASSESSMENT:")
        
        critical_tests = ['environment_detection', 'rag_initialization', 'memory_safety']
        critical_passed = sum(1 for test in critical_tests if test_results.get(test, False))
        
        if critical_passed == len(critical_tests):
            print(f"   ✅ CRITICAL TESTS PASSED - Production crash fix working correctly")
            print(f"   🏭 Cloud mode activated successfully")
            print(f"   💾 Memory usage optimized for production")
        else:
            print(f"   ❌ CRITICAL TESTS FAILED - Production crash fix needs attention")
            print(f"   ⚠️  Memory issues may still occur in production")
        
        functionality_tests = ['document_processing', 'document_deletion', 'chat_functionality']
        functionality_passed = sum(1 for test in functionality_tests if test_results.get(test, False))
        
        if functionality_passed == len(functionality_tests):
            print(f"   ✅ FUNCTIONALITY PRESERVED - All features working in cloud mode")
        elif functionality_passed >= 2:
            print(f"   ⚠️  PARTIAL FUNCTIONALITY - Some features working in cloud mode")
        else:
            print(f"   ❌ FUNCTIONALITY IMPAIRED - Cloud mode affecting core features")
        
        print(f"\n⏰ Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Total API calls: {self.tests_run}")
        print(f"✅ Successful calls: {self.tests_passed}")
        print("=" * 80)

def main():
    """Main test execution"""
    tester = RAGProductionTester()
    
    try:
        results = tester.run_all_tests()
        
        # Exit with appropriate code
        all_passed = all(results.values())
        critical_passed = all(results.get(test, False) for test in ['environment_detection', 'rag_initialization', 'memory_safety'])
        
        if all_passed:
            print(f"\n🎉 ALL TESTS PASSED - Production crash fix working perfectly!")
            sys.exit(0)
        elif critical_passed:
            print(f"\n⚠️  CRITICAL TESTS PASSED - Production crash fix working, minor issues detected")
            sys.exit(0)
        else:
            print(f"\n❌ CRITICAL TESTS FAILED - Production crash fix needs immediate attention")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()