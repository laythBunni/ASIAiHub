#!/usr/bin/env python3
"""
Migrate production database from local MongoDB to MongoDB Atlas
"""

import asyncio
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient

async def migrate_to_atlas(atlas_connection_string):
    """Migrate from local MongoDB to Atlas"""
    
    # Local MongoDB
    local_url = "mongodb://localhost:27017"
    local_db_name = "asi_aihub_production"
    
    # Atlas MongoDB  
    atlas_url = atlas_connection_string
    atlas_db_name = "asi_aihub_production"
    
    print(f"🚀 MIGRATING TO MONGODB ATLAS")
    print(f"📤 From: {local_url}/{local_db_name}")
    print(f"📥 To: Atlas/{atlas_db_name}")
    
    try:
        # Connect to both databases
        local_client = AsyncIOMotorClient(local_url)
        atlas_client = AsyncIOMotorClient(atlas_url, tlsAllowInvalidCertificates=True)
        
        local_db = local_client[local_db_name]
        atlas_db = atlas_client[atlas_db_name]
        
        # Test connections
        await local_client.admin.command('ping')
        await atlas_client.admin.command('ping')
        print("✅ Both database connections successful")
        
        # Get all collections from local database
        collections = await local_db.list_collection_names()
        print(f"📊 Found {len(collections)} collections to migrate")
        
        migration_stats = {}
        total_docs = 0
        
        # Migrate each collection
        for collection_name in collections:
            print(f"\n🔄 Migrating collection: {collection_name}")
            
            # Get documents from local
            local_collection = local_db[collection_name]
            documents = await local_collection.find({}).to_list(length=None)
            
            if documents:
                # Insert into Atlas
                atlas_collection = atlas_db[collection_name]
                
                # Check if collection already exists in Atlas
                existing_count = await atlas_collection.count_documents({})
                if existing_count > 0:
                    print(f"⚠️ Atlas collection {collection_name} has {existing_count} documents")
                    print(f"🔄 Clearing existing data...")
                    await atlas_collection.delete_many({})
                
                # Insert all documents
                await atlas_collection.insert_many(documents)
                
                migration_stats[collection_name] = len(documents)
                total_docs += len(documents)
                print(f"✅ Migrated {len(documents)} documents to {collection_name}")
            else:
                migration_stats[collection_name] = 0
                print(f"ℹ️ No documents in {collection_name}")
        
        # Migration summary
        print(f"\n🎉 ATLAS MIGRATION COMPLETE!")
        print(f"📊 MIGRATION SUMMARY:")
        for collection, count in migration_stats.items():
            print(f"  📋 {collection}: {count} documents")
        print(f"  📈 Total: {total_docs} documents migrated")
        
        # Verify critical collections
        print(f"\n🔍 VERIFICATION:")
        users_count = await atlas_db.users.count_documents({}) + await atlas_db.simple_users.count_documents({}) + await atlas_db.beta_users.count_documents({})
        docs_count = await atlas_db.documents.count_documents({})
        tickets_count = await atlas_db.boost_tickets.count_documents({})
        chats_count = await atlas_db.chat_sessions.count_documents({})
        
        print(f"👥 Total Users: {users_count}")
        print(f"📄 Documents: {docs_count}")
        print(f"🎫 Tickets: {tickets_count}")
        print(f"💬 Chat Sessions: {chats_count}")
        
        # Check admin user
        admin_user = await atlas_db.simple_users.find_one({"email": "layth.bunni@adamsmithinternational.com"})
        if not admin_user:
            admin_user = await atlas_db.beta_users.find_one({"email": "layth.bunni@adamsmithinternational.com"})
        
        if admin_user:
            print(f"✅ Admin user found: {admin_user.get('name', 'Unknown')} ({admin_user.get('role', 'Unknown role')})")
        else:
            print(f"⚠️ Admin user not found - may need to check user collections")
        
        # Close connections
        local_client.close()
        atlas_client.close()
        
        print(f"\n🎉 SUCCESS! Production database is now on MongoDB Atlas")
        print(f"🔗 Atlas Connection String: {atlas_url[:50]}...")
        
    except Exception as e:
        print(f"❌ Migration error: {str(e)}")
        return False
    
    return True

async def test_atlas_connection(atlas_connection_string):
    """Test Atlas connection"""
    try:
        client = AsyncIOMotorClient(atlas_connection_string, tlsAllowInvalidCertificates=True)
        await client.admin.command('ping')
        print("✅ Atlas connection test successful")
        client.close()
        return True
    except Exception as e:
        print(f"❌ Atlas connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 MongoDB Atlas Migration Tool")
    
    if len(sys.argv) != 2:
        print("Usage: python migrate_to_atlas.py 'mongodb+srv://username:password@cluster.mongodb.net/'")
        sys.exit(1)
    
    atlas_url = sys.argv[1]
    
    print(f"Testing Atlas connection...")
    if asyncio.run(test_atlas_connection(atlas_url)):
        print(f"Starting migration...")
        success = asyncio.run(migrate_to_atlas(atlas_url))
        if success:
            print(f"\n✅ READY FOR PRODUCTION DEPLOYMENT!")
        else:
            print(f"\n❌ Migration failed")
    else:
        print(f"❌ Cannot connect to Atlas. Please check your connection string.")