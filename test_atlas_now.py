#!/usr/bin/env python3
"""
Test Atlas connection with updated drivers
"""

import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient

async def test_atlas_connection():
    """Test Atlas connection with new drivers"""
    atlas_url = "mongodb+srv://laythbunni_db_user:mDxnDebnOwfp8l1B@asi-aihub-production.qhg0eyt.mongodb.net/?retryWrites=true&w=majority&appName=ASI-AiHub-Production"
    
    print("🔌 Testing Atlas connection with updated drivers...")
    
    try:
        # Test with updated motor/pymongo
        print("📡 Connecting to Atlas...")
        client = AsyncIOMotorClient(atlas_url, serverSelectionTimeoutMS=5000)
        
        # Test connection
        print("🔍 Testing ping...")
        await client.admin.command('ping')
        print("✅ Atlas connection successful!")
        
        # Test database access
        db = client['asi_aihub_production']
        collections = await db.list_collection_names()
        print(f"📊 Found {len(collections)} collections in Atlas database")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Atlas connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_atlas_connection())
    if success:
        print("\n🎉 Atlas is ready to use!")
    else:
        print("\n❌ Atlas connection still not working")