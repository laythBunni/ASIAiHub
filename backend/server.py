from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
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

# Load environment variables FIRST
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import RAG system AFTER environment is loaded
from rag_system import get_rag_system

# MongoDB connection with MongoDB's recommended Stable API configuration
mongo_url = os.environ['MONGO_URL']

# Configure MongoDB client with Stable API (MongoDB's recommended approach)
if mongo_url.startswith('mongodb+srv://'):
    # Atlas connection using MongoDB's Stable API configuration
    client = AsyncIOMotorClient(
        mongo_url,
        server_api=ServerApi('1', strict=True, deprecation_errors=True),
        tlsAllowInvalidCertificates=False,  # Use valid certificates with Stable API
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
        maxPoolSize=10,
        retryWrites=True
    )
else:
    # Local MongoDB connection
    client = AsyncIOMotorClient(mongo_url)

db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="ASI AiHub - AI-Powered Knowledge Management Platform")

cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],  # Use environment variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add startup event to ensure all users have personal codes
@app.on_event("startup")
async def startup_event():
    """Run startup tasks"""
    await ensure_all_users_have_codes()

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
    conversation_session_id: Optional[str] = None  # For tickets created from chat conversations
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
    stream: bool = False  # Enable streaming response

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
    requester_id: str = "default_user"  # Add requester_id field
    business_unit_id: Optional[str] = None
    channel: TicketChannel = TicketChannel.HUB
    conversation_session_id: Optional[str] = None  # For tickets created from chat conversations

class BoostTicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolution_type: Optional[ResolutionType] = None
    updated_by: Optional[str] = None  # Add field to track who made the update

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

class BoostAuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    action: str  # "created", "status_changed", "priority_changed", "assigned", etc.
    description: str
    user_name: str
    user_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    active: Optional[bool] = None

# Utility Functions
async def process_document_with_rag(document_data: Dict[str, Any]) -> None:
    """Process document with RAG system in background with resilient error handling"""
    try:
        # Update processing status with timeout
        await asyncio.wait_for(
            db.documents.update_one(
                {"id": document_data["id"]},
                {"$set": {"processing_status": "processing"}}
            ),
            timeout=10.0
        )
        
        # Process with RAG system with timeout and graceful fallback
        try:
            async def rag_processing_with_timeout():
                try:
                    rag = get_rag_system(EMERGENT_LLM_KEY)
                    
                    # Add detailed logging
                    logger.info(f"🔥 RAG processing starting for document {document_data.get('id')}")
                    logger.info(f"🔥 File path: {document_data.get('file_path')}")
                    logger.info(f"🔥 MIME type: {document_data.get('mime_type')}")
                    
                    # Use async method directly (cleanest approach)
                    result = await rag.process_and_store_document_async(document_data)
                    
                    logger.info(f"🔥 RAG processing result: {result}")
                    return result
                    
                except Exception as rag_error:
                    logger.error(f"🔥 RAG processing exception: {rag_error}")
                    logger.error(f"🔥 Exception type: {type(rag_error).__name__}")
                    raise rag_error
            
            # 60 second timeout for RAG processing
            success = await asyncio.wait_for(rag_processing_with_timeout(), timeout=60.0)
            
            if success:
                # Get collection stats with timeout
                try:
                    async def get_stats_with_timeout():
                        rag = get_rag_system(EMERGENT_LLM_KEY)
                        return rag.get_collection_stats()
                    
                    stats = await asyncio.wait_for(get_stats_with_timeout(), timeout=10.0)
                    chunks_count = stats.get("total_chunks", 0) // max(stats.get("unique_documents", 1), 1)
                except asyncio.TimeoutError:
                    logger.warning(f"Stats timeout for document {document_data['original_name']}, using default")
                    chunks_count = 10  # Default reasonable value
                
                # Update document as processed
                await asyncio.wait_for(
                    db.documents.update_one(
                        {"id": document_data["id"]},
                        {
                            "$set": {
                                "processed": True,
                                "processing_status": "completed",
                                "chunks_count": chunks_count
                            }
                        }
                    ),
                    timeout=10.0
                )
                logger.info(f"Successfully processed document {document_data['original_name']}")
            else:
                # Mark as failed
                await asyncio.wait_for(
                    db.documents.update_one(
                        {"id": document_data["id"]},
                        {"$set": {"processing_status": "failed"}}
                    ),
                    timeout=10.0
                )
                logger.error(f"RAG processing failed for document {document_data['original_name']}")
        
        except asyncio.TimeoutError:
            # RAG processing timed out - mark with partial success
            await db.documents.update_one(
                {"id": document_data["id"]},
                {
                    "$set": {
                        "processed": True,  # Still mark as processed so it appears in search
                        "processing_status": "timeout", 
                        "chunks_count": 0,
                        "notes": "Processing timed out - document approved but not fully indexed"
                    }
                }
            )
            logger.warning(f"RAG processing timeout for document {document_data['original_name']} - marked as approved anyway")
        
    except Exception as e:
        # Any other error - mark as failed but don't crash
        try:
            await db.documents.update_one(
                {"id": document_data["id"]},
                {"$set": {"processing_status": "failed", "notes": f"Processing error: {str(e)[:100]}"}}
            )
        except:
            pass  # Don't crash if even the error update fails
        
        logger.error(f"Error processing document {document_data.get('original_name', 'unknown')}: {e}")

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
async def log_audit_entry(ticket_id: str, action: str, description: str, user_name: str, 
                         user_id: str = None, details: str = None, old_value: str = None, new_value: str = None):
    """Log an audit entry for a ticket"""
    try:
        audit_entry = BoostAuditEntry(
            ticket_id=ticket_id,
            action=action,
            description=description,
            user_name=user_name,
            user_id=user_id,
            details=details,
            old_value=old_value,
            new_value=new_value
        )
        await db.boost_audit_trail.insert_one(audit_entry.dict())
        logger.info(f"Audit entry logged: {action} for ticket {ticket_id} by {user_name}")
    except Exception as e:
        logger.error(f"Failed to log audit entry: {e}")
        # Don't raise exception to avoid breaking the main operation

def generate_personal_code():
    """Generate a random 6-digit personal code"""
    import random
    return f"{random.randint(100000, 999999):06d}"

async def ensure_all_users_have_codes():
    """Ensure all existing users have personal codes"""
    try:
        # Check beta_users collection
        beta_users_without_codes = await db.beta_users.find({"personal_code": {"$exists": False}}).to_list(length=None)
        for user in beta_users_without_codes:
            personal_code = generate_personal_code()
            await db.beta_users.update_one(
                {"id": user["id"]},
                {"$set": {"personal_code": personal_code}}
            )
            logger.info(f"Generated personal code for beta user: {user['email']}")
        
        # Check simple_users collection 
        simple_users_without_codes = await db.simple_users.find({"personal_code": {"$exists": False}}).to_list(length=None)
        for user in simple_users_without_codes:
            personal_code = generate_personal_code()
            await db.simple_users.update_one(
                {"id": user["id"]},
                {"$set": {"personal_code": personal_code}}
            )
            logger.info(f"Generated personal code for simple user: {user['email']}")
            
        logger.info("All users now have personal codes")
        
    except Exception as e:
        logger.error(f"Error ensuring users have codes: {e}")

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
    """Process RAG query using advanced semantic search with caching and model selection"""
    try:
        # Check cache first
        cache_result = await check_response_cache(message)
        if cache_result:
            logger.info(f"Cache hit for query: {message[:50]}...")
            return cache_result
        
        # Get system settings for AI model selection
        settings = await db.system_settings.find_one({"_id": "global"})
        ai_model = settings.get("ai_model", "gpt-5") if settings else "gpt-5"
        
        # Get RAG system instance
        rag = get_rag_system(EMERGENT_LLM_KEY)
        
        # Debug: Test search before RAG response
        logger.info(f"Testing RAG search for query: {message}")
        search_results = rag.search_similar_chunks(message, n_results=3)
        logger.info(f"RAG search returned {len(search_results)} results")
        if search_results:
            logger.info(f"Top result similarity: {search_results[0].get('similarity_score', 'N/A')}")
        
        # Use the advanced RAG system for semantic search and response generation
        result = await rag.generate_rag_response(message, session_id, ai_model=ai_model)
        
        # Cache the result
        await cache_response(message, result)
        
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

async def check_response_cache(message: str) -> Dict[str, Any]:
    """Check if we have a cached response for this message"""
    try:
        import hashlib
        message_hash = hashlib.md5(message.lower().strip().encode()).hexdigest()
        
        # Look for cached response within 24 hours
        cache_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        cached = await db.response_cache.find_one({
            "message_hash": message_hash,
            "created_at": {"$gte": cache_cutoff}
        })
        
        if cached:
            return cached["response"]
        return None
        
    except Exception as e:
        logger.error(f"Error checking response cache: {e}")
        return None

async def cache_response(message: str, response: Dict[str, Any]):
    """Cache a response for future use"""
    try:
        import hashlib
        message_hash = hashlib.md5(message.lower().strip().encode()).hexdigest()
        
        cache_entry = {
            "message_hash": message_hash,
            "original_message": message,
            "response": response,
            "created_at": datetime.now(timezone.utc)
        }
        
        # Upsert (update or insert)
        await db.response_cache.update_one(
            {"message_hash": message_hash},
            {"$set": cache_entry},
            upsert=True
        )
        
    except Exception as e:
        logger.error(f"Error caching response: {e}")

