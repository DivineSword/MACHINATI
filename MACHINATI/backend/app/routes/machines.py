from fastapi import APIRouter

from ..db import connect

router = APIRouter(prefix="/api")


@router.get("/machines")
def machines():
    with connect() as con:
        return [dict(row) for row in con.execute("SELECT * FROM machines ORDER BY id DESC")]