#!/usr/bin/env python3
"""
Check current database status
"""

import asyncio
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from rag_system import get_rag_system

async def check_database():
    """Check current database status"""
    
    mongo_url = "mongodb://localhost:27017"
    db_name = "asi_aihub_production"
    
    print(f"🔍 Checking database: {db_name}")
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Check collections
        collections = await db.list_collection_names()
        print(f"📊 Collections: {collections}")
        
        # Check key data
        users = await db.simple_users.count_documents({})
        documents = await db.documents.count_documents({})
        tickets = await db.boost_tickets.count_documents({})
        chats = await db.chat_sessions.count_documents({})
        
        print(f"👥 Users: {users}")
        print(f"📄 Documents: {documents}")
        print(f"🎫 Tickets: {tickets}")
        print(f"💬 Chats: {chats}")
        
        # Check admin user
        admin = await db.simple_users.find_one({"email": "layth.bunni@adamsmithinternational.com"})
        if admin:
            print(f"✅ Admin user: {admin['name']} ({admin['role']})")
        
        # Check documents
        if documents > 0:
            docs = await db.documents.find({}).to_list(length=5)
            print(f"📋 Sample documents: {[doc.get('original_name') for doc in docs]}")
        
        # Check RAG system
        emergent_key = os.environ.get('EMERGENT_LLM_KEY')
        rag = get_rag_system(emergent_key)
        stats = rag.get_collection_stats()
        print(f"🔍 RAG Stats: {stats}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_database())