#!/usr/bin/env python3
"""
Debug document processing step by step
"""

import asyncio
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from rag_system import get_rag_system

async def debug_processing():
    """Debug each step of document processing"""
    
    mongo_url = "mongodb://localhost:27017"
    db_name = "asi_aihub_production"
    emergent_key = os.environ.get('EMERGENT_LLM_KEY')
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Get one document
        document = await db.documents.find_one({})
        print(f"Document: {document.get('original_name')}")
        
        # Initialize RAG
        rag = get_rag_system(emergent_key)
        
        # Step 1: Extract text
        print("\n1. Extracting text...")
        text = rag.extract_text_from_file(document['file_path'], document['mime_type'])
        print(f"   Text extracted: {len(text)} characters")
        print(f"   Text preview: {text[:200]}...")
        
        if not text.strip():
            print("   ERROR: No text extracted!")
            return
        
        # Step 2: Create metadata
        print("\n2. Creating metadata...")
        doc_metadata = {
            "document_id": document['id'],
            "filename": document['filename'],
            "original_name": document['original_name'],
            "department": document.get('department') or "General",
            "tags": ",".join(document.get('tags', [])),
            "uploaded_at": str(document['uploaded_at']),
            "mime_type": document['mime_type'],
            "file_size": document['file_size']
        }
        print(f"   Metadata created: {doc_metadata}")
        
        # Step 3: Chunk document
        print("\n3. Chunking document...")
        chunks = rag.chunk_document(text, doc_metadata)
        print(f"   Chunks created: {len(chunks)}")
        
        if len(chunks) == 0:
            print("   ERROR: No chunks created!")
            return
        
        print(f"   First chunk preview: {chunks[0]['chunk_text'][:100]}...")
        
        # Step 4: Store in ChromaDB
        print("\n4. Storing in ChromaDB...")
        chunk_texts = [chunk['chunk_text'] for chunk in chunks]
        chunk_ids = [chunk['chunk_id'] for chunk in chunks]
        chunk_metadatas = [
            {k: v for k, v in chunk.items() if k != 'chunk_text'}
            for chunk in chunks
        ]
        
        print(f"   Prepared {len(chunk_texts)} texts, {len(chunk_ids)} IDs, {len(chunk_metadatas)} metadatas")
        
        # Try storing
        rag.collection.add(
            documents=chunk_texts,
            ids=chunk_ids,
            metadatas=chunk_metadatas
        )
        print("   ✅ Successfully stored in ChromaDB!")
        
        # Step 5: Verify storage
        print("\n5. Verifying storage...")
        stats = rag.get_collection_stats()
        print(f"   Final stats: {stats}")
        
        client.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_processing())