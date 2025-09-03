from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import aiofiles
import json
from enum import Enum
import asyncio
import secrets
import hashlib
import re
from fastapi import Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Import emergent integrations
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType

# Import RAG system
from rag_system import get_rag_system

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="ASI AiHub - AI-Powered Knowledge Management Platform")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize LLM Chat
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Enums and Models
class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Department(str, Enum):
    FINANCE = "Finance"
    PEOPLE_TALENT = "People and Talent"
    INFORMATION_TECHNOLOGY = "Information Technology"
    LEGAL_ETHICS = "Legal, Ethics and Compliance"
    BUSINESS_DEVELOPMENT = "Business Development"
    PROJECT_MANAGEMENT = "Project Management"
    OTHER = "Other"

# BOOST Ticketing System Enums
class SupportDepartment(str, Enum):
    OS_SUPPORT = "OS Support"
    FINANCE = "Finance"
    HR_PT = "HR/P&T"
    IT = "IT"
    DEVOPS = "DevOps"

class TicketClassification(str, Enum):
    INCIDENT = "Incident"
    BUG = "Bug"
    SERVICE_REQUEST = "ServiceRequest"
    CHANGE_REQUEST = "ChangeRequest"
    IMPLEMENTATION = "Implementation"
    HOW_TO_QUERY = "HowToQuery"

class TicketChannel(str, Enum):
    HUB = "Hub"
    EMAIL = "Email"
    TEAMS = "Teams"
    PHONE = "Phone"
    MANUAL = "Manual"

class ResolutionType(str, Enum):
    SOP_FOLLOWED = "SOPFollowed"
    CUSTOM_ACTION = "CustomAction"
    ESCALATION_DECISION = "EscalationDecision"

