#!/usr/bin/env python3
"""
Fix admin role for layth.bunni@adamsmithinternational.com
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def fix_admin_role():
    """Fix admin role"""
    
    mongo_url = "mongodb://localhost:27017"
    db_name = "asi_aihub_production"
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Fix in simple_users collection
        result1 = await db.simple_users.update_one(
            {"email": "layth.bunni@adamsmithinternational.com"},
            {"$set": {"role": "Admin", "is_active": True}}
        )
        
        # Fix in beta_users collection  
        result2 = await db.beta_users.update_one(
            {"email": "layth.bunni@adamsmithinternational.com"},
            {"$set": {"role": "Admin", "boost_role": "Admin", "is_active": True}}
        )
        
        print(f"Updated simple_users: {result1.modified_count} records")
        print(f"Updated beta_users: {result2.modified_count} records")
        
        # Verify the fix
        admin_user = await db.simple_users.find_one({"email": "layth.bunni@adamsmithinternational.com"})
        if not admin_user:
            admin_user = await db.beta_users.find_one({"email": "layth.bunni@adamsmithinternational.com"})
        
        if admin_user:
            print(f"FIXED: {admin_user['name']} role is now: {admin_user['role']}")
        else:
            print("User not found!")
        
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_admin_role())