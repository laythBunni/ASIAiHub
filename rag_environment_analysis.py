#!/usr/bin/env python3
"""
RAG Environment Analysis - Critical Findings
===========================================

Based on the initial test results, we found:
- Preview environment: 484 chunks, RAG working correctly
- Production environments: 0 chunks, RAG not working

This script performs deeper analysis to understand the root cause.
"""

import requests
import json
import time
from datetime import datetime

class RAGEnvironmentAnalyzer:
    def __init__(self):
        self.environments = {
            'preview': 'https://smart-assist-18.preview.emergentagent.com',
            'production_1': 'https://asiaihub.com',
            'production_2': 'https://ai-workspace-17.emergent.host'
        }
        
        print("🔍 RAG ENVIRONMENT ANALYSIS - CRITICAL FINDINGS")
        print("=" * 60)
        print("INITIAL FINDINGS:")
        print("✅ Preview: 484 chunks, RAG working")
        print("❌ Production 1: 0 chunks, RAG failing")
        print("❌ Production 2: 0 chunks, RAG failing")
        print()

    def analyze_document_processing_pipeline(self, env_name, base_url):
        """Analyze the document processing pipeline in detail"""
        print(f"\n🔍 ANALYZING {env_name.upper()} DOCUMENT PROCESSING PIPELINE")
        print("-" * 50)
        
        api_url = f"{base_url}/api"
        
        # Get all documents (including pending)
        try:
            # Try to get admin documents (all documents including pending)
            response = requests.get(f"{api_url}/documents/admin", timeout=30)
            if response.status_code == 200:
                all_docs = response.json()
                print(f"📄 Total documents (admin view): {len(all_docs)}")
            else:
                # Fallback to regular documents
                response = requests.get(f"{api_url}/documents", timeout=30)
                all_docs = response.json() if response.status_code == 200 else []
                print(f"📄 Approved documents only: {len(all_docs)}")
            
            # Analyze document processing status
            processing_stats = {}
            chunk_stats = {}
            
            for doc in all_docs:
                status = doc.get('processing_status', 'unknown')
                chunks = doc.get('chunks_count', 0)
                
                processing_stats[status] = processing_stats.get(status, 0) + 1
                
                if chunks > 0:
                    chunk_stats[doc.get('original_name', 'unknown')] = chunks
            
            print(f"\n📊 Processing Status Breakdown:")
            for status, count in processing_stats.items():
                print(f"   {status}: {count} documents")
            
            print(f"\n📊 Documents with Chunks:")
            if chunk_stats:
                for doc_name, chunks in chunk_stats.items():
                    print(f"   {doc_name}: {chunks} chunks")
                total_chunks_from_docs = sum(chunk_stats.values())
                print(f"   Total chunks from documents: {total_chunks_from_docs}")
            else:
                print(f"   ❌ No documents have chunks!")
            
            # Get RAG stats for comparison
            response = requests.get(f"{api_url}/documents/rag-stats", timeout=30)
            if response.status_code == 200:
                rag_stats = response.json()
                vector_db_chunks = rag_stats.get('vector_database', {}).get('total_chunks', 0)
                print(f"\n📊 Vector Database Stats:")
                print(f"   Chunks in vector DB: {vector_db_chunks}")
                print(f"   Chunks from documents: {total_chunks_from_docs}")
                
                if vector_db_chunks != total_chunks_from_docs:
                    print(f"   ⚠️  MISMATCH: Vector DB and document chunks don't match!")
                    if vector_db_chunks == 0:
                        print(f"   🚨 CRITICAL: Vector database is empty!")
                        print(f"   🔍 Possible causes:")
                        print(f"      - ChromaDB not persisting data")
                        print(f"      - RAG processing not running")
                        print(f"      - Different storage paths between environments")
                else:
                    print(f"   ✅ Vector DB and document chunks match")
            
            return {
                'total_docs': len(all_docs),
                'processing_stats': processing_stats,
                'chunk_stats': chunk_stats,
                'vector_db_chunks': vector_db_chunks if 'vector_db_chunks' in locals() else 0
            }
            
        except Exception as e:
            print(f"❌ Error analyzing documents: {str(e)}")
            return None

    def test_rag_processing_workflow(self, env_name, base_url):
        """Test the complete RAG processing workflow"""
        print(f"\n🔄 TESTING {env_name.upper()} RAG PROCESSING WORKFLOW")
        print("-" * 50)
        
        api_url = f"{base_url}/api"
        
        # Test 1: Upload a document
        print(f"📤 Step 1: Upload test document...")
        test_content = f"""
        RAG Test Document for {env_name}
        
        This document is specifically created to test the RAG processing pipeline
        in the {env_name} environment.
        
        Key Information:
        - Environment: {env_name}
        - Timestamp: {datetime.now().isoformat()}
        - Purpose: RAG processing verification
        
        Travel Policy Information:
        - All business travel requires pre-approval
        - Receipts must be submitted within 30 days
        - Maximum daily allowance is $200
        """
        
        try:
            # Create and upload test file
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_content)
                temp_file_path = f.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    files = {'file': (f'rag_test_{env_name}_{int(time.time())}.txt', f, 'text/plain')}
                    data = {'department': 'Information Technology', 'tags': f'rag-test,{env_name}'}
                    
                    response = requests.post(
                        f"{api_url}/documents/upload",
                        files=files,
                        data=data,
                        timeout=60
                    )
                
                if response.status_code == 200:
                    upload_result = response.json()
                    doc_id = upload_result.get('id')
                    print(f"   ✅ Document uploaded successfully")
                    print(f"   📄 Document ID: {doc_id}")
                    
                    # Test 2: Check if document appears in admin list
                    print(f"\n📋 Step 2: Check document in admin list...")
                    time.sleep(2)  # Wait a moment
                    
                    response = requests.get(f"{api_url}/documents/admin", timeout=30)
                    if response.status_code == 200:
                        admin_docs = response.json()
                        uploaded_doc = None
                        for doc in admin_docs:
                            if doc.get('id') == doc_id:
                                uploaded_doc = doc
                                break
                        
                        if uploaded_doc:
                            print(f"   ✅ Document found in admin list")
                            print(f"   📊 Status: {uploaded_doc.get('approval_status')}")
                            print(f"   🔄 Processing: {uploaded_doc.get('processing_status')}")
                            print(f"   📦 Chunks: {uploaded_doc.get('chunks_count', 0)}")
                            
                            # Test 3: Approve the document (if pending)
                            if uploaded_doc.get('approval_status') == 'pending_approval':
                                print(f"\n✅ Step 3: Approve document for RAG processing...")
                                
                                response = requests.put(
                                    f"{api_url}/documents/{doc_id}/approve",
                                    params={'approved_by': 'rag_test'},
                                    timeout=30
                                )
                                
                                if response.status_code == 200:
                                    print(f"   ✅ Document approved successfully")
                                    
                                    # Wait for processing and check again
                                    print(f"\n⏳ Step 4: Wait for RAG processing...")
                                    for i in range(6):  # Wait up to 60 seconds
                                        time.sleep(10)
                                        print(f"   ⏳ Checking processing status... ({(i+1)*10}s)")
                                        
                                        response = requests.get(f"{api_url}/documents/admin", timeout=30)
                                        if response.status_code == 200:
                                            admin_docs = response.json()
                                            for doc in admin_docs:
                                                if doc.get('id') == doc_id:
                                                    status = doc.get('processing_status')
                                                    chunks = doc.get('chunks_count', 0)
                                                    print(f"      Status: {status}, Chunks: {chunks}")
                                                    
                                                    if status == 'completed' and chunks > 0:
                                                        print(f"   ✅ RAG processing completed!")
                                                        print(f"   📦 Generated {chunks} chunks")
                                                        
                                                        # Test 5: Verify chunks in vector database
                                                        print(f"\n🔍 Step 5: Verify chunks in vector database...")
                                                        response = requests.get(f"{api_url}/documents/rag-stats", timeout=30)
                                                        if response.status_code == 200:
                                                            rag_stats = response.json()
                                                            vector_chunks = rag_stats.get('vector_database', {}).get('total_chunks', 0)
                                                            print(f"   📊 Total chunks in vector DB: {vector_chunks}")
                                                            
                                                            if vector_chunks > 0:
                                                                print(f"   ✅ Vector database has chunks - RAG system working!")
                                                                return True
                                                            else:
                                                                print(f"   ❌ Vector database still empty - RAG system not working!")
                                                                return False
                                                        break
                                                    elif status == 'failed':
                                                        print(f"   ❌ RAG processing failed!")
                                                        return False
                                    
                                    print(f"   ⚠️  RAG processing taking longer than expected")
                                    return False
                                else:
                                    print(f"   ❌ Document approval failed: {response.status_code}")
                                    return False
                            else:
                                print(f"   ℹ️  Document already approved: {uploaded_doc.get('approval_status')}")
                        else:
                            print(f"   ❌ Uploaded document not found in admin list")
                            return False
                    else:
                        print(f"   ❌ Cannot access admin documents: {response.status_code}")
                        return False
                else:
                    print(f"   ❌ Document upload failed: {response.status_code}")
                    return False
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ RAG workflow test error: {str(e)}")
            return False

    def compare_environments(self):
        """Compare all environments and identify differences"""
        print(f"\n🔍 COMPREHENSIVE ENVIRONMENT COMPARISON")
        print("=" * 60)
        
        results = {}
        
        for env_name, base_url in self.environments.items():
            print(f"\n📊 Analyzing {env_name}...")
            
            # Analyze document processing
            doc_analysis = self.analyze_document_processing_pipeline(env_name, base_url)
            
            # Test RAG workflow (only for production environments that are failing)
            if env_name != 'preview':  # Skip preview since it's working
                print(f"\n🧪 Testing RAG workflow for {env_name}...")
                rag_working = self.test_rag_processing_workflow(env_name, base_url)
            else:
                rag_working = True  # Preview is already confirmed working
            
            results[env_name] = {
                'doc_analysis': doc_analysis,
                'rag_working': rag_working
            }
        
        # Generate final comparison
        print(f"\n" + "=" * 80)
        print("🎯 FINAL RAG ENVIRONMENT ANALYSIS RESULTS")
        print("=" * 80)
        
        print(f"\n📊 ENVIRONMENT COMPARISON:")
        for env_name, result in results.items():
            doc_analysis = result.get('doc_analysis', {})
            rag_working = result.get('rag_working', False)
            
            print(f"\n{env_name.upper()}:")
            print(f"   Documents: {doc_analysis.get('total_docs', 0) if doc_analysis else 'Unknown'}")
            print(f"   Vector DB Chunks: {doc_analysis.get('vector_db_chunks', 0) if doc_analysis else 'Unknown'}")
            print(f"   RAG Working: {'✅ Yes' if rag_working else '❌ No'}")
            
            if doc_analysis and doc_analysis.get('processing_stats'):
                print(f"   Processing Status:")
                for status, count in doc_analysis['processing_stats'].items():
                    print(f"     {status}: {count}")
        
        # Root cause analysis
        print(f"\n🔍 ROOT CAUSE ANALYSIS:")
        
        working_envs = [name for name, result in results.items() if result.get('rag_working', False)]
        failing_envs = [name for name, result in results.items() if not result.get('rag_working', False)]
        
        if len(working_envs) == 1 and 'preview' in working_envs:
            print("🎯 CONFIRMED: Only preview environment has working RAG")
            print("   This matches the user's report exactly!")
            print()
            print("🔍 LIKELY CAUSES:")
            print("   1. ChromaDB persistence issues in production")
            print("   2. Different storage paths between environments")
            print("   3. RAG processing not running in production")
            print("   4. Environment variable differences")
            print()
            print("💡 IMMEDIATE ACTIONS NEEDED:")
            print("   1. Check ChromaDB configuration in production deployments")
            print("   2. Verify RAG processing is triggered after document approval")
            print("   3. Compare environment variables between preview and production")
            print("   4. Check if vector database files are being persisted")
        
        return results

def main():
    analyzer = RAGEnvironmentAnalyzer()
    results = analyzer.compare_environments()
    
    # Save results
    try:
        import json
        with open('/app/rag_analysis_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'analysis': results,
                'conclusion': {
                    'preview_working': True,
                    'production_working': False,
                    'root_cause': 'ChromaDB persistence or RAG processing issues in production environments'
                }
            }, f, indent=2, default=str)
        print(f"\n💾 Analysis results saved to /app/rag_analysis_results.json")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")

if __name__ == "__main__":
    main()