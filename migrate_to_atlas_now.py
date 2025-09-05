#!/usr/bin/env python3
"""
Migrate all data from local MongoDB to Atlas
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

async def migrate_to_atlas():
    """Migrate all local data to Atlas"""
    
    # Local MongoDB
    local_client = AsyncIOMotorClient("mongodb://localhost:27017")
    local_db = local_client['asi_aihub_production']
    
    # Atlas MongoDB with ServerApi
    atlas_uri = "mongodb+srv://laythbunni_db_user:mDxnDebnOwfp8l1B@asi-aihub-production.qhg0eyt.mongodb.net/?retryWrites=true&w=majority&appName=ASI-AiHub-Production"
    atlas_client = AsyncIOMotorClient(
        atlas_uri,
        server_api=ServerApi('1', strict=True, deprecation_errors=True)
    )
    atlas_db = atlas_client['asi_aihub_production']
    
    print("🚀 Starting migration from local to Atlas...")
    
    try:
        # Test connections
        await local_client.admin.command({'ping': 1})
        await atlas_client.admin.command({'ping': 1})
        print("✅ Both connections successful")
        
        # Get collections from local
        local_collections = await local_db.list_collection_names()
        print(f"📊 Found {len(local_collections)} collections to migrate")
        
        total_docs = 0
        
        for collection_name in local_collections:
            print(f"\n🔄 Migrating collection: {collection_name}")
            
            local_collection = local_db[collection_name]
            atlas_collection = atlas_db[collection_name]
            
            # Get all documents
            documents = await local_collection.find({}).to_list(length=None)
            
            if documents:
                # Clear existing data in Atlas
                existing_count = await atlas_collection.count_documents({})
                if existing_count > 0:
                    await atlas_collection.delete_many({})
                    print(f"🧹 Cleared {existing_count} existing documents")
                
                # Insert all documents
                await atlas_collection.insert_many(documents)
                total_docs += len(documents)
                print(f"✅ Migrated {len(documents)} documents")
            else:
                print(f"ℹ️ No documents in {collection_name}")
        
        print(f"\n🎉 MIGRATION COMPLETE!")
        print(f"📊 Total documents migrated: {total_docs}")
        
        # Verify key data
        users = await atlas_db.simple_users.count_documents({})
        docs = await atlas_db.documents.count_documents({})
        tickets = await atlas_db.boost_tickets.count_documents({})
        chats = await atlas_db.chat_sessions.count_documents({})
        
        print(f"\n🔍 VERIFICATION:")
        print(f"👥 Users: {users}")
        print(f"📄 Documents: {docs}")
        print(f"🎫 Tickets: {tickets}")
        print(f"💬 Chats: {chats}")
        
        # Check admin user
        admin = await atlas_db.simple_users.find_one({"email": "layth.bunni@adamsmithinternational.com"})
        if admin:
            print(f"✅ Admin user: {admin['name']} ({admin['role']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {str(e)}")
        return False
        
    finally:
        local_client.close()
        atlas_client.close()

if __name__ == "__main__":
    success = asyncio.run(migrate_to_atlas())
    if success:
        print("\n🎉 All data successfully migrated to Atlas!")
    else:
        print("\n❌ Migration failed")