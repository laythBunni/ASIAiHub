#!/usr/bin/env python3
"""
CRITICAL PRODUCTION DOCUMENT PROCESSING INVESTIGATION
====================================================

ISSUE: Documents marked as "processed: true" and "processing_status: completed" 
but chunks_count remains 0. Frontend shows "Processing..." and chat finds no 
documents because no chunks exist.

INVESTIGATION FOCUS:
1. Test recent document processing with direct approval endpoint
2. Verify if chunks are actually being stored in MongoDB document_chunks collection
3. Check if chunks_count field is being properly updated in document records
4. Identify disconnect between successful chunk storage logs and 0 chunks_count in API
5. Compare working MongoDB RAG test vs failing real document processing
"""

import requests
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
import os

class DocumentProcessingInvestigator:
    def __init__(self):
        # Get backend URL from frontend/.env
        self.base_url = None
        self.load_backend_url()
        self.api_url = f"{self.base_url}/api"
        self.auth_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.investigation_results = []
        
    def load_backend_url(self):
        """Load backend URL from frontend/.env"""
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
        
        print(f"🔗 Backend URL: {self.base_url}")
    
    def log_result(self, test_name, status, details):
        """Log investigation result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.investigation_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {details}")
    
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
    
    def authenticate_as_admin(self):
        """Authenticate as admin user"""
        print(f"\n🔐 AUTHENTICATING AS ADMIN...")
        
        login_data = {
            "email": "layth.bunni@adamsmithinternational.com",
            "personal_code": "899443"
        }
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "/auth/login",
            200,
            login_data
        )
        
        if success:
            self.auth_token = response.get('access_token') or response.get('token')
            print(f"   ✅ Admin authenticated successfully")
            print(f"   🔑 Token: {self.auth_token[:20] if self.auth_token else 'None'}...")
            return True
        else:
            print(f"   ❌ Admin authentication failed")
            return False
    
    def get_existing_documents(self):
        """Get list of existing approved documents"""
        print(f"\n📋 GETTING EXISTING APPROVED DOCUMENTS...")
        
        success, response = self.run_test(
            "Get Approved Documents",
            "GET",
            "/documents",
            200
        )
        
        if success:
            documents = response if isinstance(response, list) else []
            print(f"   📄 Found {len(documents)} approved documents")
            
            # Show document details
            for i, doc in enumerate(documents[:5]):  # Show first 5
                print(f"   {i+1}. {doc.get('original_name', 'Unknown')} - "
                      f"Chunks: {doc.get('chunks_count', 0)}, "
                      f"Status: {doc.get('processing_status', 'unknown')}, "
                      f"Processed: {doc.get('processed', False)}")
            
            self.log_result("Get Existing Documents", "PASS", f"Found {len(documents)} approved documents")
            return documents
        else:
            self.log_result("Get Existing Documents", "FAIL", "Could not retrieve approved documents")
            return []
    
    def get_admin_documents(self):
        """Get list of all documents from admin endpoint"""
        print(f"\n👑 GETTING ALL DOCUMENTS FROM ADMIN ENDPOINT...")
        
        if not self.auth_token:
            self.log_result("Get Admin Documents", "FAIL", "No admin token available")
            return []
        
        auth_headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        success, response = self.run_test(
            "Get Admin Documents",
            "GET",
            "/documents/admin",
            200,
            headers=auth_headers
        )
        
        if success:
            documents = response if isinstance(response, list) else []
            print(f"   📄 Found {len(documents)} total documents (admin view)")
            
            # Analyze document statuses
            status_counts = {}
            processing_counts = {}
            chunk_analysis = {"zero_chunks": 0, "has_chunks": 0}
            
            for doc in documents:
                # Count approval statuses
                approval_status = doc.get('approval_status', 'unknown')
                status_counts[approval_status] = status_counts.get(approval_status, 0) + 1
                
                # Count processing statuses
                processing_status = doc.get('processing_status', 'unknown')
                processing_counts[processing_status] = processing_counts.get(processing_status, 0) + 1
                
                # Analyze chunks
                chunks_count = doc.get('chunks_count', 0)
                if chunks_count == 0:
                    chunk_analysis["zero_chunks"] += 1
                else:
                    chunk_analysis["has_chunks"] += 1
            
            print(f"   📊 Approval Status Breakdown: {status_counts}")
            print(f"   📊 Processing Status Breakdown: {processing_counts}")
            print(f"   📊 Chunks Analysis: {chunk_analysis}")
            
            # Find problematic documents (approved + completed but 0 chunks)
            problematic_docs = []
            for doc in documents:
                if (doc.get('approval_status') == 'approved' and 
                    doc.get('processing_status') == 'completed' and 
                    doc.get('processed') == True and 
                    doc.get('chunks_count', 0) == 0):
                    problematic_docs.append(doc)
            
            if problematic_docs:
                print(f"   🚨 FOUND {len(problematic_docs)} PROBLEMATIC DOCUMENTS:")
                for doc in problematic_docs:
                    print(f"      - {doc.get('original_name')}: "
                          f"approved + completed + processed=True but chunks_count=0")
                
                self.log_result("Get Admin Documents", "WARN", 
                               f"Found {len(problematic_docs)} documents with processing inconsistency")
            else:
                self.log_result("Get Admin Documents", "PASS", 
                               f"No problematic documents found among {len(documents)} total")
            
            return documents, problematic_docs
        else:
            self.log_result("Get Admin Documents", "FAIL", "Could not retrieve admin documents")
            return [], []
    
    def test_direct_approval_endpoint(self, document_id):
        """Test the direct approval endpoint for a specific document"""
        print(f"\n🎯 TESTING DIRECT APPROVAL ENDPOINT FOR DOCUMENT: {document_id}")
        
        success, response = self.run_test(
            f"Direct Approval Test - {document_id}",
            "GET",
            f"/debug/test-approval-direct/{document_id}",
            200
        )
        
        if success:
            status = response.get('status', 'unknown')
            document_name = response.get('document_name', 'unknown')
            approval_result = response.get('approval_result', {})
            
            print(f"   📄 Document: {document_name}")
            print(f"   📊 Status: {status}")
            print(f"   📋 Approval Result: {approval_result}")
            
            if status == "SUCCESS":
                self.log_result("Direct Approval Test", "PASS", 
                               f"Document {document_name} processed successfully")
                return True, approval_result
            else:
                self.log_result("Direct Approval Test", "FAIL", 
                               f"Document {document_name} processing failed: {status}")
                return False, {}
        else:
            self.log_result("Direct Approval Test", "FAIL", 
                           f"Direct approval endpoint failed for {document_id}")
            return False, {}
    
    async def verify_mongodb_chunks(self, document_id=None):
        """Verify chunks in MongoDB document_chunks collection"""
        print(f"\n🔍 VERIFYING MONGODB DOCUMENT CHUNKS...")
        
        try:
            # Connect to MongoDB
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client['ai-workspace-17-test_database']
            
            # Get total chunk count
            total_chunks = await db.document_chunks.count_documents({})
            print(f"   📊 Total chunks in MongoDB: {total_chunks}")
            
            if document_id:
                # Get chunks for specific document
                doc_chunks = await db.document_chunks.count_documents({"document_id": document_id})
                print(f"   📄 Chunks for document {document_id}: {doc_chunks}")
                
                # Get sample chunk
                sample_chunk = await db.document_chunks.find_one({"document_id": document_id})
                if sample_chunk:
                    print(f"   📝 Sample chunk text: {sample_chunk.get('text', '')[:100]}...")
                    print(f"   🔢 Sample chunk has embedding: {bool(sample_chunk.get('embedding'))}")
                    print(f"   📏 Embedding length: {len(sample_chunk.get('embedding', []))}")
            
            # Get chunks by document_id (group by document)
            pipeline = [
                {"$group": {"_id": "$document_id", "chunk_count": {"$sum": 1}}},
                {"$sort": {"chunk_count": -1}}
            ]
            
            chunk_distribution = []
            async for result in db.document_chunks.aggregate(pipeline):
                chunk_distribution.append({
                    "document_id": result["_id"],
                    "chunk_count": result["chunk_count"]
                })
            
            print(f"   📊 Chunk distribution by document:")
            for dist in chunk_distribution[:10]:  # Show top 10
                print(f"      {dist['document_id']}: {dist['chunk_count']} chunks")
            
            client.close()
            
            self.log_result("MongoDB Chunks Verification", "PASS", 
                           f"Total chunks: {total_chunks}, Documents with chunks: {len(chunk_distribution)}")
            
            return total_chunks, chunk_distribution
            
        except Exception as e:
            print(f"   ❌ MongoDB verification failed: {e}")
            self.log_result("MongoDB Chunks Verification", "FAIL", f"Error: {str(e)}")
            return 0, []
    
    async def compare_document_vs_chunks(self, documents):
        """Compare document records with actual chunks in MongoDB"""
        print(f"\n🔍 COMPARING DOCUMENT RECORDS VS ACTUAL CHUNKS...")
        
        try:
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client['ai-workspace-17-test_database']
            
            mismatches = []
            
            for doc in documents:
                doc_id = doc.get('id')
                recorded_chunks = doc.get('chunks_count', 0)
                
                # Get actual chunks from MongoDB
                actual_chunks = await db.document_chunks.count_documents({"document_id": doc_id})
                
                if recorded_chunks != actual_chunks:
                    mismatch = {
                        "document_id": doc_id,
                        "document_name": doc.get('original_name', 'unknown'),
                        "recorded_chunks": recorded_chunks,
                        "actual_chunks": actual_chunks,
                        "processing_status": doc.get('processing_status', 'unknown'),
                        "processed": doc.get('processed', False)
                    }
                    mismatches.append(mismatch)
                    
                    print(f"   🚨 MISMATCH: {doc.get('original_name')}")
                    print(f"      Recorded chunks_count: {recorded_chunks}")
                    print(f"      Actual chunks in DB: {actual_chunks}")
                    print(f"      Processing status: {doc.get('processing_status')}")
                    print(f"      Processed flag: {doc.get('processed')}")
            
            client.close()
            
            if mismatches:
                self.log_result("Document vs Chunks Comparison", "FAIL", 
                               f"Found {len(mismatches)} documents with chunk count mismatches")
                return mismatches
            else:
                self.log_result("Document vs Chunks Comparison", "PASS", 
                               "All document chunk counts match actual MongoDB chunks")
                return []
                
        except Exception as e:
            print(f"   ❌ Comparison failed: {e}")
            self.log_result("Document vs Chunks Comparison", "FAIL", f"Error: {str(e)}")
            return []
    
    def test_mongodb_rag_directly(self):
        """Test MongoDB RAG system directly"""
        print(f"\n🧪 TESTING MONGODB RAG SYSTEM DIRECTLY...")
        
        success, response = self.run_test(
            "MongoDB RAG Direct Test",
            "GET",
            "/debug/test-mongodb-rag-directly",
            200
        )
        
        if success:
            test_status = response.get('test_status', 'unknown')
            steps = response.get('steps', [])
            
            print(f"   📊 Test Status: {test_status}")
            
            for step in steps:
                step_name = step.get('step', 'unknown')
                step_status = step.get('status', 'unknown')
                step_details = step.get('chunks_created', step.get('chunks_stored', step.get('results_found', '')))
                
                status_icon = "✅" if step_status == "SUCCESS" else "❌"
                print(f"   {status_icon} {step_name}: {step_status} - {step_details}")
            
            if test_status == "COMPLETED":
                # Check if chunks were created
                chunks_created = False
                chunks_stored = False
                search_working = False
                
                for step in steps:
                    if step.get('step') == 'TEXT_CHUNKING' and step.get('status') == 'SUCCESS':
                        chunks_created = True
                    if step.get('step') == 'MONGODB_STORAGE' and step.get('status') == 'SUCCESS':
                        chunks_stored = True
                    if step.get('step') == 'SEARCH_TEST' and step.get('status') == 'SUCCESS':
                        search_working = True
                
                if chunks_created and chunks_stored and search_working:
                    self.log_result("MongoDB RAG Direct Test", "PASS", 
                                   "RAG system working correctly - chunks created, stored, and searchable")
                else:
                    self.log_result("MongoDB RAG Direct Test", "WARN", 
                                   f"RAG system partial success - chunks:{chunks_created}, stored:{chunks_stored}, search:{search_working}")
            else:
                self.log_result("MongoDB RAG Direct Test", "FAIL", 
                               f"RAG test failed with status: {test_status}")
            
            return success, response
        else:
            self.log_result("MongoDB RAG Direct Test", "FAIL", "Could not run MongoDB RAG direct test")
            return False, {}
    
    def create_and_test_new_document(self):
        """Create a new document and test the full processing pipeline"""
        print(f"\n📄 CREATING NEW DOCUMENT FOR PROCESSING TEST...")
        
        # Create test file content
        test_content = f"""
        DOCUMENT PROCESSING INVESTIGATION TEST - {datetime.now().isoformat()}
        
        This document is created specifically to investigate the document processing issue
        where documents show processed=true and processing_status=completed but chunks_count=0.
        
        INVESTIGATION DETAILS:
        - Created at: {datetime.now().isoformat()}
        - Purpose: Test document processing pipeline
        - Expected outcome: Document should be chunked and stored in MongoDB
        
        CONTENT FOR CHUNKING:
        This document contains multiple paragraphs to ensure proper chunking.
        
        Paragraph 1: Company policies and procedures are essential for maintaining
        operational efficiency and compliance with regulatory requirements.
        
        Paragraph 2: Employee handbook guidelines specify that all staff members
        must follow established protocols for document management and processing.
        
        Paragraph 3: IT security policies require regular updates and maintenance
        of all systems to ensure data integrity and protection.
        
        Paragraph 4: Financial procedures mandate proper approval workflows
        for all expenditures and budget allocations.
        
        END OF TEST DOCUMENT
        """
        
        test_file_path = Path("/tmp/processing_investigation_test.txt")
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        try:
            # Upload document
            with open(test_file_path, 'rb') as f:
                files = {'file': ('processing_investigation_test.txt', f, 'text/plain')}
                data = {'department': 'Information Technology', 'tags': 'investigation,test,processing'}
                
                success, response = self.run_test(
                    "Upload Investigation Document",
                    "POST",
                    "/documents/upload",
                    200,
                    data=data,
                    files=files
                )
                
                if success:
                    document_id = response.get('id')
                    print(f"   ✅ Document uploaded: {document_id}")
                    
                    # Approve document to trigger processing
                    if self.auth_token:
                        auth_headers = {'Authorization': f'Bearer {self.auth_token}'}
                        approve_success, approve_response = self.run_test(
                            "Approve Investigation Document",
                            "PUT",
                            f"/documents/{document_id}/approve?approved_by=investigation_test",
                            200,
                            headers=auth_headers
                        )
                        
                        if approve_success:
                            print(f"   ✅ Document approved and processing triggered")
                            
                            # Wait for processing
                            print(f"   ⏳ Waiting 30 seconds for processing...")
                            time.sleep(30)
                            
                            # Check document status
                            status_success, status_response = self.run_test(
                                "Check Investigation Document Status",
                                "GET",
                                f"/documents/admin",
                                200,
                                headers=auth_headers
                            )
                            
                            if status_success:
                                documents = status_response if isinstance(status_response, list) else []
                                test_doc = None
                                
                                for doc in documents:
                                    if doc.get('id') == document_id:
                                        test_doc = doc
                                        break
                                
                                if test_doc:
                                    print(f"   📊 Final Document Status:")
                                    print(f"      Processing Status: {test_doc.get('processing_status')}")
                                    print(f"      Processed: {test_doc.get('processed')}")
                                    print(f"      Chunks Count: {test_doc.get('chunks_count', 0)}")
                                    print(f"      Approval Status: {test_doc.get('approval_status')}")
                                    
                                    # This is the key test - check if we have the same issue
                                    if (test_doc.get('processing_status') == 'completed' and 
                                        test_doc.get('processed') == True and 
                                        test_doc.get('chunks_count', 0) == 0):
                                        
                                        self.log_result("New Document Processing Test", "FAIL", 
                                                       "REPRODUCED ISSUE: Document shows completed/processed but chunks_count=0")
                                        return document_id, test_doc, True  # Issue reproduced
                                    else:
                                        self.log_result("New Document Processing Test", "PASS", 
                                                       f"Document processed correctly with {test_doc.get('chunks_count', 0)} chunks")
                                        return document_id, test_doc, False  # Issue not reproduced
                                else:
                                    self.log_result("New Document Processing Test", "FAIL", 
                                                   "Could not find uploaded document in admin list")
                                    return document_id, None, False
                            else:
                                self.log_result("New Document Processing Test", "FAIL", 
                                               "Could not check document status after processing")
                                return document_id, None, False
                        else:
                            self.log_result("New Document Processing Test", "FAIL", 
                                           "Could not approve document")
                            return document_id, None, False
                    else:
                        self.log_result("New Document Processing Test", "FAIL", 
                                       "No admin token for approval")
                        return document_id, None, False
                else:
                    self.log_result("New Document Processing Test", "FAIL", 
                                   "Could not upload test document")
                    return None, None, False
        finally:
            if test_file_path.exists():
                test_file_path.unlink()
    
    def run_investigation(self):
        """Run the complete document processing investigation"""
        print(f"🔍 CRITICAL PRODUCTION DOCUMENT PROCESSING INVESTIGATION")
        print("=" * 80)
        print("ISSUE: Documents marked as processed=true and processing_status=completed")
        print("       but chunks_count remains 0. Frontend shows 'Processing...' and")
        print("       chat finds no documents because no chunks exist.")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate_as_admin():
            print(f"❌ Cannot proceed without admin authentication")
            return False
        
        # Step 2: Get existing documents and identify problematic ones
        print(f"\n📊 STEP 1: ANALYZING EXISTING DOCUMENTS...")
        approved_docs = self.get_existing_documents()
        all_docs, problematic_docs = self.get_admin_documents()
        
        # Step 3: Verify MongoDB chunks
        print(f"\n📊 STEP 2: VERIFYING MONGODB CHUNKS...")
        total_chunks, chunk_distribution = asyncio.run(self.verify_mongodb_chunks())
        
        # Step 4: Compare document records vs actual chunks
        print(f"\n📊 STEP 3: COMPARING DOCUMENT RECORDS VS ACTUAL CHUNKS...")
        mismatches = asyncio.run(self.compare_document_vs_chunks(all_docs))
        
        # Step 5: Test MongoDB RAG system directly
        print(f"\n📊 STEP 4: TESTING MONGODB RAG SYSTEM DIRECTLY...")
        rag_success, rag_response = self.test_mongodb_rag_directly()
        
        # Step 6: Test direct approval endpoint on problematic document
        if problematic_docs:
            print(f"\n📊 STEP 5: TESTING DIRECT APPROVAL ON PROBLEMATIC DOCUMENT...")
            test_doc = problematic_docs[0]  # Test first problematic document
            approval_success, approval_result = self.test_direct_approval_endpoint(test_doc.get('id'))
            
            # Verify chunks after direct approval test
            if approval_success:
                print(f"   ⏳ Waiting 30 seconds for processing after direct approval...")
                time.sleep(30)
                asyncio.run(self.verify_mongodb_chunks(test_doc.get('id')))
        
        # Step 7: Create new document and test full pipeline
        print(f"\n📊 STEP 6: CREATING NEW DOCUMENT TO TEST FULL PIPELINE...")
        new_doc_id, new_doc_data, issue_reproduced = self.create_and_test_new_document()
        
        if new_doc_id and issue_reproduced:
            # Verify chunks for new document
            asyncio.run(self.verify_mongodb_chunks(new_doc_id))
        
        # Step 8: Generate investigation summary
        print(f"\n📊 INVESTIGATION SUMMARY")
        print("=" * 50)
        
        print(f"\n🔍 FINDINGS:")
        for result in self.investigation_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_icon} {result['test']}: {result['details']}")
        
        print(f"\n📊 KEY METRICS:")
        print(f"   Total Documents: {len(all_docs)}")
        print(f"   Approved Documents: {len(approved_docs)}")
        print(f"   Problematic Documents: {len(problematic_docs)}")
        print(f"   Total Chunks in MongoDB: {total_chunks}")
        print(f"   Documents with Chunks: {len(chunk_distribution)}")
        print(f"   Chunk Count Mismatches: {len(mismatches)}")
        
        print(f"\n🎯 ROOT CAUSE ANALYSIS:")
        if mismatches:
            print(f"   ❌ CONFIRMED: {len(mismatches)} documents have chunk count mismatches")
            print(f"   📋 This indicates the disconnect between processing logs and actual chunk storage")
            
            for mismatch in mismatches[:3]:  # Show first 3 mismatches
                print(f"      - {mismatch['document_name']}: "
                      f"recorded={mismatch['recorded_chunks']}, actual={mismatch['actual_chunks']}")
        else:
            print(f"   ✅ No chunk count mismatches found")
        
        if issue_reproduced:
            print(f"   ❌ ISSUE REPRODUCED: New document also shows processing inconsistency")
        else:
            print(f"   ✅ Issue not reproduced with new document")
        
        print(f"\n🔧 RECOMMENDATIONS:")
        if mismatches or issue_reproduced:
            print(f"   1. Check RAG processing pipeline for chunk count update logic")
            print(f"   2. Verify MongoDB chunk storage is completing successfully")
            print(f"   3. Check if chunks_count field is being updated after chunk storage")
            print(f"   4. Review process_document_with_rag function for error handling")
            print(f"   5. Consider adding transaction support for atomic updates")
        else:
            print(f"   1. Document processing appears to be working correctly")
            print(f"   2. Issue may be environment-specific or intermittent")
            print(f"   3. Monitor production logs for processing errors")
        
        # Return summary for test_result.md update
        return {
            "total_documents": len(all_docs),
            "problematic_documents": len(problematic_docs),
            "total_chunks": total_chunks,
            "chunk_mismatches": len(mismatches),
            "issue_reproduced": issue_reproduced,
            "rag_system_working": rag_success,
            "investigation_results": self.investigation_results
        }

def main():
    """Main function"""
    investigator = DocumentProcessingInvestigator()
    
    try:
        summary = investigator.run_investigation()
        
        print(f"\n🎉 INVESTIGATION COMPLETED!")
        print(f"📊 Results: {investigator.tests_passed}/{investigator.tests_run} tests passed")
        
        return summary
        
    except Exception as e:
        print(f"\n❌ Investigation failed: {e}")
        return None

if __name__ == "__main__":
    import sys
    result = main()
    sys.exit(0 if result else 1)