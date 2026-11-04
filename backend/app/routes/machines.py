from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..db import connect

router = APIRouter(prefix="/api")


class MachineCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    machine_type: str = Field(min_length=1, max_length=120)
    location: str | None = Field(default=None, max_length=160)
    hourly_rate: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    available: bool = True

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


class MachineUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    machine_type: str | None = Field(default=None, min_length=1, max_length=120)
    location: str | None = Field(default=None, max_length=160)
    hourly_rate: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    available: bool | None = None

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

    @field_validator("available")
    @classmethod
    def require_availability(cls, value):
        if value is None:
            raise ValueError("Availability must be true or false")
        return value


@router.get("/machines")
def machines():
    with connect() as con:
        return [dict(row) for row in con.execute("SELECT * FROM machines ORDER BY id DESC")]


@router.post("/machines", status_code=201)
def create_machine(payload: MachineCreate):
    data = payload.model_dump()
    with connect() as con:
        cursor = con.execute(
            """INSERT INTO machines(name, machine_type, location, hourly_rate, available)
            VALUES (?, ?, ?, ?, ?)""",
            (data["name"], data["machine_type"], data["location"], data["hourly_rate"], int(data["available"])),
        )
        row = con.execute("SELECT * FROM machines WHERE id=?", (cursor.lastrowid,)).fetchone()
    return dict(row)


@router.patch("/machines/{machine_id}")
def update_machine(machine_id: int, payload: MachineUpdate):
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(422, "At least one field is required")
    if "available" in updates and updates["available"] is not None:
        updates["available"] = int(updates["available"])

    with connect() as con:
        if not con.execute("SELECT 1 FROM machines WHERE id=?", (machine_id,)).fetchone():
            raise HTTPException(404, "Machine listing not found")
        assignments = ", ".join(f"{field}=?" for field in updates)
        con.execute(
            f"UPDATE machines SET {assignments} WHERE id=?",
            (*updates.values(), machine_id),
        )
        row = con.execute("SELECT * FROM machines WHERE id=?", (machine_id,)).fetchone()
    return dict(row)