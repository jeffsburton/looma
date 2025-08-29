from enum import Enum
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import StreamingResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db.models.person import Person
from app.db.models.subject import Subject
from app.db.models.team import Team
from app.core.id_codec import decode_id, OpaqueIdError


router = APIRouter(dependencies=[Depends(get_current_user)])


class Kind(str, Enum):
    person = "person"
    subject = "subject"
    team = "team"


async def _get_blob(db: AsyncSession, kind: Kind, pk: int) -> Optional[bytes]:
    model = {Kind.person: Person, Kind.subject: Subject, Kind.team: Team}[kind]
    obj = await db.get(model, pk)
    if not obj:
        return None
    return getattr(obj, "profile_pic", None)


@router.get("/media/pfp/{kind}/{id}", summary="Profile picture (raw bytes or redirect to placeholder)")
async def get_pfp(
    kind: Kind,
    id: str = Path(..., description="Opaque ID"),
    db: AsyncSession = Depends(get_db),
):
    try:
        pk = decode_id(kind.value, id)
    except OpaqueIdError:
        # Hide existence
        raise HTTPException(status_code=404, detail="Not found")

    blob = await _get_blob(db, kind, pk)
    if not blob:
        # Redirect to a static generic avatar served by the frontend
        # Place file at frontend/public/images/pfp-generic.png
        return RedirectResponse(url="/images/pfp-generic.png", status_code=302)

    # Minimal content-type sniff
    media_type = "application/octet-stream"
    if blob.startswith(b"\x89PNG\r\n\x1a\n"):
        media_type = "image/png"
    elif blob.startswith(b"\xff\xd8\xff"):
        media_type = "image/jpeg"
    elif blob.startswith(b"GIF8"):
        media_type = "image/gif"
    elif blob[:4] == b"RIFF" and b"WEBP" in blob[:32]:
        media_type = "image/webp"

    return StreamingResponse(BytesIO(blob), media_type=media_type)
