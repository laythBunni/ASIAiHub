#!/usr/bin/env python3
"""
Production MongoDB RAG System Diagnostic
Check production environment configuration and MongoDB connection
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def diagnose_production_mongodb():
    print("🔍 PRODUCTION MONGODB RAG SYSTEM DIAGNOSTIC")
    print("=" * 60)
    
    # Check environment variables
    print("\n1. ENVIRONMENT VARIABLES:")
    mongo_url = os.environ.get('MONGO_URL', 'NOT SET')
    db_name = os.environ.get('DB_NAME', 'NOT SET')
    node_env = os.environ.get('NODE_ENV', 'NOT SET')
    backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'NOT SET')
    
    print(f"   MONGO_URL: {mongo_url}")
    print(f"   DB_NAME: {db_name}")
    print(f"   NODE_ENV: {node_env}")
    print(f"   REACT_APP_BACKEND_URL: {backend_url}")
    
    # Check production indicators
    print("\n2. PRODUCTION DETECTION:")
    production_indicators = [
        os.environ.get('NODE_ENV') == 'production',
        os.environ.get('ENVIRONMENT') == 'production', 
        'emergentagent.com' in os.environ.get('REACT_APP_BACKEND_URL', ''),
        'ai-workspace-17' in os.environ.get('REACT_APP_BACKEND_URL', ''),
    ]
    print(f"   Production indicators: {production_indicators}")
    print(f"   Is production: {any(production_indicators)}")
    
    # Test MongoDB connection
    print("\n3. MONGODB CONNECTION TEST:")
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Test connection
        server_info = await client.server_info()
        print(f"   ✅ Connected to MongoDB: {server_info.get('version')}")
        
        # Check collections
        collections = await db.list_collection_names()
        print(f"   📁 Available collections: {collections}")
        
        # Check document_chunks collection specifically
        if 'document_chunks' in collections:
            chunk_count = await db.document_chunks.count_documents({})
            print(f"   📄 document_chunks collection: {chunk_count} documents")
            
            if chunk_count > 0:
                # Sample a few chunks
                sample_chunks = await db.document_chunks.find().limit(3).to_list(3)
                print(f"   🔍 Sample chunks:")
                for i, chunk in enumerate(sample_chunks, 1):
                    print(f"      {i}. Document ID: {chunk.get('document_id')}")
                    print(f"         Text preview: {chunk.get('text', '')[:100]}...")
                    print(f"         Has embedding: {bool(chunk.get('embedding'))}")
        else:
            print(f"   ❌ document_chunks collection NOT FOUND")
            
        # Check documents collection
        if 'documents' in collections:
            doc_count = await db.documents.count_documents({})
            approved_count = await db.documents.count_documents({"approval_status": "approved"})
            processed_count = await db.documents.count_documents({"processed": True})
            print(f"   📋 documents collection: {doc_count} total, {approved_count} approved, {processed_count} processed")
        
    except Exception as e:
        print(f"   ❌ MongoDB connection failed: {e}")
    
    # Test RAG system initialization
    print("\n4. RAG SYSTEM INITIALIZATION TEST:")
    try:
        # Import and test RAG system
        from rag_system import RAGSystem
        
        emergent_key = os.environ.get('EMERGENT_LLM_KEY')
        if emergent_key:
            rag = RAGSystem(emergent_key)
            print(f"   ✅ RAG System initialized with mode: {rag.rag_mode}")
            
            # Test MongoDB storage method
            if hasattr(rag, '_store_chunks_mongodb'):
                print(f"   ✅ MongoDB storage method available")
            else:
                print(f"   ❌ MongoDB storage method NOT available")
                
            # Test MongoDB search method  
            if hasattr(rag, '_search_chunks_mongodb'):
                print(f"   ✅ MongoDB search method available")
            else:
                print(f"   ❌ MongoDB search method NOT available")
        else:
            print(f"   ❌ EMERGENT_LLM_KEY not found")
            
    except Exception as e:
        print(f"   ❌ RAG system initialization failed: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 DIAGNOSTIC COMPLETE")

if __name__ == "__main__":
    # Load environment
    from pathlib import Path
    from dotenv import load_dotenv
    
    env_path = Path(__file__).parent / 'backend' / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"📁 Loaded .env from: {env_path}")
    else:
        print(f"⚠️ .env file not found at: {env_path}")
    
    asyncio.run(diagnose_production_mongodb())