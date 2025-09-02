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
from datetime import datetime, timezone
import aiofiles
import json
from enum import Enum
import asyncio

# Import emergent integrations
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="ASI OS - AI-Powered Operations Platform")

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
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Department(str, Enum):
    USER_ACCESS = "User & Access Management"
    CONTRACTS = "Contracts & Change Log"
    FINANCE = "Finance & Purchasing"
    PROJECT = "Project & Performance"
    LEAVE = "Leave & People Management"
    SYSTEM_IT = "System & IT Support"
    KNOWLEDGE = "Knowledge Base Requests"

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    END_USER = "end_user"

# Database Models
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
    assigned_to: Optional[str] = None
    sla_due: Optional[datetime] = None
    attachments: List[str] = []
    chat_session_id: Optional[str] = None

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
    document_ids: List[str] = []

class ChatResponse(BaseModel):
    session_id: str
    response: str
    suggested_ticket: Optional[Dict[str, Any]] = None

class TicketCreate(BaseModel):
    subject: str
    description: str
    department: Department
    priority: TicketPriority = TicketPriority.MEDIUM
    category: str = ""
    sub_category: str = ""

class FinanceSOPUpdate(BaseModel):
    prior_month_reviewed: Optional[bool] = None
    monthly_reports_prepared: Optional[bool] = None
    budget_variance_analyzed: Optional[bool] = None
    forecasts_updated: Optional[bool] = None
    review_meeting_held: Optional[bool] = None
    reports_approved: Optional[bool] = None
    results_communicated: Optional[bool] = None
    notes: Optional[str] = None

# Utility Functions
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
    """Process RAG query with uploaded documents"""
    try:
        # Get documents from database
        documents = []
        if document_ids:
            for doc_id in document_ids:
                doc = await db.documents.find_one({"id": doc_id})
                if doc:
                    documents.append(doc)
        
        # Initialize chat with GPT-5
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message="""You are an AI assistant for an operations platform. You help with support tickets, 
            policy questions, and operational guidance. When answering questions:
            
            1. Use the uploaded documents as your primary knowledge source
            2. Provide clear, actionable answers
            3. If a question requires creating a support ticket, suggest it
            4. Reference specific policies or procedures when applicable
            5. Be concise but comprehensive
            
            If you determine a support ticket should be created, include in your response:
            TICKET_SUGGESTION: {subject: "...", description: "...", department: "..."}"""
        ).with_model("openai", "gpt-5")
        
        # Prepare file attachments for Gemini (if available)
        file_contents = []
        context_text = ""
        
        if documents:
            # Add document context to message for GPT-5
            context_text = "\n\nDocument Context:\n"
            for doc in documents:
                context_text += f"- {doc['original_name']}: {doc['filename']}\n"
        
        user_message = UserMessage(
            text=f"{message}{context_text}"
        )
        
        response = await chat.send_message(user_message)
        
        # Check if response suggests creating a ticket
        suggested_ticket = None
        if "TICKET_SUGGESTION:" in response:
            try:
                ticket_part = response.split("TICKET_SUGGESTION:")[1].strip()
                # Simple parsing for ticket suggestion
                if "{" in ticket_part:
                    suggested_ticket = {"create_ticket": True, "suggestion": ticket_part}
            except:
                pass
        
        return {
            "response": response.replace("TICKET_SUGGESTION:", "").strip(),
            "suggested_ticket": suggested_ticket
        }
        
    except Exception as e:
        logger.error(f"Error in RAG processing: {e}")
        return {
            "response": "I apologize, but I encountered an error processing your request. Please try again or contact support.",
            "suggested_ticket": None
        }

# API Routes
@api_router.get("/")
async def root():
    return {"message": "ASI OS - AI-Powered Operations Platform API"}

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
            message="Document uploaded successfully"
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document")

@api_router.get("/documents", response_model=List[Document])
async def get_documents():
    """Get all uploaded documents"""
    documents = await db.documents.find().to_list(1000)
    return [Document(**doc) for doc in documents]

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
        
        # Save AI response
        ai_message = ChatMessage(
            session_id=request.session_id,
            role="assistant",
            content=result["response"]
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
            suggested_ticket=result["suggested_ticket"]
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

# Ticket Routes
@api_router.post("/tickets", response_model=Ticket)
async def create_ticket(ticket_data: TicketCreate):
    """Create a new support ticket"""
    try:
        # Auto-categorize with AI
        categorization = await categorize_ticket_with_ai(ticket_data.subject, ticket_data.description)
        
        ticket = Ticket(
            subject=ticket_data.subject,
            description=ticket_data.description,
            department=ticket_data.department,
            priority=ticket_data.priority,
            category=categorization["category"],
            sub_category=categorization["sub_category"]
        )
        
        await db.tickets.insert_one(ticket.dict())
        return ticket
        
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ticket")

@api_router.get("/tickets", response_model=List[Ticket])
async def get_tickets():
    """Get all tickets"""
    tickets = await db.tickets.find().sort("created_at", -1).to_list(1000)
    return [Ticket(**ticket) for ticket in tickets]

@api_router.get("/tickets/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: str):
    """Get a specific ticket"""
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return Ticket(**ticket)

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
        open_tickets = await db.tickets.count_documents({"status": "open"})
        total_documents = await db.documents.count_documents({})
        total_chat_sessions = await db.chat_sessions.count_documents({})
        
        # Tickets by department
        pipeline = [
            {"$group": {"_id": "$department", "count": {"$sum": 1}}}
        ]
        tickets_by_dept = await db.tickets.aggregate(pipeline).to_list(None)
        
        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "total_documents": total_documents,
            "total_chat_sessions": total_chat_sessions,
            "tickets_by_department": tickets_by_dept
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard stats")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
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