#!/usr/bin/env python3

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

async def check_layth_detailed():
    """Check all Layth entries in detail"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔍 Detailed check of Layth's entries...")
    print("=" * 60)
    
    # Find ALL entries for Layth
    layth_entries = await db.beta_users.find({"email": "layth.bunni@adamsmithinternational.com"}).to_list(length=None)
    
    print(f"Found {len(layth_entries)} entries for Layth:")
    
    for i, entry in enumerate(layth_entries, 1):
        print(f"\n📋 Entry {i}:")
        print(f"   ID: {entry.get('id')}")
        print(f"   Email: {entry.get('email')}")
        print(f"   Role: {entry.get('role')}")
        print(f"   Personal Code: {entry.get('personal_code')}")
        print(f"   Created At: {entry.get('created_at')}")
        print(f"   Department: {entry.get('department')}")
        print(f"   Is Active: {entry.get('is_active')}")
        print(f"   Access Token: {entry.get('access_token', 'None')[:20] if entry.get('access_token') else 'None'}...")
    
    # Check which one is being returned by the query in the endpoint
    print(f"\n🔍 Testing endpoint query (find_one)...")
    endpoint_result = await db.beta_users.find_one({"email": "layth.bunni@adamsmithinternational.com"})
    if endpoint_result:
        print(f"Endpoint returns entry with:")
        print(f"   ID: {endpoint_result.get('id')}")
        print(f"   Personal Code: {endpoint_result.get('personal_code')}")
        print(f"   Created At: {endpoint_result.get('created_at')}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_layth_detailed())