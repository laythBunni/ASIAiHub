#!/usr/bin/env python3
"""
Reprocess all documents in MongoDB through the RAG system
This will fix the missing document chunks issue
"""

import asyncio
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'backend'))
from motor.motor_asyncio import AsyncIOMotorClient
from rag_system import RAGSystem

async def reprocess_all_documents():
    """Reprocess all documents through RAG system"""
    
    # Get MongoDB connection
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    emergent_key = os.environ.get('EMERGENT_LLM_KEY')
    
    print(f"🔧 Connecting to MongoDB: {mongo_url}")
    print(f"📄 Database: {db_name}")
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Initialize RAG system
        rag_system = RAGSystem(emergent_key)
        print("✅ RAG system initialized")
        
        # Get current ChromaDB stats
        try:
            collection_stats = rag_system.get_collection_stats()
            print(f"📊 Current ChromaDB chunks: {collection_stats}")
        except:
            print("📊 ChromaDB stats not available")
        
        # Get all documents from MongoDB
        documents = await db.documents.find({}).to_list(length=None)
        print(f"📚 Found {len(documents)} documents in MongoDB")
        
        if not documents:
            print("❌ No documents found to process")
            return
        
        # Process each document through RAG system
        processed_count = 0
        failed_count = 0
        
        for doc in documents:
            try:
                print(f"🔄 Processing: {doc.get('original_name', 'Unknown')}")
                
                # Call the RAG processing method
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
        
        # Final stats
        try:
            final_stats = rag_system.get_collection_stats()
            print(f"\n🎉 PROCESSING COMPLETE!")
            print(f"✅ Successfully processed: {processed_count} documents")
            print(f"❌ Failed: {failed_count} documents")
            print(f"📊 Total ChromaDB chunks: {final_stats}")
            print(f"\n🚀 James AI should now find your documents!")
            
        except Exception as e:
            print(f"📊 Final stats not available: {e}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Reprocessing all documents through RAG system...")
    asyncio.run(reprocess_all_documents())