@api_router.get("/debug/test-embedding-generation") 
async def test_embedding_generation():
    """Test OpenAI embedding generation specifically"""
    try:
        result = {
            "timestamp": str(datetime.now(timezone.utc)),
            "test_status": "STARTING",
            "steps": []
        }
        
        # Test 1: Check EMERGENT_LLM_KEY
        emergent_key = os.environ.get('EMERGENT_LLM_KEY')
        if emergent_key:
            result["steps"].append({
                "step": "EMERGENT_KEY_CHECK",
                "status": "SUCCESS",
                "key_length": len(emergent_key),
                "key_prefix": emergent_key[:10] + "..." if len(emergent_key) > 10 else emergent_key
            })
        else:
            result["steps"].append({
                "step": "EMERGENT_KEY_CHECK", 
                "status": "FAILED",
                "error": "EMERGENT_LLM_KEY not found"
            })
            return result
            
        # Test 2: Initialize LlmChat
        try:
            from emergentintegrations.llm.chat import LlmChat
            chat = LlmChat(
                api_key=emergent_key,
                session_id="embedding-test",
                system_message="You are an embedding generator."
            )
            result["steps"].append({
                "step": "LLMCHAT_INITIALIZATION",
                "status": "SUCCESS"
            })
        except Exception as e:
            result["steps"].append({
                "step": "LLMCHAT_INITIALIZATION",
                "status": "FAILED", 
                "error": str(e)
            })
            return result
            
        # Test 3: Generate embedding using OpenAI directly with user's API key
        try:
            import openai
            test_text = "This is a simple test for embedding generation."
            
            openai_api_key = os.environ.get('OPENAI_API_KEY')
            if not openai_api_key:
                result["steps"].append({
                    "step": "EMBEDDING_GENERATION",
                    "status": "FAILED",
                    "error": "OPENAI_API_KEY not found in environment variables"
                })
            else:
                openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
                embedding_response = await asyncio.wait_for(
                    openai_client.embeddings.create(
                        input=test_text,
                        model="text-embedding-ada-002"
                    ),
                    timeout=30.0
                )
                
                embedding = embedding_response.data[0].embedding
                
                result["steps"].append({
                    "step": "EMBEDDING_GENERATION",
                    "status": "SUCCESS",
                    "method": "openai_direct_with_user_key",
                    "embedding_type": type(embedding).__name__,
                    "embedding_length": len(embedding),
                    "first_few_values": embedding[:3] if len(embedding) > 3 else embedding
                })
            
        except asyncio.TimeoutError:
            result["steps"].append({
                "step": "EMBEDDING_GENERATION",
                "status": "TIMEOUT",
                "error": "Embedding generation timed out after 30 seconds"
            })
        except Exception as e:
            result["steps"].append({
                "step": "EMBEDDING_GENERATION", 
                "status": "FAILED",
                "error": str(e)
            })
            
        # Test 4: Test MongoDB connection and write
        try:
            mongo_url = os.environ.get('MONGO_URL')
            db_name = os.environ.get('DB_NAME')
            client = AsyncIOMotorClient(mongo_url)
            database = client[db_name]
            
            # Use dummy embedding if embedding generation failed
            test_embedding = [0.1, 0.2, 0.3]  # Default dummy embedding
            
            # Check if we got a real embedding from the previous step
            if result["steps"] and result["steps"][-1].get("step") == "EMBEDDING_GENERATION":
                if result["steps"][-1].get("status") == "SUCCESS":
                    # We can't access the embedding variable here, so we'll use a success indicator
                    test_embedding = [0.5] * 1536  # Standard embedding size
            
            # Try to write a test document
            test_doc = {
                "test_id": "embedding_test_" + str(int(datetime.now().timestamp())),
                "text": "Test embedding storage",
                "embedding": test_embedding,
                "created_at": datetime.now(timezone.utc)
            }
            
            await database.document_chunks.insert_one(test_doc)
            
            result["steps"].append({
                "step": "MONGODB_WRITE_TEST",
                "status": "SUCCESS",
                "collection": "document_chunks"
            })
            
            # Verify the write
            stored_doc = await database.document_chunks.find_one({"test_id": test_doc["test_id"]})
            if stored_doc:
                result["steps"].append({
                    "step": "MONGODB_READ_VERIFICATION",
                    "status": "SUCCESS",
                    "document_found": True
                })
                
                # Clean up test document
                await database.document_chunks.delete_one({"test_id": test_doc["test_id"]})
            else:
                result["steps"].append({
                    "step": "MONGODB_READ_VERIFICATION", 
                    "status": "FAILED",
                    "document_found": False
                })
                
        except Exception as e:
            result["steps"].append({
                "step": "MONGODB_WRITE_TEST",
                "status": "FAILED",
                "error": str(e)
            })
            
        result["test_status"] = "COMPLETED"
        return result
        
    except Exception as e:
        return {
            "test_status": "CRITICAL_ERROR",
            "error": str(e),
            "timestamp": str(datetime.now(timezone.utc))
        }

@api_router.get("/debug/test-mongodb-rag-directly")
async def test_mongodb_rag_directly():
    """Direct test of MongoDB RAG system with a simple document"""
    try:
        result = {
            "timestamp": str(datetime.now(timezone.utc)),
            "test_status": "STARTING",
            "steps": []
        }
        
        # Step 1: Initialize RAG system
        try:
            rag = get_rag_system(EMERGENT_LLM_KEY)
            result["steps"].append({
                "step": "RAG_INITIALIZATION",
                "status": "SUCCESS",
                "rag_mode": getattr(rag, 'rag_mode', 'unknown')
            })
        except Exception as e:
            result["steps"].append({
                "step": "RAG_INITIALIZATION", 
                "status": "FAILED",
                "error": str(e)
            })
            return result
        
        # Step 2: Create test document data
        test_doc_data = {
            "id": "test-mongodb-rag-" + str(int(datetime.now().timestamp())),
            "original_name": "test_mongodb_rag.txt",
            "file_path": "/tmp/test_mongodb_rag.txt",
            "mime_type": "text/plain",
            "department": "Information Technology",
            "uploaded_at": datetime.now(timezone.utc)
        }
        
        # Create test file
        test_content = """
        MongoDB RAG Test Document
        
        This is a test document to verify that the MongoDB RAG system is working correctly.
        
        REQUIREMENTS:
        - Documents should be chunked properly
        - Chunks should be stored in MongoDB with embeddings
        - Search functionality should work
        
        PROCEDURES:
        1. Upload document
        2. Process and chunk document  
        3. Generate embeddings using OpenAI
        4. Store in document_chunks collection
        
        EXPECTED OUTCOME:
        This test should create chunks in MongoDB and enable search functionality.
        """
        
        import aiofiles
        async with aiofiles.open(test_doc_data["file_path"], 'w') as f:
            await f.write(test_content)
            
        result["steps"].append({
            "step": "TEST_FILE_CREATION",
            "status": "SUCCESS",
            "file_size": len(test_content)
        })
        
        # Step 3: Test MongoDB chunk storage directly
        try:
            chunks = rag._simple_text_splitter(test_content)
            result["steps"].append({
                "step": "TEXT_CHUNKING",
                "status": "SUCCESS", 
                "chunks_created": len(chunks),
                "sample_chunk": chunks[0][:100] + "..." if chunks else None
            })
            
            # Test MongoDB storage
            success = await rag._store_chunks_mongodb(test_doc_data["id"], chunks, test_doc_data)
            result["steps"].append({
                "step": "MONGODB_STORAGE",
                "status": "SUCCESS" if success else "FAILED",
                "chunks_stored": len(chunks) if success else 0
            })
            
        except Exception as e:
            result["steps"].append({
                "step": "MONGODB_STORAGE",
                "status": "FAILED",
                "error": str(e)
            })
        
        # Step 4: Verify chunks in database
        try:
            mongo_url = os.environ.get('MONGO_URL')
            db_name = os.environ.get('DB_NAME')
            client = AsyncIOMotorClient(mongo_url)
            database = client[db_name]
            
            chunk_count = await database.document_chunks.count_documents({"document_id": test_doc_data["id"]})
            
            if chunk_count > 0:
                sample_chunk = await database.document_chunks.find_one({"document_id": test_doc_data["id"]})
                result["steps"].append({
                    "step": "DATABASE_VERIFICATION",
                    "status": "SUCCESS",
                    "chunks_in_db": chunk_count,
                    "sample_chunk_has_embedding": bool(sample_chunk.get("embedding") if sample_chunk else False)
                })
            else:
                result["steps"].append({
                    "step": "DATABASE_VERIFICATION",
                    "status": "FAILED",
                    "chunks_in_db": 0
                })
                
        except Exception as e:
            result["steps"].append({
                "step": "DATABASE_VERIFICATION",
                "status": "FAILED", 
                "error": str(e)
            })
        
        # Step 5: Test search functionality
        try:
            search_results = await rag._search_chunks_mongodb("MongoDB RAG test", limit=2)
            result["steps"].append({
                "step": "SEARCH_TEST",
                "status": "SUCCESS",
                "results_found": len(search_results),
                "top_similarity": search_results[0].get("similarity", 0) if search_results else 0
            })
        except Exception as e:
            result["steps"].append({
                "step": "SEARCH_TEST",
                "status": "FAILED",
                "error": str(e)
            })
        
        # Cleanup test file
        try:
            import os
            if os.path.exists(test_doc_data["file_path"]):
                os.remove(test_doc_data["file_path"])
        except:
            pass
            
        result["test_status"] = "COMPLETED"
        return result
        
    except Exception as e:
        return {
            "test_status": "CRITICAL_ERROR",
            "error": str(e),
            "timestamp": str(datetime.now(timezone.utc))
        }

@api_router.get("/debug/list-documents")
async def list_documents():
    """List actual document IDs for testing"""
    try:
        docs = await db.documents.find({
            "approval_status": "approved"
        }).limit(10).to_list(10)
        
        document_list = []
        for doc in docs:
            document_list.append({
                "id": doc["id"],
                "name": doc["original_name"],
                "processing_status": doc.get("processing_status", "unknown"),
                "processed": doc.get("processed", False),
                "chunks_count": doc.get("chunks_count", 0),
                "test_url": f"https://asiaihub.com/api/debug/test-approval-direct/{doc['id']}"
            })
        
        return {
            "timestamp": str(datetime.now(timezone.utc)),
            "total_documents": len(document_list),
            "documents": document_list,
            "instructions": "Click any test_url to test direct approval for that document"
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e)
        }

