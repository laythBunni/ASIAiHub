import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path

class ASIOSAPITester:
    def __init__(self, base_url="https://intelliops-asi.preview.emergentagent.com"):
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
            print(f"   AI Response: {response.get('response', 'No response')[:100]}...")
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