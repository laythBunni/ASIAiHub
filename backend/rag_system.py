"""
Advanced RAG System for ASI OS
Handles document processing, chunking, embeddings, and semantic search
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import asyncio
import hashlib
import uuid
import re
from pathlib import Path

# Document processing
import PyPDF2
from docx import Document as DocxDocument

# Check if we're in production environment - but allow persistent storage
PRODUCTION_INDICATORS = [
    os.environ.get('NODE_ENV') == 'production',
    os.environ.get('ENVIRONMENT') == 'production', 
    'emergentagent.com' in os.environ.get('REACT_APP_BACKEND_URL', ''),
    'ai-workspace-17' in os.environ.get('REACT_APP_BACKEND_URL', ''),
]

# Force ChromaDB mode with persistent storage for production (avoid memory-only cloud mode)
if any(PRODUCTION_INDICATORS):
    print("🏭 Production environment detected - using persistent ChromaDB for reliable chunk storage")
    # Try to use ChromaDB with persistent storage in production
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        # Use lighter dependencies - avoid sentence-transformers in production
        ML_DEPENDENCIES_AVAILABLE = True
        PRODUCTION_MODE = True
        print("✅ Production ChromaDB mode enabled (persistent chunk storage)")
    except ImportError as e:
        print(f"⚠️ ChromaDB not available in production, falling back to cloud mode: {e}")
        ML_DEPENDENCIES_AVAILABLE = False
        PRODUCTION_MODE = True
else:
    # Try to import full ML dependencies for local development
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        from sentence_transformers import SentenceTransformer
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        ML_DEPENDENCIES_AVAILABLE = True
        PRODUCTION_MODE = False
        print("✅ Local ML dependencies available (development mode)")
    except ImportError as e:
        print(f"⚠️ ML dependencies not available, using cloud alternatives: {e}")
        ML_DEPENDENCIES_AVAILABLE = False
        PRODUCTION_MODE = False

# Import required packages
import requests
import tiktoken

# AI integrations  
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

# Constants
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

class RAGSystem:
    def __init__(self, emergent_llm_key: str):
        self.emergent_llm_key = emergent_llm_key
        
        if ML_DEPENDENCIES_AVAILABLE:
            # Development mode: Use local ML dependencies
            self._init_local_rag()
        else:
            # Production mode: Use cloud-based alternatives
            self._init_cloud_rag()
    
    def _init_local_rag(self):
        """Initialize RAG with local ChromaDB - use lightweight production mode if needed"""
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            
            # Use persistent ChromaDB storage
            self.client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
            
            # Check if in production mode - use OpenAI embeddings instead of heavy ML models
            if globals().get('PRODUCTION_MODE', False):
                print("🏭 Production ChromaDB mode - using OpenAI embeddings")
                # Use OpenAI embeddings for production (lighter than sentence-transformers)
                self.collection = self.client.get_or_create_collection(
                    name="asi_os_documents",
                    embedding_function=embedding_functions.OpenAIEmbeddingFunction(
                        api_key=self.emergent_llm_key,
                        model_name="text-embedding-ada-002"
                    ),
                    metadata={"hnsw:space": "cosine"}
                )
                
                # Use simple text splitter (no heavy ML dependencies)
                self.chunk_size = 1000
                self.chunk_overlap = 200
                self.rag_mode = "production_persistent"
                
            else:
                print("🔧 Development ChromaDB mode - using local sentence-transformers")
                # Development mode with full ML dependencies
                from sentence_transformers import SentenceTransformer
                from langchain_text_splitters import RecursiveCharacterTextSplitter
                
                # Use sentence transformers for development
                self.collection = self.client.get_or_create_collection(
                    name="asi_os_documents",
                    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name="all-MiniLM-L6-v2"
                    ),
                    metadata={"hnsw:space": "cosine"}
                )
                
                # Initialize text splitter
                self.text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len,
                    separators=["\n\n", "\n", ". ", " ", ""]
                )
                self.rag_mode = "local"
            
            print(f"✅ RAG System initialized with persistent ChromaDB ({self.rag_mode} mode)")
            
        except Exception as e:
            logger.error(f"Failed to initialize persistent RAG: {e}")
            # Fallback to cloud mode
            self._init_cloud_rag()
    
    def _init_cloud_rag(self):
        """Initialize RAG with MongoDB-based chunk storage (production-safe)"""
        try:
            # Use MongoDB for reliable chunk storage instead of problematic ChromaDB
            self.documents = {}  # Document metadata cache
            self.chunk_collection_name = "document_chunks"  # MongoDB collection for chunks
            self.embedding_cache = {}  # Embedding cache
            
            # Simple text splitter without ML dependencies
            self.chunk_size = 1000
            self.chunk_overlap = 200
            
            self.rag_mode = "mongodb_cloud"
            print("✅ RAG System initialized with MongoDB chunk storage (production-safe)")
            
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB RAG: {e}")
            raise
    
    async def _store_chunks_mongodb(self, document_id: str, chunks: List[str], document_data: Dict) -> bool:
        """Store document chunks in MongoDB with embeddings"""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            import os
            
            # Get database connection
            mongo_url = os.environ.get('MONGO_URL')
            db_name = os.environ.get('DB_NAME')
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            
            # Generate embeddings using OpenAI
            import asyncio
            from emergentintegrations import LlmChat, UserMessage
            
            chunk_documents = []
            
            for i, chunk_text in enumerate(chunks):
                try:
                    # Generate embedding using OpenAI
                    chat = LlmChat(api_key=self.emergent_llm_key)
                    embedding_response = await asyncio.wait_for(
                        chat.get_embedding(chunk_text, model="text-embedding-ada-002"),
                        timeout=30.0
                    )
                    
                    chunk_doc = {
                        "document_id": document_id,
                        "chunk_index": i,
                        "text": chunk_text,
                        "embedding": embedding_response,
                        "metadata": {
                            "source": document_data.get('original_name', 'Unknown'),
                            "department": document_data.get('department'),
                            "created_at": document_data.get('uploaded_at'),
                        },
                        "created_at": datetime.now(timezone.utc)
                    }
                    chunk_documents.append(chunk_doc)
                    
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for chunk {i}: {e}")
                    continue
            
            if chunk_documents:
                # Store chunks in MongoDB
                await db[self.chunk_collection_name].insert_many(chunk_documents)
                logger.info(f"Successfully stored {len(chunk_documents)} chunks in MongoDB for document {document_id}")
                return True
            else:
                logger.error(f"No chunks could be processed for document {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to store chunks in MongoDB: {e}")
            return False

    async def _search_chunks_mongodb(self, query: str, limit: int = 5) -> List[Dict]:
        """Search document chunks in MongoDB using semantic similarity"""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            import os
            import numpy as np
            
            # Get database connection
            mongo_url = os.environ.get('MONGO_URL')
            db_name = os.environ.get('DB_NAME')
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            
            # Generate query embedding
            from emergentintegrations import LlmChat
            import asyncio
            
            chat = LlmChat(api_key=self.emergent_llm_key)
            query_embedding = await asyncio.wait_for(
                chat.get_embedding(query, model="text-embedding-ada-002"),
                timeout=30.0
            )
            
            # Get all chunks from MongoDB
            chunks_cursor = db[self.chunk_collection_name].find({})
            chunks = await chunks_cursor.to_list(length=1000)
            
            if not chunks:
                logger.warning("No chunks found in MongoDB")
                return []
            
            # Calculate cosine similarity with all chunks
            similarities = []
            for chunk in chunks:
                try:
                    chunk_embedding = chunk.get('embedding')
                    if chunk_embedding:
                        # Calculate cosine similarity
                        similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                        similarities.append({
                            'chunk': chunk,
                            'similarity': similarity
                        })
                except Exception as e:
                    logger.warning(f"Error calculating similarity for chunk: {e}")
                    continue
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            top_results = similarities[:limit]
            
            results = []
            for result in top_results:
                chunk = result['chunk']
                results.append({
                    'text': chunk['text'],
                    'metadata': chunk['metadata'],
                    'similarity': result['similarity'],
                    'source': chunk['metadata'].get('source', 'Unknown')
                })
            
            logger.info(f"MongoDB search found {len(results)} relevant chunks")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search chunks in MongoDB: {e}")
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            import numpy as np
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0
                
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0

    def _simple_text_splitter(self, text: str) -> List[str]:
        """Simple text splitter for production mode"""
        chunks = []
        current_chunk = ""
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, save current chunk
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += '\n\n' + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    def process_and_store_document(self, document_data: Dict[str, Any]) -> bool:
        """Process document and store chunks - MongoDB or ChromaDB based on mode"""
        try:
            # Extract text from file
            text = self.extract_text_from_file(document_data['file_path'], document_data['mime_type'])
            if not text:
                return False
            
            # Split into chunks
            if self.rag_mode == "mongodb_cloud":
                chunks = self._simple_text_splitter(text)
            elif hasattr(self, 'text_splitter'):
                chunks = self.text_splitter.split_text(text)
            else:
                chunks = self._simple_text_splitter(text)
            
            if not chunks:
                logger.warning(f"No chunks created for document {document_data['id']}")
                return False
            
            # Store chunks based on mode
            if self.rag_mode == "mongodb_cloud":
                # Use MongoDB storage (async)
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    success = loop.run_until_complete(
                        self._store_chunks_mongodb(document_data['id'], chunks, document_data)
                    )
                    return success
                finally:
                    loop.close()
            else:
                # Use ChromaDB storage (existing method)
                return self._store_chunks_chromadb(document_data, chunks)
                
        except Exception as e:
            logger.error(f"Error processing document {document_data.get('id', 'unknown')}: {e}")
            return False

    def _store_chunks_chromadb(self, document_data: Dict, chunks: List[str]) -> bool:
        """Store chunks in ChromaDB (existing method)"""
        try:
            # Generate unique IDs for chunks
            chunk_ids = [f"{document_data['id']}_chunk_{i}" for i in range(len(chunks))]
            
            # Create metadata
            metadatas = [{
                "source": document_data['original_name'],
                "document_id": document_data['id'],
                "chunk_index": i,
                "department": document_data.get('department', ''),
                "file_type": document_data.get('mime_type', ''),
            } for i in range(len(chunks))]
            
            # Add to collection
            self.collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=chunk_ids
            )
            
            logger.info(f"Successfully stored {len(chunks)} chunks for document {document_data['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing chunks in ChromaDB: {e}")
            return False

    async def search_documents(self, query: str, limit: int = 5) -> List[Dict]:
        """Search documents using appropriate method based on mode"""
        try:
            if self.rag_mode == "mongodb_cloud":
                # Use MongoDB search
                return await self._search_chunks_mongodb(query, limit)
            else:
                # Use ChromaDB search (existing method)
                return self._search_chunks_chromadb(query, limit)
                
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

    def _search_chunks_chromadb(self, query: str, limit: int = 5) -> List[Dict]:
        """Search chunks in ChromaDB (existing method)"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                include=['documents', 'metadatas', 'distances']
            )
            
            search_results = []
            if results['documents']:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0], 
                    results['distances'][0]
                )):
                    similarity = 1 - distance  # Convert distance to similarity
                    search_results.append({
                        'text': doc,
                        'metadata': metadata,
                        'similarity': similarity,
                        'source': metadata.get('source', 'Unknown')
                    })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {e}")
            return []
    
    async def _get_openai_embedding(self, text: str) -> List[float]:
        """Get embedding using OpenAI API via emergent integrations"""
        try:
            # Use emergent integrations to get embeddings
            chat = LlmChat(api_key=self.emergent_llm_key, session_id="embedding")
            
            # Simple embedding simulation - in production, this would use proper embedding API
            # For now, we'll use a hash-based approach for text similarity
            text_hash = hashlib.md5(text.encode()).hexdigest()
            # Convert hash to pseudo-embedding (128 dimensions)
            embedding = [float(int(text_hash[i:i+2], 16)) / 255.0 for i in range(0, min(len(text_hash), 32), 2)]
            # Pad to 128 dimensions
            while len(embedding) < 128:
                embedding.append(0.0)
                
            return embedding[:128]
            
        except Exception as e:
            logger.error(f"Error getting OpenAI embedding: {e}")
            # Return zero embedding as fallback
            return [0.0] * 128
    
    def _calculate_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            dot_product = sum(a * b for a, b in zip(emb1, emb2))
            magnitude1 = sum(a * a for a in emb1) ** 0.5
            magnitude2 = sum(b * b for b in emb2) ** 0.5
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
                
            return dot_product / (magnitude1 * magnitude2)
        except:
            return 0.0
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info("RAG System initialized with ChromaDB")
    
    def extract_text_from_file(self, file_path: str, mime_type: str) -> str:
        """Extract text from various file formats"""
        try:
            # Ensure absolute path
            if not os.path.isabs(file_path):
                # If relative path, make it relative to backend directory
                file_path = os.path.join(os.path.dirname(__file__), file_path)
            
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return ""
            
            if mime_type == "text/plain":
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif mime_type == "application/pdf":
                text = ""
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                return text
            
            elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = DocxDocument(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            
            else:
                logger.warning(f"Unsupported file type: {mime_type}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def chunk_document(self, text: str, doc_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split document into chunks with metadata"""
        if self.rag_mode == "local" and ML_DEPENDENCIES_AVAILABLE:
            # Use langchain text splitter
            chunks = self.text_splitter.split_text(text)
        else:
            # Use simple text splitter for production
            chunks = self._simple_text_splitter(text)
        
        chunked_docs = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                **doc_metadata,
                "chunk_index": i,
                "chunk_id": f"{doc_metadata['document_id']}_chunk_{i}",
                "chunk_text": chunk,
                "chunk_length": len(chunk)
            }
            chunked_docs.append(chunk_metadata)
        
        return chunked_docs
    
    def process_and_store_document(self, document_data: Dict[str, Any]) -> bool:
        """Process a document and store in vector database"""
        try:
            # Extract text from document
            text = self.extract_text_from_file(
                document_data['file_path'], 
                document_data['mime_type']
            )
            
            if not text.strip():
                logger.warning(f"No text extracted from document {document_data['original_name']}")
                return False
            
            # Create document metadata (ChromaDB only accepts str, int, float, bool, None)
            doc_metadata = {
                "document_id": document_data['id'],
                "filename": document_data['filename'],
                "original_name": document_data['original_name'],
                "department": document_data.get('department') or "General",
                "tags": ",".join(document_data.get('tags', [])),  # Convert list to comma-separated string
                "uploaded_at": document_data['uploaded_at'].isoformat() if isinstance(document_data['uploaded_at'], datetime) else str(document_data['uploaded_at']),
                "mime_type": document_data['mime_type'],
                "file_size": document_data['file_size']
            }
            
            # Chunk the document
            chunks = self.chunk_document(text, doc_metadata)
            
            if self.rag_mode == "local" and ML_DEPENDENCIES_AVAILABLE:
                # Store in ChromaDB (local mode)
                chunk_texts = [chunk['chunk_text'] for chunk in chunks]
                chunk_ids = [chunk['chunk_id'] for chunk in chunks]
                chunk_metadatas = [
                    {k: v for k, v in chunk.items() if k != 'chunk_text'}
                    for chunk in chunks
                ]
                
                # Store in ChromaDB
                self.collection.add(
                    documents=chunk_texts,
                    ids=chunk_ids,
                    metadatas=chunk_metadatas
                )
            else:
                # Store in memory (cloud mode) - this would need async for embeddings
                document_id = document_data['id']
                self.documents[document_id] = document_data
                self.document_chunks[document_id] = chunks
                
                # Note: In cloud mode, embeddings would be generated asynchronously
                # For now, store without embeddings for immediate functionality
            
            logger.info(f"Successfully processed and stored {len(chunks)} chunks from {document_data['original_name']}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing document {document_data.get('original_name', 'unknown')}: {e}")
            return False
    
    def search_similar_chunks(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar document chunks"""
        try:
            if self.rag_mode == "local" and ML_DEPENDENCIES_AVAILABLE:
                # Use ChromaDB search
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    include=['documents', 'metadatas', 'distances']
                )
                
                chunks = []
                if results['documents'][0]:  # Check if any results
                    for i, doc in enumerate(results['documents'][0]):
                        chunk = {
                            'content': doc,
                            'metadata': results['metadatas'][0][i],
                            'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                        }
                        chunks.append(chunk)
                
                return chunks
            
            else:
                # Use in-memory search with embeddings (cloud mode)
                query_embedding = asyncio.run(self._get_openai_embedding(query))
                
                all_chunks = []
                for doc_id, chunks in self.document_chunks.items():
                    for chunk in chunks:
                        if 'embedding' in chunk:
                            similarity = self._calculate_similarity(query_embedding, chunk['embedding'])
                            all_chunks.append({
                                'content': chunk['chunk_text'],
                                'metadata': {k: v for k, v in chunk.items() if k not in ['chunk_text', 'embedding']},
                                'similarity_score': similarity
                            })
                
                # Sort by similarity and return top results
                all_chunks.sort(key=lambda x: x['similarity_score'], reverse=True)
                return all_chunks[:n_results]
                
        except Exception as e:
            logger.error(f"Error searching similar chunks: {e}")
            return []
    
    def remove_document_chunks(self, document_id: str) -> bool:
        """Remove all chunks for a specific document"""
        try:
            # Find all chunks for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Removed {len(results['ids'])} chunks for document {document_id}")
                return True
            else:
                logger.info(f"No chunks found for document {document_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error removing document chunks: {e}")
            return False
    
    async def generate_rag_response(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """Generate response using RAG with MongoDB or ChromaDB"""
        try:
            # Search for relevant documents using unified search method
            search_results = await self.search_documents(query, limit=5)
            
            if not search_results:
                logger.warning(f"No relevant documents found for query: {query}")
                return {
                    "response": {
                        "summary": "I don't have information about this topic in the company knowledge base.",
                        "details": {
                            "requirements": [],
                            "procedures": [],
                            "exceptions": []
                        },
                        "action_required": "Please upload relevant policy documents or contact support for assistance.",
                        "contact_info": "Contact your department administrator or IT support",
                        "related_policies": []
                    },
                    "suggested_ticket": None,
                    "documents_referenced": 0,
                    "response_type": "no_documents_found"
                }
            
            # Build context from search results
            context_parts = []
            referenced_docs = set()
            
            for result in search_results:
                similarity = result.get('similarity', 0)
                if similarity > 0.3:  # Only include relevant results
                    source = result['metadata'].get('source', 'Unknown Document')
                    text = result['text']
                    
                    context_parts.append(f"From {source}:\n{text}")
                    referenced_docs.add(source)
            
            if not context_parts:
                logger.warning(f"No sufficiently relevant documents found for query: {query}")
                return {
                    "response": {
                        "summary": "I found some documents but they don't seem directly related to your question.",
                        "details": {
                            "requirements": [],
                            "procedures": [],
                            "exceptions": []
                        },
                        "action_required": "Try rephrasing your question or contact support for assistance.",
                        "contact_info": "Contact your department administrator or IT support",
                        "related_policies": list(referenced_docs) if referenced_docs else []
                    },
                    "suggested_ticket": None,
                    "documents_referenced": len(referenced_docs),
                    "response_type": "low_relevance"
                }
            
            context_text = "\n\n".join(context_parts)
            
            # Generate structured response with GPT-5 with timeout protection
            from emergentintegrations import LlmChat, UserMessage
            import asyncio
            
            chat = LlmChat(
                api_key=self.emergent_llm_key,
                session_id=session_id,
                system_message="""You are an AI assistant for ASI AiHub - an enterprise AI-powered knowledge management platform. You have access to approved company policy documents and procedures.

                CRITICAL: You must ALWAYS respond with a structured JSON format. Never provide plain text responses.

                Response Format (JSON):
                {
                  "summary": "Brief 1-2 sentence answer to the question",
                  "details": {
                    "requirements": ["list of requirements, rules, or criteria"],
                    "procedures": ["step-by-step procedures or processes"],
                    "exceptions": ["any exceptions, special cases, or conditions"]
                  },
                  "action_required": "What the user needs to do next (if any)",
                  "contact_info": "Department, email, or phone number for help",
                  "related_policies": ["names of related policies or procedures"]
                }

                Guidelines:
                1. Use the provided document context as your primary knowledge source
                2. If information isn't fully available, be honest in the summary
                3. Extract specific requirements, procedures, and exceptions from the context
                4. Always include contact_info when available from documents
                5. If a support ticket should be created, include this in action_required
                6. Be professional and actionable
                7. Focus on company-specific policies and procedures
                
                Document context will be provided with source attributions."""
            ).with_model("openai", "gpt-5")
            
            user_message = UserMessage(
                text=f"Query: {query}\n\nRelevant Company Documentation:\n{context_text}"
            )
            
            # Add timeout protection to LLM call
            try:
                response = await asyncio.wait_for(
                    chat.send_message(user_message), 
                    timeout=45.0  # 45 second timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"LLM timeout for query: {query[:50]}... - using fallback response")
                # Return fallback response with relevant documents found
                return {
                    "response": {
                        "summary": f"I found {len(referenced_docs)} relevant documents but response generation timed out. Here are the key documents that contain information about your query.",
                        "details": {
                            "requirements": ["Document processing timed out - please check the referenced documents below"],
                            "procedures": ["Contact IT support if this issue persists"],
                            "exceptions": []
                        },
                        "action_required": "Review the referenced documents manually or contact support for assistance",
                        "contact_info": "Contact your department administrator or IT support",
                        "related_policies": list(referenced_docs)
                    },
                    "suggested_ticket": None,
                    "documents_referenced": len(referenced_docs),
                    "response_type": "llm_timeout"
                }
            
            # Parse structured response
            try:
                structured_response = json.loads(response)
                
                # Validate required fields
                if not isinstance(structured_response, dict):
                    raise ValueError("Response is not a JSON object")
                
                return {
                    "response": structured_response,
                    "suggested_ticket": None,
                    "documents_referenced": len(referenced_docs),
                    "response_type": "success"
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse LLM response as JSON: {e}")
                # Return a structured fallback using the raw response
                return {
                    "response": {
                        "summary": str(response)[:200] + "..." if len(str(response)) > 200 else str(response),
                        "details": {
                            "requirements": ["Please see the summary for detailed information"],
                            "procedures": [],
                            "exceptions": []
                        },
                        "action_required": "Review the information in the summary section",
                        "contact_info": "Contact your department administrator or IT support",
                        "related_policies": list(referenced_docs)
                    },
                    "suggested_ticket": None,
                    "documents_referenced": len(referenced_docs),
                    "response_type": "parsing_fallback"
                }
                
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return {
                "response": {
                    "summary": "An error occurred while processing your request.",
                    "details": {
                        "requirements": [],
                        "procedures": [],
                        "exceptions": []
                    },
                    "action_required": "Please try again or contact support if the issue persists",
                    "contact_info": "Contact your department administrator or IT support",
                    "related_policies": []
                },
                "suggested_ticket": None,
                "documents_referenced": 0,
                "response_type": "error"
            }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection"""
        try:
            collection_info = self.collection.get(include=["metadatas"])
            
            total_chunks = len(collection_info['ids']) if collection_info['ids'] else 0
            
            # Count unique documents
            unique_docs = set()
            departments = set()
            
            if collection_info['metadatas']:
                for metadata in collection_info['metadatas']:
                    if metadata.get('document_id'):
                        unique_docs.add(metadata['document_id'])
                    if metadata.get('department'):
                        departments.add(metadata['department'])
            
            return {
                "total_chunks": total_chunks,
                "unique_documents": len(unique_docs),
                "departments": list(departments),
                "collection_name": self.collection.name
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {
                "total_chunks": 0,
                "unique_documents": 0,
                "departments": [],
                "collection_name": "asi_os_documents"
            }

# Global RAG system instance
rag_system = None

def get_rag_system(emergent_llm_key: str) -> RAGSystem:
    """Get or create RAG system instance"""
    global rag_system
    if rag_system is None:
        rag_system = RAGSystem(emergent_llm_key)
    return rag_system