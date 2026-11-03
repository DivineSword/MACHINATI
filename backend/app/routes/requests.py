import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db import connect

router = APIRouter(prefix="/api")


class StatusUpdate(BaseModel):
    status: str


@router.get("/requests")
def list_requests():
    with connect() as con:
        rows = con.execute("SELECT * FROM requests ORDER BY id DESC LIMIT 200").fetchall()
    return [{**dict(row), "payload": json.loads(row["payload"])} for row in rows]


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