@api_router.get("/debug/check-file-exists/{document_id}")
async def check_file_exists(document_id: str):
    """Check if the document file actually exists on the file system"""
    try:
        document = await db.documents.find_one({"id": document_id})
        
        if not document:
            return {
                "status": "DOCUMENT_NOT_FOUND",
                "document_id": document_id
            }
        
        file_path = document.get("file_path")
        
        # Check multiple possible locations
        possible_paths = [
            file_path,  # Original path
            os.path.join(os.path.dirname(__file__), file_path) if not os.path.isabs(file_path) else file_path,  # Backend relative
            os.path.join("/app/backend", file_path) if not os.path.isabs(file_path) else file_path,  # App backend
            os.path.join("/app", file_path) if not os.path.isabs(file_path) else file_path,  # App root
        ]
        
        results = {}
        for i, path in enumerate(possible_paths):
            results[f"path_{i+1}"] = {
                "path": path,
                "exists": os.path.exists(path),
                "is_file": os.path.isfile(path) if os.path.exists(path) else False,
                "size": os.path.getsize(path) if os.path.exists(path) else None
            }
        
        # Check if uploads directory exists
        upload_dirs = [
            "/app/backend/uploads",
            "/app/uploads", 
            os.path.join(os.path.dirname(__file__), "uploads")
        ]
        
        upload_dir_info = {}
        for i, dir_path in enumerate(upload_dirs):
            if os.path.exists(dir_path):
                try:
                    files = os.listdir(dir_path)[:10]  # First 10 files
                    upload_dir_info[f"dir_{i+1}"] = {
                        "path": dir_path,
                        "exists": True,
                        "file_count": len(os.listdir(dir_path)),
                        "sample_files": files
                    }
                except:
                    upload_dir_info[f"dir_{i+1}"] = {
                        "path": dir_path,
                        "exists": True,
                        "error": "Cannot read directory"
                    }
            else:
                upload_dir_info[f"dir_{i+1}"] = {
                    "path": dir_path,
                    "exists": False
                }
        
        return {
            "timestamp": str(datetime.now(timezone.utc)),
            "document_id": document_id,
            "document_name": document.get("original_name"),
            "stored_file_path": file_path,
            "path_checks": results,
            "upload_directories": upload_dir_info
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": str(datetime.now(timezone.utc))
        }

@api_router.get("/debug/test-openai-key")
async def test_openai_key():
    """Test OpenAI API key directly"""
    try:
        import openai
        
        # Get the OpenAI API key from environment
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        
        result = {
            "timestamp": str(datetime.now(timezone.utc)),
            "test_status": "STARTING",
            "steps": []
        }
        
        # Step 1: Check if key exists
        if openai_api_key:
            result["steps"].append({
                "step": "KEY_CHECK",
                "status": "SUCCESS",
                "key_length": len(openai_api_key),
                "key_prefix": openai_api_key[:20] + "..." if len(openai_api_key) > 20 else openai_api_key,
                "key_suffix": "..." + openai_api_key[-10:] if len(openai_api_key) > 20 else openai_api_key
            })
        else:
            result["steps"].append({
                "step": "KEY_CHECK",
                "status": "FAILED",
                "error": "OPENAI_API_KEY not found in environment"
            })
            return result
        
        # Step 2: Test OpenAI client initialization
        try:
            openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
            result["steps"].append({
                "step": "CLIENT_INIT",
                "status": "SUCCESS"
            })
        except Exception as e:
            result["steps"].append({
                "step": "CLIENT_INIT", 
                "status": "FAILED",
                "error": str(e)
            })
            return result
            
        # Step 3: Test simple completion call
        try:
            completion_response = await asyncio.wait_for(
                openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Say 'OpenAI API test successful' and nothing else."}],
                    max_tokens=10
                ),
                timeout=30.0
            )
            
            response_text = completion_response.choices[0].message.content
            
            result["steps"].append({
                "step": "COMPLETION_TEST",
                "status": "SUCCESS", 
                "response": response_text,
                "model_used": completion_response.model,
                "tokens_used": completion_response.usage.total_tokens if completion_response.usage else None
            })
            
        except asyncio.TimeoutError:
            result["steps"].append({
                "step": "COMPLETION_TEST",
                "status": "TIMEOUT",
                "error": "OpenAI completion timed out after 30 seconds"
            })
        except Exception as e:
            result["steps"].append({
                "step": "COMPLETION_TEST",
                "status": "FAILED",
                "error": str(e)
            })
        
        # Step 4: Test embedding generation (the one used in RAG)
        try:
            test_text = "This is a test for embedding generation in production."
            
            embedding_response = await asyncio.wait_for(
                openai_client.embeddings.create(
                    input=test_text,
                    model="text-embedding-ada-002"
                ),
                timeout=30.0
            )
            
            embedding = embedding_response.data[0].embedding
            
            result["steps"].append({
                "step": "EMBEDDING_TEST",
                "status": "SUCCESS",
                "embedding_length": len(embedding),
                "model_used": embedding_response.model,
                "tokens_used": embedding_response.usage.total_tokens if embedding_response.usage else None,
                "embedding_preview": embedding[:3] if len(embedding) > 3 else embedding
            })
            
        except asyncio.TimeoutError:
            result["steps"].append({
                "step": "EMBEDDING_TEST", 
                "status": "TIMEOUT",
                "error": "OpenAI embedding timed out after 30 seconds"
            })
        except Exception as e:
            result["steps"].append({
                "step": "EMBEDDING_TEST",
                "status": "FAILED",
                "error": str(e)
            })
        
        result["test_status"] = "COMPLETED"
        return result
        
    except Exception as e:
        return {
            "test_status": "CRITICAL_ERROR",
            "error": str(e),
            "timestamp": str(datetime.now(timezone.utc))
        }

@api_router.get("/debug/check-document-debug-info/{document_id}")
async def check_document_debug_info(document_id: str):
    """Check the debug info stored for a specific document"""
    try:
        document = await db.documents.find_one({"id": document_id})
        
        if not document:
            return {
                "status": "NOT_FOUND",
                "document_id": document_id,
                "message": "Document not found"
            }
        
        return {
            "timestamp": str(datetime.now(timezone.utc)),
            "document_id": document_id,
            "document_name": document.get("original_name"),
            "processing_status": document.get("processing_status"),
            "processed": document.get("processed"),
            "file_path": document.get("file_path"),
            "mime_type": document.get("mime_type"),
            "debug_info": document.get("debug_info"),
            "last_processed_at": document.get("last_processed_at"),
            "chunks_count": document.get("chunks_count", 0)
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": str(datetime.now(timezone.utc))
        }

@api_router.get("/debug/simple-document-list")
async def simple_document_list():
    """Simple endpoint to get document IDs for testing"""
    try:
        mongo_url = os.environ.get('MONGO_URL')
        db_name = os.environ.get('DB_NAME')
        client = AsyncIOMotorClient(mongo_url)
        database = client[db_name]
        
        # Get just the first 5 approved documents with minimal data
        docs = await database.documents.find(
            {"approval_status": "approved"},
            {"id": 1, "original_name": 1, "_id": 0}
        ).limit(5).to_list(5)
        
        return {
            "timestamp": str(datetime.now(timezone.utc)),
            "found_documents": len(docs),
            "documents": [
                {
                    "id": doc["id"],
                    "name": doc["original_name"],
                    "test_url": f"https://asiaihub.com/api/debug/test-approval-direct/{doc['id']}"
                }
                for doc in docs
            ]
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": str(datetime.now(timezone.utc))
        }

@api_router.get("/debug/reset-failed-documents")
async def reset_failed_documents():
    """Reset failed documents back to pending for reprocessing AND clear all chunks"""
    try:
        # First, clear all document chunks
        mongo_url = os.environ.get('MONGO_URL')
        db_name = os.environ.get('DB_NAME')
        client = AsyncIOMotorClient(mongo_url)
        database = client[db_name]
        
        # Count and clear chunks
        chunk_count_before = await database.document_chunks.count_documents({})
        chunk_delete_result = await database.document_chunks.delete_many({})
        
        # Find all documents that failed or have issues
        problem_docs = await db.documents.find({
            "approval_status": "approved",
            "$or": [
                {"processing_status": "failed"},
                {"processing_status": "timeout"},
                {"processing_status": "completed", "processed": False},
                {"processed": False}
            ]
        }).to_list(100)
        
        reset_results = {
            "timestamp": str(datetime.now(timezone.utc)),
            "chunks_cleared": chunk_delete_result.deleted_count,
            "chunks_before": chunk_count_before,
            "found_problem_docs": len(problem_docs),
            "reset_status": [],
            "reset_count": 0
        }
        
        for doc in problem_docs:
            try:
                # Reset to pending status
                await db.documents.update_one(
                    {"id": doc["id"]},
                    {
                        "$set": {
                            "processing_status": "pending",
                            "processed": False,
                            "chunks_count": 0,
                            "notes": "Reset for reprocessing - MongoDB RAG system"
                        }
                    }
                )
                
                reset_results["reset_status"].append({
                    "document_id": doc["id"],
                    "name": doc["original_name"],
                    "old_status": doc.get("processing_status", "unknown"),
                    "old_processed": doc.get("processed", False),
                    "new_status": "pending"
                })
                reset_results["reset_count"] += 1
                
            except Exception as e:
                reset_results["reset_status"].append({
                    "document_id": doc["id"],
                    "name": doc.get("original_name", "unknown"),
                    "status": "RESET_ERROR",
                    "error": str(e)
                })
        
        return reset_results
        
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": str(datetime.now(timezone.utc))
        }

