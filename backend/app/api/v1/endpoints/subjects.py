from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select, asc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db.models.subject import Subject
from app.schemas.subject import SubjectRead
from app.core.id_codec import encode_id
from app.db.models.subject_case import SubjectCase

# Simple authenticated listing for subjects
router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/subjects", response_model=List[SubjectRead], summary="List subjects")
async def list_subjects(db: AsyncSession = Depends(get_db)) -> List[SubjectRead]:
    q = select(Subject).order_by(asc(Subject.last_name), asc(Subject.first_name))
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/subjects/select", summary="List subjects for selection with enriched display")
async def list_subjects_for_select(db: AsyncSession = Depends(get_db)):
    # Base: subject fields + has_pic boolean
    q = select(
        Subject.id,
        Subject.first_name,
        Subject.last_name,
        Subject.nicknames,
        Subject.phone,
        Subject.email,
        Subject.dangerous,
        Subject.danger,
        Subject.profile_pic.isnot(None).label("has_pic"),
        # any subject_case rows for this subject?
        func.count(SubjectCase.id).label("case_count"),
    ).join(SubjectCase, SubjectCase.subject_id == Subject.id, isouter=True)
    q = q.group_by(
        Subject.id,
        Subject.first_name,
        Subject.last_name,
        Subject.nicknames,
        Subject.phone,
        Subject.email,
        Subject.dangerous,
        Subject.danger,
        Subject.profile_pic,
    )
    q = q.order_by(asc(Subject.last_name), asc(Subject.first_name))

    rows = (await db.execute(q)).all()

    items = []
    for sid, first, last, nicknames, phone, email, dangerous, danger, has_pic, case_count in rows:
        # Compose display name with nicknames inserted between first and last if present
        nickname_part = f' "{nicknames.strip()}"' if nicknames and str(nicknames).strip() else ""
        display_name = f"{first}{nickname_part} {last}".strip()
        items.append({
            "id": encode_id("subject", int(sid)),
            "name": display_name,
            "phone": phone,
            "email": email,
            "photo_url": f"/api/v1/media/pfp/subject/{encode_id('subject', int(sid))}?s=sm" if has_pic else "/images/pfp-generic.png",
            "has_subject_case": (int(case_count or 0) > 0),
            "dangerous": bool(dangerous),
            "danger": danger,
        })

    return items
