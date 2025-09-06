from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db.models.app_user import AppUser
from app.db.models.ref_value import RefValue
from app.db.models.social_media import SocialMedia
from app.db.models.social_media_alias import SocialMediaAlias
from app.core.id_codec import decode_id, OpaqueIdError, encode_id

from .case_utils import _decode_or_404, can_user_access_case

router = APIRouter()


# -------- Social Media (social_media) --------
from pydantic import BaseModel
from typing import Optional as _OptionalForSM

class SocialMediaCreate(BaseModel):
    platform_id: Optional[str] = None
    platform_other: Optional[str] = None
    username: Optional[str] = None
    notes: Optional[str] = None
    link: Optional[str] = None


@router.get("/{case_id}/social-media", summary="List social media for a case")
async def list_social_media(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    plat = aliased(RefValue)
    q = (
        select(
            SocialMedia.id,
            SocialMedia.platform_id,
            SocialMedia.platform_other,
            SocialMedia.url,
            SocialMedia.notes,
            plat.name,
            plat.code,
        )
        .join(plat, plat.id == SocialMedia.platform_id, isouter=True)
        .where(SocialMedia.case_id == int(case_db_id))
        .order_by(asc(SocialMedia.id))
    )

    rows = (await db.execute(q)).all()
    items = []
    for (
        sm_id,
        platform_id,
        platform_other,
        url,
        notes,
        platform_name,
        platform_code,
    ) in rows:
        items.append({
            "id": encode_id("social_media", int(sm_id)),
            "platform_id": encode_id("ref_value", int(platform_id)) if platform_id is not None else None,
            "platform_other": platform_other,
            "username": None,
            "notes": notes,
            "link": url,
            "platform_name": platform_name,
            "platform_code": platform_code,
        })

    return items


@router.post("/{case_id}/social-media", summary="Create a social media record for a case")
async def create_social_media(
    case_id: str,
    payload: SocialMediaCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    def _dec_ref(oid: _OptionalForSM[str]):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("ref_value", s)) if not s.isdigit() else int(s)
        except Exception:
            return None

    row = SocialMedia(
        case_id=int(case_db_id),
        platform_id=_dec_ref(payload.platform_id) if hasattr(payload, "platform_id") else None,
        platform_other=getattr(payload, "platform_other", None),
        notes=getattr(payload, "notes", None),
        url=getattr(payload, "link", None),
    )
    
    db.add(row)
    await db.commit()

    return {"ok": True}


class SocialMediaPartial(BaseModel):
    platform_id: Optional[str] = None
    platform_other: Optional[str] = None
    username: Optional[str] = None
    notes: Optional[str] = None
    link: Optional[str] = None


@router.patch("/{case_id}/social-media/{social_media_id}", summary="Update a social media record for a case")
async def update_social_media(
    case_id: str,
    social_media_id: str,
    payload: SocialMediaPartial = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        sm_db_id = decode_id("social_media", social_media_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Social media record not found")

    row = (await db.execute(select(SocialMedia).where(SocialMedia.id == int(sm_db_id), SocialMedia.case_id == int(case_db_id)))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Social media record not found")

    def _dec_ref(oid: _OptionalForSM[str]):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("ref_value", s)) if not s.isdigit() else int(s)
        except Exception:
            return None

    fields_set = getattr(payload, "model_fields_set", set())

    if "platform_id" in fields_set:
        row.platform_id = _dec_ref(payload.platform_id)
    if "platform_other" in fields_set:
        row.platform_other = payload.platform_other
    if "username" in fields_set:
        # 'username' is not a column on SocialMedia; currently ignored to avoid errors
        pass
    if "notes" in fields_set:
        row.notes = payload.notes
    if "link" in fields_set:
        row.url = payload.link

    await db.commit()
    return {"ok": True}


# -------- Social Media Aliases (social_media_alias) --------
class SocialMediaAliasCreate(BaseModel):
    alias_status_id: Optional[str] = None
    alias: Optional[str] = None
    alias_owner_id: Optional[str] = None

class SocialMediaAliasPartial(BaseModel):
    alias_status_id: Optional[str] = None
    alias: Optional[str] = None
    alias_owner_id: Optional[str] = None


@router.get("/{case_id}/social-media/{social_media_id}/aliases", summary="List aliases for a social media record")
async def list_social_media_aliases(
    case_id: str,
    social_media_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        sm_db_id = decode_id("social_media", social_media_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Social media record not found")

    sm_row = (await db.execute(select(SocialMedia.id).where(SocialMedia.id == int(sm_db_id), SocialMedia.case_id == int(case_db_id)))).scalar_one_or_none()
    if sm_row is None:
        raise HTTPException(status_code=404, detail="Social media record not found")

    st_ref = aliased(RefValue)
    rows = (
        await db.execute(
            select(
                SocialMediaAlias.id,
                SocialMediaAlias.alias_status_id,
                SocialMediaAlias.alias,
                SocialMediaAlias.alias_owner_id,
                st_ref.name,
                st_ref.code,
            ).join(st_ref, st_ref.id == SocialMediaAlias.alias_status_id, isouter=True).where(SocialMediaAlias.social_media_id == int(sm_db_id))
        )
    ).all()

    items = []
    for (
        alias_id,
        alias_status_id,
        alias,
        alias_owner_id,
        status_name,
        status_code,
    ) in rows:
        items.append({
            "id": encode_id("social_media_alias", int(alias_id)),
            "alias_status_id": encode_id("ref_value", int(alias_status_id)) if alias_status_id is not None else None,
            "alias": alias,
            "alias_owner_id": encode_id("person", int(alias_owner_id)) if alias_owner_id is not None else None,
            "status_name": status_name,
            "status_code": status_code,
        })

    return items


@router.post("/{case_id}/social-media/{social_media_id}/aliases", summary="Create an alias for a social media record")
async def create_social_media_alias(
    case_id: str,
    social_media_id: str,
    payload: SocialMediaAliasCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        sm_db_id = decode_id("social_media", social_media_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Social media record not found")

    sm_row = (
        await db.execute(select(SocialMedia.id).where(SocialMedia.id == int(sm_db_id), SocialMedia.case_id == int(case_db_id)))
    ).scalar_one_or_none()
    if sm_row is None:
        raise HTTPException(status_code=404, detail="Social media record not found")

    def _dec_ref(oid: Optional[str]):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("ref_value", s)) if not s.isdigit() else int(s)
        except Exception:
            return None

    def _dec_person(oid: Optional[str]):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("person", s)) if not s.isdigit() else int(s)
        except Exception:
            return None

    row = SocialMediaAlias(
        social_media_id=int(sm_db_id),
        alias_status_id=_dec_ref(payload.alias_status_id),
        alias=getattr(payload, "alias", None),
        alias_owner_id=_dec_person(payload.alias_owner_id),
    )

    db.add(row)
    await db.commit()

    return {"ok": True}


@router.patch(
    "/{case_id}/social-media/{social_media_id}/aliases/{alias_id}",
    summary="Update an alias for a social media record",
)
async def update_social_media_alias(
    case_id: str,
    social_media_id: str,
    alias_id: str,
    payload: SocialMediaAliasPartial = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        sm_db_id = decode_id("social_media", social_media_id)
        alias_db_id = decode_id("social_media_alias", alias_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Record not found")

    # Ensure the social media record belongs to this case
    sm_row = (
        await db.execute(select(SocialMedia.id).where(SocialMedia.id == int(sm_db_id), SocialMedia.case_id == int(case_db_id)))
    ).scalar_one_or_none()
    if sm_row is None:
        raise HTTPException(status_code=404, detail="Social media record not found")

    # Load alias row and ensure it belongs to the social media record
    alias_row = (
        await db.execute(
            select(SocialMediaAlias).where(
                SocialMediaAlias.id == int(alias_db_id),
                SocialMediaAlias.social_media_id == int(sm_db_id),
            )
        )
    ).scalar_one_or_none()
    if alias_row is None:
        raise HTTPException(status_code=404, detail="Alias not found")

    def _dec_ref(oid: Optional[str]):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("ref_value", s)) if not s.isdigit() else int(s)
        except Exception:
            return None

    def _dec_person(oid: Optional[str]):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("person", s)) if not s.isdigit() else int(s)
        except Exception:
            return None

    fields_set = getattr(payload, "model_fields_set", set())

    if "alias_status_id" in fields_set:
        alias_row.alias_status_id = _dec_ref(payload.alias_status_id) or alias_row.alias_status_id
    if "alias" in fields_set:
        alias_row.alias = payload.alias
    if "alias_owner_id" in fields_set:
        alias_row.alias_owner_id = _dec_person(payload.alias_owner_id)

    await db.commit()
    return {"ok": True}
