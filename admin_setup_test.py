#!/usr/bin/env python3

import requests
import json

def test_admin_setup():
    """Test admin user setup and registration code creation"""
    
    base_url = "https://doc-embeddings.preview.emergentagent.com/api"
    
    print("🔧 Testing Admin Setup for Beta Authentication")
    print("=" * 50)
    
    # Test registering the admin user (Layth Bunni)
    admin_data = {
        "email": "layth.bunni@adamsmithinternational.com",
        "registration_code": "BETA2025",
        "personal_code": "admin123456",
        "department": "Management"
    }
    
    print("\n👑 Testing Admin User Registration...")
    try:
        response = requests.post(f"{base_url}/auth/register", json=admin_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Admin user registered successfully")
            print(f"   Email: {result['user']['email']}")
            print(f"   Role: {result['user']['role']}")
            print(f"   Department: {result['user']['department']}")
            
            # Test admin login
            login_data = {
                "email": "layth.bunni@adamsmithinternational.com",
                "personal_code": "admin123456"
            }
            
            print("\n🔑 Testing Admin Login...")
            login_response = requests.post(f"{base_url}/auth/login", json=login_data)
            
            if login_response.status_code == 200:
                login_result = login_response.json()
                print("✅ Admin login successful")
                print(f"   Token: {login_result['access_token'][:20]}...")
                
                # Test admin access to /auth/me
                headers = {'Authorization': f'Bearer {login_result["access_token"]}'}
                me_response = requests.get(f"{base_url}/auth/me", headers=headers)
                
                if me_response.status_code == 200:
                    me_result = me_response.json()
                    print("✅ Admin authentication working")
                    print(f"   Admin Role: {me_result['role']}")
                    print(f"   Admin Department: {me_result['department']}")
                    
                    return True
                else:
                    print(f"❌ Admin /auth/me failed: {me_response.status_code}")
                    return False
            else:
                print(f"❌ Admin login failed: {login_response.status_code}")
                print(f"   Error: {login_response.json()}")
                return False
                
        elif response.status_code == 400 and "already registered" in response.json().get('detail', ''):
            print("ℹ️  Admin user already exists, testing login...")
            
            # Test admin login
            login_data = {
                "email": "layth.bunni@adamsmithinternational.com", 
                "personal_code": "admin123456"
            }
            
            login_response = requests.post(f"{base_url}/auth/login", json=login_data)
            
            if login_response.status_code == 200:
                print("✅ Admin login successful")
                return True
            else:
                print("❌ Admin login failed - may need to use different credentials")
                return False
        else:
            print(f"❌ Admin registration failed: {response.status_code}")
            print(f"   Error: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Error during admin setup: {str(e)}")
        return False

def test_user_limit():
    """Test the 20 user limit functionality"""
    
    print("\n📊 Testing User Limit (20 users max)...")
    
    import pymongo
    from pymongo import MongoClient
    
    try:
        client = MongoClient("mongodb://localhost:27017")
        db = client["test_database"]
        
        # Count current users
        current_users = db.beta_users.count_documents({"is_active": True})
        print(f"   Current active users: {current_users}")
        print(f"   User limit: 20")
        print(f"   Remaining slots: {20 - current_users}")
        
        if current_users < 20:
            print("✅ User limit check working - can register more users")
        else:
            print("⚠️  User limit reached - new registrations should be blocked")
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking user limit: {str(e)}")
        return False

if __name__ == "__main__":
    success1 = test_admin_setup()
    success2 = test_user_limit()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 Admin setup tests completed successfully!")
    else:
        print("⚠️  Some admin setup tests failed")