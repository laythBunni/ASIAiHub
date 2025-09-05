#!/usr/bin/env python3
"""
Initialize production database for ASI AiHub authentication system
Run this once after deployment to set up required collections
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def init_database():
    """Initialize production database with required authentication settings"""
    
    # Get MongoDB connection from environment
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    print(f"Connecting to MongoDB: {mongo_url}")
    print(f"Database: {db_name}")
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Initialize beta_settings collection
        beta_settings = {
            "registration_code": "BETA2025",
            "allowed_domain": "adamsmithinternational.com", 
            "max_users": 20,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Check if settings already exist
        existing_settings = await db.beta_settings.find_one()
        if existing_settings:
            print("⚠️  Beta settings already exist")
        else:
            await db.beta_settings.insert_one(beta_settings)
            print("✅ Beta settings initialized")
            print(f"   - Registration Code: BETA2025")
            print(f"   - Allowed Domain: @adamsmithinternational.com")
            print(f"   - Max Users: 20")
        
        # Check collections
        collections = await db.list_collection_names()
        print(f"📊 Available collections: {collections}")
        
        # Check existing users
        user_count = await db.beta_users.count_documents({})
        print(f"👥 Existing users: {user_count}")
        
        print("\n🎉 Database initialization complete!")
        print("✅ Registration should now work at https://asiaihub.com")
        print("✅ Use registration code: BETA2025")
        print("✅ Email domain: @adamsmithinternational.com")
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    print("🚀 Initializing ASI AiHub production database...")
    asyncio.run(init_database())