class BoostRole(str, Enum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    AGENT = "Agent"
    USER = "User"

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    END_USER = "end_user"

class CommentType(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"

# Database Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    full_name: str
    role: UserRole = UserRole.END_USER
    department: Optional[Department] = None
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# BOOST Ticketing System Models
class BusinessUnit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BoostUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    boost_role: BoostRole = BoostRole.USER
    business_unit_id: Optional[str] = None
    business_unit_name: Optional[str] = None
    department: Optional[SupportDepartment] = None
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BoostTicket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_number: str = Field(default_factory=lambda: f"BST-{str(uuid.uuid4())[:8].upper()}")
    subject: str
    description: str
    requester_id: str
    requester_name: str
    requester_email: str
    business_unit_id: Optional[str] = None
    business_unit_name: Optional[str] = None
    
    # Categorization
    support_department: SupportDepartment
    category: str
    subcategory: str
    classification: TicketClassification
    
    # Status and Priority
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority
    
    # Assignment
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    
    # Metadata
    channel: TicketChannel = TicketChannel.HUB
    justification: str = ""  # Required for Critical priority
    resolution_notes: str = ""
    resolution_type: Optional[ResolutionType] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    due_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

class BoostComment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    author_id: str
    author_name: str
    body: str
    is_internal: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BoostAttachment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    filename: str
    original_name: str
    file_path: str
    file_url: str = ""
    file_size: int
    mime_type: str
    uploaded_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DocumentStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved" 
    REJECTED = "rejected"

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_name: str
    file_path: str
    mime_type: str
    file_size: int
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    department: Optional[Department] = None
    tags: List[str] = []
    processed: bool = False
    chunks_count: int = 0
    processing_status: str = "pending"  # pending, processing, completed, failed
    approval_status: DocumentStatus = DocumentStatus.PENDING_APPROVAL
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    uploaded_by: str = "system_user"
    notes: str = ""

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attachments: List[str] = []  # Document IDs

class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"  # For MVP, using default user
    title: str = "New Conversation"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    messages_count: int = 0

class TicketComment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    author: str = "default_user"
    author_name: str = "System User"
    content: str
    comment_type: CommentType = CommentType.PUBLIC
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attachments: List[str] = []

class Ticket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_number: str = Field(default_factory=lambda: f"TKT-{str(uuid.uuid4())[:8].upper()}")
    subject: str
    description: str
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM
    department: Department
    category: str = ""
    sub_category: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    requester: str = "default_user"
    requester_name: str = "System User"
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    sla_due: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    attachments: List[str] = []
    chat_session_id: Optional[str] = None
    tags: List[str] = []
    resolution_notes: str = ""

class FinanceSOP(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    month: str  # Format: "2025-01"
    year: int
    status: str = "in_progress"  # in_progress, review, approved, completed
    prior_month_reviewed: bool = False
    monthly_reports_prepared: bool = False
    budget_variance_analyzed: bool = False
    forecasts_updated: bool = False
    review_meeting_held: bool = False
    reports_approved: bool = False
    results_communicated: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approver: Optional[str] = None
    notes: str = ""

# Request/Response Models
class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    message: str

class ChatRequest(BaseModel):
    session_id: str
    message: str
    document_ids: List[str] = []  # Optional - for backward compatibility, but not used

class ChatResponse(BaseModel):
    session_id: str
    response: Dict[str, Any]  # Now returns structured response
    suggested_ticket: Optional[Dict[str, Any]] = None
    documents_referenced: int = 0
    response_type: str = "structured"

class TicketCreate(BaseModel):
    subject: str
    description: str
    department: Department
    priority: TicketPriority = TicketPriority.MEDIUM
    category: str = ""
    sub_category: str = ""
    requester_name: str = "System User"
    tags: List[str] = []

class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    resolution_notes: Optional[str] = None
    tags: Optional[List[str]] = None

class CommentCreate(BaseModel):
    content: str
    comment_type: CommentType = CommentType.PUBLIC
    author_name: str = "System User"

class FinanceSOPUpdate(BaseModel):
    prior_month_reviewed: Optional[bool] = None
    monthly_reports_prepared: Optional[bool] = None
    budget_variance_analyzed: Optional[bool] = None
    forecasts_updated: Optional[bool] = None
    review_meeting_held: Optional[bool] = None
    reports_approved: Optional[bool] = None
    results_communicated: Optional[bool] = None
    notes: Optional[str] = None

# BOOST Ticketing Request/Response Models
class BoostTicketCreate(BaseModel):
    subject: str
    description: str
    support_department: SupportDepartment
    category: str
    subcategory: str
    classification: TicketClassification
    priority: TicketPriority
    justification: str = ""
    requester_name: str = "System User"
    requester_email: str = "user@company.com"
    business_unit_id: Optional[str] = None
    channel: TicketChannel = TicketChannel.HUB

class BoostTicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolution_type: Optional[ResolutionType] = None

class BoostCommentCreate(BaseModel):
    body: str
    is_internal: bool = False
    author_name: str = "System User"

class BusinessUnitCreate(BaseModel):
    name: str
    code: str = ""

class BoostUserCreate(BaseModel):
    name: str
    email: str
    boost_role: BoostRole = BoostRole.USER
    business_unit_id: Optional[str] = None
    department: Optional[SupportDepartment] = None

class BoostUserUpdate(BaseModel):
    boost_role: Optional[BoostRole] = None
    business_unit_id: Optional[str] = None
    department: Optional[SupportDepartment] = None
    active: Optional[bool] = None

# Utility Functions
async def process_document_with_rag(document_data: Dict[str, Any]) -> None:
    """Process document with RAG system in background"""
    try:
        # Get RAG system instance
        rag = get_rag_system(EMERGENT_LLM_KEY)
        
        # Update processing status
        await db.documents.update_one(
            {"id": document_data["id"]},
            {"$set": {"processing_status": "processing"}}
        )
        
        # Process and store document
        success = await rag.process_and_store_document(document_data)
        
        if success:
            # Get collection stats for chunks count
            stats = rag.get_collection_stats()
            
            # Update document as processed
            await db.documents.update_one(
                {"id": document_data["id"]},
                {
                    "$set": {
                        "processed": True,
                        "processing_status": "completed",
                        "chunks_count": stats.get("total_chunks", 0) // stats.get("unique_documents", 1)
                    }
                }
            )
            logger.info(f"Successfully processed document {document_data['original_name']}")
        else:
            # Mark as failed
            await db.documents.update_one(
                {"id": document_data["id"]},
                {"$set": {"processing_status": "failed"}}
            )
            logger.error(f"Failed to process document {document_data['original_name']}")
            
    except Exception as e:
        logger.error(f"Error in background document processing: {e}")
        # Mark as failed
        await db.documents.update_one(
            {"id": document_data["id"]},
            {"$set": {"processing_status": "failed"}}
        )

def calculate_sla_due(priority: TicketPriority, created_at: datetime) -> datetime:
    """Calculate SLA due date based on priority"""
    sla_hours = {
        TicketPriority.URGENT: 4,
        TicketPriority.HIGH: 24,
        TicketPriority.MEDIUM: 72,
        TicketPriority.LOW: 168  # 1 week
    }
    
    hours = sla_hours.get(priority, 72)
    return created_at + timedelta(hours=hours)

def calculate_boost_sla_due(priority: TicketPriority, created_at: datetime) -> datetime:
    """Calculate BOOST SLA due date based on priority"""
    # BOOST SLA: Critical 1h, High 4h, Medium 1 business day, Low 2 business days
    sla_hours = {
        TicketPriority.URGENT: 1,      # Critical
        TicketPriority.HIGH: 4,        # High
        TicketPriority.MEDIUM: 24,     # Medium (1 business day)
        TicketPriority.LOW: 48         # Low (2 business days)
    }
    
    hours = sla_hours.get(priority, 24)
    return created_at + timedelta(hours=hours)

def auto_prefix_subject(department: SupportDepartment, category: str, subject: str) -> str:
    """Auto-prefix subject with department and category"""
    dept_name = department.value  # Get the actual string value from enum
    if subject.startswith(f"{dept_name}: {category}"):
        return subject
    return f"{dept_name}: {category} – {subject}"

# BOOST Categorization Data
BOOST_CATEGORIES = {
    SupportDepartment.FINANCE: {
        "Purchase Orders": ["Creation", "Amendment", "Approval"],
        "Invoices": ["AP", "Associate", "Supplier"],
        "Sage Sync": ["Failures", "Duplicates"],
        "Expenses": ["Claims", "Approvals", "Policies"],
        "Supplier Management": ["Setup", "Changes", "Issues"]
    },
    SupportDepartment.HR_PT: {
        "Contracts": ["Core", "Non-Core", "AC", "Subcontractor"],
        "Amendments": ["Extension", "Secondment", "Variation"],
        "Change Log": ["Role", "Salary", "Probation", "Line Manager"],
        "Leave": ["Requests", "Reversals", "Balances"],
        "Onboarding": ["New Starter", "Documentation", "Access"]
    },
    SupportDepartment.IT: {
        "Access": ["Login", "MFA", "Email"],
        "Device Compliance": ["Intune", "Encryption", "Company Portal"],
        "Software/OS": ["Updates", "Patches", "Installation"],
        "Integrations": ["SharePoint", "Teams", "Third Party"],
        "Infrastructure": ["Network", "Servers", "Security"]
    },
    SupportDepartment.OS_SUPPORT: {
        "General Support": ["How-to", "Training", "Documentation"],
        "Process Issues": ["Workflow", "Approval", "System"],
        "Data Issues": ["Reporting", "Export", "Import"],
        "User Management": ["Access", "Permissions", "Roles"]
    },
    SupportDepartment.DEVOPS: {
        "Deployment": ["Production", "Staging", "Testing"],
        "Infrastructure": ["Monitoring", "Scaling", "Performance"],
        "CI/CD": ["Pipeline", "Build", "Release"],
        "Security": ["Vulnerabilities", "Compliance", "Access"]
    }
}

async def categorize_ticket_with_ai(subject: str, description: str) -> Dict[str, str]:
    """Use AI to categorize tickets automatically"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"categorization-{uuid.uuid4()}",
            system_message="""You are an expert ticket categorization system. Based on the subject and description, 
            categorize the ticket into the appropriate department, category, and sub-category.
            
            Departments:
            - User & Access Management: login, MFA, account lifecycle, onboarding/offboarding, permissions
            - Contracts & Change Log: core staff, non-core, consultants, subcontractors, amendments, salary/role updates
            - Finance & Purchasing: PO creation/amendment/approvals, AP invoices, supplier invoices, Sage sync failures, expense logs, petty cash
            - Project & Performance: project setup, appraisals, training, compliance
            - Leave & People Management: leave requests, reversals, balances, people directory issues, onboarding verification
            - System & IT Support: device compliance, email/Outlook, Mac/Windows updates, integrations, technical debt, bug reports
            - Knowledge Base Requests: how-to guidance, policies, training material
            
            Respond with a JSON object containing department, category, and sub_category."""
        ).with_model("openai", "gpt-5")
        
        user_message = UserMessage(
            text=f"Subject: {subject}\nDescription: {description}\n\nCategorize this ticket."
        )
        
        response = await chat.send_message(user_message)
        
        # Try to parse JSON response
        try:
            categorization = json.loads(response)
            return {
                "department": categorization.get("department", "System & IT Support"),
                "category": categorization.get("category", "General"),
                "sub_category": categorization.get("sub_category", "Other")
            }
        except json.JSONDecodeError:
            # Fallback categorization
            return {
                "department": "System & IT Support",
                "category": "General",
                "sub_category": "Other"
            }
    except Exception as e:
        logger.error(f"Error in AI categorization: {e}")
        return {
            "department": "System & IT Support",
            "category": "General",
            "sub_category": "Other"
        }

async def process_rag_query(message: str, document_ids: List[str], session_id: str) -> Dict[str, Any]:
    """Process RAG query using advanced semantic search"""
    try:
        # Get RAG system instance
        rag = get_rag_system(EMERGENT_LLM_KEY)
        
        # Use the advanced RAG system for semantic search and response generation
        result = await rag.generate_rag_response(message, session_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in RAG processing: {e}")
        return {
            "response": {
                "summary": "I apologize, but I encountered an error processing your request. Please try again or contact support.",
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

# API Routes
@api_router.get("/")
async def root():
    return {"message": "ASI AiHub - AI-Powered Knowledge Management Platform API"}

@api_router.post("/documents/reprocess-all")
async def reprocess_all_documents():
    """Reprocess all existing documents with RAG system"""
    try:
        documents = await db.documents.find().to_list(1000)
        processed_count = 0
        
        for doc in documents:
            # Skip if already processed
            if doc.get("processed", False):
                continue
                
            # Process document in background
            asyncio.create_task(process_document_with_rag(doc))
            processed_count += 1
        
        return {
            "message": f"Started reprocessing {processed_count} documents",
            "total_documents": len(documents),
            "reprocessed": processed_count
        }
        
    except Exception as e:
        logger.error(f"Error reprocessing documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to reprocess documents")

@api_router.post("/documents/fix-departments")
async def fix_document_departments():
    """Fix existing documents with old department names"""
    try:
        # Update all existing documents to Finance department and approved status
        result = await db.documents.update_many(
            {},  # All documents
            {
                "$set": {
                    "department": "Finance",
                    "approval_status": "approved",
                    "approved_by": "system_migration",
                    "approved_at": datetime.now(timezone.utc)
                }
            }
        )
        
        return {
            "message": f"Updated {result.modified_count} documents to Finance department",
            "modified_count": result.modified_count
        }
        
    except Exception as e:
        logger.error(f"Error fixing departments: {e}")
        raise HTTPException(status_code=500, detail="Failed to fix departments")

@api_router.put("/documents/{document_id}/approve")
async def approve_document(document_id: str, approved_by: str = "admin"):
    """Approve a document for inclusion in knowledge base"""
    try:
        # Update document approval status
        result = await db.documents.update_one(
            {"id": document_id},
            {
                "$set": {
                    "approval_status": DocumentStatus.APPROVED,
                    "approved_by": approved_by,
                    "approved_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get updated document and process with RAG
        document = await db.documents.find_one({"id": document_id})
        if document:
            asyncio.create_task(process_document_with_rag(document))
        
        return {"message": "Document approved and processing for knowledge base"}
        
    except Exception as e:
        logger.error(f"Error approving document: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve document")

@api_router.put("/documents/{document_id}/reject")
async def reject_document(document_id: str, notes: str = "", rejected_by: str = "admin"):
    """Reject a document"""
    try:
        result = await db.documents.update_one(
            {"id": document_id},
            {
                "$set": {
                    "approval_status": DocumentStatus.REJECTED,
                    "approved_by": rejected_by,
                    "approved_at": datetime.now(timezone.utc),
                    "notes": notes
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document rejected"}
        
    except Exception as e:
        logger.error(f"Error rejecting document: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject document")

@api_router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and remove from knowledge base"""
    try:
        # Get document info
        document = await db.documents.find_one({"id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Remove from vector database
        rag = get_rag_system(EMERGENT_LLM_KEY)
        rag.remove_document_chunks(document_id)
        
        # Delete file from disk
        try:
            import os
            if os.path.exists(document['file_path']):
                os.remove(document['file_path'])
        except Exception as e:
            logger.warning(f"Could not delete file {document['file_path']}: {e}")
        
        # Remove from database
        await db.documents.delete_one({"id": document_id})
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")

@api_router.get("/documents/{document_id}/download")
async def download_document(document_id: str):
    """Download a document file"""
    try:
        # Get document info
        document = await db.documents.find_one({"id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if file exists
        file_path = Path(document['file_path'])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            filename=document['original_name'],
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document: {e}")
        raise HTTPException(status_code=500, detail="Download failed")

# Document Management Routes
@api_router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    department: Optional[str] = Form(None),
    tags: Optional[str] = Form("")
):
    """Upload a document for RAG processing"""
    try:
        # Validate file type
        allowed_types = ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="File type not supported. Please upload PDF, TXT, or DOCX files.")
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create document record
        document = Document(
            filename=unique_filename,
            original_name=file.filename,
            file_path=str(file_path),
            mime_type=file.content_type,
            file_size=len(content),
            department=Department(department) if department else None,
            tags=tags.split(",") if tags else []
        )
        
        # Save to database
        await db.documents.insert_one(document.dict())
        
        return DocumentUploadResponse(
            id=document.id,
            filename=document.original_name,
            message="Document uploaded successfully and pending approval"
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document")

@api_router.get("/documents", response_model=List[Document])
async def get_documents(
    department: Optional[Department] = None,
    approval_status: Optional[DocumentStatus] = None,
    show_all: bool = False
):
    """Get documents with optional filtering"""
    query = {}
    
    # For regular users, only show approved documents by default
    if not show_all:
        query["approval_status"] = DocumentStatus.APPROVED
    
    if department:
        query["department"] = department
    if approval_status:
        query["approval_status"] = approval_status
    
    documents = await db.documents.find(query).to_list(1000)
    return [Document(**doc) for doc in documents]

@api_router.get("/documents/admin", response_model=List[Document])
async def get_documents_admin():
    """Get all documents for admin review"""
    documents = await db.documents.find().sort("uploaded_at", -1).to_list(1000)
    return [Document(**doc) for doc in documents]

@api_router.get("/documents/rag-stats")
async def get_rag_stats():
    """Get RAG system statistics"""
    try:
        rag = get_rag_system(EMERGENT_LLM_KEY)
        stats = rag.get_collection_stats()
        
        # Get processing status from database
        processing_stats = await db.documents.aggregate([
            {"$group": {"_id": "$processing_status", "count": {"$sum": 1}}}
        ]).to_list(None)
        
        processing_counts = {item["_id"]: item["count"] for item in processing_stats}
        
        return {
            "vector_database": stats,
            "processing_status": processing_counts,
            "total_documents": await db.documents.count_documents({}),
            "processed_documents": await db.documents.count_documents({"processed": True})
        }
    except Exception as e:
        logger.error(f"Error getting RAG stats: {e}")
        return {
            "vector_database": {"total_chunks": 0, "unique_documents": 0},
            "processing_status": {},
            "total_documents": 0,
            "processed_documents": 0
        }

# Chat Routes
@api_router.post("/chat/send", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    """Send a message to RAG chat system"""
    try:
        # Process RAG query
        result = await process_rag_query(request.message, request.document_ids, request.session_id)
        
        # Save user message
        user_message = ChatMessage(
            session_id=request.session_id,
            role="user",
            content=request.message,
            attachments=request.document_ids
        )
        await db.chat_messages.insert_one(user_message.dict())
        
        # Save AI response (convert structured response to JSON string for storage)
        ai_message = ChatMessage(
            session_id=request.session_id,
            role="assistant",
            content=json.dumps(result["response"]) if isinstance(result["response"], dict) else result["response"]
        )
        await db.chat_messages.insert_one(ai_message.dict())
        
        # Update or create chat session
        session_exists = await db.chat_sessions.find_one({"id": request.session_id})
        if not session_exists:
            session = ChatSession(
                id=request.session_id,
                title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
                messages_count=2
            )
            await db.chat_sessions.insert_one(session.dict())
        else:
            await db.chat_sessions.update_one(
                {"id": request.session_id},
                {
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                    "$inc": {"messages_count": 2}
                }
            )
        
        return ChatResponse(
            session_id=request.session_id,
            response=result["response"],
            suggested_ticket=result["suggested_ticket"],
            documents_referenced=result.get("documents_referenced", 0),
            response_type=result.get("response_type", "structured")
        )
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")

@api_router.get("/chat/sessions", response_model=List[ChatSession])
async def get_chat_sessions():
    """Get all chat sessions"""
    sessions = await db.chat_sessions.find().sort("updated_at", -1).to_list(100)
    return [ChatSession(**session) for session in sessions]

@api_router.get("/chat/sessions/{session_id}/messages", response_model=List[ChatMessage])
async def get_chat_messages(session_id: str):
    """Get messages for a specific chat session"""
    messages = await db.chat_messages.find({"session_id": session_id}).sort("timestamp", 1).to_list(1000)
    return [ChatMessage(**message) for message in messages]

@api_router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session and all its messages"""
    try:
        # Delete all messages for this session
        messages_result = await db.chat_messages.delete_many({"session_id": session_id})
        
        # Delete the session
        session_result = await db.chat_sessions.delete_one({"id": session_id})
        
        if session_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return {
            "message": "Chat session deleted successfully",
            "messages_deleted": messages_result.deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat session")

@api_router.delete("/chat/sessions")
async def delete_all_chat_sessions():
    """Delete all chat sessions and messages"""
    try:
        # Delete all messages
        messages_result = await db.chat_messages.delete_many({})
        
        # Delete all sessions
        sessions_result = await db.chat_sessions.delete_many({})
        
        return {
            "message": "All chat sessions deleted successfully",
            "sessions_deleted": sessions_result.deleted_count,
            "messages_deleted": messages_result.deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error deleting all chat sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat sessions")

# Enhanced Ticket Routes
@api_router.post("/tickets", response_model=Ticket)
async def create_ticket(ticket_data: TicketCreate):
    """Create a new support ticket"""
    try:
        # Auto-categorize with AI
        categorization = await categorize_ticket_with_ai(ticket_data.subject, ticket_data.description)
        
        created_at = datetime.now(timezone.utc)
        ticket = Ticket(
            subject=ticket_data.subject,
            description=ticket_data.description,
            department=ticket_data.department,
            priority=ticket_data.priority,
            category=categorization["category"],
            sub_category=categorization["sub_category"],
            requester_name=ticket_data.requester_name,
            tags=ticket_data.tags,
            sla_due=calculate_sla_due(ticket_data.priority, created_at),
            created_at=created_at
        )
        
        await db.tickets.insert_one(ticket.dict())
        
        # Create initial comment
        initial_comment = TicketComment(
            ticket_id=ticket.id,
            content=f"Ticket created by {ticket_data.requester_name}",
            comment_type=CommentType.INTERNAL,
            author_name="System"
        )
        await db.ticket_comments.insert_one(initial_comment.dict())
        
        return ticket
        
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ticket")

@api_router.get("/tickets", response_model=List[Ticket])
async def get_tickets(
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    department: Optional[Department] = None,
    assigned_to: Optional[str] = None
):
    """Get all tickets with optional filtering"""
    query = {}
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if department:
        query["department"] = department
    if assigned_to:
        query["assigned_to"] = assigned_to
    
    tickets = await db.tickets.find(query).sort("created_at", -1).to_list(1000)
    return [Ticket(**ticket) for ticket in tickets]

@api_router.get("/tickets/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: str):
    """Get a specific ticket"""
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return Ticket(**ticket)

@api_router.put("/tickets/{ticket_id}", response_model=Ticket)
async def update_ticket(ticket_id: str, update_data: TicketUpdate):
    """Update a ticket"""
    try:
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        # Handle status transitions
        if update_data.status:
            if update_data.status == TicketStatus.RESOLVED:
                update_dict["resolved_at"] = datetime.now(timezone.utc)
            elif update_data.status == TicketStatus.CLOSED:
                update_dict["closed_at"] = datetime.now(timezone.utc)
        
        result = await db.tickets.update_one(
            {"id": ticket_id},
            {"$set": update_dict}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Add status change comment
        if update_data.status:
            status_comment = TicketComment(
                ticket_id=ticket_id,
                content=f"Status changed to {update_data.status}",
                comment_type=CommentType.INTERNAL,
                author_name="System"
            )
            await db.ticket_comments.insert_one(status_comment.dict())
        
        updated_ticket = await db.tickets.find_one({"id": ticket_id})
        return Ticket(**updated_ticket)
        
    except Exception as e:
        logger.error(f"Error updating ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to update ticket")

# Ticket Comments Routes
@api_router.post("/tickets/{ticket_id}/comments", response_model=TicketComment)
async def add_ticket_comment(ticket_id: str, comment_data: CommentCreate):
    """Add a comment to a ticket"""
    try:
        # Verify ticket exists
        ticket = await db.tickets.find_one({"id": ticket_id})
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        comment = TicketComment(
            ticket_id=ticket_id,
            content=comment_data.content,
            comment_type=comment_data.comment_type,
            author_name=comment_data.author_name
        )
        
        await db.ticket_comments.insert_one(comment.dict())
        
        # Update ticket's updated_at timestamp
        await db.tickets.update_one(
            {"id": ticket_id},
            {"$set": {"updated_at": datetime.now(timezone.utc)}}
        )
        
        return comment
        
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to add comment")

@api_router.get("/tickets/{ticket_id}/comments", response_model=List[TicketComment])
async def get_ticket_comments(ticket_id: str):
    """Get all comments for a ticket"""
    comments = await db.ticket_comments.find({"ticket_id": ticket_id}).sort("created_at", 1).to_list(1000)
    return [TicketComment(**comment) for comment in comments]

# Finance SOP Routes
@api_router.post("/finance-sop", response_model=FinanceSOP)
async def create_finance_sop(month: str, year: int):
    """Create a new Finance SOP cycle"""
    try:
        sop = FinanceSOP(month=month, year=year)
        await db.finance_sops.insert_one(sop.dict())
        return sop
    except Exception as e:
        logger.error(f"Error creating Finance SOP: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Finance SOP")

@api_router.get("/finance-sop", response_model=List[FinanceSOP])
async def get_finance_sops():
    """Get all Finance SOP cycles"""
    sops = await db.finance_sops.find().sort("created_at", -1).to_list(100)
    return [FinanceSOP(**sop) for sop in sops]

@api_router.put("/finance-sop/{sop_id}", response_model=FinanceSOP)
async def update_finance_sop(sop_id: str, update_data: FinanceSOPUpdate):
    """Update Finance SOP progress"""
    try:
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        result = await db.finance_sops.update_one(
            {"id": sop_id},
            {"$set": update_dict}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Finance SOP not found")
        
        updated_sop = await db.finance_sops.find_one({"id": sop_id})
        return FinanceSOP(**updated_sop)
        
    except Exception as e:
        logger.error(f"Error updating Finance SOP: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Finance SOP")

# Dashboard/Analytics Routes
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        total_tickets = await db.tickets.count_documents({})
        open_tickets = await db.tickets.count_documents({"status": {"$in": ["open", "in_progress", "waiting_customer"]}})
        resolved_tickets = await db.tickets.count_documents({"status": "resolved"})
        overdue_tickets = await db.tickets.count_documents({
            "sla_due": {"$lt": datetime.now(timezone.utc)},
            "status": {"$nin": ["resolved", "closed"]}
        })
        total_documents = await db.documents.count_documents({})
        total_chat_sessions = await db.chat_sessions.count_documents({})
        
        # Tickets by department
        pipeline = [
            {"$group": {"_id": "$department", "count": {"$sum": 1}}}
        ]
        tickets_by_dept = await db.tickets.aggregate(pipeline).to_list(None)
        
        # Tickets by status
        status_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        tickets_by_status = await db.tickets.aggregate(status_pipeline).to_list(None)
        
        # Tickets by priority
        priority_pipeline = [
            {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
        ]
        tickets_by_priority = await db.tickets.aggregate(priority_pipeline).to_list(None)
        
        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "resolved_tickets": resolved_tickets,
            "overdue_tickets": overdue_tickets,
            "total_documents": total_documents,
            "total_chat_sessions": total_chat_sessions,
            "tickets_by_department": tickets_by_dept,
            "tickets_by_status": tickets_by_status,
            "tickets_by_priority": tickets_by_priority
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard stats")

# BOOST Ticketing System API Routes

# Business Units Management
@api_router.post("/boost/business-units", response_model=BusinessUnit)
async def create_business_unit(unit_data: BusinessUnitCreate):
    """Create a new business unit"""
    try:
        unit = BusinessUnit(**unit_data.dict())
        await db.boost_business_units.insert_one(unit.dict())
        return unit
    except Exception as e:
        logger.error(f"Error creating business unit: {e}")
        raise HTTPException(status_code=500, detail="Failed to create business unit")

@api_router.get("/boost/business-units", response_model=List[BusinessUnit])
async def get_business_units():
    """Get all business units"""
    try:
        units = await db.boost_business_units.find().to_list(1000)
        return [BusinessUnit(**unit) for unit in units]
    except Exception as e:
        logger.error(f"Error fetching business units: {e}")
        return []

@api_router.put("/boost/business-units/{unit_id}", response_model=BusinessUnit)
async def update_business_unit(unit_id: str, unit_data: BusinessUnitCreate):
    """Update a business unit"""
    try:
        result = await db.boost_business_units.update_one(
            {"id": unit_id},
            {"$set": unit_data.dict()}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Business unit not found")
        
        updated_unit = await db.boost_business_units.find_one({"id": unit_id})
        return BusinessUnit(**updated_unit)
    except Exception as e:
        logger.error(f"Error updating business unit: {e}")
        raise HTTPException(status_code=500, detail="Failed to update business unit")

@api_router.delete("/boost/business-units/{unit_id}")
async def delete_business_unit(unit_id: str):
    """Delete a business unit"""
    try:
        result = await db.boost_business_units.delete_one({"id": unit_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Business unit not found")
        return {"message": "Business unit deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting business unit: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete business unit")

# BOOST Users Management
@api_router.post("/boost/users", response_model=BoostUser)
async def create_boost_user(user_data: BoostUserCreate):
    """Create a new BOOST user"""
    try:
        # Get business unit name if provided
        business_unit_name = None
        if user_data.business_unit_id:
            unit = await db.boost_business_units.find_one({"id": user_data.business_unit_id})
            if unit:
                business_unit_name = unit["name"]
        
        user = BoostUser(
            **user_data.dict(),
            business_unit_name=business_unit_name
        )
        await db.boost_users.insert_one(user.dict())
        return user
    except Exception as e:
        logger.error(f"Error creating BOOST user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

@api_router.get("/boost/users", response_model=List[BoostUser])
async def get_boost_users():
    """Get all BOOST users"""
    try:
        users = await db.boost_users.find().to_list(1000)
        return [BoostUser(**user) for user in users]
    except Exception as e:
        logger.error(f"Error fetching BOOST users: {e}")
        return []

@api_router.put("/boost/users/{user_id}", response_model=BoostUser)
async def update_boost_user(user_id: str, update_data: BoostUserUpdate):
    """Update a BOOST user"""
    try:
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        
        # Update business unit name if business_unit_id changed
        if "business_unit_id" in update_dict and update_dict["business_unit_id"]:
            unit = await db.boost_business_units.find_one({"id": update_dict["business_unit_id"]})
            if unit:
                update_dict["business_unit_name"] = unit["name"]
        elif "business_unit_id" in update_dict and not update_dict["business_unit_id"]:
            update_dict["business_unit_name"] = None
        
        result = await db.boost_users.update_one(
            {"id": user_id},
            {"$set": update_dict}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        updated_user = await db.boost_users.find_one({"id": user_id})
        return BoostUser(**updated_user)
    except Exception as e:
        logger.error(f"Error updating BOOST user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

@api_router.delete("/boost/users/{user_id}")
async def delete_boost_user(user_id: str):
    """Delete a BOOST user"""
    try:
        result = await db.boost_users.delete_one({"id": user_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting BOOST user: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")

# BOOST Tickets
@api_router.post("/boost/tickets", response_model=BoostTicket)
async def create_boost_ticket(ticket_data: BoostTicketCreate):
    """Create a new BOOST ticket"""
    try:
        # Auto-prefix subject
        prefixed_subject = auto_prefix_subject(
            ticket_data.support_department,
            ticket_data.category,
            ticket_data.subject
        )
        
        # Calculate SLA due date
        created_at = datetime.now(timezone.utc)
        due_at = calculate_boost_sla_due(ticket_data.priority, created_at)
        
        # Get business unit name if provided
        business_unit_name = None
        if ticket_data.business_unit_id:
            unit = await db.boost_business_units.find_one({"id": ticket_data.business_unit_id})
            if unit:
                business_unit_name = unit["name"]
        
        # Create ticket data dict and update with calculated values
        ticket_dict = ticket_data.dict()
        ticket_dict.update({
            "subject": prefixed_subject,
            "created_at": created_at,
            "updated_at": created_at,
            "due_at": due_at,
            "business_unit_name": business_unit_name,
            "requester_id": "default_user"  # For MVP
        })
        
        ticket = BoostTicket(**ticket_dict)
        
        await db.boost_tickets.insert_one(ticket.dict())
        return ticket
        
    except Exception as e:
        logger.error(f"Error creating BOOST ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ticket")

@api_router.get("/boost/tickets", response_model=List[BoostTicket])
async def get_boost_tickets(
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    support_department: Optional[SupportDepartment] = None,
    business_unit_id: Optional[str] = None,
    requester_id: Optional[str] = None,
    owner_id: Optional[str] = None,
    search: Optional[str] = None
):
    """Get BOOST tickets with optional filtering"""
    try:
        query = {}
        
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority
        if support_department:
            query["support_department"] = support_department
        if business_unit_id:
            query["business_unit_id"] = business_unit_id
        if requester_id:
            query["requester_id"] = requester_id
        if owner_id:
            query["owner_id"] = owner_id
        if search:
            query["$or"] = [
                {"subject": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        tickets = await db.boost_tickets.find(query).sort("created_at", -1).to_list(1000)
        return [BoostTicket(**ticket) for ticket in tickets]
        
    except Exception as e:
        logger.error(f"Error fetching BOOST tickets: {e}")
        return []

@api_router.get("/boost/tickets/{ticket_id}", response_model=BoostTicket)
async def get_boost_ticket(ticket_id: str):
    """Get a specific BOOST ticket"""
    try:
        ticket = await db.boost_tickets.find_one({"id": ticket_id})
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return BoostTicket(**ticket)
    except Exception as e:
        logger.error(f"Error fetching BOOST ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ticket")

@api_router.put("/boost/tickets/{ticket_id}", response_model=BoostTicket)
async def update_boost_ticket(ticket_id: str, update_data: BoostTicketUpdate):
    """Update a BOOST ticket"""
    try:
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        # Handle status transitions
        if update_data.status:
            if update_data.status == TicketStatus.RESOLVED:
                update_dict["resolved_at"] = datetime.now(timezone.utc)
            elif update_data.status == TicketStatus.CLOSED:
                update_dict["closed_at"] = datetime.now(timezone.utc)
        
        result = await db.boost_tickets.update_one(
            {"id": ticket_id},
            {"$set": update_dict}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        updated_ticket = await db.boost_tickets.find_one({"id": ticket_id})
        return BoostTicket(**updated_ticket)
        
    except Exception as e:
        logger.error(f"Error updating BOOST ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to update ticket")

# BOOST Comments
@api_router.post("/boost/tickets/{ticket_id}/comments", response_model=BoostComment)
async def add_boost_comment(ticket_id: str, comment_data: BoostCommentCreate):
    """Add a comment to a BOOST ticket"""
    try:
        # Verify ticket exists
        ticket = await db.boost_tickets.find_one({"id": ticket_id})
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        comment = BoostComment(
            ticket_id=ticket_id,
            **comment_data.dict(),
            author_id="default_user"  # For MVP
        )
        
        await db.boost_comments.insert_one(comment.dict())
        
        # Update ticket's updated_at timestamp
        await db.boost_tickets.update_one(
            {"id": ticket_id},
            {"$set": {"updated_at": datetime.now(timezone.utc)}}
        )
        
        return comment
        
    except Exception as e:
        logger.error(f"Error adding BOOST comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to add comment")

@api_router.get("/boost/tickets/{ticket_id}/comments", response_model=List[BoostComment])
async def get_boost_comments(ticket_id: str, include_internal: bool = True):
    """Get comments for a BOOST ticket"""
    try:
        query = {"ticket_id": ticket_id}
        if not include_internal:
            query["is_internal"] = False
        
        comments = await db.boost_comments.find(query).sort("created_at", 1).to_list(1000)
        return [BoostComment(**comment) for comment in comments]
    except Exception as e:
        logger.error(f"Error fetching BOOST comments: {e}")
        return []

# BOOST Categories
@api_router.get("/boost/categories")
async def get_boost_categories():
    """Get BOOST categorization data"""
    return BOOST_CATEGORIES

@api_router.get("/boost/categories/{department}")
async def get_department_categories(department: SupportDepartment):
    """Get categories for a specific department"""
    return BOOST_CATEGORIES.get(department, {})

# BOOST Ticket Attachments
class BoostAttachment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    original_name: str
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

@api_router.post("/boost/tickets/{ticket_id}/attachments")
async def upload_ticket_attachment(
    ticket_id: str,
    file: UploadFile = File(...),
    uploaded_by: str = Form(...),
):
    """Upload file attachment to ticket"""
    try:
        # Validate file size (10MB limit)
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
        
        # Validate file type
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'image/jpeg',
            'image/png',
            'image/jpg'
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="File type not allowed")
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads/attachments")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = upload_dir / unique_filename
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Create attachment record
        attachment = BoostAttachment(
            ticket_id=ticket_id,
            original_name=file.filename,
            file_name=unique_filename,
            file_path=str(file_path),
            file_size=file_size,
            mime_type=file.content_type,
            uploaded_by=uploaded_by
        )
        
        # Save to database
        await db.boost_attachments.insert_one(attachment.dict())
        
        # Update ticket updated_at timestamp
        await db.boost_tickets.update_one(
            {"id": ticket_id},
            {"$set": {"updated_at": datetime.now(timezone.utc)}}
        )
        
        return attachment.dict()
        
    except Exception as e:
        logging.error(f"Error uploading attachment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@api_router.get("/boost/tickets/{ticket_id}/attachments")
async def get_ticket_attachments(ticket_id: str):
    """Get all attachments for a ticket"""
    try:
        attachments = await db.boost_attachments.find(
            {"ticket_id": ticket_id}
        ).to_list(length=None)
        
        for attachment in attachments:
            attachment['_id'] = str(attachment['_id'])
            
        return attachments
    except Exception as e:
        logging.error(f"Error fetching attachments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch attachments")

@api_router.get("/boost/tickets/{ticket_id}/attachments/{attachment_id}")
async def download_attachment(ticket_id: str, attachment_id: str):
    """Download a specific attachment"""
    try:
        attachment = await db.boost_attachments.find_one(
            {"id": attachment_id, "ticket_id": ticket_id}
        )
        
        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")
        
        file_path = Path(attachment['file_path'])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            filename=attachment['original_name'],
            media_type=attachment['mime_type']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error downloading attachment: {str(e)}")
        raise HTTPException(status_code=500, detail="Download failed")

@api_router.delete("/boost/tickets/{ticket_id}/attachments/{attachment_id}")
async def delete_attachment(ticket_id: str, attachment_id: str):
    """Delete a specific attachment"""
    try:
        attachment = await db.boost_attachments.find_one(
            {"id": attachment_id, "ticket_id": ticket_id}
        )
        
        if not attachment:
            raise HTTPException(status_code=404, detail="Attachment not found")
        
        # Delete file from disk
        file_path = Path(attachment['file_path'])
        if file_path.exists():
            file_path.unlink()
        
        # Delete from database
        await db.boost_attachments.delete_one(
            {"id": attachment_id, "ticket_id": ticket_id}
        )
        
        return {"message": "Attachment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting attachment: {str(e)}")
        raise HTTPException(status_code=500, detail="Delete failed")

# BOOST Audit Trail
@api_router.get("/boost/tickets/{ticket_id}/audit")
async def get_ticket_audit_trail(ticket_id: str):
    """Get comprehensive audit trail for a ticket"""
    try:
        # Get ticket details
        ticket = await db.boost_tickets.find_one({"id": ticket_id})
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Get comments
        comments = await db.boost_comments.find({"ticket_id": ticket_id}).to_list(length=None)
        
        # Get attachments
        attachments = await db.boost_attachments.find({"ticket_id": ticket_id}).to_list(length=None)
        
        # Build comprehensive audit trail
        trail = []
        
        # Ticket creation
        trail.append({
            "id": str(uuid.uuid4()),
            "action": "created",
            "description": f"Ticket created by {ticket['requester_name']}",
            "user_name": ticket['requester_name'],
            "timestamp": ticket['created_at'],
            "details": f"Priority: {ticket['priority'].upper()}, Department: {ticket['support_department']}, Category: {ticket['category']}"
        })
        
        # Assignment
        if ticket.get('owner_name'):
            trail.append({
                "id": str(uuid.uuid4()),
                "action": "assigned",
                "description": f"Assigned to {ticket['owner_name']}",
                "user_name": "System",
                "timestamp": ticket['updated_at'],
                "details": f"Owner: {ticket['owner_name']} ({ticket['support_department']})"
            })
        
        # Status changes
        if ticket['status'] != 'open':
            trail.append({
                "id": str(uuid.uuid4()),
                "action": "status_changed", 
                "description": f"Status changed to {ticket['status'].replace('_', ' ')}",
                "user_name": ticket.get('owner_name', 'System'),
                "timestamp": ticket['updated_at'],
                "details": f"New status: {ticket['status'].upper().replace('_', ' ')}"
            })
        
        # Comments
        for comment in comments:
            trail.append({
                "id": str(uuid.uuid4()),
                "action": "comment_added",
                "description": "Internal comment added" if comment['is_internal'] else "Comment added",
                "user_name": comment['author_name'],
                "timestamp": comment['created_at'],
                "details": comment['body'][:100] + ('...' if len(comment['body']) > 100 else '')
            })
        
        # Attachments
        for attachment in attachments:
            trail.append({
                "id": str(uuid.uuid4()),
                "action": "attachment_added",
                "description": f"File attached: {attachment['original_name']}",
                "user_name": attachment['uploaded_by'],
                "timestamp": attachment['uploaded_at'],
                "details": f"File: {attachment['original_name']} ({attachment['file_size']} bytes)"
            })
        
        # SLA breach check
        if ticket.get('due_at'):
            due_date = ticket['due_at']
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            
            if due_date < datetime.now(timezone.utc) and ticket['status'] not in ['resolved', 'closed']:
                trail.append({
                    "id": str(uuid.uuid4()),
                    "action": "sla_breach",
                    "description": "SLA deadline exceeded",
                    "user_name": "System",
                    "timestamp": due_date,
                    "details": f"Due date: {due_date.isoformat()}"
                })
        
        # Sort by timestamp (newest first)
        trail.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return trail
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching audit trail: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch audit trail")

# Beta Authentication System Models
class BetaUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    personal_code: str
    role: str = "User"  # Admin, Manager, Agent, User
    department: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

class BetaSettings(BaseModel):
    registration_code: str
    admin_email: str = "layth.bunni@adamsmithinternational.com"
    allowed_domain: str = "adamsmithinternational.com"
    max_users: int = 20
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RegistrationRequest(BaseModel):
    email: str
    registration_code: str
    personal_code: str
    department: Optional[str] = None

class LoginRequest(BaseModel):
    email: str  
    personal_code: str

class LoginResponse(BaseModel):
    access_token: str
    user: BetaUser

# Beta Authentication Helper
security = HTTPBearer()

def generate_access_token(user_id: str, email: str) -> str:
    """Generate a simple access token"""
    # In production, use proper JWT tokens
    token_data = f"{user_id}:{email}:{datetime.now(timezone.utc).timestamp()}"
    return hashlib.sha256(token_data.encode()).hexdigest()

def validate_email_domain(email: str) -> bool:
    """Validate email domain"""
    domain = email.split('@')[-1].lower()
    return domain == "adamsmithinternational.com"

def validate_email_format(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> BetaUser:
    """Get current user from token"""
    try:
        token = credentials.credentials
        # Simple token validation - in production use proper JWT
        
        # For now, extract user info from token
        # This is a simplified implementation
        users = await db.beta_users.find().to_list(length=None)
        for user in users:
            expected_token = generate_access_token(user['id'], user['email'])
            if expected_token == token:
                return BetaUser(**user)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

async def require_admin(current_user: BetaUser = Depends(get_current_user)) -> BetaUser:
    """Require admin role"""
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Beta Authentication Endpoints
@api_router.post("/auth/register", response_model=LoginResponse)
async def register_user(request: RegistrationRequest):
    """Register new beta user"""
    try:
        # Validate email format
        if not validate_email_format(request.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Validate email domain
        if not validate_email_domain(request.email):
            raise HTTPException(status_code=400, detail="Only adamsmithinternational.com emails allowed")
        
        # Check if user already exists
        existing_user = await db.beta_users.find_one({"email": request.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="User already registered")
        
        # Validate registration code
        settings = await db.beta_settings.find_one({})
        if not settings or settings.get('registration_code') != request.registration_code:
            raise HTTPException(status_code=400, detail="Invalid registration code")
        
        # Check user limit
        user_count = await db.beta_users.count_documents({"is_active": True})
        if user_count >= settings.get('max_users', 20):
            raise HTTPException(status_code=400, detail="Beta user limit reached")
        
        # Validate personal code
        if len(request.personal_code) < 6:
            raise HTTPException(status_code=400, detail="Personal code must be at least 6 characters")
        
        # Create new user
        new_user = BetaUser(
            email=request.email,
            personal_code=hashlib.sha256(request.personal_code.encode()).hexdigest(),
            department=request.department,
            role="Manager" if request.email == "layth.bunni@adamsmithinternational.com" else "User"
        )
        
        # Save to database
        await db.beta_users.insert_one(new_user.dict())
        
        # Generate access token
        access_token = generate_access_token(new_user.id, new_user.email)
        
        # Return response without password hash
        user_response = new_user.copy()
        user_response.personal_code = "***"
        
        return LoginResponse(access_token=access_token, user=user_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/auth/login", response_model=LoginResponse)
async def login_user(request: LoginRequest):
    """Login beta user"""
    try:
        # Find user
        user_data = await db.beta_users.find_one({"email": request.email})
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid email or personal code")
        
        user = BetaUser(**user_data)
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(status_code=401, detail="User account is inactive")
        
        # Validate personal code
        hashed_code = hashlib.sha256(request.personal_code.encode()).hexdigest()
        if user.personal_code != hashed_code:
            raise HTTPException(status_code=401, detail="Invalid email or personal code")
        
        # Update last login
        await db.beta_users.update_one(
            {"id": user.id},
            {"$set": {"last_login": datetime.now(timezone.utc)}}
        )
        
        # Generate access token
        access_token = generate_access_token(user.id, user.email)
        
        # Return response without password hash
        user_response = user.copy()
        user_response.personal_code = "***"
        
        return LoginResponse(access_token=access_token, user=user_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@api_router.get("/auth/me", response_model=BetaUser)
async def get_current_user_info(current_user: BetaUser = Depends(get_current_user)):
    """Get current user information"""
    user_response = current_user.copy()
    user_response.personal_code = "***"
    return user_response

@api_router.get("/auth/settings")
async def get_auth_settings(admin_user: BetaUser = Depends(require_admin)):
    """Get authentication settings (admin only)"""
    settings = await db.beta_settings.find_one({})
    if not settings:
        return {
            "registration_code": "Not set",
            "allowed_domain": "adamsmithinternational.com",
            "max_users": 20,
            "current_users": await db.beta_users.count_documents({"is_active": True})
        }
    
    return {
        "registration_code": settings.get('registration_code', 'Not set'),
        "allowed_domain": settings.get('allowed_domain', 'adamsmithinternational.com'),
        "max_users": settings.get('max_users', 20),
        "current_users": await db.beta_users.count_documents({"is_active": True})
    }

@api_router.post("/auth/settings/registration-code")
async def update_registration_code(
    new_code: dict,
    admin_user: BetaUser = Depends(require_admin)
):
    """Update registration code (admin only)"""
    try:
        registration_code = new_code.get('registration_code', '').strip()
        
        if len(registration_code) < 8:
            raise HTTPException(status_code=400, detail="Registration code must be at least 8 characters")
        
        # Update or create settings
        await db.beta_settings.update_one(
            {},
            {
                "$set": {
                    "registration_code": registration_code,
                    "admin_email": admin_user.email,
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        
        return {"message": "Registration code updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating registration code: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update registration code")

@api_router.get("/auth/users")
async def list_beta_users(admin_user: BetaUser = Depends(require_admin)):
    """List all beta users (admin only)"""
    users = await db.beta_users.find().to_list(length=None)
    
    # Remove personal codes from response
    for user in users:
        user['personal_code'] = "***"
        user['_id'] = str(user['_id'])
    
    return users

@api_router.put("/auth/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role_data: dict,
    admin_user: BetaUser = Depends(require_admin)
):
    """Update user role (admin only)"""
    try:
        new_role = role_data.get('role')
        if new_role not in ['Admin', 'Manager', 'Agent', 'User']:
            raise HTTPException(status_code=400, detail="Invalid role")
        
        result = await db.beta_users.update_one(
            {"id": user_id},
            {"$set": {"role": new_role}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User role updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user role: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update user role")

# Include the router in the main app
app.include_router(api_router)

# CORS setup
origins = [
    "http://localhost:3000",  # React development server
    "https://asi-aihub.preview.emergentagent.com",  # Production URL (if different)
    # Add other allowed origins here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()