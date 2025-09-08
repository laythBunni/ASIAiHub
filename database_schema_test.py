#!/usr/bin/env python3
"""
DATABASE SCHEMA VERIFICATION TESTS
==================================

This script verifies the production database schema matches what the application expects.
It examines the MongoDB database structure, collections, and field types to identify
any schema mismatches that could cause upload/chat issues.

Target Database: asi_aihub_production (MongoDB Atlas)
Connection: User's configured MongoDB connection
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import uuid

# MongoDB imports
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo.server_api import ServerApi
    import pymongo
except ImportError:
    print("❌ MongoDB dependencies not found. Installing...")
    os.system("pip install motor pymongo")
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo.server_api import ServerApi
    import pymongo

class DatabaseSchemaVerifier:
    def __init__(self):
        """Initialize database connection using backend configuration"""
        self.load_database_config()
        self.client = None
        self.db = None
        self.tests_run = 0
        self.tests_passed = 0
        self.schema_issues = []
        
    def load_database_config(self):
        """Load database configuration from backend/.env"""
        try:
            backend_env_path = Path("/app/backend/.env")
            if not backend_env_path.exists():
                raise FileNotFoundError("Backend .env file not found")
            
            with open(backend_env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('MONGO_URL='):
                        self.mongo_url = line.split('=', 1)[1]
                    elif line.startswith('DB_NAME='):
                        self.db_name = line.split('=', 1)[1]
            
            if not hasattr(self, 'mongo_url'):
                raise ValueError("MONGO_URL not found in backend/.env")
            if not hasattr(self, 'db_name'):
                raise ValueError("DB_NAME not found in backend/.env")
                
            print(f"📊 Database Configuration Loaded:")
            print(f"   MongoDB URL: {self.mongo_url}")
            print(f"   Database Name: {self.db_name}")
            
        except Exception as e:
            print(f"❌ Failed to load database config: {e}")
            # Fallback to default values
            self.mongo_url = "mongodb://localhost:27017"
            self.db_name = "ai-workspace-17-test_database"
            print(f"   Using fallback: {self.mongo_url}/{self.db_name}")
    
    async def connect_to_database(self):
        """Establish connection to MongoDB database"""
        try:
            print(f"\n🔌 Connecting to MongoDB...")
            
            # Configure MongoDB client based on connection type
            if self.mongo_url.startswith('mongodb+srv://'):
                # Atlas connection using MongoDB's Stable API configuration
                self.client = AsyncIOMotorClient(
                    self.mongo_url,
                    server_api=ServerApi('1', strict=True, deprecation_errors=True),
                    tlsAllowInvalidCertificates=False,
                    serverSelectionTimeoutMS=30000,
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                    maxPoolSize=10,
                    retryWrites=True
                )
            else:
                # Local MongoDB connection
                self.client = AsyncIOMotorClient(self.mongo_url)
            
            self.db = self.client[self.db_name]
            
            # Test connection
            await self.client.admin.command('ping')
            print(f"   ✅ Successfully connected to MongoDB")
            print(f"   📊 Database: {self.db_name}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to connect to MongoDB: {e}")
            return False
    
    async def disconnect_from_database(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            print(f"🔌 Database connection closed")
    
    def run_test(self, name: str, test_func, *args, **kwargs):
        """Run a single test and track results"""
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            result = test_func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = asyncio.run(result)
            
            if result:
                self.tests_passed += 1
                print(f"   ✅ Passed")
                return True
            else:
                print(f"   ❌ Failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False
    
    async def get_collections_inventory(self):
        """Get complete inventory of collections in the database"""
        try:
            collections = await self.db.list_collection_names()
            
            print(f"\n📋 COLLECTIONS INVENTORY:")
            print(f"   Total Collections: {len(collections)}")
            
            collection_details = {}
            
            for collection_name in sorted(collections):
                try:
                    # Get collection stats
                    stats = await self.db.command("collStats", collection_name)
                    count = stats.get('count', 0)
                    size = stats.get('size', 0)
                    
                    collection_details[collection_name] = {
                        'count': count,
                        'size': size,
                        'exists': True
                    }
                    
                    print(f"   📁 {collection_name}: {count} documents ({size} bytes)")
                    
                except Exception as e:
                    collection_details[collection_name] = {
                        'count': 0,
                        'size': 0,
                        'exists': True,
                        'error': str(e)
                    }
                    print(f"   📁 {collection_name}: Error getting stats - {e}")
            
            return collection_details
            
        except Exception as e:
            print(f"❌ Failed to get collections inventory: {e}")
            return {}
    
    async def verify_expected_collections(self):
        """Verify all expected collections exist"""
        expected_collections = [
            'documents',
            'chat_sessions', 
            'chat_messages',
            'beta_users',
            'simple_users',
            'tickets',
            'boost_tickets',
            'boost_users',
            'boost_business_units',
            'boost_comments',
            'boost_audit_trail',
            'finance_sops'
        ]
        
        print(f"\n🔍 VERIFYING EXPECTED COLLECTIONS:")
        
        collections = await self.db.list_collection_names()
        missing_collections = []
        found_collections = []
        
        for expected in expected_collections:
            if expected in collections:
                found_collections.append(expected)
                print(f"   ✅ {expected}: Found")
            else:
                missing_collections.append(expected)
                print(f"   ❌ {expected}: Missing")
        
        print(f"\n📊 COLLECTION VERIFICATION SUMMARY:")
        print(f"   Found: {len(found_collections)}/{len(expected_collections)}")
        print(f"   Missing: {missing_collections}")
        
        if missing_collections:
            self.schema_issues.append({
                'type': 'missing_collections',
                'collections': missing_collections,
                'impact': 'high'
            })
        
        return len(missing_collections) == 0
    
    async def verify_documents_collection_schema(self):
        """Verify documents collection schema matches expected structure"""
        print(f"\n📄 VERIFYING DOCUMENTS COLLECTION SCHEMA:")
        
        try:
            # Get sample documents
            sample_docs = await self.db.documents.find().limit(5).to_list(length=5)
            
            if not sample_docs:
                print(f"   ⚠️  No documents found in collection")
                return True
            
            print(f"   📊 Analyzing {len(sample_docs)} sample documents...")
            
            # Expected fields for documents
            expected_fields = {
                'id': str,
                'filename': str,
                'original_name': str,
                'file_path': str,
                'mime_type': str,
                'file_size': int,
                'uploaded_at': datetime,
                'department': str,
                'tags': list,
                'processed': bool,
                'chunks_count': int,
                'processing_status': str,
                'approval_status': str,
                'approved_by': (str, type(None)),
                'approved_at': (datetime, type(None)),
                'uploaded_by': str,
                'notes': str
            }
            
            schema_issues = []
            
            for i, doc in enumerate(sample_docs):
                print(f"\n   📋 Document {i+1} Schema Analysis:")
                print(f"      ID: {doc.get('id', 'MISSING')}")
                print(f"      Filename: {doc.get('original_name', 'MISSING')}")
                print(f"      Approval Status: {doc.get('approval_status', 'MISSING')}")
                
                # Check each expected field
                for field_name, expected_type in expected_fields.items():
                    if field_name in doc:
                        actual_value = doc[field_name]
                        actual_type = type(actual_value)
                        
                        # Handle multiple allowed types
                        if isinstance(expected_type, tuple):
                            type_match = actual_type in expected_type
                        else:
                            type_match = actual_type == expected_type
                        
                        if type_match:
                            print(f"      ✅ {field_name}: {actual_type.__name__}")
                        else:
                            print(f"      ❌ {field_name}: Expected {expected_type}, got {actual_type.__name__}")
                            schema_issues.append({
                                'document_id': doc.get('id', 'unknown'),
                                'field': field_name,
                                'expected_type': str(expected_type),
                                'actual_type': actual_type.__name__,
                                'value': str(actual_value)[:50]
                            })
                    else:
                        print(f"      ❌ {field_name}: MISSING")
                        schema_issues.append({
                            'document_id': doc.get('id', 'unknown'),
                            'field': field_name,
                            'issue': 'missing_field'
                        })
            
            if schema_issues:
                print(f"\n   ⚠️  Found {len(schema_issues)} schema issues in documents collection")
                self.schema_issues.append({
                    'type': 'documents_schema_mismatch',
                    'issues': schema_issues,
                    'impact': 'high'
                })
                return False
            else:
                print(f"\n   ✅ Documents collection schema is correct")
                return True
                
        except Exception as e:
            print(f"   ❌ Error verifying documents schema: {e}")
            return False
    
    async def verify_chat_collections_schema(self):
        """Verify chat_sessions and chat_messages collections schema"""
        print(f"\n💬 VERIFYING CHAT COLLECTIONS SCHEMA:")
        
        # Verify chat_sessions
        print(f"\n   📋 Chat Sessions Schema:")
        try:
            sessions = await self.db.chat_sessions.find().limit(3).to_list(length=3)
            
            expected_session_fields = {
                'id': str,
                'user_id': str,
                'title': str,
                'created_at': datetime,
                'updated_at': datetime,
                'messages_count': int
            }
            
            if sessions:
                for i, session in enumerate(sessions):
                    print(f"      Session {i+1}: {session.get('id', 'NO_ID')}")
                    print(f"         Title: {session.get('title', 'NO_TITLE')}")
                    print(f"         Messages: {session.get('messages_count', 0)}")
                    
                    # Check field types
                    for field, expected_type in expected_session_fields.items():
                        if field in session:
                            actual_type = type(session[field])
                            if actual_type == expected_type:
                                print(f"         ✅ {field}: {actual_type.__name__}")
                            else:
                                print(f"         ❌ {field}: Expected {expected_type.__name__}, got {actual_type.__name__}")
                        else:
                            print(f"         ❌ {field}: MISSING")
            else:
                print(f"      ⚠️  No chat sessions found")
        
        except Exception as e:
            print(f"      ❌ Error checking chat sessions: {e}")
        
        # Verify chat_messages
        print(f"\n   💬 Chat Messages Schema:")
        try:
            messages = await self.db.chat_messages.find().limit(3).to_list(length=3)
            
            expected_message_fields = {
                'id': str,
                'session_id': str,
                'role': str,
                'content': str,
                'timestamp': datetime,
                'attachments': list
            }
            
            if messages:
                for i, message in enumerate(messages):
                    print(f"      Message {i+1}: {message.get('id', 'NO_ID')}")
                    print(f"         Role: {message.get('role', 'NO_ROLE')}")
                    print(f"         Content: {str(message.get('content', ''))[:50]}...")
                    
                    # Check field types
                    for field, expected_type in expected_message_fields.items():
                        if field in message:
                            actual_type = type(message[field])
                            if actual_type == expected_type:
                                print(f"         ✅ {field}: {actual_type.__name__}")
                            else:
                                print(f"         ❌ {field}: Expected {expected_type.__name__}, got {actual_type.__name__}")
                        else:
                            print(f"         ❌ {field}: MISSING")
            else:
                print(f"      ⚠️  No chat messages found")
        
        except Exception as e:
            print(f"      ❌ Error checking chat messages: {e}")
        
        return True
    
    async def verify_user_collections_schema(self):
        """Verify beta_users and simple_users collections schema"""
        print(f"\n👥 VERIFYING USER COLLECTIONS SCHEMA:")
        
        # Check beta_users collection
        print(f"\n   👤 Beta Users Schema:")
        try:
            beta_users = await self.db.beta_users.find().limit(3).to_list(length=3)
            
            expected_beta_user_fields = {
                'id': str,
                'email': str,
                'name': str,
                'role': str,
                'department': str,
                'personal_code': str,
                'is_active': bool,
                'created_at': datetime
            }
            
            if beta_users:
                for i, user in enumerate(beta_users):
                    print(f"      User {i+1}: {user.get('email', 'NO_EMAIL')}")
                    print(f"         Name: {user.get('name', 'NO_NAME')}")
                    print(f"         Role: {user.get('role', 'NO_ROLE')}")
                    print(f"         Personal Code: {user.get('personal_code', 'NO_CODE')}")
                    
                    # Check field types
                    for field, expected_type in expected_beta_user_fields.items():
                        if field in user:
                            actual_type = type(user[field])
                            if actual_type == expected_type:
                                print(f"         ✅ {field}: {actual_type.__name__}")
                            else:
                                print(f"         ❌ {field}: Expected {expected_type.__name__}, got {actual_type.__name__}")
                        else:
                            print(f"         ❌ {field}: MISSING")
            else:
                print(f"      ⚠️  No beta users found")
        
        except Exception as e:
            print(f"      ❌ Error checking beta users: {e}")
        
        # Check simple_users collection
        print(f"\n   👤 Simple Users Schema:")
        try:
            simple_users = await self.db.simple_users.find().limit(3).to_list(length=3)
            
            if simple_users:
                for i, user in enumerate(simple_users):
                    print(f"      User {i+1}: {user.get('email', 'NO_EMAIL')}")
                    print(f"         Fields: {list(user.keys())}")
            else:
                print(f"      ⚠️  No simple users found")
        
        except Exception as e:
            print(f"      ❌ Error checking simple users: {e}")
        
        return True
    
    async def verify_field_types_compatibility(self):
        """Verify field types match Pydantic models expectations"""
        print(f"\n🔍 VERIFYING FIELD TYPE COMPATIBILITY:")
        
        compatibility_issues = []
        
        # Check for ObjectId vs UUID issues
        print(f"\n   🆔 Checking ID Field Types:")
        
        collections_to_check = ['documents', 'chat_sessions', 'chat_messages', 'beta_users']
        
        for collection_name in collections_to_check:
            try:
                sample = await self.db[collection_name].find_one()
                if sample and 'id' in sample:
                    id_value = sample['id']
                    id_type = type(id_value)
                    
                    print(f"      {collection_name}.id: {id_type.__name__} = {id_value}")
                    
                    # Check if it's a proper UUID string
                    if isinstance(id_value, str):
                        try:
                            uuid.UUID(id_value)
                            print(f"         ✅ Valid UUID format")
                        except ValueError:
                            print(f"         ❌ Invalid UUID format")
                            compatibility_issues.append({
                                'collection': collection_name,
                                'field': 'id',
                                'issue': 'invalid_uuid_format',
                                'value': str(id_value)
                            })
                    else:
                        print(f"         ❌ ID is not string type (expected for UUID)")
                        compatibility_issues.append({
                            'collection': collection_name,
                            'field': 'id',
                            'issue': 'wrong_type',
                            'expected': 'str',
                            'actual': id_type.__name__
                        })
                else:
                    print(f"      {collection_name}: No documents or no 'id' field")
            
            except Exception as e:
                print(f"      {collection_name}: Error - {e}")
        
        # Check datetime formats
        print(f"\n   📅 Checking Datetime Field Types:")
        
        datetime_fields = [
            ('documents', 'uploaded_at'),
            ('documents', 'approved_at'),
            ('chat_sessions', 'created_at'),
            ('chat_sessions', 'updated_at'),
            ('chat_messages', 'timestamp'),
            ('beta_users', 'created_at')
        ]
        
        for collection_name, field_name in datetime_fields:
            try:
                sample = await self.db[collection_name].find_one({field_name: {"$exists": True}})
                if sample and field_name in sample:
                    datetime_value = sample[field_name]
                    datetime_type = type(datetime_value)
                    
                    print(f"      {collection_name}.{field_name}: {datetime_type.__name__}")
                    
                    if isinstance(datetime_value, datetime):
                        print(f"         ✅ Correct datetime type")
                    else:
                        print(f"         ❌ Wrong type for datetime field")
                        compatibility_issues.append({
                            'collection': collection_name,
                            'field': field_name,
                            'issue': 'wrong_datetime_type',
                            'expected': 'datetime',
                            'actual': datetime_type.__name__
                        })
                else:
                    print(f"      {collection_name}.{field_name}: No data found")
            
            except Exception as e:
                print(f"      {collection_name}.{field_name}: Error - {e}")
        
        if compatibility_issues:
            print(f"\n   ⚠️  Found {len(compatibility_issues)} field type compatibility issues")
            self.schema_issues.append({
                'type': 'field_type_compatibility',
                'issues': compatibility_issues,
                'impact': 'medium'
            })
            return False
        else:
            print(f"\n   ✅ All field types are compatible")
            return True
    
    async def check_document_approval_workflow(self):
        """Check if document approval workflow is working correctly"""
        print(f"\n📋 CHECKING DOCUMENT APPROVAL WORKFLOW:")
        
        try:
            # Count documents by approval status
            total_docs = await self.db.documents.count_documents({})
            pending_docs = await self.db.documents.count_documents({"approval_status": "pending_approval"})
            approved_docs = await self.db.documents.count_documents({"approval_status": "approved"})
            rejected_docs = await self.db.documents.count_documents({"approval_status": "rejected"})
            
            print(f"   📊 Document Approval Status:")
            print(f"      Total Documents: {total_docs}")
            print(f"      Pending Approval: {pending_docs}")
            print(f"      Approved: {approved_docs}")
            print(f"      Rejected: {rejected_docs}")
            
            # Check for documents without approval_status field
            no_status = await self.db.documents.count_documents({"approval_status": {"$exists": False}})
            if no_status > 0:
                print(f"      ❌ Documents without approval_status: {no_status}")
                self.schema_issues.append({
                    'type': 'missing_approval_status',
                    'count': no_status,
                    'impact': 'high'
                })
            
            # Check for documents with processing issues
            failed_processing = await self.db.documents.count_documents({"processing_status": "failed"})
            if failed_processing > 0:
                print(f"      ⚠️  Documents with failed processing: {failed_processing}")
            
            # Sample some pending documents to check their structure
            pending_samples = await self.db.documents.find({"approval_status": "pending_approval"}).limit(3).to_list(length=3)
            
            if pending_samples:
                print(f"\n   📋 Sample Pending Documents:")
                for doc in pending_samples:
                    print(f"      📄 {doc.get('original_name', 'NO_NAME')}")
                    print(f"         ID: {doc.get('id', 'NO_ID')}")
                    print(f"         Department: {doc.get('department', 'NO_DEPT')}")
                    print(f"         Processing Status: {doc.get('processing_status', 'NO_STATUS')}")
                    print(f"         Uploaded By: {doc.get('uploaded_by', 'NO_USER')}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error checking document approval workflow: {e}")
            return False
    
    async def generate_schema_report(self):
        """Generate comprehensive schema verification report"""
        print(f"\n📊 GENERATING SCHEMA VERIFICATION REPORT:")
        print("=" * 80)
        
        # Summary statistics
        print(f"\n📈 TEST SUMMARY:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "N/A")
        
        # Schema issues summary
        if self.schema_issues:
            print(f"\n⚠️  SCHEMA ISSUES FOUND ({len(self.schema_issues)}):")
            
            for i, issue in enumerate(self.schema_issues, 1):
                print(f"\n   Issue {i}: {issue['type']}")
                print(f"      Impact: {issue.get('impact', 'unknown')}")
                
                if issue['type'] == 'missing_collections':
                    print(f"      Missing Collections: {issue['collections']}")
                    print(f"      Recommendation: Create missing collections or verify collection names")
                
                elif issue['type'] == 'documents_schema_mismatch':
                    print(f"      Schema Issues: {len(issue['issues'])}")
                    for schema_issue in issue['issues'][:3]:  # Show first 3
                        print(f"         - {schema_issue}")
                    print(f"      Recommendation: Update document schema or fix data types")
                
                elif issue['type'] == 'field_type_compatibility':
                    print(f"      Compatibility Issues: {len(issue['issues'])}")
                    for compat_issue in issue['issues'][:3]:  # Show first 3
                        print(f"         - {compat_issue}")
                    print(f"      Recommendation: Convert field types to match Pydantic models")
                
                elif issue['type'] == 'missing_approval_status':
                    print(f"      Documents without approval_status: {issue['count']}")
                    print(f"      Recommendation: Add approval_status field to all documents")
        
        else:
            print(f"\n✅ NO SCHEMA ISSUES FOUND!")
            print(f"   Database schema matches application expectations")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if any(issue['impact'] == 'high' for issue in self.schema_issues):
            print(f"   🚨 HIGH PRIORITY:")
            print(f"      - Fix missing collections and approval status fields")
            print(f"      - Verify document upload and approval workflow")
            print(f"      - Check chat system database integration")
        
        if any(issue['impact'] == 'medium' for issue in self.schema_issues):
            print(f"   ⚠️  MEDIUM PRIORITY:")
            print(f"      - Fix field type mismatches")
            print(f"      - Ensure UUID format consistency")
            print(f"      - Verify datetime field formats")
        
        if not self.schema_issues:
            print(f"   ✅ Database schema is production-ready")
            print(f"   ✅ All collections and fields match expectations")
            print(f"   ✅ No compatibility issues found")
        
        print("=" * 80)
        
        return len(self.schema_issues) == 0

async def main():
    """Main function to run database schema verification"""
    print("🔍 DATABASE SCHEMA VERIFICATION - PRODUCTION SCHEMA VS EXPECTED SCHEMA")
    print("=" * 80)
    print("Target: Verify production database schema matches application expectations")
    print("Focus: Collections, field types, and data compatibility")
    print("=" * 80)
    
    verifier = DatabaseSchemaVerifier()
    
    try:
        # Connect to database
        if not await verifier.connect_to_database():
            print("❌ Cannot connect to database - stopping verification")
            return False
        
        # Run verification tests
        print(f"\n🔍 STARTING SCHEMA VERIFICATION TESTS...")
        
        # 1. Collections Inventory
        collections_data = await verifier.get_collections_inventory()
        
        # 2. Verify Expected Collections
        verifier.run_test(
            "Expected Collections Verification",
            verifier.verify_expected_collections
        )
        
        # 3. Documents Collection Schema
        verifier.run_test(
            "Documents Collection Schema",
            verifier.verify_documents_collection_schema
        )
        
        # 4. Chat Collections Schema
        verifier.run_test(
            "Chat Collections Schema", 
            verifier.verify_chat_collections_schema
        )
        
        # 5. User Collections Schema
        verifier.run_test(
            "User Collections Schema",
            verifier.verify_user_collections_schema
        )
        
        # 6. Field Type Compatibility
        verifier.run_test(
            "Field Type Compatibility",
            verifier.verify_field_types_compatibility
        )
        
        # 7. Document Approval Workflow
        verifier.run_test(
            "Document Approval Workflow",
            verifier.check_document_approval_workflow
        )
        
        # Generate final report
        schema_ok = await verifier.generate_schema_report()
        
        return schema_ok
        
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False
        
    finally:
        await verifier.disconnect_from_database()

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if result:
            print(f"\n🎉 DATABASE SCHEMA VERIFICATION COMPLETED SUCCESSFULLY!")
            sys.exit(0)
        else:
            print(f"\n⚠️  DATABASE SCHEMA VERIFICATION FOUND ISSUES!")
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n⚠️  Schema verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Schema verification failed: {e}")
        sys.exit(1)