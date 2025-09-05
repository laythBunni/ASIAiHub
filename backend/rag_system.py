"""
Advanced RAG System for ASI OS
Handles document processing, chunking, embeddings, and semantic search
"""

import os
import uuid
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime, timezone

# Document processing
import PyPDF2
from docx import Document as DocxDocument
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

# AI integrations  
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

# Initialize ChromaDB client
CHROMA_DB_PATH = "/app/backend/chroma_db"
os.makedirs(CHROMA_DB_PATH, exist_ok=True)

class RAGSystem:
    def __init__(self, emergent_llm_key: str):
        self.emergent_llm_key = emergent_llm_key
        
        # Use OpenAI embeddings instead of sentence transformers for production deployment
        try:
            # Try to use sentence transformers first (for development)
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            self.embedding_mode = "local"
            print("RAG System using local sentence transformers")
        except Exception as e:
            # Fall back to OpenAI embeddings (for production)
            self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=emergent_llm_key,  # Use same emergent key
                model_name="text-embedding-ada-002"
            )
            self.embedding_mode = "openai"
            print("RAG System using OpenAI embeddings (production mode)")
        
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(
                name="asi_os_documents",
                embedding_function=self.embedding_function
            )
        except:
            self.collection = self.chroma_client.create_collection(
                name="asi_os_documents",
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
        
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
        chunks = self.text_splitter.split_text(text)
        
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
    
    async def process_and_store_document(self, document_data: Dict[str, Any]) -> bool:
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
            
            # Prepare data for ChromaDB
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
            
            logger.info(f"Successfully processed and stored {len(chunks)} chunks from {document_data['original_name']}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing document {document_data.get('original_name', 'unknown')}: {e}")
            return False
    
    def search_similar_chunks(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar document chunks"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            similar_chunks = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    chunk_data = {
                        "content": doc,
                        "metadata": results['metadatas'][0][i],
                        "similarity_score": 1 - results['distances'][0][i],  # Convert distance to similarity
                        "chunk_id": results['metadatas'][0][i]['chunk_id']
                    }
                    similar_chunks.append(chunk_data)
            
            return similar_chunks
            
        except Exception as e:
            logger.error(f"Error searching chunks: {e}")
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
    
    async def generate_rag_response(self, query: str, session_id: str) -> Dict[str, Any]:
        """Generate structured response using RAG"""
        try:
            # Search for relevant chunks
            relevant_chunks = self.search_similar_chunks(query, n_results=8)
            
            if not relevant_chunks:
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
                    "response_type": "no_knowledge"
                }
            
            # Build context from relevant chunks
            context_parts = []
            referenced_docs = set()
            
            for chunk in relevant_chunks:
                if chunk['similarity_score'] > 0.3:  # Relevance threshold
                    context_parts.append(f"[From {chunk['metadata']['original_name']}]:\n{chunk['content']}\n")
                    referenced_docs.add(chunk['metadata']['original_name'])
            
            context_text = "\n".join(context_parts)
            
            # Generate structured response with GPT-5
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
            
            response = await chat.send_message(user_message)
            
            # Parse structured JSON response
            try:
                structured_response = json.loads(response)
                
                # Validate required fields
                required_fields = ["summary", "details", "action_required", "contact_info", "related_policies"]
                if not all(field in structured_response for field in required_fields):
                    raise ValueError("Missing required fields in JSON response")
                
                # Check if action suggests creating a ticket
                suggested_ticket = None
                if structured_response.get("action_required") and "ticket" in structured_response["action_required"].lower():
                    suggested_ticket = {"create_ticket": True, "suggestion": structured_response["action_required"]}
                
                # Add source information
                structured_response["sources"] = list(referenced_docs)
                
                return {
                    "response": structured_response,
                    "suggested_ticket": suggested_ticket,
                    "documents_referenced": len(referenced_docs),
                    "response_type": "structured",
                    "relevance_scores": [chunk['similarity_score'] for chunk in relevant_chunks[:3]]
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse structured response: {e}")
                
                # Fallback response
                return {
                    "response": {
                        "summary": response[:200] + "..." if len(response) > 200 else response,
                        "details": {
                            "requirements": [],
                            "procedures": [],
                            "exceptions": []
                        },
                        "action_required": "Please contact support for detailed guidance",
                        "contact_info": "Contact your department administrator for assistance",
                        "related_policies": [],
                        "sources": list(referenced_docs)
                    },
                    "suggested_ticket": None,
                    "documents_referenced": len(referenced_docs),
                    "response_type": "fallback"
                }
                
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return {
                "response": {
                    "summary": "I encountered an error processing your request. Please try again or contact support.",
                    "details": {
                        "requirements": [],
                        "procedures": [],
                        "exceptions": []
                    },
                    "action_required": "Please try again or contact IT support if the issue persists",
                    "contact_info": "IT Support: ithelp@asi-os.com or extension 3000",
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