import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from ..db import connect
from ..priority import machine_compatibility_for, priority_for

router = APIRouter(prefix="/api")


class StatusUpdate(BaseModel):
    status: str


class UrgencyVerification(BaseModel):
    reviewer: str = Field(min_length=1, max_length=80)

    @field_validator('reviewer')
    @classmethod
    def clean_reviewer(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Reviewer must not be empty')
        return value


@router.get("/requests")
def list_requests():
    with connect() as con:
        rows = con.execute("SELECT * FROM requests ORDER BY id DESC LIMIT 200").fetchall()
        machines = [dict(row) for row in con.execute('SELECT * FROM machines')]
    items = []
    for row in rows:
        item = {**dict(row), 'payload': json.loads(row['payload'])}
        item['machine_fit'], item['machine_fit_reason'], item['matching_machines'] = machine_compatibility_for(
            item['payload'], machines
        )
        item['priority_score'], item['priority_reason'] = priority_for(
            item['payload'], item['created_at'], machine_fit=item['machine_fit']
        )
        items.append(item)
    return sorted(items, key=lambda item: (-item['priority_score'], -item['id']))


@router.patch('/requests/{request_id}/urgency-verification')
def verify_urgency(request_id: int, payload: UrgencyVerification):
    with connect() as con:
        row = con.execute('SELECT payload, status FROM requests WHERE id=?', (request_id,)).fetchone()
        if not row:
            raise HTTPException(404, 'Request not found')
        if row['status'] != 'pending_review':
            raise HTTPException(409, 'Only requests pending review can have urgency verified')
        request_payload = json.loads(row['payload'])
        if request_payload.get('urgency_level') not in ('urgent', 'critical'):
            raise HTTPException(409, 'Only declared urgent requests need urgency verification')
        request_payload['verified_by'] = payload.reviewer
        con.execute(
            'UPDATE requests SET payload=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',
            (json.dumps(request_payload, ensure_ascii=False), request_id),
        )
    return {'id': request_id, 'verified_by': payload.reviewer}


@router.patch("/requests/{request_id}/status")
def change_status(request_id: int, payload: StatusUpdate | None = None, status: str | None = None):
    status = payload.status if payload is not None else status
    if status is None:
        raise HTTPException(422, "Status is required")
    if status not in ("pending_review", "approved", "rejected", "completed"):
        raise HTTPException(400, "Invalid status")
    with connect() as con:
        row = con.execute("SELECT status FROM requests WHERE id=?", (request_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Request not found")
        if row["status"] == "draft":
            raise HTTPException(409, "Draft must be confirmed first")
        con.execute(
            "UPDATE requests SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, request_id),
        )
    return {"id": request_id, "status": status}