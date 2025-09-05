#!/usr/bin/env python3
"""
Simple Atlas connection test
"""

import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import ssl

async def test_atlas_simple(connection_string):
    """Test Atlas with different SSL configurations"""
    
    print("🔌 Testing Atlas connection with different SSL methods...")
    
    # Method 1: Standard connection
    try:
        print("📡 Method 1: Standard connection...")
        client = AsyncIOMotorClient(connection_string)
        await asyncio.wait_for(client.admin.command('ping'), timeout=10)
        print("✅ Method 1: SUCCESS!")
        client.close()
        return True
    except Exception as e:
        print(f"❌ Method 1 failed: {str(e)[:100]}...")
    
    # Method 2: Disable SSL verification
    try:
        print("📡 Method 2: SSL verification disabled...")
        client = AsyncIOMotorClient(connection_string, tlsAllowInvalidCertificates=True)
        await asyncio.wait_for(client.admin.command('ping'), timeout=10)
        print("✅ Method 2: SUCCESS!")
        client.close()
        return True
    except Exception as e:
        print(f"❌ Method 2 failed: {str(e)[:100]}...")
    
    # Method 3: Custom SSL context
    try:
        print("📡 Method 3: Custom SSL context...")
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        client = AsyncIOMotorClient(connection_string, ssl_context=ssl_context)
        await asyncio.wait_for(client.admin.command('ping'), timeout=10)
        print("✅ Method 3: SUCCESS!")
        client.close()
        return True
    except Exception as e:
        print(f"❌ Method 3 failed: {str(e)[:100]}...")
    
    # Method 4: No SSL
    try:
        print("📡 Method 4: SSL disabled...")
        no_ssl_url = connection_string.replace('mongodb+srv://', 'mongodb://')
        if '?' in no_ssl_url:
            no_ssl_url = no_ssl_url.split('?')[0]
        client = AsyncIOMotorClient(no_ssl_url, ssl=False)
        await asyncio.wait_for(client.admin.command('ping'), timeout=10)
        print("✅ Method 4: SUCCESS!")
        client.close()
        return True
    except Exception as e:
        print(f"❌ Method 4 failed: {str(e)[:100]}...")
    
    print("❌ All methods failed - Atlas connection issue")
    return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_atlas_simple.py 'connection_string'")
        sys.exit(1)
    
    connection_string = sys.argv[1]
    success = asyncio.run(test_atlas_simple(connection_string))
    
    if success:
        print("\n✅ Atlas connection working!")
    else:
        print("\n❌ Could not connect to Atlas")