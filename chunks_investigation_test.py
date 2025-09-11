#!/usr/bin/env python3
"""
CHUNKS INVESTIGATION TEST

The production RAG test revealed that:
1. ✅ MongoDB mode is working (mongodb_cloud)
2. ✅ OpenAI API key is working
3. ✅ Documents are being processed (processed=true, processing_status=completed)
4. ❌ BUT chunks_count = 0 (this is the critical issue)
5. ✅ RAG search is working and finding documents

This suggests the issue is specifically with chunk counting or storage.
Let's investigate deeper.
"""

import requests
import json
import time

class ChunksInvestigator:
    def __init__(self):
        # Use production URL
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
        
        print(f"🔍 CHUNKS INVESTIGATION")
        print(f"📍 Backend URL: {self.base_url}")
        print("=" * 60)

    def authenticate(self):
        """Authenticate as admin"""
        login_data = {
            "email": "layth.bunni@adamsmithinternational.com",
            "personal_code": "899443"
        }
        
        try:
            response = requests.post(f"{self.api_url}/auth/login", json=login_data, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token') or data.get('token')
                print(f"✅ Authenticated as admin")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def get_headers(self):
        return {'Authorization': f'Bearer {self.auth_token}'} if self.auth_token else {}

    def investigate_chunks_issue(self):
        """Investigate why chunks_count is 0 despite successful processing"""
        print(f"\n🔍 INVESTIGATING CHUNKS ISSUE")
        print("=" * 40)
        
        if not self.authenticate():
            return False
        
        # 1. Get all documents and their chunk status
        print(f"\n📋 1. DOCUMENT CHUNK STATUS:")
        try:
            response = requests.get(f"{self.api_url}/documents/admin", headers=self.get_headers(), timeout=30)
            if response.status_code == 200:
                docs = response.json()
                print(f"   Found {len(docs)} total documents")
                
                processed_docs = [d for d in docs if d.get('processed')]
                completed_docs = [d for d in docs if d.get('processing_status') == 'completed']
                docs_with_chunks = [d for d in docs if d.get('chunks_count', 0) > 0]
                
                print(f"   📊 Processed documents: {len(processed_docs)}")
                print(f"   📊 Completed processing: {len(completed_docs)}")
                print(f"   📊 Documents with chunks: {len(docs_with_chunks)}")
                
                # Show sample documents
                print(f"\n   📄 Sample document statuses:")
                for i, doc in enumerate(docs[:5]):
                    print(f"      {i+1}. {doc.get('original_name')}")
                    print(f"         - Processed: {doc.get('processed')}")
                    print(f"         - Status: {doc.get('processing_status')}")
                    print(f"         - Chunks: {doc.get('chunks_count', 0)}")
                    print(f"         - Notes: {doc.get('notes', 'None')}")
                
                if docs_with_chunks:
                    print(f"\n   ✅ DOCUMENTS WITH CHUNKS FOUND:")
                    for doc in docs_with_chunks:
                        print(f"      - {doc.get('original_name')}: {doc.get('chunks_count')} chunks")
                else:
                    print(f"\n   ❌ NO DOCUMENTS HAVE CHUNKS!")
                    print(f"      This is the root cause of the issue")
                
            else:
                print(f"   ❌ Failed to get documents: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Error getting documents: {e}")
            return False
        
        # 2. Test direct MongoDB RAG system
        print(f"\n🧪 2. DIRECT MONGODB RAG TEST:")
        try:
            response = requests.get(f"{self.api_url}/debug/test-mongodb-rag-directly", timeout=60)
            if response.status_code == 200:
                data = response.json()
                steps = data.get('steps', [])
                
                for step in steps:
                    step_name = step.get('step')
                    status = step.get('status')
                    print(f"   {step_name}: {status}")
                    
                    if step_name == 'MONGODB_STORAGE':
                        chunks_stored = step.get('chunks_stored', 0)
                        print(f"      - Chunks stored: {chunks_stored}")
                    elif step_name == 'DATABASE_VERIFICATION':
                        chunks_in_db = step.get('chunks_in_db', 0)
                        has_embedding = step.get('sample_chunk_has_embedding', False)
                        print(f"      - Chunks in DB: {chunks_in_db}")
                        print(f"      - Has embeddings: {has_embedding}")
                    elif step_name == 'SEARCH_TEST':
                        results_found = step.get('results_found', 0)
                        similarity = step.get('top_similarity', 0)
                        print(f"      - Search results: {results_found}")
                        print(f"      - Top similarity: {similarity}")
                
                # Check if the test created chunks successfully
                mongodb_storage_step = next((s for s in steps if s.get('step') == 'MONGODB_STORAGE'), None)
                if mongodb_storage_step and mongodb_storage_step.get('status') == 'SUCCESS':
                    print(f"   ✅ MongoDB storage is working correctly")
                else:
                    print(f"   ❌ MongoDB storage has issues")
                    
            else:
                print(f"   ❌ Failed to test MongoDB RAG: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error testing MongoDB RAG: {e}")
        
        # 3. Test embedding generation specifically
        print(f"\n🤖 3. OPENAI EMBEDDING TEST:")
        try:
            response = requests.get(f"{self.api_url}/debug/test-embedding-generation", timeout=60)
            if response.status_code == 200:
                data = response.json()
                steps = data.get('steps', [])
                
                for step in steps:
                    step_name = step.get('step')
                    status = step.get('status')
                    print(f"   {step_name}: {status}")
                    
                    if step_name == 'EMBEDDING_GENERATION' and status == 'SUCCESS':
                        embedding_length = step.get('embedding_length', 0)
                        print(f"      - Embedding length: {embedding_length}")
                        print(f"   ✅ Embeddings are working correctly")
                    elif step_name == 'MONGODB_WRITE_TEST':
                        print(f"      - MongoDB write test: {status}")
                        
            else:
                print(f"   ❌ Failed to test embeddings: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error testing embeddings: {e}")
        
        # 4. Test a complete document processing cycle
        print(f"\n🔄 4. COMPLETE PROCESSING CYCLE TEST:")
        test_content = f"""
        CHUNKS INVESTIGATION TEST DOCUMENT
        
        This document is created to investigate why chunks_count is 0.
        
        INVESTIGATION FINDINGS:
        - MongoDB mode is working (mongodb_cloud)
        - OpenAI API key is working
        - Documents are being processed successfully
        - But chunks_count remains 0
        
        POSSIBLE CAUSES:
        1. Chunks are being created but not counted properly
        2. Chunks are being stored but document metadata not updated
        3. Processing completes but chunk creation fails silently
        4. Environment loading order issue (fixed but may have residual effects)
        
        This document should be chunked into multiple pieces if the system is working.
        Each chunk should have OpenAI embeddings and be stored in MongoDB.
        The document metadata should show chunks_count > 0.
        
        TEST KEYWORDS: investigation, chunks, mongodb, embeddings, processing
        """
        
        # Create and upload test document
        try:
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_content)
                temp_path = f.name
            
            try:
                with open(temp_path, 'rb') as f:
                    files = {'file': ('chunks_investigation_test.txt', f, 'text/plain')}
                    data = {'department': 'Information Technology', 'tags': 'investigation,chunks,test'}
                    
                    response = requests.post(f"{self.api_url}/documents/upload", files=files, data=data, timeout=30)
                    
                if response.status_code == 200:
                    upload_data = response.json()
                    doc_id = upload_data.get('id')
                    print(f"   ✅ Test document uploaded: {doc_id}")
                    
                    # Approve the document
                    response = requests.put(f"{self.api_url}/documents/{doc_id}/approve", headers=self.get_headers(), timeout=30)
                    if response.status_code == 200:
                        approval_data = response.json()
                        print(f"   ✅ Test document approved")
                        print(f"      - Message: {approval_data.get('message')}")
                        print(f"      - Chunks count: {approval_data.get('chunks_count', 0)}")
                        print(f"      - Processing status: {approval_data.get('processing_status')}")
                        
                        # Wait and check final status
                        print(f"   ⏳ Waiting 15 seconds for processing...")
                        time.sleep(15)
                        
                        # Check final document status
                        response = requests.get(f"{self.api_url}/documents/admin", headers=self.get_headers(), timeout=30)
                        if response.status_code == 200:
                            docs = response.json()
                            test_doc = next((d for d in docs if d.get('id') == doc_id), None)
                            
                            if test_doc:
                                print(f"   📊 FINAL TEST DOCUMENT STATUS:")
                                print(f"      - Processing status: {test_doc.get('processing_status')}")
                                print(f"      - Processed: {test_doc.get('processed')}")
                                print(f"      - Chunks count: {test_doc.get('chunks_count', 0)}")
                                print(f"      - Notes: {test_doc.get('notes', 'None')}")
                                
                                if test_doc.get('chunks_count', 0) > 0:
                                    print(f"   ✅ SUCCESS: Document was properly chunked!")
                                    return True
                                else:
                                    print(f"   ❌ ISSUE CONFIRMED: Document processed but no chunks created")
                                    return False
                            else:
                                print(f"   ❌ Test document not found after processing")
                        else:
                            print(f"   ❌ Failed to check final document status")
                    else:
                        print(f"   ❌ Failed to approve document: {response.status_code}")
                else:
                    print(f"   ❌ Failed to upload test document: {response.status_code}")
                    
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            print(f"   ❌ Error in processing cycle test: {e}")
        
        return False

    def run_investigation(self):
        """Run the complete investigation"""
        print(f"\n🚀 STARTING CHUNKS INVESTIGATION")
        print("=" * 60)
        
        success = self.investigate_chunks_issue()
        
        print(f"\n🎯 INVESTIGATION COMPLETE")
        print("=" * 60)
        
        if success:
            print(f"✅ CHUNKS ISSUE RESOLVED!")
            print(f"   The RAG system is now creating chunks correctly")
        else:
            print(f"❌ CHUNKS ISSUE PERSISTS!")
            print(f"   Documents are processed but chunks_count remains 0")
            print(f"\n🔍 POSSIBLE ROOT CAUSES:")
            print(f"   1. Chunk creation logic has a bug")
            print(f"   2. MongoDB chunk storage is failing silently")
            print(f"   3. Document metadata update is not working")
            print(f"   4. Environment configuration issue")
            print(f"\n💡 RECOMMENDATIONS:")
            print(f"   1. Check backend logs for RAG processing errors")
            print(f"   2. Verify MongoDB connection and chunk collection")
            print(f"   3. Test chunk creation logic directly")
            print(f"   4. Check if chunks exist in DB but count is wrong")
        
        return success

if __name__ == "__main__":
    investigator = ChunksInvestigator()
    investigator.run_investigation()