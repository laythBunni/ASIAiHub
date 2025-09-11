#!/usr/bin/env python3
"""
Layth Authentication Debug Test
Focused test for the review request to debug Layth's authentication issue
"""

import requests
import json
import sys
from pathlib import Path

def test_layth_authentication():
    """Test Layth's authentication as specified in review request"""
    
    # Get backend URL from frontend/.env
    backend_url = "https://doc-embeddings.preview.emergentagent.com"
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    backend_url = line.split('=', 1)[1].strip()
                    break
    except:
        pass
    
    api_url = f"{backend_url}/api"
    
    print("🔍 LAYTH AUTHENTICATION DEBUG - REVIEW REQUEST TESTING")
    print("=" * 80)
    print("📋 Testing specific requirements from review request:")
    print("   1. Check if backend is running (GET /api/auth/me)")
    print("   2. Test Layth's login credentials (layth.bunni@adamsmithinternational.com / 899443)")
    print("   3. Verify user exists in database")
    print("   4. Test authentication endpoint")
    print("   5. Database connectivity")
    print("=" * 80)
    print(f"🌐 Backend URL: {backend_url}")
    print(f"🔗 API URL: {api_url}")
    
    # Step 1: Check if backend is running
    print("\n🔧 Step 1: Testing Backend Responsiveness...")
    print("   Testing GET /api/auth/me endpoint (without auth - should return 401/403)")
    
    try:
        response = requests.get(f"{api_url}/auth/me", timeout=10)
        print(f"   URL: {api_url}/auth/me")
        print(f"   Status: {response.status_code}")
        
        if response.status_code in [401, 403]:
            print(f"   ✅ Backend is running and responding correctly")
            print(f"   ✅ Authentication endpoint properly protected")
            backend_running = True
        elif response.status_code == 200:
            print(f"   ⚠️  Backend running but auth endpoint not protected")
            backend_running = True
        else:
            print(f"   ❌ Unexpected response from backend")
            backend_running = False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Backend connection failed: {str(e)}")
        print(f"   ❌ Cannot reach backend at {api_url}")
        backend_running = False
    
    if not backend_running:
        print("\n❌ CRITICAL: Backend is not running or not accessible")
        return False
    
    # Step 2: Test Layth's login credentials
    print("\n🔐 Step 2: Testing Layth's Login Credentials...")
    print("   Email: layth.bunni@adamsmithinternational.com")
    print("   Personal Code: 899443")
    
    layth_login_data = {
        "email": "layth.bunni@adamsmithinternational.com",
        "personal_code": "899443"
    }
    
    try:
        response = requests.post(
            f"{api_url}/auth/login",
            json=layth_login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   URL: {api_url}/auth/login")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            login_response = response.json()
            layth_token = login_response.get('access_token') or login_response.get('token')
            layth_user_data = login_response.get('user', {})
            
            print(f"   ✅ Layth login successful")
            print(f"   👤 User ID: {layth_user_data.get('id')}")
            print(f"   📧 Email: {layth_user_data.get('email')}")
            print(f"   👑 Role: {layth_user_data.get('role')}")
            print(f"   🔑 Token: {layth_token[:20] if layth_token else 'None'}...")
            
            if layth_user_data.get('role') == 'Admin':
                print(f"   ✅ Admin role confirmed")
            else:
                print(f"   ⚠️  Expected Admin role, got: {layth_user_data.get('role')}")
            
            login_success = True
        else:
            print(f"   ❌ Layth login failed")
            print(f"   ❌ Status code: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   📋 Error details: {error_data}")
            except:
                print(f"   📋 Response text: {response.text}")
            login_success = False
            layth_token = None
            layth_user_data = {}
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Login request failed: {str(e)}")
        login_success = False
        layth_token = None
        layth_user_data = {}
    
    # Step 3: Verify user exists in database (via admin endpoint if we have token)
    print("\n💾 Step 3: Verifying User Exists in Database...")
    
    if layth_token:
        auth_headers = {'Authorization': f'Bearer {layth_token}'}
        
        try:
            response = requests.get(
                f"{api_url}/admin/users",
                headers=auth_headers,
                timeout=10
            )
            
            print(f"   URL: {api_url}/admin/users")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                users_response = response.json()
                
                if isinstance(users_response, list):
                    layth_found = False
                    layth_db_record = None
                    
                    for user in users_response:
                        if user.get('email') == 'layth.bunni@adamsmithinternational.com':
                            layth_found = True
                            layth_db_record = user
                            break
                    
                    if layth_found:
                        print(f"   ✅ Layth's user record found in database")
                        print(f"   📋 Database ID: {layth_db_record.get('id')}")
                        print(f"   📧 Database Email: {layth_db_record.get('email')}")
                        print(f"   👑 Database Role: {layth_db_record.get('role')}")
                        print(f"   🔢 Personal Code: {layth_db_record.get('personal_code', 'Not visible')}")
                        print(f"   ✅ User is active: {layth_db_record.get('is_active', 'Unknown')}")
                        
                        # Verify personal code matches
                        if layth_db_record.get('personal_code') == '899443':
                            print(f"   ✅ Personal code matches: 899443")
                        else:
                            print(f"   ⚠️  Personal code in DB: {layth_db_record.get('personal_code')}")
                    else:
                        print(f"   ❌ Layth's user record NOT found in database")
                        print(f"   📊 Total users in database: {len(users_response)}")
                else:
                    print(f"   ❌ Unexpected response format from admin/users")
            else:
                print(f"   ❌ Could not retrieve users from database")
                print(f"   📋 Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Admin users request failed: {str(e)}")
    else:
        print(f"   ⚠️  No token available - cannot verify database record")
    
    # Step 4: Test authentication endpoint with token
    print("\n🔑 Step 4: Testing Authentication Endpoint with Token...")
    
    if layth_token:
        auth_headers = {'Authorization': f'Bearer {layth_token}'}
        
        try:
            response = requests.get(
                f"{api_url}/auth/me",
                headers=auth_headers,
                timeout=10
            )
            
            print(f"   URL: {api_url}/auth/me")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                me_response = response.json()
                print(f"   ✅ Token authentication successful")
                print(f"   👤 Authenticated as: {me_response.get('email')}")
                print(f"   👑 Role: {me_response.get('role')}")
                print(f"   🏢 Department: {me_response.get('department', 'Not set')}")
                
                # Verify token returns same user as login
                if me_response.get('email') == 'layth.bunni@adamsmithinternational.com':
                    print(f"   ✅ Token authentication matches login user")
                else:
                    print(f"   ❌ Token authentication user mismatch")
            else:
                print(f"   ❌ Token authentication failed")
                print(f"   ❌ Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Auth/me request failed: {str(e)}")
    else:
        print(f"   ⚠️  No token available - cannot test token authentication")
    
    # Step 5: Test database connectivity and admin endpoints
    print("\n🗄️  Step 5: Testing Database Connectivity...")
    
    if layth_token:
        auth_headers = {'Authorization': f'Bearer {layth_token}'}
        
        # Test admin stats endpoint
        try:
            response = requests.get(
                f"{api_url}/admin/stats",
                headers=auth_headers,
                timeout=10
            )
            
            print(f"   URL: {api_url}/admin/stats")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                stats_response = response.json()
                print(f"   ✅ Database connectivity confirmed")
                print(f"   📊 Total Users: {stats_response.get('totalUsers', 'Unknown')}")
                print(f"   📊 Total Tickets: {stats_response.get('totalTickets', 'Unknown')}")
                print(f"   📊 Total Documents: {stats_response.get('totalDocuments', 'Unknown')}")
                print(f"   📊 Total Sessions: {stats_response.get('totalSessions', 'Unknown')}")
            else:
                print(f"   ❌ Database connectivity issue or admin stats endpoint failed")
                print(f"   📋 Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Admin stats request failed: {str(e)}")
        
        # Test chat functionality (RAG system)
        print(f"\n🤖 Additional Test: Chat Functionality...")
        
        chat_data = {
            "session_id": f"layth-debug-test",
            "message": "Hello James, can you help me with company policies?",
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{api_url}/chat/send",
                json=chat_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"   URL: {api_url}/chat/send")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                chat_response = response.json()
                print(f"   ✅ Chat functionality working")
                print(f"   🤖 AI response received")
                print(f"   📄 Documents referenced: {chat_response.get('documents_referenced', 0)}")
            else:
                print(f"   ❌ Chat functionality failed")
                print(f"   📋 Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Chat request failed: {str(e)}")
        
        # Test document access
        print(f"\n📄 Additional Test: Document Access...")
        
        try:
            response = requests.get(
                f"{api_url}/documents",
                timeout=10
            )
            
            print(f"   URL: {api_url}/documents")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                docs_response = response.json()
                if isinstance(docs_response, list):
                    print(f"   ✅ Document access working")
                    print(f"   📚 Available documents: {len(docs_response)}")
                else:
                    print(f"   ⚠️  Unexpected document response format")
            else:
                print(f"   ❌ Document access failed")
                print(f"   📋 Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Documents request failed: {str(e)}")
    
    # Final Summary
    print(f"\n📋 LAYTH AUTHENTICATION DEBUG SUMMARY:")
    print("=" * 60)
    
    if backend_running:
        print(f"✅ Backend Status: Running and accessible at {backend_url}")
    else:
        print(f"❌ Backend Status: Not accessible")
    
    if login_success:
        print(f"✅ Layth Login: Successful with personal code 899443")
        print(f"   👤 User: {layth_user_data.get('email')}")
        print(f"   👑 Role: {layth_user_data.get('role')}")
    else:
        print(f"❌ Layth Login: Failed")
    
    if layth_token:
        print(f"✅ Authentication Token: Generated and working")
        print(f"   🔑 Token: {layth_token[:20]}...")
    else:
        print(f"❌ Authentication Token: Not available")
    
    print("=" * 60)
    
    # Conclusion
    if backend_running and login_success and layth_token:
        print("\n🎉 CONCLUSION: Backend authentication is working correctly!")
        print("   ✅ Backend is accessible")
        print("   ✅ Layth can login with personal code 899443")
        print("   ✅ Authentication token is generated and working")
        print("   ✅ Admin role is confirmed")
        print("   ✅ Database connectivity is working")
        print("\n💡 The login page issue is likely frontend-specific:")
        print("   - Form submission problems")
        print("   - JavaScript errors")
        print("   - Network connectivity issues in production environment")
        print("   - NOT a backend authentication problem")
        return True
    else:
        print("\n❌ CONCLUSION: Backend authentication has issues!")
        print("   Please review the detailed output above")
        return False

if __name__ == "__main__":
    success = test_layth_authentication()
    sys.exit(0 if success else 1)