@api_router.get("/debug/test-approval-direct/{document_id}")
async def test_approval_direct(document_id: str):
    """Test approval endpoint directly"""
    logger.info(f"🔥🔥🔥 DIRECT APPROVAL TEST STARTED for {document_id}")
    print(f"🔥🔥🔥 DIRECT APPROVAL TEST STARTED for {document_id}")
    
    try:
        # Check if document exists
        document = await db.documents.find_one({"id": document_id})
        if not document:
            return {
                "status": "DOCUMENT_NOT_FOUND",
                "document_id": document_id,
                "message": "🔥 Document not found in database"
            }
        
        # Call the approval function directly
        result = await approve_document(document_id, "direct_test")
        
        return {
            "status": "SUCCESS",
            "document_id": document_id, 
            "document_name": document.get("original_name"),
            "approval_result": result,
            "message": "🔥 Direct approval test completed"
        }
        
    except Exception as e:
        logger.error(f"🔥🔥🔥 DIRECT APPROVAL TEST ERROR: {e}")
        print(f"🔥🔥🔥 DIRECT APPROVAL TEST ERROR: {e}")
        return {
            "status": "ERROR",
            "error": str(e),
            "message": "🔥 Direct approval test failed"
        }

@api_router.get("/debug/test-deployment")
async def test_deployment():
    """Test if the latest code is deployed"""
    return {
        "timestamp": str(datetime.now(timezone.utc)),
        "message": "🔥 LATEST CODE IS DEPLOYED - SIMPLE WORKING VERSION",
        "version": "event_loop_fix_v1", 
        "approval_endpoint_available": True,
        "enhanced_debug_info": False,
        "using_original_process_and_store_document": True,
        "file_path_fix": "basic_relative_to_absolute"
    }

@api_router.get("/debug/check-backend-logs")
async def check_backend_logs():
    """Check recent backend logs from multiple possible locations"""
    try:
        import subprocess
        import glob
        
        log_results = {
            "timestamp": str(datetime.now(timezone.utc)),
            "log_locations": {},
            "supervisor_status": "",
            "recent_entries": []
        }
        
        # Check supervisor status
        try:
            status_result = subprocess.run(["supervisorctl", "status"], capture_output=True, text=True, timeout=5)
            log_results["supervisor_status"] = status_result.stdout
        except:
            log_results["supervisor_status"] = "Could not get supervisor status"
        
        # Try multiple log locations
        possible_log_paths = [
            "/var/log/supervisor/backend*.log",
            "/var/log/supervisor/*.log", 
            "/tmp/*.log",
            "/app/backend*.log",
            "/app/*.log"
        ]
        
        for path_pattern in possible_log_paths:
            try:
                log_files = glob.glob(path_pattern)
                log_results["log_locations"][path_pattern] = log_files
                
                # If we find log files, try to read the most recent one
                if log_files:
                    latest_log = max(log_files, key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0)
                    try:
                        result = subprocess.run(["tail", "-n", "50", latest_log], capture_output=True, text=True, timeout=10)
                        if result.stdout:
                            log_results["recent_entries"].extend([
                                f"=== FROM {latest_log} ===",
                                result.stdout
                            ])
                    except:
                        pass
            except:
                log_results["log_locations"][path_pattern] = "Error checking path"
        
        return log_results
        
    except Exception as e:
        return {
            "status": "ERROR", 
            "error": str(e),
            "timestamp": str(datetime.now(timezone.utc))
        }

@api_router.get("/debug/check-document-status")
async def check_document_status():
    """Check the actual status of all documents"""
    try:
        # Get all documents with their current status
        all_docs = await db.documents.find({}).to_list(100)
        
        status_summary = {
            "timestamp": str(datetime.now(timezone.utc)),
            "total_documents": len(all_docs),
            "status_counts": {},
            "processing_status_counts": {},
            "sample_documents": []
        }
        
        # Count by approval status
        for doc in all_docs:
            approval_status = doc.get("approval_status", "unknown")
            processing_status = doc.get("processing_status", "unknown")
            processed = doc.get("processed", False)
            
            # Count approval statuses
            status_summary["status_counts"][approval_status] = status_summary["status_counts"].get(approval_status, 0) + 1
            
            # Count processing statuses
            processing_key = f"{processing_status}_{processed}"
            status_summary["processing_status_counts"][processing_key] = status_summary["processing_status_counts"].get(processing_key, 0) + 1
        
        # Get sample documents to see their actual state
        sample_docs = all_docs[:5]  # First 5 documents
        for doc in sample_docs:
            status_summary["sample_documents"].append({
                "id": doc["id"],
                "name": doc["original_name"],
                "approval_status": doc.get("approval_status"),
                "processing_status": doc.get("processing_status"),
                "processed": doc.get("processed"),
                "chunks_count": doc.get("chunks_count", 0),
                "notes": doc.get("notes", "")
            })
        
        return status_summary
        
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": str(datetime.now(timezone.utc))
        }

@api_router.get("/debug/process-documents-now")
async def process_documents_now():
    """Process documents immediately and wait for completion"""
    try:
        # Find documents that need processing
        pending_docs = await db.documents.find({
            "approval_status": "approved",
            "processing_status": {"$in": ["pending", "processing"]}
        }).to_list(100)
        
        if not pending_docs:
            return {
                "status": "NO_PENDING_DOCUMENTS",
                "message": "No documents found that need processing",
                "timestamp": str(datetime.now(timezone.utc))
            }
        
        processing_results = {
            "timestamp": str(datetime.now(timezone.utc)),
            "total_pending": len(pending_docs),
            "processing_status": [],
            "success_count": 0,
            "error_count": 0
        }
        
        # Process each document sequentially to avoid overwhelming the system
        for doc in pending_docs:
            try:
                # Process document with RAG system
                await process_document_with_rag(doc)
                
                # Check if processing was successful
                updated_doc = await db.documents.find_one({"id": doc["id"]})
                
                if updated_doc and updated_doc.get("processed"):
                    processing_results["processing_status"].append({
                        "document_id": doc["id"],
                        "name": doc["original_name"],
                        "status": "SUCCESS",
                        "chunks_count": updated_doc.get("chunks_count", 0)
                    })
                    processing_results["success_count"] += 1
                else:
                    processing_results["processing_status"].append({
                        "document_id": doc["id"],
                        "name": doc["original_name"],
                        "status": "FAILED",
                        "processing_status": updated_doc.get("processing_status") if updated_doc else "unknown"
                    })
                    processing_results["error_count"] += 1
                
            except Exception as e:
                processing_results["processing_status"].append({
                    "document_id": doc["id"],
                    "name": doc.get("original_name", "unknown"),
                    "status": "ERROR",
                    "error": str(e)
                })
                processing_results["error_count"] += 1
        
        return processing_results
        
    except Exception as e:
        return {
            "status": "CRITICAL_ERROR",
            "error": str(e),
            "timestamp": str(datetime.now(timezone.utc))
        }

# System Settings Management
@api_router.get("/admin/system-settings")
async def get_system_settings():
    """Get current system settings"""
    try:
        settings = await db.system_settings.find_one({"_id": "global"})
        if not settings:
            # Default settings
            default_settings = {
                "_id": "global",
                "ai_model": "gpt-5",
                "allow_user_registration": False,
                "require_document_approval": True,
                "enable_audit_logging": True,
                "response_cache_hours": 24,
                "use_personal_openai_key": False,
                "personal_openai_key": "",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            await db.system_settings.insert_one(default_settings)
            settings = default_settings
            
        return {
            "ai_model": settings.get("ai_model", "gpt-5"),
            "allow_user_registration": settings.get("allow_user_registration", False),
            "require_document_approval": settings.get("require_document_approval", True),
            "enable_audit_logging": settings.get("enable_audit_logging", True),
            "response_cache_hours": settings.get("response_cache_hours", 24),
            "use_personal_openai_key": settings.get("use_personal_openai_key", False),
            "personal_openai_key": settings.get("personal_openai_key", "")
        }
    except Exception as e:
        logger.error(f"Error getting system settings: {e}")
        return {"error": str(e)}

@api_router.put("/admin/system-settings")
async def update_system_settings(settings: dict):
    """Update system settings"""
    try:
        settings["updated_at"] = datetime.now(timezone.utc)
        
        await db.system_settings.update_one(
            {"_id": "global"},
            {"$set": settings},
            upsert=True
        )
        
        return {"message": "System settings updated successfully"}
    except Exception as e:
        logger.error(f"Error updating system settings: {e}")
        return {"error": str(e)}

@api_router.get("/admin/chat-analytics")
async def get_chat_analytics():
    """Get chat analytics for admin dashboard"""
    try:
        # Get all chat sessions
        chat_sessions = await db.chat_sessions.find({}).to_list(100)
        
        # Analyze most asked questions
        question_counts = {}
        no_answer_questions = []
        user_activity = {}
        
        for session in chat_sessions:
            messages = session.get("messages", [])
            user_id = session.get("user_id", "anonymous")
            
            if user_id not in user_activity:
                user_activity[user_id] = 0
            user_activity[user_id] += len([m for m in messages if m.get("role") == "user"])
            
            for message in messages:
                if message.get("role") == "user":
                    question = message.get("content", "").lower().strip()
                    if len(question) > 10:  # Filter out very short questions
                        question_counts[question] = question_counts.get(question, 0) + 1
                        
                elif message.get("role") == "assistant":
                    response = message.get("content", {})
                    if isinstance(response, dict) and response.get("response_type") == "no_documents_found":
                        # Find the previous user question
                        prev_msg = messages[messages.index(message) - 1] if messages.index(message) > 0 else None
                        if prev_msg and prev_msg.get("role") == "user":
                            no_answer_questions.append(prev_msg.get("content", ""))
        
        # Sort and get top questions
        top_questions = sorted(question_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_sessions": len(chat_sessions),
            "top_questions": [{"question": q, "count": c} for q, c in top_questions],
            "no_answer_questions": no_answer_questions[:10],
            "user_activity": dict(sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10]),
            "timestamp": str(datetime.now(timezone.utc))
        }
        
    except Exception as e:
        logger.error(f"Error getting chat analytics: {e}")
        return {"error": str(e)}

