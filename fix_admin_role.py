#!/usr/bin/env python3
"""
Force set layth.bunni@adamsmithinternational.com to Admin role
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def fix_admin_role():
    """Force set admin role for layth.bunni"""
    
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
        
        # Force update layth.bunni to Admin
        result = await db.beta_users.update_one(
            {'email': 'layth.bunni@adamsmithinternational.com'},
            {
                '$set': {
                    'role': 'Admin',
                    'name': 'Layth Bunni',
                    'is_active': True,
                    'updated_at': datetime.now(timezone.utc)
                }
            }
        )
        
        if result.matched_count > 0:
            print('✅ SUCCESS: Updated Layth Bunni to Admin role')
            print(f'   Modified count: {result.modified_count}')
        else:
            print('❌ ERROR: User not found in database')
        
        # Verify the update
        user = await db.beta_users.find_one({'email': 'layth.bunni@adamsmithinternational.com'})
        if user:
            print(f'✅ VERIFIED: Role is now: {user.get("role")}')
            print(f'   Name: {user.get("name")}')
            print(f'   Active: {user.get("is_active")}')
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🔧 Forcing Admin role for layth.bunni@adamsmithinternational.com...")
    asyncio.run(fix_admin_role())