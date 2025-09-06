#!/usr/bin/env python3
"""
Force reprocess all documents
"""

import asyncio
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from rag_system import get_rag_system

async def force_reprocess_all():
    """Force reprocess all documents"""
    
    mongo_url = "mongodb://localhost:27017"
    db_name = "asi_aihub_production"
    emergent_key = os.environ.get('EMERGENT_LLM_KEY')
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        documents = await db.documents.find({}).to_list(length=None)
        print(f"Processing {len(documents)} documents...")
        
        rag = get_rag_system(emergent_key)
        
        processed = 0
        for doc in documents:
            try:
                success = rag.process_and_store_document(doc)
                if success:
                    processed += 1
                    print(f"✅ {doc.get('original_name')}")
                else:
                    print(f"❌ {doc.get('original_name')}")
            except Exception as e:
                print(f"❌ {doc.get('original_name')}: {e}")
        
        stats = rag.get_collection_stats()
        print(f"\nFinal Stats: {stats}")
        print(f"✅ Processed: {processed}/{len(documents)}")
        
        # Test search
        results = rag.search_similar_chunks("travel policy", n_results=2)
        print(f"🔍 Search test: {len(results)} results")
        
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(force_reprocess_all())