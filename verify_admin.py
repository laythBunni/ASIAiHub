#!/usr/bin/env python3
"""
Verify admin user exists in Atlas database
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

async def verify_admin_user():
    """Verify Layth's admin account exists in Atlas"""
    
    atlas_uri = "mongodb+srv://laythbunni_db_user:mDxnDebnOwfp8l1B@asi-aihub-production.qhg0eyt.mongodb.net/?retryWrites=true&w=majority&appName=ASI-AiHub-Production"
    client = AsyncIOMotorClient(
        atlas_uri,
        server_api=ServerApi('1', strict=True, deprecation_errors=True)
    )
    
    try:
        db = client['asi_aihub_production']
        
        # Check in simple_users
        simple_admin = await db.simple_users.find_one({"email": "layth.bunni@adamsmithinternational.com"})
        if simple_admin:
            print("✅ FOUND in simple_users:")
            print(f"   ID: {simple_admin['id']}")
            print(f"   Name: {simple_admin['name']}")
            print(f"   Role: {simple_admin['role']}")
            print(f"   Department: {simple_admin['department']}")
            print(f"   Active: {simple_admin['is_active']}")
        
        # Check in beta_users
        beta_admin = await db.beta_users.find_one({"email": "layth.bunni@adamsmithinternational.com"})
        if beta_admin:
            print("✅ FOUND in beta_users:")
            print(f"   ID: {beta_admin['id']}")
            print(f"   Name: {beta_admin['name']}")
            print(f"   Role: {beta_admin['role']}")
            print(f"   Department: {beta_admin['department']}")
            print(f"   Active: {beta_admin['is_active']}")
        
        if not simple_admin and not beta_admin:
            print("❌ ADMIN USER NOT FOUND in Atlas database!")
            return False
        
        print("\n🎉 ADMIN USER VERIFIED IN ATLAS DATABASE!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(verify_admin_user())