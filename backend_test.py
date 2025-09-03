import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path

class ASIOSAPITester:
    def __init__(self, base_url="https://asi-aihub.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = f"test-session-{int(time.time())}"

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}{endpoint}"
        headers = {'Content-Type': 'application/json'} if not files else {}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, data=data)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

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

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "/", 200)

    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        return self.run_test("Dashboard Stats", "GET", "/dashboard/stats", 200)

    def test_document_upload(self):
        """Test document upload functionality"""
        # Create a test file
        test_content = """
        ASI OS Company Policy Document
        
        Leave Management Policy:
        1. All employees are entitled to 25 days of annual leave
        2. Leave requests must be submitted 2 weeks in advance
        3. Emergency leave can be approved by direct manager
        
        IT Support Policy:
        1. All IT issues should be reported via support ticket
        2. Password resets are handled by IT department
        3. Software installation requires approval
        """
        
        test_file_path = Path("/tmp/test_policy.txt")
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        try:
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test_policy.txt', f, 'text/plain')}
                data = {'department': 'System & IT Support', 'tags': 'policy,test'}
                success, response = self.run_test(
                    "Document Upload", 
                    "POST", 
                    "/documents/upload", 
                    200, 
                    data=data, 
                    files=files
                )
                if success:
                    return success, response.get('id')
                return success, None
        finally:
            if test_file_path.exists():
                test_file_path.unlink()

    def test_get_documents(self):
        """Test getting all documents"""
        return self.run_test("Get Documents", "GET", "/documents", 200)

    def test_chat_send(self, document_id=None):
        """Test RAG chat functionality"""
        chat_data = {
            "session_id": self.session_id,
            "message": "What are the company policies for leave management?",
            "document_ids": [document_id] if document_id else []
        }
        
        success, response = self.run_test("RAG Chat Send", "POST", "/chat/send", 200, chat_data)
        
        if success:
            ai_response = response.get('response', 'No response')
            if isinstance(ai_response, dict):
                ai_response = str(ai_response)
            print(f"   AI Response: {ai_response[:100]}...")
            # Wait a bit for GPT-5 processing
            time.sleep(2)
        
        return success, response

    def test_get_chat_sessions(self):
        """Test getting chat sessions"""
        return self.run_test("Get Chat Sessions", "GET", "/chat/sessions", 200)

    def test_get_chat_messages(self):
        """Test getting chat messages for a session"""
        return self.run_test(
            "Get Chat Messages", 
            "GET", 
            f"/chat/sessions/{self.session_id}/messages", 
            200
        )

    def test_create_ticket(self):
        """Test ticket creation with AI categorization"""
        ticket_data = {
            "subject": "Cannot access email on new laptop",
            "description": "I received a new laptop but cannot configure my email. Getting authentication errors when trying to set up Outlook.",
            "department": "System & IT Support",
            "priority": "medium"
        }
        
        success, response = self.run_test("Create Ticket", "POST", "/tickets", 200, ticket_data)
        
        if success:
            print(f"   Ticket Number: {response.get('ticket_number')}")
            print(f"   AI Category: {response.get('category')}")
            print(f"   AI Sub-category: {response.get('sub_category')}")
            return success, response.get('id')
        
        return success, None

    def test_get_tickets(self):
        """Test getting all tickets"""
        return self.run_test("Get Tickets", "GET", "/tickets", 200)

    def test_get_ticket_by_id(self, ticket_id):
        """Test getting a specific ticket"""
        if not ticket_id:
            print("⚠️  Skipping ticket by ID test - no ticket ID available")
            return True, {}
        
        return self.run_test("Get Ticket by ID", "GET", f"/tickets/{ticket_id}", 200)

    def test_finance_sop_create(self):
        """Test Finance SOP creation"""
        sop_data = {
            "month": "2025-01",
            "year": 2025
        }
        
        success, response = self.run_test("Create Finance SOP", "POST", "/finance-sop", 200, sop_data)
        
        if success:
            return success, response.get('id')
        return success, None

    def test_get_finance_sops(self):
        """Test getting Finance SOPs"""
        return self.run_test("Get Finance SOPs", "GET", "/finance-sop", 200)

    def test_update_finance_sop(self, sop_id):
        """Test updating Finance SOP"""
        if not sop_id:
            print("⚠️  Skipping Finance SOP update test - no SOP ID available")
            return True, {}
        
        update_data = {
            "prior_month_reviewed": True,
            "monthly_reports_prepared": True,
            "notes": "Test update from API testing"
        }
        
        return self.run_test("Update Finance SOP", "PUT", f"/finance-sop/{sop_id}", 200, update_data)

    # BOOST Support Ticketing System Tests
    
    def test_boost_categories(self):
        """Test getting BOOST categories"""
        return self.run_test("BOOST Categories", "GET", "/boost/categories", 200)
    
    def test_boost_department_categories(self):
        """Test getting categories for specific department"""
        return self.run_test("BOOST Finance Categories", "GET", "/boost/categories/Finance", 200)
    
    def test_create_business_unit(self):
        """Test creating a business unit"""
        unit_data = {
            "name": "Engineering Division",
            "code": "ENG001"
        }
        
        success, response = self.run_test("Create Business Unit", "POST", "/boost/business-units", 200, unit_data)
        
        if success:
            print(f"   Business Unit ID: {response.get('id')}")
            print(f"   Business Unit Name: {response.get('name')}")
            return success, response.get('id')
        
        return success, None
    
    def test_get_business_units(self):
        """Test getting all business units"""
        return self.run_test("Get Business Units", "GET", "/boost/business-units", 200)
    
    def test_update_business_unit(self, unit_id):
        """Test updating a business unit"""
        if not unit_id:
            print("⚠️  Skipping business unit update test - no unit ID available")
            return True, {}
        
        update_data = {
            "name": "Engineering Division - Updated",
            "code": "ENG001-UPD"
        }
        
        return self.run_test("Update Business Unit", "PUT", f"/boost/business-units/{unit_id}", 200, update_data)
    
    def test_create_boost_user(self, business_unit_id=None):
        """Test creating a BOOST user"""
        user_data = {
            "name": "John Smith",
            "email": "john.smith@company.com",
            "boost_role": "Agent",
            "business_unit_id": business_unit_id,
            "department": "IT"
        }
        
        success, response = self.run_test("Create BOOST User", "POST", "/boost/users", 200, user_data)
        
        if success:
            print(f"   User ID: {response.get('id')}")
            print(f"   User Name: {response.get('name')}")
            print(f"   User Role: {response.get('boost_role')}")
            return success, response.get('id')
        
        return success, None
    
    def test_get_boost_users(self):
        """Test getting all BOOST users"""
        return self.run_test("Get BOOST Users", "GET", "/boost/users", 200)
    
    def test_update_boost_user(self, user_id):
        """Test updating a BOOST user"""
        if not user_id:
            print("⚠️  Skipping BOOST user update test - no user ID available")
            return True, {}
        
        update_data = {
            "boost_role": "Manager",
            "department": "DevOps"
        }
        
        return self.run_test("Update BOOST User", "PUT", f"/boost/users/{user_id}", 200, update_data)
    
    def test_create_boost_ticket(self, business_unit_id=None):
        """Test creating a BOOST ticket"""
        ticket_data = {
            "subject": "Email configuration issue on new laptop",
            "description": "Unable to configure corporate email on newly issued laptop. Getting authentication errors when setting up Outlook with company credentials.",
            "support_department": "IT",
            "category": "Access",
            "subcategory": "Email",
            "classification": "Incident",
            "priority": "high",
            "justification": "User cannot access email for daily work",
            "requester_name": "Jane Doe",
            "requester_email": "jane.doe@company.com",
            "business_unit_id": business_unit_id,
            "channel": "Hub"
        }
        
        success, response = self.run_test("Create BOOST Ticket", "POST", "/boost/tickets", 200, ticket_data)
        
        if success:
            print(f"   Ticket ID: {response.get('id')}")
            print(f"   Ticket Number: {response.get('ticket_number')}")
            print(f"   Subject: {response.get('subject')}")
            print(f"   Status: {response.get('status')}")
            print(f"   Priority: {response.get('priority')}")
            return success, response.get('id')
        
        return success, None
    
    def test_get_boost_tickets(self):
        """Test getting all BOOST tickets"""
        return self.run_test("Get BOOST Tickets", "GET", "/boost/tickets", 200)
    
    def test_get_boost_tickets_filtered(self):
        """Test getting BOOST tickets with filters"""
        return self.run_test("Get BOOST Tickets (High Priority)", "GET", "/boost/tickets?priority=high", 200)
    
    def test_get_boost_ticket_by_id(self, ticket_id):
        """Test getting a specific BOOST ticket"""
        if not ticket_id:
            print("⚠️  Skipping BOOST ticket by ID test - no ticket ID available")
            return True, {}
        
        return self.run_test("Get BOOST Ticket by ID", "GET", f"/boost/tickets/{ticket_id}", 200)
    
    def test_update_boost_ticket(self, ticket_id):
        """Test updating a BOOST ticket"""
        if not ticket_id:
            print("⚠️  Skipping BOOST ticket update test - no ticket ID available")
            return True, {}
        
        update_data = {
            "status": "in_progress",
            "owner_id": "agent001",
            "owner_name": "Support Agent",
            "resolution_notes": "Investigating email configuration issue"
        }
        
        return self.run_test("Update BOOST Ticket", "PUT", f"/boost/tickets/{ticket_id}", 200, update_data)
    
    def test_add_boost_comment(self, ticket_id):
        """Test adding a comment to a BOOST ticket"""
        if not ticket_id:
            print("⚠️  Skipping BOOST comment test - no ticket ID available")
            return True, {}
        
        comment_data = {
            "body": "I have reviewed the ticket and will start investigating the email configuration issue. Please provide your laptop model and current Outlook version.",
            "is_internal": False,
            "author_name": "Support Agent"
        }
        
        success, response = self.run_test("Add BOOST Comment", "POST", f"/boost/tickets/{ticket_id}/comments", 200, comment_data)
        
        if success:
            print(f"   Comment ID: {response.get('id')}")
            print(f"   Comment Body: {response.get('body')[:50]}...")
            return success, response.get('id')
        
        return success, None
    
    def test_get_boost_comments(self, ticket_id):
        """Test getting comments for a BOOST ticket"""
        if not ticket_id:
            print("⚠️  Skipping get BOOST comments test - no ticket ID available")
            return True, {}
        
        return self.run_test("Get BOOST Comments", "GET", f"/boost/tickets/{ticket_id}/comments", 200)
    
    def test_delete_boost_user(self, user_id):
        """Test deleting a BOOST user"""
        if not user_id:
            print("⚠️  Skipping BOOST user deletion test - no user ID available")
            return True, {}
        
        return self.run_test("Delete BOOST User", "DELETE", f"/boost/users/{user_id}", 200)
    
    def test_delete_business_unit(self, unit_id):
        """Test deleting a business unit"""
        if not unit_id:
            print("⚠️  Skipping business unit deletion test - no unit ID available")
            return True, {}
        
        return self.run_test("Delete Business Unit", "DELETE", f"/boost/business-units/{unit_id}", 200)

