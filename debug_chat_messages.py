#!/usr/bin/env python3
"""
Debug script to investigate the Historic Chat Modal Fix issue
"""

import requests
import json
import time

def debug_chat_messages():
    # Get base URL
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    base_url = line.split('=', 1)[1].strip()
                    break
            else:
                base_url = "http://localhost:8001"
    except:
        base_url = "http://localhost:8001"
    
    api_url = f"{base_url}/api"
    
    # Authenticate
    login_data = {
        "email": "layth.bunni@adamsmithinternational.com",
        "personal_code": "899443"
    }
    
    print("🔐 Authenticating...")
    response = requests.post(f"{api_url}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        return
    
    auth_data = response.json()
    token = auth_data.get('access_token') or auth_data.get('token')
    print(f"✅ Authenticated successfully")
    
    # Get existing chat sessions
    print("\n📋 Getting existing chat sessions...")
    response = requests.get(f"{api_url}/chat/sessions")
    if response.status_code == 200:
        sessions = response.json()
        print(f"✅ Found {len(sessions)} sessions")
        
        # Test with an existing session that has messages
        if sessions:
            test_session = sessions[0]  # Use first session
            session_id = test_session.get('id')
            messages_count = test_session.get('messages_count', 0)
            
            print(f"\n🔍 Testing with existing session:")
            print(f"   Session ID: {session_id}")
            print(f"   Title: {test_session.get('title', 'No title')}")
            print(f"   Messages count: {messages_count}")
            print(f"   Created: {test_session.get('created_at')}")
            
            # Try to get messages for this session
            print(f"\n💬 Getting messages for session {session_id}...")
            response = requests.get(f"{api_url}/chat/sessions/{session_id}/messages")
            
            if response.status_code == 200:
                messages = response.json()
                print(f"✅ Retrieved messages")
                print(f"   Messages type: {type(messages)}")
                print(f"   Messages content: {messages}")
                
                if isinstance(messages, list) and messages:
                    print(f"\n📨 Sample messages ({len(messages)} total):")
                    sample_messages = messages[:3] if len(messages) > 3 else messages
                    for i, msg in enumerate(sample_messages):  # Show first 3 messages
                        print(f"   Message {i+1}:")
                        print(f"     ID: {msg.get('id')}")
                        print(f"     Role: {msg.get('role')}")
                        print(f"     Content: {msg.get('content', '')[:100]}...")
                        print(f"     Timestamp: {msg.get('timestamp')}")
                        print(f"     ---")
                else:
                    print(f"⚠️  No messages found in session despite messages_count = {messages_count}")
                    
                    # Let's check the database directly
                    print(f"\n🔍 Investigating database issue...")
                    
                    # Try to create a new message in this session
                    print(f"📝 Sending a test message to session {session_id}...")
                    chat_data = {
                        "session_id": session_id,
                        "message": "Debug test message to check message storage",
                        "stream": False
                    }
                    
                    response = requests.post(f"{api_url}/chat/send", json=chat_data)
                    if response.status_code == 200:
                        print(f"✅ Test message sent successfully")
                        
                        # Wait a moment then try to retrieve messages again
                        time.sleep(2)
                        
                        print(f"🔍 Checking messages again...")
                        response = requests.get(f"{api_url}/chat/sessions/{session_id}/messages")
                        if response.status_code == 200:
                            messages = response.json()
                            print(f"✅ Now retrieved {len(messages)} messages")
                            
                            if isinstance(messages, list) and messages:
                                print(f"📨 Latest messages:")
                                latest_messages = messages[-2:] if len(messages) >= 2 else messages
                                for msg in latest_messages:  # Show last 2 messages
                                    print(f"   Role: {msg.get('role')}")
                                    print(f"   Content: {msg.get('content', '')[:100]}...")
                                    print(f"   ---")
                            else:
                                print(f"❌ Still no messages retrieved - there's a database issue")
                        else:
                            print(f"❌ Failed to retrieve messages: {response.status_code}")
                    else:
                        print(f"❌ Failed to send test message: {response.status_code}")
            else:
                print(f"❌ Failed to get messages: {response.status_code}")
                print(f"   Error: {response.text}")
        else:
            print(f"⚠️  No existing sessions found")
    else:
        print(f"❌ Failed to get sessions: {response.status_code}")

if __name__ == "__main__":
    debug_chat_messages()