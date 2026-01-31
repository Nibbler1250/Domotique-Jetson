"""Emails/Invoices API endpoints for viewing and managing invoices."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.response import api_response
from app.services.emails import get_email_service

router = APIRouter(prefix="/emails", tags=["emails"])


class TodoUpdateSchema(BaseModel):
    """Schema for updating a todo status."""

    status: str  # pending, completed, cancelled


# ============================================================================
# Invoices
# ============================================================================


@router.get("", response_model=dict[str, Any])
async def list_invoices(
    category: str | None = None,
    is_paid: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List invoices with optional filtering."""
    service = get_email_service()
    invoices = await service.get_invoices(
        category=category,
        is_paid=is_paid,
        limit=limit,
        offset=offset,
    )
    return api_response(invoices)


@router.get("/stats", response_model=dict[str, Any])
async def get_invoice_stats() -> dict[str, Any]:
    """Get invoice statistics by category."""
    service = get_email_service()
    stats = await service.get_invoice_stats()
    return api_response(stats)


@router.get("/upcoming", response_model=dict[str, Any])
async def get_upcoming_due_dates(limit: int = 10) -> dict[str, Any]:
    """Get invoices with upcoming due dates."""
    service = get_email_service()
    upcoming = await service.get_upcoming_due_dates(limit=limit)
    return api_response(upcoming)


@router.post("/{invoice_id}/mark-paid", response_model=dict[str, Any])
async def mark_invoice_paid(invoice_id: int) -> dict[str, Any]:
    """Mark an invoice as paid."""
    service = get_email_service()
    success = await service.mark_invoice_paid(invoice_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found or update failed",
        )
    return api_response({"success": True, "invoice_id": invoice_id})


# ============================================================================
# Todos (Invoice-related tasks)
# ============================================================================


@router.get("/todos", response_model=dict[str, Any])
async def list_todos(
    status_filter: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """List invoice-related todos."""
    service = get_email_service()
    todos = await service.get_todos(status=status_filter, limit=limit)
    return api_response(todos)


@router.patch("/todos/{todo_id}", response_model=dict[str, Any])
async def update_todo(
    todo_id: int,
    update_data: TodoUpdateSchema,
) -> dict[str, Any]:
    """Update a todo's status."""
    service = get_email_service()
    todo = await service.update_todo_status(todo_id, update_data.status)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    return api_response(todo)


# ============================================================================
# One Page (Trading emails)
# ============================================================================


@router.get("/onepage", response_model=dict[str, Any])
async def list_onepage_emails(limit: int = 20) -> dict[str, Any]:
    """List One Page trading newsletter emails."""
    service = get_email_service()
    emails = await service.get_onepage_emails(limit=limit)
    return api_response(emails)


# ============================================================================
# Processing
# ============================================================================


@router.get("/logs", response_model=dict[str, Any])
async def get_processing_logs(limit: int = 10) -> dict[str, Any]:
    """Get recent email processing logs."""
    service = get_email_service()
    logs = await service.get_processing_logs(limit=limit)
    return api_response(logs)


@router.post("/run-sorter", response_model=dict[str, Any])
async def run_email_sorter() -> dict[str, Any]:
    """Manually run the Gmail invoice sorter."""
    service = get_email_service()
    result = await service.run_sorter()
    return api_response(result)


@router.get("/health", response_model=dict[str, Any])
async def check_email_service_health() -> dict[str, Any]:
    """Check if the email service on Jetson is available."""
    service = get_email_service()
    available = await service.is_available()
    return api_response({
        "available": available,
        "host": "192.168.1.118",
        "service": "gmail_invoice_sorter",
    })
