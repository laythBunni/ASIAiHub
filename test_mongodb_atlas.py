#!/usr/bin/env python3
"""
Test MongoDB Atlas connection using the exact pattern MongoDB recommends
Python equivalent of the MongoDB JavaScript example
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

async def test_mongodb_atlas():
    """Test Atlas connection using MongoDB's recommended pattern"""
    
    # MongoDB Atlas connection string with credentials
    uri = "mongodb+srv://laythbunni_db_user:mDxnDebnOwfp8l1B@asi-aihub-production.qhg0eyt.mongodb.net/?retryWrites=true&w=majority&appName=ASI-AiHub-Production"
    
    # Create a MongoClient with ServerApi to set the Stable API version
    client = AsyncIOMotorClient(
        uri,
        server_api=ServerApi('1', strict=True, deprecation_errors=True)
    )
    
    try:
        print("🔌 Connecting to MongoDB Atlas...")
        
        # Connect the client to the server (optional starting in v4.7)
        # Motor connects automatically on first operation, but we can test with ping
        
        # Send a ping to confirm a successful connection
        await client.admin.command({'ping': 1})
        print("✅ Pinged your deployment. You successfully connected to MongoDB!")
        
        # Test database access
        db = client['asi_aihub_production']
        collections = await db.list_collection_names()
        print(f"📊 Available collections: {len(collections)}")
        if collections:
            print(f"📋 Sample collections: {collections[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False
        
    finally:
        # Ensures that the client will close when you finish/error
        client.close()
        print("🔌 Connection closed")

if __name__ == "__main__":
    print("🚀 Testing MongoDB Atlas Connection")
    success = asyncio.run(test_mongodb_atlas())
    if success:
        print("🎉 Atlas connection successful!")
    else:
        print("❌ Atlas connection failed")