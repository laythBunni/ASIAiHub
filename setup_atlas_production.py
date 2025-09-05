#!/usr/bin/env python3
"""
Setup Atlas production database with essential data
This will be run during deployment to populate Atlas with initial data
"""

import asyncio
import os
import json
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent / 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def setup_atlas_production():
    """Setup Atlas database with essential production data"""
    
    # Atlas connection with deployment-ready configuration
    atlas_url = "mongodb+srv://laythbunni_db_user:mDxnDebnOwfp8l1B@asi-aihub-production.qhg0eyt.mongodb.net/?retryWrites=true&w=majority&appName=ASI-AiHub-Production"
    db_name = "asi_aihub_production"
    
    print(f"🚀 Setting up Atlas production database: {db_name}")
    
    try:
        # Connect with deployment-compatible settings
        client = AsyncIOMotorClient(
            atlas_url,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            maxPoolSize=10,
            retryWrites=True
        )
        
        db = client[db_name]
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Atlas connection successful")
        
        # Setup essential data
        print("🔧 Setting up essential collections...")
        
        # 1. Create admin user
        admin_user = {
            "id": "admin-user-001",
            "email": "layth.bunni@adamsmithinternational.com",
            "name": "Layth Bunni",
            "personal_code": "***",
            "role": "Admin",
            "department": "Management", 
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "last_login": datetime.now(timezone.utc),
            "access_token": None
        }
        
        # Check if admin user exists
        existing_admin = await db.simple_users.find_one({"email": "layth.bunni@adamsmithinternational.com"})
        if not existing_admin:
            await db.simple_users.insert_one(admin_user)
            print("✅ Admin user created")
        else:
            print("✅ Admin user already exists")
        
        # 2. Setup beta settings
        beta_settings = {
            "registration_code": "ASI2025",
            "max_users": 100,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }
        
        existing_settings = await db.beta_settings.find_one({})
        if not existing_settings:
            await db.beta_settings.insert_one(beta_settings)
            print("✅ Beta settings created")
        else:
            print("✅ Beta settings already exist")
        
        # 3. Verify database setup
        collections = await db.list_collection_names()
        print(f"📊 Database collections: {len(collections)}")
        
        # Count documents
        users_count = await db.simple_users.count_documents({})
        settings_count = await db.beta_settings.count_documents({})
        
        print(f"👥 Users: {users_count}")
        print(f"⚙️ Settings: {settings_count}")
        
        client.close()
        print(f"🎉 Atlas production database ready!")
        
        return True
        
    except Exception as e:
        print(f"❌ Atlas setup error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Atlas Production Database Setup")
    success = asyncio.run(setup_atlas_production())
    if success:
        print("✅ Atlas setup completed successfully")
    else:
        print("❌ Atlas setup failed")
        sys.exit(1)