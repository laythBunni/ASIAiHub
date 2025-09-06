#!/usr/bin/env python3
"""
Test single document processing
"""

import asyncio
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from rag_system import get_rag_system

async def test_single_document():
    """Test processing a single document"""
    
    mongo_url = "mongodb://localhost:27017"
    db_name = "asi_aihub_production"
    emergent_key = os.environ.get('EMERGENT_LLM_KEY')
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Get one document
        document = await db.documents.find_one({})
        if not document:
            print("No documents found!")
            return
            
        print(f"Testing document: {document.get('original_name')}")
        print(f"File path: {document.get('file_path')}")
        print(f"MIME type: {document.get('mime_type')}")
        
        # Process with RAG
        rag = get_rag_system(emergent_key)
        
        print("Processing document...")
        success = rag.process_and_store_document(document)
        print(f"Processing result: {success}")
        
        # Check stats
        stats = rag.get_collection_stats()
        print(f"RAG Stats after processing: {stats}")
        
        # Test search
        results = rag.search_similar_chunks("policy", n_results=2)
        print(f"Search results: {len(results)}")
        
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_single_document())