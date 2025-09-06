#!/usr/bin/env python3
"""
Process all documents directly
"""

import asyncio
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from rag_system import get_rag_system

async def process_all_documents():
    """Process all documents directly"""
    
    mongo_url = "mongodb://localhost:27017"
    db_name = "asi_aihub_production"
    emergent_key = os.environ.get('EMERGENT_LLM_KEY')
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Get all documents
        documents = await db.documents.find({}).to_list(length=None)
        print(f"Processing {len(documents)} documents...")
        
        # Initialize RAG
        rag = get_rag_system(emergent_key)
        
        processed = 0
        failed = 0
        
        for doc in documents:
            try:
                print(f"Processing: {doc.get('original_name')}")
                success = rag.process_and_store_document(doc)
                if success:
                    processed += 1
                    print(f"  ✅ Success")
                else:
                    failed += 1
                    print(f"  ❌ Failed")
            except Exception as e:
                failed += 1
                print(f"  ❌ Error: {e}")
        
        # Final stats
        stats = rag.get_collection_stats()
        print(f"\n🎉 PROCESSING COMPLETE!")
        print(f"✅ Processed: {processed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Final stats: {stats}")
        
        # Test search
        results = rag.search_similar_chunks("travel policy", n_results=3)
        print(f"🔍 Search test: {len(results)} results found")
        
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(process_all_documents())