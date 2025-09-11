#!/usr/bin/env python3
"""
Production vs Preview Environment RAG Testing
============================================

This script tests the actual deployed environments to understand why RAG works 
locally but fails in preview/production as reported by the user.

Key Focus Areas:
1. Test Preview Environment RAG (asi-platform.preview.emergentagent.com)
2. Test Production Environment RAG (if accessible)
3. Environment Comparison - Local vs Preview vs Production
4. Document processing pipeline verification
5. Chat functionality with RAG integration
6. Storage system verification (ChromaDB vs other)
"""

import requests
import json
import time
import sys
from datetime import datetime
from pathlib import Path

class ProductionEnvironmentTester:
    def __init__(self):
        # Environment URLs
        self.environments = {
            'preview': 'https://doc-embeddings.preview.emergentagent.com',
            'production_1': 'https://asiaihub.com',
            'production_2': 'https://ai-workspace-17.emergent.host'
        }
        
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = f"prod-test-{int(time.time())}"
        self.results = {}
        
        print("🌐 PRODUCTION VS PREVIEW ENVIRONMENT RAG TESTING")
        print("=" * 60)
        print("Testing environments:")
        for name, url in self.environments.items():
            print(f"  {name}: {url}")
        print()

    def test_environment(self, env_name, base_url):
        """Test a specific environment comprehensively"""
        print(f"\n🔍 TESTING {env_name.upper()} ENVIRONMENT")
        print(f"URL: {base_url}")
        print("-" * 50)
        
        api_url = f"{base_url}/api"
        env_results = {
            'base_url': base_url,
            'api_url': api_url,
            'tests': {},
            'rag_working': False,
            'documents_count': 0,
            'chunks_count': 0,
            'chat_working': False,
            'errors': []
        }
        
        # Test 1: Basic API Health Check
        print(f"\n📡 Test 1: API Health Check...")
        try:
            response = requests.get(f"{api_url}/", timeout=30)
            if response.status_code == 200:
                print(f"✅ API accessible - Status: {response.status_code}")
                env_results['tests']['api_health'] = True
            else:
                print(f"❌ API not accessible - Status: {response.status_code}")
                env_results['tests']['api_health'] = False
                env_results['errors'].append(f"API health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ API connection failed: {str(e)}")
            env_results['tests']['api_health'] = False
            env_results['errors'].append(f"API connection error: {str(e)}")
            return env_results
        
        # Test 2: RAG Stats Endpoint
        print(f"\n📊 Test 2: RAG Stats Endpoint...")
        try:
            response = requests.get(f"{api_url}/documents/rag-stats", timeout=30)
            if response.status_code == 200:
                rag_stats = response.json()
                print(f"✅ RAG Stats accessible")
                print(f"   Vector DB Stats: {rag_stats.get('vector_database', {})}")
                print(f"   Total Documents: {rag_stats.get('total_documents', 0)}")
                print(f"   Processed Documents: {rag_stats.get('processed_documents', 0)}")
                
                # Extract key metrics
                vector_db = rag_stats.get('vector_database', {})
                env_results['chunks_count'] = vector_db.get('total_chunks', 0)
                env_results['documents_count'] = rag_stats.get('total_documents', 0)
                env_results['tests']['rag_stats'] = True
                
                if env_results['chunks_count'] > 0:
                    print(f"✅ RAG system has {env_results['chunks_count']} chunks")
                    env_results['rag_working'] = True
                else:
                    print(f"⚠️  RAG system has 0 chunks - may not be working")
                    env_results['errors'].append("RAG system has 0 chunks")
                    
            else:
                print(f"❌ RAG Stats failed - Status: {response.status_code}")
                env_results['tests']['rag_stats'] = False
                env_results['errors'].append(f"RAG stats failed: {response.status_code}")
        except Exception as e:
            print(f"❌ RAG Stats error: {str(e)}")
            env_results['tests']['rag_stats'] = False
            env_results['errors'].append(f"RAG stats error: {str(e)}")
        
        # Test 3: Document List
        print(f"\n📄 Test 3: Document List...")
        try:
            response = requests.get(f"{api_url}/documents", timeout=30)
            if response.status_code == 200:
                documents = response.json()
                print(f"✅ Documents accessible - Found {len(documents)} approved documents")
                env_results['tests']['documents'] = True
                
                if len(documents) > 0:
                    sample_doc = documents[0]
                    print(f"   Sample document: {sample_doc.get('original_name', 'Unknown')}")
                    print(f"   Processing status: {sample_doc.get('processing_status', 'Unknown')}")
                    print(f"   Chunks count: {sample_doc.get('chunks_count', 0)}")
                else:
                    print(f"⚠️  No approved documents found")
                    env_results['errors'].append("No approved documents found")
                    
            else:
                print(f"❌ Documents failed - Status: {response.status_code}")
                env_results['tests']['documents'] = False
                env_results['errors'].append(f"Documents endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Documents error: {str(e)}")
            env_results['tests']['documents'] = False
            env_results['errors'].append(f"Documents error: {str(e)}")
        
        # Test 4: Chat Functionality
        print(f"\n💬 Test 4: Chat Functionality...")
        chat_data = {
            "session_id": f"{self.session_id}-{env_name}",
            "message": "What is the company travel policy for business trips?",
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{api_url}/chat/send", 
                json=chat_data, 
                headers={'Content-Type': 'application/json'},
                timeout=120  # Longer timeout for LLM processing
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                print(f"✅ Chat working - Status: {response.status_code}")
                
                ai_response = chat_response.get('response', {})
                docs_referenced = chat_response.get('documents_referenced', 0)
                response_type = chat_response.get('response_type', 'unknown')
                
                print(f"   Response type: {response_type}")
                print(f"   Documents referenced: {docs_referenced}")
                
                if isinstance(ai_response, dict):
                    summary = ai_response.get('summary', '')
                    print(f"   Response summary: {summary[:100]}...")
                    
                    # Check if response contains actual policy information
                    response_text = json.dumps(ai_response).lower()
                    policy_keywords = ['travel', 'policy', 'business', 'trip', 'expense', 'approval']
                    found_keywords = [kw for kw in policy_keywords if kw in response_text]
                    
                    if found_keywords:
                        print(f"   ✅ RAG working - Found policy keywords: {found_keywords}")
                        env_results['chat_working'] = True
                    else:
                        print(f"   ⚠️  Generic response - RAG may not be working properly")
                        env_results['errors'].append("Chat response appears generic, RAG may not be working")
                else:
                    print(f"   Response: {str(ai_response)[:100]}...")
                
                env_results['tests']['chat'] = True
                
            else:
                print(f"❌ Chat failed - Status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                    env_results['errors'].append(f"Chat error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                    env_results['errors'].append(f"Chat error: {response.text}")
                env_results['tests']['chat'] = False
                
        except requests.exceptions.Timeout:
            print(f"❌ Chat timeout - Request took longer than 120 seconds")
            env_results['tests']['chat'] = False
            env_results['errors'].append("Chat request timeout (>120s)")
        except Exception as e:
            print(f"❌ Chat error: {str(e)}")
            env_results['tests']['chat'] = False
            env_results['errors'].append(f"Chat error: {str(e)}")
        
        # Test 5: Document Upload Test (if possible)
        print(f"\n📤 Test 5: Document Upload Test...")
        test_content = f"""
        Test Document for {env_name} Environment
        
        This is a test document uploaded to verify the document processing pipeline
        in the {env_name} environment at {datetime.now().isoformat()}.
        
        Travel Policy Test Content:
        - Business travel requires manager approval
        - Expense receipts must be submitted within 30 days
        - Maximum daily allowance is $200 for meals
        """
        
        try:
            # Create temporary test file
            test_file_path = Path(f"/tmp/test_doc_{env_name}_{int(time.time())}.txt")
            with open(test_file_path, 'w') as f:
                f.write(test_content)
            
            # Upload the file
            with open(test_file_path, 'rb') as f:
                files = {'file': (f'test_doc_{env_name}.txt', f, 'text/plain')}
                data = {'department': 'Finance', 'tags': f'test,{env_name}'}
                
                response = requests.post(
                    f"{api_url}/documents/upload",
                    files=files,
                    data=data,
                    timeout=60
                )
            
            # Clean up test file
            test_file_path.unlink(missing_ok=True)
            
            if response.status_code == 200:
                upload_response = response.json()
                print(f"✅ Document upload working")
                print(f"   Document ID: {upload_response.get('id')}")
                print(f"   Message: {upload_response.get('message')}")
                env_results['tests']['upload'] = True
            else:
                print(f"❌ Document upload failed - Status: {response.status_code}")
                env_results['tests']['upload'] = False
                env_results['errors'].append(f"Document upload failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Document upload error: {str(e)}")
            env_results['tests']['upload'] = False
            env_results['errors'].append(f"Document upload error: {str(e)}")
        
        # Test 6: Chat Sessions
        print(f"\n📝 Test 6: Chat Sessions...")
        try:
            response = requests.get(f"{api_url}/chat/sessions", timeout=30)
            if response.status_code == 200:
                sessions = response.json()
                print(f"✅ Chat sessions accessible - Found {len(sessions)} sessions")
                env_results['tests']['sessions'] = True
                
                # Look for our test session
                test_session = None
                for session in sessions:
                    if session.get('id', '').startswith(f"{self.session_id}-{env_name}"):
                        test_session = session
                        break
                
                if test_session:
                    print(f"   ✅ Test session found: {test_session.get('title', 'Unknown')}")
                    print(f"   Messages count: {test_session.get('messages_count', 0)}")
                else:
                    print(f"   ⚠️  Test session not found in sessions list")
                    
            else:
                print(f"❌ Chat sessions failed - Status: {response.status_code}")
                env_results['tests']['sessions'] = False
                env_results['errors'].append(f"Chat sessions failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Chat sessions error: {str(e)}")
            env_results['tests']['sessions'] = False
            env_results['errors'].append(f"Chat sessions error: {str(e)}")
        
        # Calculate overall health
        total_tests = len(env_results['tests'])
        passed_tests = sum(1 for result in env_results['tests'].values() if result)
        env_results['health_score'] = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 {env_name.upper()} ENVIRONMENT SUMMARY:")
        print(f"   Health Score: {env_results['health_score']:.1f}% ({passed_tests}/{total_tests} tests passed)")
        print(f"   RAG Working: {'✅ Yes' if env_results['rag_working'] else '❌ No'}")
        print(f"   Chat Working: {'✅ Yes' if env_results['chat_working'] else '❌ No'}")
        print(f"   Documents: {env_results['documents_count']}")
        print(f"   Chunks: {env_results['chunks_count']}")
        
        if env_results['errors']:
            print(f"   Errors: {len(env_results['errors'])}")
            for error in env_results['errors'][:3]:  # Show first 3 errors
                print(f"     - {error}")
        
        return env_results

    def run_comprehensive_test(self):
        """Run comprehensive testing across all environments"""
        print("🚀 Starting comprehensive environment testing...")
        
        for env_name, base_url in self.environments.items():
            try:
                self.results[env_name] = self.test_environment(env_name, base_url)
                time.sleep(2)  # Brief pause between environments
            except Exception as e:
                print(f"❌ Failed to test {env_name}: {str(e)}")
                self.results[env_name] = {
                    'base_url': base_url,
                    'error': str(e),
                    'health_score': 0,
                    'rag_working': False,
                    'chat_working': False
                }
        
        self.generate_comparison_report()

    def generate_comparison_report(self):
        """Generate comprehensive comparison report"""
        print(f"\n" + "=" * 80)
        print("🔍 PRODUCTION VS PREVIEW ENVIRONMENT COMPARISON REPORT")
        print("=" * 80)
        
        # Environment Status Table
        print(f"\n📊 ENVIRONMENT STATUS OVERVIEW:")
        print(f"{'Environment':<15} {'Health':<8} {'RAG':<6} {'Chat':<6} {'Docs':<6} {'Chunks':<8} {'Status'}")
        print("-" * 70)
        
        for env_name, results in self.results.items():
            health = f"{results.get('health_score', 0):.1f}%"
            rag_status = "✅" if results.get('rag_working', False) else "❌"
            chat_status = "✅" if results.get('chat_working', False) else "❌"
            docs = str(results.get('documents_count', 0))
            chunks = str(results.get('chunks_count', 0))
            
            if results.get('error'):
                status = "ERROR"
            elif results.get('health_score', 0) >= 80:
                status = "HEALTHY"
            elif results.get('health_score', 0) >= 50:
                status = "PARTIAL"
            else:
                status = "FAILING"
            
            print(f"{env_name:<15} {health:<8} {rag_status:<6} {chat_status:<6} {docs:<6} {chunks:<8} {status}")
        
        # Detailed Analysis
        print(f"\n🔍 DETAILED ANALYSIS:")
        
        # Find working environments
        working_envs = [name for name, results in self.results.items() 
                       if results.get('rag_working', False) and results.get('chat_working', False)]
        
        failing_envs = [name for name, results in self.results.items() 
                       if not results.get('rag_working', False) or not results.get('chat_working', False)]
        
        if working_envs:
            print(f"\n✅ WORKING ENVIRONMENTS: {', '.join(working_envs)}")
            for env in working_envs:
                results = self.results[env]
                print(f"   {env}: {results['chunks_count']} chunks, {results['documents_count']} documents")
        
        if failing_envs:
            print(f"\n❌ FAILING ENVIRONMENTS: {', '.join(failing_envs)}")
            for env in failing_envs:
                results = self.results[env]
                print(f"   {env}: Issues detected")
                for error in results.get('errors', [])[:2]:
                    print(f"     - {error}")
        
        # Root Cause Analysis
        print(f"\n🔍 ROOT CAUSE ANALYSIS:")
        
        # Check if it's a universal failure or environment-specific
        all_failing = all(not results.get('rag_working', False) for results in self.results.values())
        all_working = all(results.get('rag_working', False) for results in self.results.values())
        
        if all_failing:
            print("❌ ALL ENVIRONMENTS FAILING:")
            print("   - This suggests a fundamental issue with RAG system configuration")
            print("   - Possible causes: LLM API issues, ChromaDB configuration, document processing")
            print("   - Recommendation: Check LLM integration and vector database setup")
        elif all_working:
            print("✅ ALL ENVIRONMENTS WORKING:")
            print("   - RAG system appears to be functioning correctly across all environments")
            print("   - User-reported issues may be frontend-specific or network-related")
        else:
            print("⚠️  MIXED RESULTS - ENVIRONMENT-SPECIFIC ISSUES:")
            print("   - Some environments working, others failing")
            print("   - This suggests deployment or configuration differences")
            print("   - Recommendation: Compare working vs failing environment configurations")
        
        # Storage System Analysis
        print(f"\n💾 STORAGE SYSTEM ANALYSIS:")
        for env_name, results in self.results.items():
            chunks = results.get('chunks_count', 0)
            if chunks > 0:
                print(f"   {env_name}: {chunks} chunks stored (likely ChromaDB)")
            else:
                print(f"   {env_name}: 0 chunks (storage system may not be working)")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if 'preview' in self.results:
            preview_results = self.results['preview']
            if preview_results.get('rag_working', False):
                print("✅ Preview environment RAG is working correctly")
            else:
                print("❌ Preview environment RAG is failing - this matches user reports")
                print("   - Check ChromaDB persistence in preview environment")
                print("   - Verify document processing pipeline")
                print("   - Check LLM integration configuration")
        
        production_working = any(
            results.get('rag_working', False) 
            for name, results in self.results.items() 
            if 'production' in name
        )
        
        if production_working:
            print("✅ At least one production environment is working")
        else:
            print("❌ All production environments failing")
            print("   - Urgent: Production RAG system needs immediate attention")
            print("   - Check deployment configuration differences")
            print("   - Verify environment variables and database connections")
        
        # Next Steps
        print(f"\n🎯 NEXT STEPS:")
        print("1. Focus on environments showing 0 chunks - likely storage issues")
        print("2. Compare environment configurations (ChromaDB paths, LLM keys)")
        print("3. Check deployment logs for RAG processing errors")
        print("4. Verify document approval workflow in failing environments")
        print("5. Test document upload → approval → RAG processing pipeline")
        
        # Final Summary
        print(f"\n📋 FINAL SUMMARY:")
        total_envs = len(self.results)
        working_count = len(working_envs)
        
        if working_count == 0:
            print("🚨 CRITICAL: No environments have working RAG systems")
            print("   User reports are accurate - RAG is not functioning in deployed environments")
        elif working_count == total_envs:
            print("✅ SUCCESS: All environments have working RAG systems")
            print("   User issues may be frontend-specific or intermittent")
        else:
            print(f"⚠️  PARTIAL: {working_count}/{total_envs} environments working")
            print("   Environment-specific configuration issues detected")
        
        print("=" * 80)

def main():
    """Main execution function"""
    tester = ProductionEnvironmentTester()
    
    try:
        tester.run_comprehensive_test()
        
        # Save results to file for analysis
        results_file = Path("/app/environment_test_results.json")
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': tester.results,
                'summary': {
                    'total_environments': len(tester.results),
                    'working_environments': [
                        name for name, results in tester.results.items() 
                        if results.get('rag_working', False)
                    ],
                    'failing_environments': [
                        name for name, results in tester.results.items() 
                        if not results.get('rag_working', False)
                    ]
                }
            }, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed with error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())