@api_router.get("/debug/mongodb-direct-count")
async def mongodb_direct_count():
    """Directly count chunks in MongoDB collection"""
    try:
        mongo_url = os.environ.get('MONGO_URL')
        db_name = os.environ.get('DB_NAME')
        client = AsyncIOMotorClient(mongo_url)
        database = client[db_name]
        
        # Count documents in chunks collection
        chunk_count = await database.document_chunks.count_documents({})
        
        # Get sample chunks
        sample_chunks = await database.document_chunks.find({}).limit(3).to_list(3)
        
        # Get unique document IDs
        pipeline = [{"$group": {"_id": "$document_id"}}, {"$count": "unique_docs"}]
        unique_result = await database.document_chunks.aggregate(pipeline).to_list(1)
        unique_docs = unique_result[0]["unique_docs"] if unique_result else 0
        
        client.close()
        
        return {
            "timestamp": str(datetime.now(timezone.utc)),
            "mongodb_url": mongo_url,
            "database_name": db_name,
            "collection_name": "document_chunks",
            "total_chunks": chunk_count,
            "unique_documents": unique_docs,
            "sample_chunks": [
                {
                    "document_id": chunk.get("document_id"),
                    "chunk_index": chunk.get("chunk_index"),
                    "text_preview": chunk.get("text", "")[:100] + "..." if chunk.get("text") else "No text"
                } for chunk in sample_chunks
            ],
            "status": "SUCCESS"
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": str(datetime.now(timezone.utc))
        }

@api_router.get("/debug/clear-chunks")
async def clear_document_chunks():
    """Clear all document chunks from MongoDB collection"""
    try:
        mongo_url = os.environ.get('MONGO_URL')
        db_name = os.environ.get('DB_NAME')
        client = AsyncIOMotorClient(mongo_url)
        database = client[db_name]
        
        # Count chunks before deletion
        chunk_count_before = await database.document_chunks.count_documents({})
        
        # Delete all chunks
        delete_result = await database.document_chunks.delete_many({})
        
        # Verify deletion
        chunk_count_after = await database.document_chunks.count_documents({})
        
        return {
            "timestamp": str(datetime.now(timezone.utc)),
            "status": "SUCCESS",
            "chunks_before": chunk_count_before,
            "chunks_deleted": delete_result.deleted_count,
            "chunks_after": chunk_count_after,
            "message": f"Successfully cleared {delete_result.deleted_count} chunks from document_chunks collection"
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": str(datetime.now(timezone.utc))
        }

@api_router.get("/debug/migrate-documents-to-mongodb")
async def migrate_documents_to_mongodb():
    """Migrate existing approved documents to MongoDB RAG system"""
    try:
        # Find all approved documents that need MongoDB processing
        approved_docs = await db.documents.find({
            "approval_status": "approved"
        }).to_list(100)
        
        migration_results = {
            "timestamp": str(datetime.now(timezone.utc)),
            "total_approved": len(approved_docs),
            "migration_status": [],
            "success_count": 0,
            "error_count": 0
        }
        
        for doc in approved_docs:
            try:
                # Reset processing status to trigger MongoDB processing
                await db.documents.update_one(
                    {"id": doc["id"]},
                    {
                        "$set": {
                            "processing_status": "pending",
                            "processed": False,
                            "chunks_count": 0,
                            "notes": "Migrating to MongoDB RAG system"
                        }
                    }
                )
                
                # Trigger MongoDB RAG processing
                asyncio.create_task(process_document_with_rag(doc))
                
                migration_results["migration_status"].append({
                    "document_id": doc["id"],
                    "name": doc["original_name"],
                    "status": "QUEUED_FOR_PROCESSING"
                })
                migration_results["success_count"] += 1
                
            except Exception as e:
                migration_results["migration_status"].append({
                    "document_id": doc["id"],
                    "name": doc.get("original_name", "unknown"),
                    "status": "ERROR",
                    "error": str(e)
                })
                migration_results["error_count"] += 1
        
        return migration_results
        
    except Exception as e:
        return {
            "status": "MIGRATION_FAILED",
            "error": str(e),
            "timestamp": str(datetime.now(timezone.utc))
        }

