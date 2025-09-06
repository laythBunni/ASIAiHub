#!/usr/bin/env python3
"""
Post-deployment setup script to populate production database
This runs AFTER deployment succeeds to set up essential data
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

async def setup_production_data():
    """Set up essential production data after deployment"""
    
    # Connect to local MongoDB (which will be available after deployment)
    mongo_url = "mongodb://localhost:27017"
    db_name = "asi_aihub_production"
    
    print(f"🚀 Setting up production data...")
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Production database connection successful")
        
        # Create admin user (your account)
        admin_user = {
            "id": str(uuid.uuid4()),
            "email": "layth.bunni@adamsmithinternational.com",
            "name": "Layth Bunni",
            "personal_code": "***",
            "role": "Admin",
            "department": "Management",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "last_login": None,
            "access_token": None
        }
        
        # Check if admin user exists
        existing_admin = await db.simple_users.find_one({"email": "layth.bunni@adamsmithinternational.com"})
        if not existing_admin:
            await db.simple_users.insert_one(admin_user)
            print("✅ Admin user created")
        else:
            # Update to ensure Admin role
            await db.simple_users.update_one(
                {"email": "layth.bunni@adamsmithinternational.com"},
                {"$set": {"role": "Admin", "is_active": True}}
            )
            print("✅ Admin user verified/updated")
        
        # Create beta settings
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
        
        # Verify setup
        admin_count = await db.simple_users.count_documents({"role": "Admin"})
        total_users = await db.simple_users.count_documents({})
        
        print(f"\n🎉 PRODUCTION SETUP COMPLETE!")
        print(f"✅ Admin users: {admin_count}")
        print(f"✅ Total users: {total_users}")
        print(f"✅ Login ready: layth.bunni@adamsmithinternational.com + ASI2025")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Setup error: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_production_data())
    if success:
        print("✅ Production ready!")
    else:
        print("❌ Setup failed")