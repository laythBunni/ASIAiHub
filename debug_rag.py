#!/usr/bin/env python3
"""
Debug RAG system chunks
"""

import asyncio
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from rag_system import get_rag_system

async def debug_rag_system():
    """Debug the RAG system"""
    
    mongo_url = "mongodb://localhost:27017"
    db_name = "asi_aihub_production"
    emergent_key = os.environ.get('EMERGENT_LLM_KEY')
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Check documents in database
        doc_count = await db.documents.count_documents({})
        print(f"Documents in MongoDB: {doc_count}")
        
        if doc_count > 0:
            sample_docs = await db.documents.find({}).limit(3).to_list(length=3)
            for doc in sample_docs:
                print(f"- {doc.get('original_name', 'Unknown')}")
        
        # Check RAG system
        rag = get_rag_system(emergent_key)
        stats = rag.get_collection_stats()
        print(f"RAG System Stats: {stats}")
        
        # Test search
        results = rag.search_similar_chunks("travel policy", n_results=3)
        print(f"Search results: {len(results)}")
        
        if len(results) == 0:
            print("NO CHUNKS FOUND - RAG SYSTEM IS EMPTY!")
        else:
            print("Chunks found:")
            for i, result in enumerate(results):
                print(f"  {i+1}. Score: {result.get('similarity_score', 'N/A')}")
        
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_rag_system())