@api_router.get("/debug/production-rag-status")
async def production_rag_status():
    """Debug endpoint to check production RAG system status"""
    try:
        result = {
            "timestamp": str(datetime.now(timezone.utc)),
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
            database = client[db_name]
            
            # Test connection
            server_info = await client.server_info()
            collections = await database.list_collection_names()
            
            result["mongodb_check"] = {
                "connection_status": "SUCCESS",
                "server_version": server_info.get('version'),
                "collections": collections,
                "has_document_chunks": "document_chunks" in collections,
                "documents_count": await database.documents.count_documents({}),
                "approved_docs": await database.documents.count_documents({"approval_status": "approved"}),
                "processed_docs": await database.documents.count_documents({"processed": True})
            }
            
            # Check document_chunks collection
            if "document_chunks" in collections:
                chunk_count = await database.document_chunks.count_documents({})
                result["mongodb_check"]["chunk_count"] = chunk_count
                
                if chunk_count > 0:
                    sample_chunk = await database.document_chunks.find_one()
                    result["mongodb_check"]["sample_chunk"] = {
                        "document_id": sample_chunk.get("document_id"),
                        "has_text": bool(sample_chunk.get("text")),
                        "has_embedding": bool(sample_chunk.get("embedding")),
                        "text_preview": sample_chunk.get("text", "")[:100] + "..." if sample_chunk.get("text") else None
                    }
            else:
                result["mongodb_check"]["chunk_count"] = 0
            
            # ADD DOCUMENT LIST HERE - in working section
            try:
                # Get ALL approved documents for testing with file paths
                sample_docs = await database.documents.find(
                    {"approval_status": "approved"},
                    {"id": 1, "original_name": 1, "file_path": 1, "_id": 0}
                ).limit(5).to_list(5)
                
                # ADD FILE EXISTENCE CHECK HERE
                try:
                    # Check file existence for sample documents
                    file_check_results = []
                    for doc in sample_docs[:3]:  # Check first 3 documents
                        file_path = doc.get("file_path", "")
                        if not file_path:
                            continue
                            
                        # Check multiple possible locations
                        possible_paths = [
                            file_path,  # Original path
                            os.path.join("/app/backend", file_path),
                            os.path.join("/app", file_path),
                        ]
                        
                        file_found = False
                        working_path = None
                        for path in possible_paths:
                            try:
                                if os.path.exists(path) and os.path.isfile(path):
                                    file_found = True
                                    working_path = path
                                    break
                            except:
                                continue
                        
                        file_check_results.append({
                            "document_id": doc["id"],
                            "name": doc["original_name"],
                            "stored_path": file_path,
                            "file_exists": file_found,
                            "working_path": working_path,
                            "file_size": os.path.getsize(working_path) if working_path and file_found else None
                        })
                    
                    result["mongodb_check"]["file_existence_check"] = file_check_results
                    
                    # Also check upload directories
                    upload_dirs = ["/app/backend/uploads", "/app/uploads", "/tmp/uploads"]
                    upload_dir_info = []
                    
                    for dir_path in upload_dirs:
                        try:
                            if os.path.exists(dir_path):
                                files = os.listdir(dir_path)
                                upload_dir_info.append({
                                    "path": dir_path,
                                    "exists": True,
                                    "file_count": len(files),
                                    "sample_files": files[:5]  # First 5 files
                                })
                            else:
                                upload_dir_info.append({
                                    "path": dir_path,
                                    "exists": False
                                })
                        except Exception as dir_error:
                            upload_dir_info.append({
                                "path": dir_path,
                                "exists": "ERROR",
                                "error": str(dir_error)
                            })
                    
                    result["mongodb_check"]["upload_directories"] = upload_dir_info
                    
                except Exception as file_check_error:
                    result["mongodb_check"]["file_check_error"] = str(file_check_error)
                
                result["mongodb_check"]["sample_documents_for_testing"] = [
                    {
                        "id": doc["id"],
                        "name": doc["original_name"],
                        "direct_test_url": f"https://asiaihub.com/api/debug/test-approval-direct/{doc['id']}"
                    }
                    for doc in sample_docs
                ]
            except Exception as doc_err:
                result["mongodb_check"]["sample_documents_error"] = str(doc_err)
                
        except Exception as e:
            result["mongodb_check"] = {
                "connection_status": "FAILED",
                "error": str(e)
            }
        
        # 3. RAG System Check
        try:
            rag = get_rag_system(EMERGENT_LLM_KEY)
            
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
        
        # 4. Document Processing Check with Document List
        try:
            # Check if we have any pending documents to process
            pending_docs = await db.documents.find({
                "approval_status": "approved",
                "processing_status": {"$in": ["pending", "processing"]}
            }).to_list(5)
            
            # Get ALL approved documents for testing
            try:
                all_approved_docs = await database.documents.find({
                    "approval_status": "approved"
                }).limit(10).to_list(10)
                
                document_list = []
                for doc in all_approved_docs:
                    try:
                        document_list.append({
                            "id": doc["id"],
                            "name": doc["original_name"],
                            "processing_status": doc.get("processing_status", "unknown"),
                            "processed": doc.get("processed", False),
                            "chunks_count": doc.get("chunks_count", 0),
                            "test_approval_url": f"https://asiaihub.com/api/debug/test-approval-direct/{doc['id']}"
                        })
                    except Exception as doc_error:
                        document_list.append({
                            "id": doc.get("id", "unknown"),
                            "name": "ERROR_PROCESSING_DOCUMENT",
                            "error": str(doc_error)
                        })
                
                document_list_success = True
                document_list_error = None
                
            except Exception as list_error:
                document_list = []
                document_list_success = False 
                document_list_error = str(list_error)
            
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
                ],
                "all_approved_documents": document_list,
                "total_approved_documents": len(document_list),
                "document_list_success": document_list_success,
                "document_list_error": document_list_error
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
            "timestamp": str(datetime.now(timezone.utc))
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
    # Add immediate logging
    logger.info(f"🔥 APPROVAL STARTED for document {document_id} by {approved_by}")
    print(f"🔥 APPROVAL STARTED for document {document_id} by {approved_by}")  # Force console output
    
    try:
        # Update document approval status
        logger.info(f"🔥 Updating document approval status for {document_id}")
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
            logger.error(f"🔥 Document not found: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info(f"🔥 Document approval status updated, now fetching document data")
        
        # Get updated document and process with RAG immediately
        document = await db.documents.find_one({"id": document_id})
        if document:
            # Store debug trace directly in database
            debug_trace = []
            
            try:
                debug_trace.append("Document found, starting RAG processing")
                debug_trace.append("About to call process_document_with_rag...")
                
                # Store initial debug trace
                await db.documents.update_one(
                    {"id": document_id},
                    {"$set": {"debug_trace": debug_trace, "debug_updated_at": datetime.now(timezone.utc)}}
                )
                
                # Process document synchronously so we can catch errors
                debug_trace.append("Calling process_document_with_rag")
                await process_document_with_rag(document)
                
                debug_trace.append("process_document_with_rag completed")
                
                # Update debug trace after processing
                await db.documents.update_one(
                    {"id": document_id},
                    {"$set": {"debug_trace": debug_trace}}
                )
                
                logger.info(f"🔥 RAG processing completed, checking results")
                
                # Check if processing was successful
                updated_doc = await db.documents.find_one({"id": document_id})
                if updated_doc and updated_doc.get("processed"):
                    logger.info(f"🔥 SUCCESS: Document processed with {updated_doc.get('chunks_count', 0)} chunks")
                    return {
                        "message": "Document approved and successfully processed for knowledge base",
                        "chunks_count": updated_doc.get("chunks_count", 0),
                        "processing_status": "completed"
                    }
                else:
                    processing_status = updated_doc.get("processing_status") if updated_doc else "unknown"
                    logger.error(f"🔥 FAILURE: Processing did not complete. Status: {processing_status}")
                    # Return detailed error information
                    return {
                        "message": "Document approved but processing failed",
                        "processing_status": processing_status,
                        "error": "RAG processing did not complete successfully",
                        "debug_details": {
                            "document_found_after_processing": bool(updated_doc),
                            "processed_flag": updated_doc.get("processed") if updated_doc else None,
                            "processing_status": updated_doc.get("processing_status") if updated_doc else None,
                            "chunks_count": updated_doc.get("chunks_count") if updated_doc else None,
                            "file_path": updated_doc.get("file_path") if updated_doc else None,
                            "last_processed_at": str(updated_doc.get("last_processed_at")) if updated_doc and updated_doc.get("last_processed_at") else None
                        }
                    }
            except Exception as processing_error:
                logger.error(f"🔥 EXCEPTION during RAG processing for document {document_id}: {processing_error}")
                return {
                    "message": "Document approved but processing failed",
                    "processing_error": str(processing_error),
                    "processing_status": "failed"
                }
        else:
            logger.error(f"🔥 Could not fetch document after approval: {document_id}")
            return {"message": "Document approved but could not fetch for processing"}
        
    except Exception as e:
        logger.error(f"🔥 ERROR in approval process: {e}")
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
    """Delete a document and remove from knowledge base with timeout protection"""
    try:
        # Get document info with timeout
        document = await asyncio.wait_for(
            db.documents.find_one({"id": document_id}),
            timeout=10.0
        )
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Remove from vector database with timeout protection
        try:
            async def remove_from_rag():
                rag = get_rag_system(EMERGENT_LLM_KEY)
                return rag.remove_document_chunks(document_id)
            
            await asyncio.wait_for(remove_from_rag(), timeout=30.0)
            logger.info(f"Successfully removed document {document_id} from RAG system")
        except asyncio.TimeoutError:
            logger.warning(f"RAG removal timeout for document {document_id} - continuing with file/DB deletion")
        except Exception as e:
            logger.warning(f"RAG removal failed for document {document_id}: {e} - continuing with file/DB deletion")
        
        # Delete file from disk with timeout protection
        try:
            async def delete_file():
                import os
                if os.path.exists(document['file_path']):
                    os.remove(document['file_path'])
                    return True
                return False
            
            await asyncio.wait_for(delete_file(), timeout=10.0)
        except Exception as e:
            logger.warning(f"Could not delete file {document.get('file_path', 'unknown')}: {e}")
        
        # Remove from database with timeout
        result = await asyncio.wait_for(
            db.documents.delete_one({"id": document_id}),
            timeout=10.0
        )
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found in database")
        
        return {"message": "Document deleted successfully"}
        
    except asyncio.TimeoutError:
        logger.error(f"Timeout deleting document {document_id}")
        raise HTTPException(status_code=408, detail="Delete operation timed out - please try again")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
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
    """Upload a document for RAG processing with resilient error handling"""
    try:
        # Validate file type
        allowed_types = ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="File type not supported. Please upload PDF, TXT, or DOCX files.")
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Ensure upload directory exists with better error handling
        try:
            UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
        except Exception as e:
            logger.error(f"Failed to create upload directory: {e}")
            raise HTTPException(status_code=500, detail="Upload directory unavailable")
        
        # Save file with timeout protection
        try:
            import asyncio
            async def save_file_with_timeout():
                async with aiofiles.open(file_path, 'wb') as f:
                    content = await file.read()
                    await f.write(content)
                return content
            
            # 30 second timeout for file operations
            content = await asyncio.wait_for(save_file_with_timeout(), timeout=30.0)
            
        except asyncio.TimeoutError:
            logger.error(f"File upload timeout for {file.filename}")
            raise HTTPException(status_code=408, detail="File upload timed out - please try a smaller file")
        except Exception as e:
            logger.error(f"File save error: {e}")
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")
        
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
        
        # Save to database with timeout
        try:
            await asyncio.wait_for(
                db.documents.insert_one(document.dict()), 
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.error(f"Database timeout saving document {file.filename}")
            # Clean up uploaded file
            try:
                file_path.unlink(missing_ok=True)
            except:
                pass
            raise HTTPException(status_code=408, detail="Database timeout - please try again")
        
        return DocumentUploadResponse(
            id=document.id,
            filename=document.original_name,
            message="Document uploaded successfully and pending approval"
        )
        
    except HTTPException:
        raise
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



@api_router.get("/documents/rag-stats")
async def get_rag_stats():
    """Get RAG system statistics with graceful fallback"""
    try:
        # Try to get RAG stats with timeout
        import asyncio
        async def get_stats_with_timeout():
            rag = get_rag_system(EMERGENT_LLM_KEY)
            return rag.get_collection_stats()
        
        # 5 second timeout for RAG operations
        stats = await asyncio.wait_for(get_stats_with_timeout(), timeout=5.0)
        
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
        
    except asyncio.TimeoutError:
        logger.warning("RAG stats request timed out, returning fallback data")
        return {
            "total_chunks": 0,
            "total_documents": 0,
            "departments": {},
            "status": "RAG system temporarily unavailable"
        }
    except Exception as e:
        logger.error(f"RAG stats error: {e}")
        return {
            "total_chunks": 0, 
            "total_documents": 0,
            "departments": {},
            "status": "RAG system unavailable"
        }

# Chat Routes
@api_router.post("/chat/send")
async def send_chat_message(request: ChatRequest):
    """Send a message to RAG chat system with optional streaming"""
    try:
        if request.stream:
            # Return streaming response
            return StreamingResponse(
                generate_streaming_response(request),
                media_type="text/plain"
            )
        else:
            # Original non-streaming response
            return await send_chat_message_non_streaming(request)
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")

async def send_chat_message_non_streaming(request: ChatRequest):
    """Original non-streaming chat message handler"""
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

async def generate_streaming_response(request: ChatRequest):
    """Generate streaming response for chat messages"""
    try:
        # Save user message first
        user_message = ChatMessage(
            session_id=request.session_id,
            role="user",
            content=request.message,
            attachments=request.document_ids
        )
        await db.chat_messages.insert_one(user_message.dict())
        
        # Process RAG query
        result = await process_rag_query(request.message, request.document_ids, request.session_id)
        
        # Stream the response
        response_text = ""
        if isinstance(result["response"], dict):
            response_text = json.dumps(result["response"], indent=2)
        else:
            response_text = str(result["response"])
        
        # Send metadata first
        yield f"data: {json.dumps({'type': 'metadata', 'documents_referenced': result.get('documents_referenced', 0)})}\n\n"
        
        # Stream content in chunks
        chunk_size = 10  # characters per chunk
        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i:i+chunk_size]
            yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
            await asyncio.sleep(0.05)  # Small delay for streaming effect
        
        # Send completion signal
        yield f"data: {json.dumps({'type': 'complete'})}\n\n"
        
        # Save AI response to database
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
            
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to process message'})}\n\n"

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
            # Use the provided requester_id instead of hardcoding "default_user"
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
        # Get the current ticket to compare changes
        current_ticket = await db.boost_tickets.find_one({"id": ticket_id})
        if not current_ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        # Track changes for audit trail
        changes_made = []
        user_name = update_dict.get("updated_by", "System")  # Get user name from frontend
        
        # Handle status transitions
        if update_data.status and update_data.status != current_ticket.get("status"):
            old_status = current_ticket.get("status", "unknown")
            new_status = update_data.status
            changes_made.append({
                "action": "status_changed",
                "description": f"Status changed from {old_status.replace('_', ' ')} to {new_status.replace('_', ' ')}",
                "old_value": old_status,
                "new_value": new_status
            })
            
            if update_data.status == TicketStatus.RESOLVED:
                update_dict["resolved_at"] = datetime.now(timezone.utc)
            elif update_data.status == TicketStatus.CLOSED:
                update_dict["closed_at"] = datetime.now(timezone.utc)
        
        # Handle priority changes
        if update_data.priority and update_data.priority != current_ticket.get("priority"):
            old_priority = current_ticket.get("priority", "unknown")
            new_priority = update_data.priority
            changes_made.append({
                "action": "priority_changed",
                "description": f"Priority changed from {old_priority} to {new_priority}",
                "old_value": old_priority,
                "new_value": new_priority
            })
        
        # Handle assignment changes
        if "owner_id" in update_dict:
            old_owner = current_ticket.get("owner_name", "Unassigned")
            new_owner = update_data.owner_name or "Unassigned"
            if old_owner != new_owner:
                changes_made.append({
                    "action": "assigned",
                    "description": f"Assigned from {old_owner} to {new_owner}",
                    "old_value": old_owner,
                    "new_value": new_owner
                })
        
        # Update the ticket
        result = await db.boost_tickets.update_one(
            {"id": ticket_id},
            {"$set": update_dict}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Log audit entries for all changes
        for change in changes_made:
            await log_audit_entry(
                ticket_id=ticket_id,
                action=change["action"],
                description=change["description"],
                user_name=user_name,
                details=f"Changed from '{change['old_value']}' to '{change['new_value']}'",
                old_value=change["old_value"],
                new_value=change["new_value"]
            )
        
        # Get and return updated ticket
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
        
        # Get real audit entries from database
        audit_entries = await db.boost_audit_trail.find({"ticket_id": ticket_id}).to_list(length=None)
        
        # Get comments
        comments = await db.boost_comments.find({"ticket_id": ticket_id}).to_list(length=None)
        
        # Get attachments
        attachments = await db.boost_attachments.find({"ticket_id": ticket_id}).to_list(length=None)
        
        # Build comprehensive audit trail
        trail = []
        
        # Add real audit entries first (these are the actual change logs)
        for entry in audit_entries:
            trail.append({
                "id": entry["id"],
                "action": entry["action"],
                "description": entry["description"],
                "user_name": entry["user_name"],
                "timestamp": entry["timestamp"],
                "details": entry.get("details", "")
            })
        
        # Add ticket creation (fallback if no audit entry exists)
        has_creation_entry = any(entry["action"] == "created" for entry in audit_entries)
        if not has_creation_entry:
            trail.append({
                "id": str(uuid.uuid4()),
                "action": "created",
                "description": f"Ticket created by {ticket['requester_name']}",
                "user_name": ticket['requester_name'],
                "timestamp": ticket['created_at'],
                "details": f"Priority: {ticket['priority'].upper()}, Department: {ticket['support_department']}, Category: {ticket['category']}"
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
                # Parse string and ensure it's timezone-aware
                due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            elif isinstance(due_date, datetime) and due_date.tzinfo is None:
                # Make naive datetime timezone-aware (assume UTC)
                due_date = due_date.replace(tzinfo=timezone.utc)
            
            # Now both datetimes are timezone-aware for safe comparison
            current_time = datetime.now(timezone.utc)
            if due_date < current_time and ticket['status'] not in ['resolved', 'closed']:
                trail.append({
                    "id": str(uuid.uuid4()),
                    "action": "sla_breach",
                    "description": "SLA deadline exceeded",
                    "user_name": "System",
                    "timestamp": due_date.isoformat() if hasattr(due_date, 'isoformat') else str(due_date),
                    "details": f"Due date: {due_date.isoformat() if hasattr(due_date, 'isoformat') else str(due_date)}"
                })
        
        # Sort by timestamp (newest first) - handle mixed datetime types safely
        def safe_timestamp_sort(item):
            timestamp = item['timestamp']
            if isinstance(timestamp, str):
                try:
                    return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    return datetime.min.replace(tzinfo=timezone.utc)
            elif isinstance(timestamp, datetime):
                if timestamp.tzinfo is None:
                    return timestamp.replace(tzinfo=timezone.utc)
                return timestamp
            else:
                return datetime.min.replace(tzinfo=timezone.utc)
                
        trail.sort(key=safe_timestamp_sort, reverse=True)
        
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
    name: Optional[str] = None  # Added name field
    personal_code: str
    role: str = "User"  # Admin, Manager, Agent, User
    department: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    access_token: Optional[str] = None

class BetaSettings(BaseModel):
    registration_code: str
    admin_email: str = "layth.bunni@adamsmithinternational.com"
    allowed_domain: str = "adamsmithinternational.com"
    max_users: int = 20
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RegistrationRequest(BaseModel):
    name: str
    email: str
    personal_code: str

class LoginRequest(BaseModel):
    name: Optional[str] = None  # Added name field
    email: str  
    personal_code: str

class LoginResponse(BaseModel):
    access_token: str
    user: BetaUser

# Beta Authentication Helper
security = HTTPBearer()

def generate_access_token(user_id: str, email: str) -> str:
    """Generate a simple access token"""
    # Generate a consistent token based on user data and a secret
    token_data = f"{user_id}:{email}:beta_auth_secret"
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
        
        # Find user by token in both collections
        user_data = await db.beta_users.find_one({"access_token": token})
        if not user_data:
            user_data = await db.simple_users.find_one({"access_token": token})
        
        if user_data:
            # Remove MongoDB _id field to avoid ObjectId serialization issues
            if '_id' in user_data:
                del user_data['_id']
            return BetaUser(**user_data)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except HTTPException:
        raise
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
    """Register new user with name + email + master code"""
    try:
        # Registration endpoint is deprecated in Phase 2 system
        # Only admin-managed user creation is allowed
        raise HTTPException(status_code=403, detail="Registration is disabled. Contact admin for account creation.")
        
        # Check if user already exists
        existing_user = await db.beta_users.find_one({"email": request.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists. Please login instead.")
        
        # Create new user with auto-registration
        user_name = request.name.strip() if request.name else request.email.split('@')[0].replace('.', ' ').title()
        
        user = BetaUser(
            email=request.email,
            personal_code="***",  # Don't store master code
            name=user_name,
            role="Manager",
            department="Management",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc)
        )
        
        # Save new user to beta_users collection
        user_dict = user.dict()
        await db.beta_users.insert_one(user_dict)
        
        # Generate access token
        access_token = generate_access_token(user.id, user.email)
        
        # Update token
        await db.beta_users.update_one(
            {"email": request.email},
            {"$set": {
                "access_token": access_token
            }}
        )
        
        # Return response
        user_response = user.copy()
        user_response.personal_code = "***"
        user_response.access_token = None
        
        return LoginResponse(access_token=access_token, user=user_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/auth/login", response_model=LoginResponse)
async def admin_managed_login(request: LoginRequest):
    """Phase 2: Admin-managed login - only pre-registered users can login"""
    try:
        # Look for existing user in both collections (no auto-registration)
        user_data = await db.beta_users.find_one({"email": request.email})
        if not user_data:
            user_data = await db.simple_users.find_one({"email": request.email})
        
        # If user doesn't exist, reject immediately
        if not user_data:
            logger.warning(f"Login attempt for non-registered email: {request.email}")
            raise HTTPException(status_code=401, detail="Invalid email or personal code")
        
        # Remove MongoDB _id field to avoid ObjectId serialization issues
        if '_id' in user_data:
            del user_data['_id']
        
        user = BetaUser(**user_data)
        
        # Verify personal code matches
        if user.personal_code != request.personal_code:
            logger.warning(f"Invalid personal code for user: {request.email}")
            raise HTTPException(status_code=401, detail="Invalid email or personal code")
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {request.email}")
            raise HTTPException(status_code=401, detail="Account is inactive")
        
        # Special check: Always ensure layth.bunni is Admin
        if user.email == "layth.bunni@adamsmithinternational.com" and user.role != "Admin":
            # Update user role to Admin in database
            collection = db.beta_users if await db.beta_users.find_one({"email": user.email}) else db.simple_users
            await collection.update_one(
                {"email": user.email},
                {"$set": {"role": "Admin"}}
            )
            user.role = "Admin"
        
        # Generate access token
        access_token = secrets.token_urlsafe(32)
        
        # Update last login and access token
        collection = db.beta_users if await db.beta_users.find_one({"email": user.email}) else db.simple_users
        await collection.update_one(
            {"email": user.email},
            {"$set": {
                "last_login": datetime.now(timezone.utc),
                "access_token": access_token
            }}
        )
        
        logger.info(f"Successful login for pre-registered user: {user.email} (Role: {user.role})")
        
        # Return response (hide sensitive data)
        user_response = user.copy()
        user_response.personal_code = "***"  # Hide personal code in response
        user_response.access_token = None
        
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
    user_response.access_token = None  # Don't expose token
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

@api_router.get("/documents/admin", response_model=List[Document])
async def get_documents_admin(admin_user: BetaUser = Depends(require_admin)):
    """Get all documents for admin review - REQUIRES ADMIN ROLE"""
    documents = await db.documents.find().sort("uploaded_at", -1).to_list(1000)
    return [Document(**doc) for doc in documents]

# Admin User Management Endpoints
@api_router.get("/admin/users")
async def get_all_users(current_user: BetaUser = Depends(get_current_user)):
    """Get all users for admin management"""
    try:
        # Verify admin access
        if current_user.role != 'Admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get users from both collections
        beta_users = await db.beta_users.find({}, {"access_token": 0}).to_list(length=None)
        simple_users = await db.simple_users.find({}, {"access_token": 0}).to_list(length=None)
        
        # Combine all users
        all_users = []
        
        # Process beta_users
        for user in beta_users:
            if '_id' in user:
                del user['_id']
            user.setdefault('role', 'User')
            user.setdefault('department', 'Unassigned')
            user.setdefault('is_active', True)
            user.setdefault('name', user.get('email', '').split('@')[0].title())
            all_users.append(user)
        
        # Process simple_users
        for user in simple_users:
            if '_id' in user:
                del user['_id']
            user.setdefault('role', 'Manager')  # Default for simple users
            user.setdefault('department', 'Management')
            user.setdefault('is_active', True)
            user.setdefault('name', user.get('name', user.get('email', '').split('@')[0].title()))
            all_users.append(user)
        
        # Remove duplicates based on email
        seen_emails = set()
        unique_users = []
        for user in all_users:
            if user['email'] not in seen_emails:
                seen_emails.add(user['email'])
                unique_users.append(user)
        
        return unique_users
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")

@api_router.put("/admin/users/{user_id}")
async def update_user_admin(
    user_id: str, 
    user_data: dict,
    current_user: BetaUser = Depends(get_current_user)
):
    """Update user details and permissions (admin only)"""
    try:
        # Verify admin access
        if current_user.role != 'Admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Handle role - accept both 'role' and 'boost_role' from frontend
        role_value = user_data.get('role') or user_data.get('boost_role')
        
        # Handle business unit
        business_unit_id = user_data.get('business_unit_id')
        business_unit_name = None
        
        # If business_unit_id is provided and not 'none', get the business unit name
        if business_unit_id and business_unit_id != 'none':
            try:
                unit = await db.boost_business_units.find_one({"id": business_unit_id})
                if unit:
                    business_unit_name = unit["name"]
            except Exception as e:
                logger.warning(f"Could not fetch business unit {business_unit_id}: {e}")
        
        update_data = {
            "role": role_value,
            "boost_role": role_value,  # Keep both for consistency
            "department": user_data.get('department'),
            "is_active": user_data.get('is_active', True),
            "name": user_data.get('name'),
            "business_unit_id": business_unit_id if business_unit_id != 'none' else None,
            "business_unit_name": business_unit_name,
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Try to update user in beta_users first
        result = await db.beta_users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        # If not found in beta_users, try simple_users
        if result.matched_count == 0:
            result = await db.simple_users.update_one(
                {"id": user_id},
                {"$set": update_data}
            )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"Admin {current_user.email} updated user {user_id} with role {user_data.get('role')}")
        return {"message": "User updated successfully", "updated_fields": update_data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

@api_router.delete("/admin/users/{user_id}")
async def delete_user_admin(
    user_id: str,
    current_user: BetaUser = Depends(get_current_user)
):
    """Delete a user (admin only)"""
    try:
        # Verify admin access
        if current_user.role != 'Admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Prevent admin from deleting themselves
        if current_user.id == user_id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        # Try to delete from beta_users first
        result = await db.beta_users.delete_one({"id": user_id})
        
        # If not found in beta_users, try simple_users
        if result.deleted_count == 0:
            result = await db.simple_users.delete_one({"id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"Admin {current_user.email} deleted user {user_id}")
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")

@api_router.get("/admin/stats")
async def get_admin_stats(current_user: BetaUser = Depends(get_current_user)):
    """Get system statistics for admin dashboard"""
    try:
        # Verify admin access
        if current_user.role != 'Admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get counts from various collections
        total_users = await db.beta_users.count_documents({})
        active_users = await db.beta_users.count_documents({"is_active": True})
        total_tickets = await db.boost_tickets.count_documents({})
        open_tickets = await db.boost_tickets.count_documents({"status": {"$nin": ["resolved", "closed"]}})
        total_documents = await db.documents.count_documents({})
        total_sessions = await db.chat_sessions.count_documents({})
        
        return {
            "totalUsers": total_users,
            "activeUsers": active_users,
            "totalTickets": total_tickets,
            "openTickets": open_tickets,
            "totalDocuments": total_documents,
            "totalSessions": total_sessions
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching admin stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch admin stats")

@api_router.post("/admin/users")
async def create_user_admin(
    user_data: dict,
    current_user: BetaUser = Depends(get_current_user)
):
    """Create a new user (Layth only)"""
    try:
        logger.info(f"User creation attempt by: {current_user.email}")
        
        # Verify admin access
        if current_user.role != 'Admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Restrict user creation to only Layth
        if current_user.email != "layth.bunni@adamsmithinternational.com":
            raise HTTPException(status_code=403, detail="Only Layth can create new users")
        
        logger.info(f"Creating user with data: {user_data}")
        
        # Validate required fields
        if not user_data.get('email') or not user_data.get('name'):
            raise HTTPException(status_code=400, detail="Email and name are required")
        
        # Check if user already exists in both collections
        existing_simple = await db.simple_users.find_one({"email": user_data['email']})
        existing_beta = await db.beta_users.find_one({"email": user_data['email']})
        
        if existing_simple or existing_beta:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create new user ID and generate personal code
        user_id = str(uuid.uuid4())
        personal_code = generate_personal_code()
        
        logger.info(f"Generated user_id: {user_id}, personal_code: {personal_code}")
        
        # Create new user document
        new_user_doc = {
            "id": user_id,
            "email": user_data['email'],
            "name": user_data['name'],
            "personal_code": personal_code,  # Generate 6-digit code
            "role": user_data.get('role', 'User'),  # Default to 'User' role
            "department": user_data.get('department'),
            "business_unit_id": user_data.get('business_unit_id'),
            "is_active": user_data.get('is_active', True),
            "created_at": datetime.now(timezone.utc),
            "last_login": None,
            "access_token": None
        }
        
        logger.info(f"About to insert user document: {new_user_doc}")
        
        # Insert into simple_users collection
        result = await db.simple_users.insert_one(new_user_doc.copy())  # Use copy to avoid modifying original
        
        logger.info(f"Insert result: {result.inserted_id}")
        
        if result.inserted_id:
            # Create clean response without sensitive data and ensure JSON serializable
            response_user = {
                "id": new_user_doc["id"],
                "email": new_user_doc["email"],
                "name": new_user_doc["name"],
                "role": new_user_doc["role"],
                "department": new_user_doc.get("department"),
                "business_unit_id": new_user_doc.get("business_unit_id"),
                "is_active": new_user_doc["is_active"],
                "created_at": new_user_doc["created_at"].isoformat()
            }
            
            logger.info(f"Returning user creation response with ID: {response_user.get('id')}")
            return response_user
        else:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to create user")

@api_router.post("/admin/users/{user_id}/regenerate-code")
async def regenerate_user_code(
    user_id: str,
    current_user: BetaUser = Depends(get_current_user)
):
    """Regenerate personal code for a user (Layth only)"""
    try:
        # Verify admin access
        if current_user.role != 'Admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Restrict to only Layth
        if current_user.email != "layth.bunni@adamsmithinternational.com":
            raise HTTPException(status_code=403, detail="Only Layth can regenerate codes")
        
        # Generate new personal code
        new_personal_code = generate_personal_code()
        
        # Try to update user in beta_users first
        result = await db.beta_users.update_one(
            {"id": user_id},
            {"$set": {"personal_code": new_personal_code}}
        )
        
        # If not found in beta_users, try simple_users
        if result.matched_count == 0:
            result = await db.simple_users.update_one(
                {"id": user_id},
                {"$set": {"personal_code": new_personal_code}}
            )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"Personal code regenerated for user {user_id} by {current_user.email}")
        return {"message": "Personal code regenerated successfully", "new_code": new_personal_code}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating code: {e}")
        raise HTTPException(status_code=500, detail="Failed to regenerate code")

@api_router.get("/admin/layth-credentials")
async def get_layth_credentials(
    current_user: BetaUser = Depends(get_current_user)
):
    """Get Layth's credentials for Phase 1 testing (temp endpoint)"""
    try:
        # Verify this is Layth himself requesting
        if current_user.email != "layth.bunni@adamsmithinternational.com":
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get Layth's user record to show his personal code
        layth_user = await db.simple_users.find_one({"email": "layth.bunni@adamsmithinternational.com"})
        if not layth_user:
            layth_user = await db.beta_users.find_one({"email": "layth.bunni@adamsmithinternational.com"})
        
        if layth_user:
            return {
                "email": layth_user["email"],
                "personal_code": layth_user.get("personal_code", "Not found"),
                "role": layth_user.get("role", "Unknown"),
                "id": layth_user.get("id")
            }
        else:
            raise HTTPException(status_code=404, detail="Layth not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Layth credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to get credentials")

@api_router.post("/auth/logout")
async def logout(current_user: BetaUser = Depends(get_current_user)):
    """Logout user and clear access token"""
    try:
        # Clear access token from database
        await db.simple_users.update_one(
            {"id": current_user.id},
            {"$set": {"access_token": None}}
        )
        
        # Also check beta_users collection
        await db.beta_users.update_one(
            {"id": current_user.id},
            {"$set": {"access_token": None}}
        )
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

# Include the router in the main app
app.include_router(api_router)

# Enhanced CORS middleware with explicit OPTIONS handling
# @app.middleware("http")
# async def enhanced_cors_middleware(request: Request, call_next):
#     """Enhanced CORS middleware to handle all cross-origin requests"""
    
#     # Get origin from request
#     origin = request.headers.get("origin")
#     allowed_origins = [
#         "https://asiaihub.com",
#         "https://www.asiaihub.com", 
#         "https://ai-workspace-17.emergent.host",
#         "http://localhost:3000",
#         "https://doc-embeddings.preview.emergentagent.com"
#     ]
    
#     # Handle preflight OPTIONS requests
#     if request.method == "OPTIONS":
#         response = JSONResponse(status_code=200, content={})
        
#         # Set CORS headers for preflight
#         if origin and (origin in allowed_origins or origin.endswith('.emergentagent.com')):
#             response.headers["Access-Control-Allow-Origin"] = origin
#             response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
#             response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, X-Org-Unit, X-API-Key"
#             response.headers["Access-Control-Allow-Credentials"] = "true"
#             response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours
#             response.headers["Vary"] = "Origin"
        
#         return response
    
#     # Process normal request
#     try:
#         response = await call_next(request)
        
#         # Add CORS headers to response
#         if origin and (origin in allowed_origins or origin.endswith('.emergentagent.com')):
#             response.headers["Access-Control-Allow-Origin"] = origin
#             response.headers["Access-Control-Allow-Credentials"] = "true"
#             response.headers["Vary"] = "Origin"
            
#         return response
        
#     except Exception as e:
#         # Ensure CORS headers on error responses too
#         error_response = JSONResponse(
#             status_code=500,
#             content={"detail": "Internal server error - service temporarily unavailable"}
#         )
        
#         if origin and (origin in allowed_origins or origin.endswith('.emergentagent.com')):
#             error_response.headers["Access-Control-Allow-Origin"] = origin
#             error_response.headers["Access-Control-Allow-Credentials"] = "true"
#             error_response.headers["Vary"] = "Origin"
            
#         logger.error(f"Unhandled error in {request.url}: {str(e)}")
#         return error_response

# Keep the original CORS middleware as backup

# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        await client.admin.command('ping')
        return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
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