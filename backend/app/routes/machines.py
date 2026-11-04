from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..db import connect

router = APIRouter(prefix="/api")


class MachineCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    machine_type: str = Field(min_length=1, max_length=120)
    location: str | None = Field(default=None, max_length=160)
    hourly_rate: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    available: bool = True
    owner_type: Literal['company', 'partner'] = 'company'
    reserved_for_own_use: bool = False
    available_from: date | None = None
    available_to: date | None = None
    compatibility_notes: str | None = Field(default=None, max_length=500)

    @field_validator("name", "machine_type")
    @classmethod
    def require_text(cls, value):
        if not value.strip():
            raise ValueError("Field must not be empty")
        return value.strip()

    @field_validator("location")
    @classmethod
    def clean_location(cls, value):
        return value.strip() or None if value is not None else None

    @field_validator('compatibility_notes')
    @classmethod
    def clean_compatibility_notes(cls, value):
        return value.strip() or None if value is not None else None

    @model_validator(mode='after')
    def validate_availability_window(self):
        if self.available_from and self.available_to and self.available_from > self.available_to:
            raise ValueError('available_from must be on or before available_to')
        return self


class MachineUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    machine_type: str | None = Field(default=None, min_length=1, max_length=120)
    location: str | None = Field(default=None, max_length=160)
    hourly_rate: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    available: bool | None = None
    owner_type: Literal['company', 'partner'] | None = None
    reserved_for_own_use: bool | None = None
    available_from: date | None = None
    available_to: date | None = None
    compatibility_notes: str | None = Field(default=None, max_length=500)

    @field_validator("name", "machine_type")
    @classmethod
    def require_nonempty_text(cls, value):
        if value is None or not value.strip():
            raise ValueError("Field must not be empty")
        return value.strip()

    @field_validator("location")
    @classmethod
    def clean_location(cls, value):
        return value.strip() or None if value is not None else None

    @field_validator('compatibility_notes')
    @classmethod
    def clean_compatibility_notes(cls, value):
        return value.strip() or None if value is not None else None

    @field_validator("available")
    @classmethod
    def require_availability(cls, value):
        if value is None:
            raise ValueError("Availability must be true or false")
        return value

    @field_validator('owner_type')
    @classmethod
    def require_owner_type(cls, value):
        if value is None:
            raise ValueError('Owner type must be company or partner')
        return value

    @field_validator('reserved_for_own_use')
    @classmethod
    def require_reservation_flag(cls, value):
        if value is None:
            raise ValueError('Reservation flag must be true or false')
        return value


@router.get("/machines")
def machines():
    with connect() as con:
        return [dict(row) for row in con.execute("SELECT * FROM machines ORDER BY id DESC")]


@router.post("/machines", status_code=201)
def create_machine(payload: MachineCreate):
    data = payload.model_dump(mode='json')
    with connect() as con:
        cursor = con.execute(
            """INSERT INTO machines(
                name, machine_type, location, hourly_rate, available, owner_type,
                reserved_for_own_use, available_from, available_to, compatibility_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data['name'], data['machine_type'], data['location'], data['hourly_rate'],
             int(data['available']), data['owner_type'], int(data['reserved_for_own_use']),
             data['available_from'], data['available_to'], data['compatibility_notes']),
        )
        row = con.execute("SELECT * FROM machines WHERE id=?", (cursor.lastrowid,)).fetchone()
    return dict(row)


@router.patch("/machines/{machine_id}")
def update_machine(machine_id: int, payload: MachineUpdate):
    updates = payload.model_dump(mode='json', exclude_unset=True)
    if not updates:
        raise HTTPException(422, "At least one field is required")
    if "available" in updates and updates["available"] is not None:
        updates["available"] = int(updates["available"])
    if 'reserved_for_own_use' in updates and updates['reserved_for_own_use'] is not None:
        updates['reserved_for_own_use'] = int(updates['reserved_for_own_use'])

    with connect() as con:
        row = con.execute("SELECT * FROM machines WHERE id=?", (machine_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Machine listing not found")
        available_from = updates.get('available_from', row['available_from'])
        available_to = updates.get('available_to', row['available_to'])
        if available_from and available_to and available_from > available_to:
            raise HTTPException(422, 'available_from must be on or before available_to')
        assignments = ", ".join(f"{field}=?" for field in updates)
        con.execute(
            f"UPDATE machines SET {assignments} WHERE id=?",
            (*updates.values(), machine_id),
        )
        row = con.execute("SELECT * FROM machines WHERE id=?", (machine_id,)).fetchone()
    return dict(row)