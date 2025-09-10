#!/usr/bin/env python3
"""
Production MongoDB RAG Debug Endpoint
Add this as an API endpoint to debug the production system directly
"""

from fastapi import APIRouter
import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from rag_system import get_rag_system

debug_router = APIRouter(prefix="/debug")

@debug_router.get("/production-rag-status")
async def production_rag_status():
    """Debug endpoint to check production RAG system status"""
    try:
        result = {
            "timestamp": str(__import__("datetime").datetime.now()),
            "environment_check": {},
            "mongodb_check": {},
            "rag_system_check": {},
            "document_processing_check": {}
        }
        
        # 1. Environment Variables Check
        result["environment_check"] = {
            "MONGO_URL": os.environ.get('MONGO_URL', 'NOT SET')[:50] + "..." if len(os.environ.get('MONGO_URL', '')) > 50 else os.environ.get('MONGO_URL', 'NOT SET'),
            "DB_NAME": os.environ.get('DB_NAME', 'NOT SET'),
            "NODE_ENV": os.environ.get('NODE_ENV', 'NOT SET'),
            "EMERGENT_LLM_KEY": "SET" if os.environ.get('EMERGENT_LLM_KEY') else "NOT SET",
            "is_atlas": "mongodb+srv" in os.environ.get('MONGO_URL', ''),
            "production_detected": any([
                os.environ.get('NODE_ENV') == 'production',
                'emergentagent.com' in os.environ.get('REACT_APP_BACKEND_URL', ''),
                'ai-workspace-17' in os.environ.get('REACT_APP_BACKEND_URL', ''),
            ])
        }
        
        # 2. MongoDB Connection Check
        try:
            mongo_url = os.environ.get('MONGO_URL')
            db_name = os.environ.get('DB_NAME')
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            
            # Test connection
            server_info = await client.server_info()
            collections = await db.list_collection_names()
            
            result["mongodb_check"] = {
                "connection_status": "SUCCESS",
                "server_version": server_info.get('version'),
                "collections": collections,
                "has_document_chunks": "document_chunks" in collections,
                "documents_count": await db.documents.count_documents({}),
                "approved_docs": await db.documents.count_documents({"approval_status": "approved"}),
                "processed_docs": await db.documents.count_documents({"processed": True})
            }
            
            # Check document_chunks collection
            if "document_chunks" in collections:
                chunk_count = await db.document_chunks.count_documents({})
                result["mongodb_check"]["chunk_count"] = chunk_count
                
                if chunk_count > 0:
                    sample_chunk = await db.document_chunks.find_one()
                    result["mongodb_check"]["sample_chunk"] = {
                        "document_id": sample_chunk.get("document_id"),
                        "has_text": bool(sample_chunk.get("text")),
                        "has_embedding": bool(sample_chunk.get("embedding")),
                        "text_preview": sample_chunk.get("text", "")[:100] + "..." if sample_chunk.get("text") else None
                    }
            else:
                result["mongodb_check"]["chunk_count"] = 0
                
        except Exception as e:
            result["mongodb_check"] = {
                "connection_status": "FAILED",
                "error": str(e)
            }
        
        # 3. RAG System Check
        try:
            emergent_key = os.environ.get('EMERGENT_LLM_KEY')
            rag = get_rag_system(emergent_key)
            
            result["rag_system_check"] = {
                "initialization_status": "SUCCESS",
                "rag_mode": getattr(rag, 'rag_mode', 'unknown'),
                "has_mongodb_store": hasattr(rag, '_store_chunks_mongodb'),
                "has_mongodb_search": hasattr(rag, '_search_chunks_mongodb'),
                "chunk_collection_name": getattr(rag, 'chunk_collection_name', 'unknown')
            }
            
            # Test search functionality
            try:
                search_results = await rag.search_documents("test query", limit=1)
                result["rag_system_check"]["search_test"] = {
                    "status": "SUCCESS",
                    "results_count": len(search_results)
                }
            except Exception as search_e:
                result["rag_system_check"]["search_test"] = {
                    "status": "FAILED",
                    "error": str(search_e)
                }
                
        except Exception as e:
            result["rag_system_check"] = {
                "initialization_status": "FAILED",
                "error": str(e)
            }
        
        # 4. Document Processing Check
        try:
            from server import process_document_with_rag
            
            # Check if we have any pending documents to process
            pending_docs = await db.documents.find({
                "approval_status": "approved",
                "processing_status": {"$in": ["pending", "processing"]}
            }).to_list(5)
            
            result["document_processing_check"] = {
                "pending_processing": len(pending_docs),
                "function_available": callable(process_document_with_rag),
                "pending_documents": [
                    {
                        "id": doc["id"],
                        "name": doc["original_name"],
                        "status": doc.get("processing_status", "unknown"),
                        "processed": doc.get("processed", False)
                    }
                    for doc in pending_docs
                ]
            }
            
        except Exception as e:
            result["document_processing_check"] = {
                "status": "FAILED",
                "error": str(e)
            }
        
        return result
        
    except Exception as e:
        return {
            "status": "CRITICAL_ERROR",
            "error": str(e),
            "timestamp": str(__import__("datetime").datetime.now())
        }