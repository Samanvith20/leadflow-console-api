from fastapi import APIRouter, HTTPException, Request

from app.api.dependencies import DatabaseSession
from app.schemas.intake_event import IntakeEventReceipt
from app.services.webhooks import WebhookError, WebhookService

router=APIRouter(prefix="/api/v1/webhooks",tags=["webhooks"])

@router.post("/{source_public_id}",response_model=IntakeEventReceipt,status_code=202)
async def receive(source_public_id:str,request:Request,db:DatabaseSession)->IntakeEventReceipt:
    """Accept only recent HMAC-signed raw JSON that matches this source's configured field allowlist."""
    try:
        event=WebhookService(db).receive(source_public_id,await request.body(),request.headers.get("X-Leadflow-Timestamp"),request.headers.get("X-Leadflow-Signature"))
        return IntakeEventReceipt(receipt_id=event.id,status=event.status)
    except WebhookError as error: raise HTTPException(error.status_code,error.detail) from error
