from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.id_codec import decode_id, OpaqueIdError

router = APIRouter(prefix="/admin")
