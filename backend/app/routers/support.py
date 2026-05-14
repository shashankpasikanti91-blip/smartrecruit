"""
Support chatbot router for SRP SmartRecruit v3.2
Handle support tickets and chatbot interactions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database.connection import get_db
from app.schemas import SupportTicketCreate, SupportTicketResponse
from app.auth.dependencies import get_optional_user, get_current_admin_user, get_current_user
from app.models.user import User
from app.models.support import SupportTicket

router = APIRouter(prefix="/api/support", tags=["Support"])


@router.post("/ticket", status_code=status.HTTP_201_CREATED)
async def create_support_ticket(
    ticket_data: SupportTicketCreate,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Create support ticket from chatbot
    
    Works for both authenticated and anonymous users
    """
    ticket = SupportTicket(
        user_id=current_user.id if current_user else None,
        user_email=ticket_data.user_email or (current_user.email if current_user else None),
        message=ticket_data.message,
        category=ticket_data.category,
        status="open"
    )
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    return {
        "id": ticket.id,
        "message": "Support ticket created successfully",
        "ticket_number": f"TICKET-{ticket.id:06d}",
        "status": ticket.status
    }


@router.get("/tickets")
async def list_user_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """List support tickets for current user"""
    tickets = db.query(SupportTicket).filter(
        SupportTicket.user_id == current_user.id
    ).order_by(SupportTicket.created_at.desc()).limit(limit).all()
    
    return {
        "tickets": [
            {
                "id": t.id,
                "ticket_number": f"TICKET-{t.id:06d}",
                "message": t.message,
                "category": t.category,
                "status": t.status,
                "admin_reply": t.admin_reply,
                "created_at": t.created_at,
                "updated_at": t.updated_at
            }
            for t in tickets
        ]
    }


@router.get("/admin/tickets")
async def list_all_tickets(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    status_filter: Optional[str] = None,
    limit: int = 50
):
    """
    Admin endpoint: List all support tickets
    
    Requires admin role
    """
    query = db.query(SupportTicket)
    
    if status_filter:
        query = query.filter(SupportTicket.status == status_filter)
    
    tickets = query.order_by(SupportTicket.created_at.desc()).limit(limit).all()
    
    return {
        "tickets": [
            {
                "id": t.id,
                "ticket_number": f"TICKET-{t.id:06d}",
                "user_id": t.user_id,
                "user_email": t.user_email,
                "message": t.message,
                "category": t.category,
                "priority": t.priority,
                "status": t.status,
                "admin_reply": t.admin_reply,
                "created_at": t.created_at,
                "updated_at": t.updated_at
            }
            for t in tickets
        ],
        "total": len(tickets)
    }


@router.patch("/admin/ticket/{ticket_id}")
async def update_ticket(
    ticket_id: int,
    admin_reply: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint: Update support ticket
    
    Requires admin role
    """
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    if admin_reply:
        ticket.admin_reply = admin_reply
    if status:
        ticket.status = status
    if priority:
        ticket.priority = priority
    
    db.commit()
    db.refresh(ticket)
    
    return {
        "message": "Ticket updated successfully",
        "ticket": {
            "id": ticket.id,
            "status": ticket.status,
            "priority": ticket.priority,
            "admin_reply": ticket.admin_reply
        }
    }
