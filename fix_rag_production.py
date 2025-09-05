#!/usr/bin/env python3
"""
Fix RAG system for production database
"""

import asyncio
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from rag_system import get_rag_system

async def fix_production_rag():
    """Fix RAG system for production"""
    
    mongo_url = "mongodb://localhost:27017"
    db_name = "asi_aihub_production"
    emergent_key = os.environ.get('EMERGENT_LLM_KEY')
    
    print(f"🔧 Fixing RAG system for production database")
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Get documents
        documents = await db.documents.find({}).to_list(length=None)
        print(f"📚 Found {len(documents)} documents in production database")
        
        if not documents:
            print("❌ No documents found in production database!")
            return
        
        # Initialize RAG system
        rag_system = get_rag_system(emergent_key)
        print("✅ RAG system initialized")
        
        # Process each document
        processed_count = 0
        for doc in documents:
            try:
                print(f"🔄 Processing: {doc.get('original_name', 'Unknown')}")
                
                # Debug document structure
                print(f"   Document ID: {doc.get('id', 'Missing')}")
                print(f"   File path: {doc.get('file_path', 'Missing')}")
                print(f"   MIME type: {doc.get('mime_type', 'Missing')}")
                
                success = rag_system.process_and_store_document(doc)
                
                if success:
                    processed_count += 1
                    print(f"✅ Processed: {doc.get('original_name')}")
                else:
                    print(f"❌ Failed: {doc.get('original_name')}")
                    
            except Exception as e:
                print(f"❌ Error processing {doc.get('original_name', 'Unknown')}: {e}")
        
        # Check final stats
        try:
            stats = rag_system.get_collection_stats()
            print(f"\n🎉 RAG PROCESSING COMPLETE!")
            print(f"✅ Processed: {processed_count}/{len(documents)} documents")
            print(f"📊 RAG Stats: {stats}")
            
            # Test search
            if stats.get('total_chunks', 0) > 0:
                results = rag_system.search_similar_chunks("travel policy", n_results=2)
                print(f"🔍 Test search results: {len(results)} found")
                if results:
                    print(f"   Top result: {results[0].get('similarity_score', 'N/A')} - {results[0].get('metadata', {}).get('original_name', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Final stats error: {e}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(fix_production_rag())