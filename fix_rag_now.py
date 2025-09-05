#!/usr/bin/env python3
"""
Fix RAG system - reprocess all documents
"""

import asyncio
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from rag_system import get_rag_system

async def fix_rag_system():
    """Fix RAG system by reprocessing all documents"""
    
    mongo_url = "mongodb://localhost:27017"
    db_name = "asi_aihub_production"
    emergent_key = os.environ.get('EMERGENT_LLM_KEY')
    
    print(f"🔧 Fixing RAG system...")
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Get all documents
        documents = await db.documents.find({}).to_list(length=None)
        print(f"📚 Found {len(documents)} documents to process")
        
        # Initialize RAG system
        rag = get_rag_system(emergent_key)
        
        processed = 0
        failed = 0
        
        for doc in documents:
            try:
                print(f"🔄 Processing: {doc.get('original_name', 'Unknown')}")
                success = rag.process_and_store_document(doc)
                if success:
                    processed += 1
                    print(f"✅ Processed: {doc.get('original_name')}")
                else:
                    failed += 1
                    print(f"❌ Failed: {doc.get('original_name')}")
            except Exception as e:
                failed += 1
                print(f"❌ Error processing {doc.get('original_name', 'Unknown')}: {e}")
        
        # Final stats
        stats = rag.get_collection_stats()
        print(f"\n🎉 RAG PROCESSING COMPLETE!")
        print(f"✅ Processed: {processed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Final stats: {stats}")
        
        client.close()
        
        return processed > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(fix_rag_system())
    if success:
        print("✅ RAG system fixed!")
    else:
        print("❌ RAG system fix failed")