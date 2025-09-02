from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.id_codec import decode_id, OpaqueIdError, encode_id
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db.models.case import Case
from app.db.models.subject import Subject


router = APIRouter(prefix="/cases")


# ---------- Helper utilities ----------

def _decode_or_404(model: str, opaque_id: str) -> int:
    try:
        return decode_id(model, opaque_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail=f"{model.replace('_', ' ').title()} not found")


@router.get("/select", summary="List active cases for selection", dependencies=[Depends(get_current_user)])
async def list_cases_for_select(db: AsyncSession = Depends(get_db)):
    # Only active cases
    q = (
        select(
            Case.id.label("case_id"),
            Subject.id.label("subject_id"),
            Subject.first_name,
            Subject.last_name,
            Subject.profile_pic.isnot(None).label("has_pic"),
        )
        .join(Subject, Subject.id == Case.subject_id)
        .where(Case.inactive == False)  # noqa: E712
        .order_by(asc(Subject.last_name), asc(Subject.first_name))
    )

    rows = (await db.execute(q)).all()

    items = []
    for case_id, subject_id, first, last, has_pic in rows:
        items.append({
            "id": encode_id("case", int(case_id)),
            "raw_db_id": int(case_id),
            "name": f"{first} {last}".strip(),
            "photo_url": f"/api/v1/media/pfp/subject/{encode_id('subject', int(subject_id))}?s=xs" if has_pic else "/images/pfp-generic.png",
        })

    return items