def main():
    print("🚀 Starting ASI OS API Testing...")
    print("=" * 60)
    
    tester = ASIOSAPITester()
    
    # Test basic connectivity
    print("\n📡 Testing Basic Connectivity...")
    success, _ = tester.test_root_endpoint()
    if not success:
        print("❌ Cannot connect to API. Stopping tests.")
        return 1
    
    # Test dashboard
    print("\n📊 Testing Dashboard...")
    tester.test_dashboard_stats()
    
    # Test document management
    print("\n📄 Testing Document Management...")
    doc_success, document_id = tester.test_document_upload()
    tester.test_get_documents()
    
    # Test RAG chat functionality
    print("\n🤖 Testing RAG Chat (GPT-5)...")
    tester.test_chat_send(document_id if doc_success else None)
    tester.test_get_chat_sessions()
    tester.test_get_chat_messages()
    
    # Test ticket management
    print("\n🎫 Testing Ticket Management...")
    ticket_success, ticket_id = tester.test_create_ticket()
    tester.test_get_tickets()
    tester.test_get_ticket_by_id(ticket_id if ticket_success else None)
    
    # Test Finance SOP
    print("\n💰 Testing Finance SOP...")
    sop_success, sop_id = tester.test_finance_sop_create()
    tester.test_get_finance_sops()
    tester.test_update_finance_sop(sop_id if sop_success else None)
    
    # Test BOOST Support Ticketing System
    print("\n🎯 Testing BOOST Support Ticketing System...")
    
    # Test categories first
    print("\n📋 Testing BOOST Categories...")
    tester.test_boost_categories()
    tester.test_boost_department_categories()
    
    # Test business units
    print("\n🏢 Testing Business Units Management...")
    bu_success, business_unit_id = tester.test_create_business_unit()
    tester.test_get_business_units()
    tester.test_update_business_unit(business_unit_id if bu_success else None)
    
    # Test BOOST users
    print("\n👥 Testing BOOST Users Management...")
    user_success, boost_user_id = tester.test_create_boost_user(business_unit_id if bu_success else None)
    tester.test_get_boost_users()
    tester.test_update_boost_user(boost_user_id if user_success else None)
    
    # Test BOOST tickets
    print("\n🎫 Testing BOOST Tickets Management...")
    boost_ticket_success, boost_ticket_id = tester.test_create_boost_ticket(business_unit_id if bu_success else None)
    tester.test_get_boost_tickets()
    tester.test_get_boost_tickets_filtered()
    tester.test_get_boost_ticket_by_id(boost_ticket_id if boost_ticket_success else None)
    tester.test_update_boost_ticket(boost_ticket_id if boost_ticket_success else None)
    
    # Test BOOST comments
    print("\n💬 Testing BOOST Comments Management...")
    tester.test_add_boost_comment(boost_ticket_id if boost_ticket_success else None)
    tester.test_get_boost_comments(boost_ticket_id if boost_ticket_success else None)
    
    # Clean up test data (optional - delete created test records)
    print("\n🧹 Cleaning up test data...")
    tester.test_delete_boost_user(boost_user_id if user_success else None)
    tester.test_delete_business_unit(business_unit_id if bu_success else None)
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Backend API is working correctly.")
        return 0
    else:
        failed_tests = tester.tests_run - tester.tests_passed
        print(f"⚠️  {failed_tests} test(s) failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())