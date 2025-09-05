#!/usr/bin/env python3
"""
Migrate all data from test_database to asi_aihub_production
This includes: users, documents, conversations, tickets, chunks, etc.
"""

import asyncio
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from rag_system import get_rag_system
import json

async def migrate_to_production():
    """Migrate all data from test database to production database"""
    
    # Database connections
    mongo_url = "mongodb://localhost:27017"
    test_db_name = "test_database"
    prod_db_name = "asi_aihub_production"
    emergent_key = os.environ.get('EMERGENT_LLM_KEY')
    
    print(f"🚀 MIGRATING DATA: {test_db_name} → {prod_db_name}")
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        test_db = client[test_db_name]
        prod_db = client[prod_db_name]
        
        # Test connections
        await client.admin.command('ping')
        print("✅ Database connections successful")
        
        # Get all collections from test database
        test_collections = await test_db.list_collection_names()
        print(f"📊 Found collections in test database: {test_collections}")
        
        migration_stats = {}
        
        # Migrate each collection
        for collection_name in test_collections:
            print(f"\n🔄 Migrating collection: {collection_name}")
            
            # Get all documents from test collection
            test_collection = test_db[collection_name]
            documents = await test_collection.find({}).to_list(length=None)
            
            if documents:
                # Insert into production collection
                prod_collection = prod_db[collection_name]
                await prod_collection.insert_many(documents)
                
                migration_stats[collection_name] = len(documents)
                print(f"✅ Migrated {len(documents)} documents from {collection_name}")
            else:
                migration_stats[collection_name] = 0
                print(f"ℹ️ No documents found in {collection_name}")
        
        # Print migration summary
        print(f"\n🎉 MIGRATION SUMMARY:")
        total_documents = 0
        for collection, count in migration_stats.items():
            print(f"  📋 {collection}: {count} documents")
            total_documents += count
        print(f"  📊 Total documents migrated: {total_documents}")
        
        # Now rebuild RAG system with migrated documents
        print(f"\n🔄 REBUILDING RAG SYSTEM...")
        
        # Get documents from production database
        documents = await prod_db.documents.find({}).to_list(length=None)
        print(f"📚 Found {len(documents)} documents to process")
        
        if documents:
            # Initialize RAG system
            rag_system = get_rag_system(emergent_key)
            
            processed_count = 0
            failed_count = 0
            
            for doc in documents:
                try:
                    print(f"🔄 Processing: {doc.get('original_name', 'Unknown')}")
                    success = rag_system.process_and_store_document(doc)
                    
                    if success:
                        processed_count += 1
                        print(f"✅ Processed: {doc.get('original_name')}")
                    else:
                        failed_count += 1
                        print(f"❌ Failed: {doc.get('original_name')}")
                        
                except Exception as e:
                    failed_count += 1
                    print(f"❌ Error processing {doc.get('original_name', 'Unknown')}: {e}")
            
            # Final RAG stats
            try:
                final_stats = rag_system.get_collection_stats()
                print(f"\n🎉 RAG SYSTEM REBUILD COMPLETE!")
                print(f"✅ Successfully processed: {processed_count} documents")
                print(f"❌ Failed: {failed_count} documents")
                print(f"📊 RAG System stats: {final_stats}")
            except Exception as e:
                print(f"📊 Final stats not available: {e}")
        
        # Verify key data
        print(f"\n🔍 VERIFICATION:")
        
        # Check users
        user_count = await prod_db.users.count_documents({})
        admin_user = await prod_db.users.find_one({"email": "layth.bunni@adamsmithinternational.com"})
        print(f"👥 Users: {user_count} total")
        if admin_user:
            print(f"✅ Admin user found: {admin_user['name']} ({admin_user['role']})")
        
        # Check documents
        doc_count = await prod_db.documents.count_documents({})
        print(f"📄 Documents: {doc_count} total")
        
        # Check conversations
        chat_count = await prod_db.chat_sessions.count_documents({})
        print(f"💬 Chat sessions: {chat_count} total")
        
        # Check tickets
        ticket_count = await prod_db.boost_tickets.count_documents({})
        print(f"🎫 BOOST tickets: {ticket_count} total")
        
        client.close()
        print(f"\n🎉 MIGRATION COMPLETE! Production database ready with all your data.")
        
    except Exception as e:
        print(f"❌ Migration error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting data migration to production database...")
    asyncio.run(migrate_to_production())