#!/usr/bin/env python3

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

async def check_layth_credentials():
    """Check Layth's credentials in the database"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔍 Checking Layth's credentials in database...")
    print("=" * 60)
    
    # Check simple_users collection
    print("\n📋 Checking simple_users collection...")
    simple_user = await db.simple_users.find_one({"email": "layth.bunni@adamsmithinternational.com"})
    if simple_user:
        print("✅ Found in simple_users:")
        print(f"   ID: {simple_user.get('id')}")
        print(f"   Email: {simple_user.get('email')}")
        print(f"   Role: {simple_user.get('role')}")
        print(f"   Personal Code: {simple_user.get('personal_code')}")
        print(f"   Created At: {simple_user.get('created_at')}")
    else:
        print("❌ Not found in simple_users")
    
    # Check beta_users collection
    print("\n📋 Checking beta_users collection...")
    beta_user = await db.beta_users.find_one({"email": "layth.bunni@adamsmithinternational.com"})
    if beta_user:
        print("✅ Found in beta_users:")
        print(f"   ID: {beta_user.get('id')}")
        print(f"   Email: {beta_user.get('email')}")
        print(f"   Role: {beta_user.get('role')}")
        print(f"   Personal Code: {beta_user.get('personal_code')}")
        print(f"   Created At: {beta_user.get('created_at')}")
    else:
        print("❌ Not found in beta_users")
    
    # Check if there are any users with personal codes
    print("\n📋 Checking all users with personal codes...")
    
    # Check simple_users
    simple_users_with_codes = await db.simple_users.find({"personal_code": {"$exists": True}}).to_list(length=10)
    print(f"Simple users with personal codes: {len(simple_users_with_codes)}")
    for user in simple_users_with_codes:
        print(f"   {user.get('email')}: {user.get('personal_code')}")
    
    # Check beta_users
    beta_users_with_codes = await db.beta_users.find({"personal_code": {"$exists": True}}).to_list(length=10)
    print(f"Beta users with personal codes: {len(beta_users_with_codes)}")
    for user in beta_users_with_codes:
        print(f"   {user.get('email')}: {user.get('personal_code')}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_layth_credentials())