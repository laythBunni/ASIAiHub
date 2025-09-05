#!/usr/bin/env python3
"""
Set up production database with documents
"""

import asyncio
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from rag_system import get_rag_system

async def setup_production_database():
    """Set up production database with sample documents"""
    
    # Connect to production database
    mongo_url = "mongodb://localhost:27017"
    db_name = "asi_aihub_production"
    emergent_key = os.environ.get('EMERGENT_LLM_KEY')
    
    print(f"🔧 Setting up production database: {db_name}")
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Production database connection successful")
        
        # Check if documents already exist
        doc_count = await db.documents.count_documents({})
        print(f"📊 Current documents in production: {doc_count}")
        
        if doc_count == 0:
            print("📚 No documents found. Need to upload documents to production database.")
            print("🔄 For now, setting up empty RAG system...")
            
            # Initialize RAG system (this will create the ChromaDB collection)
            rag_system = get_rag_system(emergent_key)
            stats = rag_system.get_collection_stats()
            print(f"📊 RAG System initialized: {stats}")
            
        else:
            print(f"📚 Found {doc_count} documents, processing through RAG system...")
            
            # Get all documents and process them
            documents = await db.documents.find({}).to_list(length=None)
            
            # Initialize RAG system
            rag_system = get_rag_system(emergent_key)
            
            processed_count = 0
            for doc in documents:
                try:
                    success = rag_system.process_and_store_document(doc)
                    if success:
                        processed_count += 1
                        print(f"✅ Processed: {doc.get('original_name')}")
                    else:
                        print(f"❌ Failed: {doc.get('original_name')}")
                except Exception as e:
                    print(f"❌ Error processing {doc.get('original_name')}: {e}")
            
            # Final stats
            final_stats = rag_system.get_collection_stats()
            print(f"\n🎉 PRODUCTION SETUP COMPLETE!")
            print(f"✅ Processed: {processed_count}/{len(documents)} documents")
            print(f"📊 RAG System stats: {final_stats}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error setting up production database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Setting up ASI AiHub production database...")
    asyncio.run(setup_production_database())