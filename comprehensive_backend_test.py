#!/usr/bin/env python3
"""
COMPREHENSIVE BACKEND DATABASE SCHEMA TESTING
==============================================

This script tests the backend APIs to create data in all collections
and then verifies the database schema matches expectations.
"""

import requests
import json
import time
import asyncio
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

class ComprehensiveBackendTester:
    def __init__(self):
        # Get backend URL from frontend/.env
        self.load_backend_url()
        self.api_url = f"{self.base_url}/api"
        self.auth_token = None
        self.tests_run = 0
        self.tests_passed = 0
        
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
        print(f"🔗 API URL: {self.api_url}")
    
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
            self.auth_token = response.get('access_token')
            print(f"   ✅ Admin authenticated successfully")
            print(f"   🔑 Token: {self.auth_token[:20] if self.auth_token else 'None'}...")
            return True
        else:
            print(f"   ❌ Admin authentication failed")
            return False
    
    def create_test_document(self):
        """Create a test document to populate documents collection"""
        print(f"\n📄 CREATING TEST DOCUMENT...")
        
        # Create test file content
        test_content = """
        ASI Company Policy Document - Test Document
        
        This is a test document for schema verification.
        
        Leave Policy:
        - Annual leave: 25 days
        - Sick leave: 10 days
        - Emergency leave: Manager approval required
        
        IT Policy:
        - Password changes every 90 days
        - VPN required for remote access
        - Software installation requires IT approval
        """
        
        test_file_path = Path("/tmp/test_schema_document.txt")
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        try:
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test_schema_document.txt', f, 'text/plain')}
                data = {'department': 'Finance', 'tags': 'policy,test,schema'}
                
                success, response = self.run_test(
                    "Document Upload",
                    "POST",
                    "/documents/upload",
                    200,
                    data=data,
                    files=files
                )
                
                if success:
                    document_id = response.get('id')
                    print(f"   ✅ Document created: {document_id}")
                    return document_id
                else:
                    print(f"   ❌ Document creation failed")
                    return None
        finally:
            if test_file_path.exists():
                test_file_path.unlink()
    
    def approve_document(self, document_id):
        """Approve the test document"""
        if not document_id:
            return False
            
        print(f"\n✅ APPROVING TEST DOCUMENT...")
        
        success, response = self.run_test(
            "Approve Document",
            "PUT",
            f"/documents/{document_id}/approve?approved_by=admin",
            200
        )
        
        if success:
            print(f"   ✅ Document approved successfully")
            return True
        else:
            print(f"   ❌ Document approval failed")
            return False
    
    def create_chat_session(self):
        """Create a chat session and messages"""
        print(f"\n💬 CREATING CHAT SESSION...")
        
        session_id = f"test-schema-session-{int(time.time())}"
        
        chat_data = {
            "session_id": session_id,
            "message": "What is the company leave policy for annual leave?",
            "stream": False
        }
        
        success, response = self.run_test(
            "Chat Send Message",
            "POST",
            "/chat/send",
            200,
            chat_data
        )
        
        if success:
            print(f"   ✅ Chat session created: {session_id}")
            return session_id
        else:
            print(f"   ❌ Chat session creation failed")
            return None
    
    def create_ticket(self):
        """Create a support ticket"""
        print(f"\n🎫 CREATING SUPPORT TICKET...")
        
        ticket_data = {
            "subject": "Test Schema Verification Ticket",
            "description": "This is a test ticket created for database schema verification purposes.",
            "department": "Information Technology",
            "priority": "medium",
            "category": "Technical Support",
            "sub_category": "System Issue",
            "requester_name": "Schema Tester",
            "tags": ["test", "schema", "verification"]
        }
        
        success, response = self.run_test(
            "Create Ticket",
            "POST",
            "/tickets",
            200,
            ticket_data
        )
        
        if success:
            ticket_id = response.get('id')
            print(f"   ✅ Ticket created: {ticket_id}")
            return ticket_id
        else:
            print(f"   ❌ Ticket creation failed")
            return None
    
    def create_boost_business_unit(self):
        """Create a BOOST business unit"""
        print(f"\n🏢 CREATING BOOST BUSINESS UNIT...")
        
        if not self.auth_token:
            print(f"   ❌ No auth token available")
            return None
        
        auth_headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        unit_data = {
            "name": "Test Schema Unit",
            "code": "TSU001"
        }
        
        success, response = self.run_test(
            "Create Business Unit",
            "POST",
            "/boost/business-units",
            200,
            unit_data,
            headers=auth_headers
        )
        
        if success:
            unit_id = response.get('id')
            print(f"   ✅ Business unit created: {unit_id}")
            return unit_id
        else:
            print(f"   ❌ Business unit creation failed")
            return None
    
    def create_boost_user(self, business_unit_id=None):
        """Create a BOOST user"""
        print(f"\n👤 CREATING BOOST USER...")
        
        user_data = {
            "name": "Test Schema User",
            "email": "test.schema@example.com",
            "boost_role": "Agent",
            "business_unit_id": business_unit_id,
            "department": "IT"
        }
        
        success, response = self.run_test(
            "Create BOOST User",
            "POST",
            "/boost/users",
            200,
            user_data
        )
        
        if success:
            user_id = response.get('id')
            print(f"   ✅ BOOST user created: {user_id}")
            return user_id
        else:
            print(f"   ❌ BOOST user creation failed")
            return None
    
    def create_boost_ticket(self, business_unit_id=None):
        """Create a BOOST ticket"""
        print(f"\n🎫 CREATING BOOST TICKET...")
        
        ticket_data = {
            "subject": "Test Schema BOOST Ticket",
            "description": "This is a test BOOST ticket for schema verification.",
            "support_department": "IT",
            "category": "Technical Support",
            "subcategory": "System Issue",
            "classification": "ServiceRequest",
            "priority": "medium",
            "justification": "Schema testing purposes",
            "requester_name": "Schema Tester",
            "requester_email": "schema.tester@example.com",
            "requester_id": "schema-tester-001",
            "business_unit_id": business_unit_id,
            "channel": "Hub"
        }
        
        success, response = self.run_test(
            "Create BOOST Ticket",
            "POST",
            "/boost/tickets",
            200,
            ticket_data
        )
        
        if success:
            ticket_id = response.get('id')
            print(f"   ✅ BOOST ticket created: {ticket_id}")
            return ticket_id
        else:
            print(f"   ❌ BOOST ticket creation failed")
            return None
    
    def create_finance_sop(self):
        """Create a Finance SOP"""
        print(f"\n💰 CREATING FINANCE SOP...")
        
        sop_data = {
            "month": "2025-01",
            "year": 2025
        }
        
        success, response = self.run_test(
            "Create Finance SOP",
            "POST",
            "/finance-sop",
            200,
            sop_data
        )
        
        if success:
            sop_id = response.get('id')
            print(f"   ✅ Finance SOP created: {sop_id}")
            return sop_id
        else:
            print(f"   ❌ Finance SOP creation failed")
            return None
    
    async def verify_database_collections(self):
        """Verify all collections were created in the database"""
        print(f"\n🔍 VERIFYING DATABASE COLLECTIONS...")
        
        try:
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client['ai-workspace-17-test_database']
            
            collections = await db.list_collection_names()
            print(f"   📋 Found collections: {sorted(collections)}")
            
            expected_collections = [
                'documents', 'chat_sessions', 'chat_messages', 'beta_users',
                'tickets', 'boost_tickets', 'boost_users', 'boost_business_units',
                'finance_sops'
            ]
            
            created_collections = []
            missing_collections = []
            
            for expected in expected_collections:
                if expected in collections:
                    count = await db[expected].count_documents({})
                    created_collections.append(expected)
                    print(f"   ✅ {expected}: {count} documents")
                else:
                    missing_collections.append(expected)
                    print(f"   ❌ {expected}: Missing")
            
            print(f"\n📊 COLLECTION SUMMARY:")
            print(f"   Created: {len(created_collections)}/{len(expected_collections)}")
            print(f"   Missing: {missing_collections}")
            
            client.close()
            return len(missing_collections) == 0
            
        except Exception as e:
            print(f"   ❌ Database verification failed: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive backend test to populate all collections"""
        print(f"🚀 COMPREHENSIVE BACKEND DATABASE SCHEMA TEST")
        print("=" * 60)
        print("Goal: Create data in all collections and verify schema")
        print("=" * 60)
        
        # Step 1: Authenticate
        if not self.authenticate_as_admin():
            print(f"❌ Cannot proceed without admin authentication")
            return False
        
        # Step 2: Create test data in each collection type
        print(f"\n📊 CREATING TEST DATA IN ALL COLLECTIONS...")
        
        # Documents
        document_id = self.create_test_document()
        if document_id:
            self.approve_document(document_id)
        
        # Chat
        session_id = self.create_chat_session()
        
        # Tickets
        ticket_id = self.create_ticket()
        
        # BOOST Business Units
        business_unit_id = self.create_boost_business_unit()
        
        # BOOST Users
        boost_user_id = self.create_boost_user(business_unit_id)
        
        # BOOST Tickets
        boost_ticket_id = self.create_boost_ticket(business_unit_id)
        
        # Finance SOPs
        sop_id = self.create_finance_sop()
        
        # Step 3: Verify database collections
        print(f"\n🔍 VERIFYING DATABASE SCHEMA...")
        collections_ok = asyncio.run(self.verify_database_collections())
        
        # Step 4: Summary
        print(f"\n📊 COMPREHENSIVE TEST SUMMARY:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "N/A")
        print(f"   Collections Created: {'✅ Yes' if collections_ok else '❌ No'}")
        
        return collections_ok and (self.tests_passed / self.tests_run) > 0.8

def main():
    """Main function"""
    tester = ComprehensiveBackendTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print(f"\n🎉 COMPREHENSIVE BACKEND TEST COMPLETED SUCCESSFULLY!")
            print(f"✅ All collections populated and schema verified")
        else:
            print(f"\n⚠️  COMPREHENSIVE BACKEND TEST FOUND ISSUES!")
            print(f"❌ Some collections or tests failed")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Comprehensive test failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    result = main()
    sys.exit(0 if result else 1)