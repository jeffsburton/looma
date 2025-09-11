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
from app.db.models.subject import Subject
from app.db.models.social_media_alias import SocialMediaAlias
from app.core.id_codec import decode_id, OpaqueIdError, encode_id

from .case_utils import _decode_or_404, can_user_access_case

router = APIRouter()


# -------- Social Media (social_media) --------
from pydantic import BaseModel
from typing import Optional as _OptionalForSM

class SocialMediaCreate(BaseModel):
    subject_id: Optional[str] = None
    platform_id: Optional[str] = None
    platform_other: Optional[str] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    status_id: Optional[str] = None
    investigated_id: Optional[str] = None
    rule_out: Optional[bool] = None


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
    stat = aliased(RefValue)
    inv = aliased(RefValue)
    q = (
        select(
            SocialMedia.id,
            SocialMedia.subject_id,
            SocialMedia.platform_id,
            SocialMedia.platform_other,
            SocialMedia.url,
            SocialMedia.notes,
            SocialMedia.status_id,
            SocialMedia.investigated_id,
            SocialMedia.rule_out,
            plat.name,
            plat.code,
            stat.name,
            stat.code,
            inv.name,
            inv.code,
            Subject.first_name,
            Subject.last_name,
            Subject.profile_pic,
        )
        .join(plat, plat.id == SocialMedia.platform_id, isouter=True)
        .join(stat, stat.id == SocialMedia.status_id, isouter=True)
        .join(inv, inv.id == SocialMedia.investigated_id, isouter=True)
        .join(Subject, Subject.id == SocialMedia.subject_id, isouter=True)
        .where(SocialMedia.case_id == int(case_db_id))
        .order_by(asc(SocialMedia.id))
    )

    rows = (await db.execute(q)).all()
    items = []
    for (
        sm_id,
        subject_id,
        platform_id,
        platform_other,
        url,
        notes,
        status_id,
        investigated_id,
        rule_out,
        platform_name,
        platform_code,
        status_name,
        status_code,
        inv_name,
        inv_code,
        first_name,
        last_name,
        profile_pic,
    ) in rows:
        photo_url = f"/api/v1/media/pfp/subject/{encode_id('subject', int(subject_id))}?s=sm" if (subject_id is not None and profile_pic) else "/images/pfp-generic.png"
        items.append({
            "id": encode_id("social_media", int(sm_id)),
            "raw_id": int(sm_id),
            "subject": {
                "id": encode_id("subject", int(subject_id)) if subject_id is not None else None,
                "first_name": first_name,
                "last_name": last_name,
                "photo_url": photo_url,
            },
            "platform_id": encode_id("ref_value", int(platform_id)) if platform_id is not None else None,
            "platform_other": platform_other,
            "notes": notes,
            "url": url,
            "platform_name": platform_name,
            "platform_code": platform_code,
            "status_id": encode_id("ref_value", int(status_id)) if status_id is not None else None,
            "status_name": status_name,
            "status_code": status_code,
            "investigated_id": encode_id("ref_value", int(investigated_id)) if investigated_id is not None else None,
            "investigated_name": inv_name,
            "investigated_code": inv_code,
            "rule_out": bool(rule_out) if rule_out is not None else False,
        })

    return items


@router.get("/{case_id}/social-media/{social_media_id}", summary="Get a social media record for a case")
async def get_social_media(
    case_id: str,
    social_media_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    # Allow either opaque id or raw integer id in the path, similar to tasks
    try:
        sm_db_id = int(decode_id("social_media", social_media_id)) if not str(social_media_id).isdigit() else int(social_media_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Social media record not found")

    plat = aliased(RefValue)
    stat = aliased(RefValue)
    inv = aliased(RefValue)

    row = (
        await db.execute(
            select(
                SocialMedia.id,
                SocialMedia.subject_id,
                SocialMedia.platform_id,
                SocialMedia.platform_other,
                SocialMedia.url,
                SocialMedia.notes,
                SocialMedia.status_id,
                SocialMedia.investigated_id,
                SocialMedia.rule_out,
                plat.name,
                plat.code,
                stat.name,
                stat.code,
                inv.name,
                inv.code,
                Subject.first_name,
                Subject.last_name,
                Subject.profile_pic,
            )
            .join(plat, plat.id == SocialMedia.platform_id, isouter=True)
            .join(stat, stat.id == SocialMedia.status_id, isouter=True)
            .join(inv, inv.id == SocialMedia.investigated_id, isouter=True)
            .join(Subject, Subject.id == SocialMedia.subject_id, isouter=True)
            .where(SocialMedia.case_id == int(case_db_id), SocialMedia.id == int(sm_db_id))
        )
    ).one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="Social media record not found")

    (
        sm_id,
        subject_id,
        platform_id,
        platform_other,
        url,
        notes,
        status_id,
        investigated_id,
        rule_out,
        platform_name,
        platform_code,
        status_name,
        status_code,
        inv_name,
        inv_code,
        first_name,
        last_name,
        profile_pic,
    ) = row

    photo_url = f"/api/v1/media/pfp/subject/{encode_id('subject', int(subject_id))}?s=sm" if (subject_id is not None and profile_pic) else "/images/pfp-generic.png"

    item = {
        "id": encode_id("social_media", int(sm_id)),
        "raw_id": int(sm_id),
        "subject": {
            "id": encode_id("subject", int(subject_id)) if subject_id is not None else None,
            "first_name": first_name,
            "last_name": last_name,
            "photo_url": photo_url,
        },
        "platform_id": encode_id("ref_value", int(platform_id)) if platform_id is not None else None,
        "platform_other": platform_other,
        "notes": notes,
        "url": url,
        "platform_name": platform_name,
        "platform_code": platform_code,
        "status_id": encode_id("ref_value", int(status_id)) if status_id is not None else None,
        "status_name": status_name,
        "status_code": status_code,
        "investigated_id": encode_id("ref_value", int(investigated_id)) if investigated_id is not None else None,
        "investigated_name": inv_name,
        "investigated_code": inv_code,
        "rule_out": bool(rule_out) if rule_out is not None else False,
    }

    return item

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

    def _dec_subject(oid: _OptionalForSM[str]):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("subject", s)) if not s.isdigit() else int(s)
        except Exception:
            return None

    row = SocialMedia(
        case_id=int(case_db_id),
        subject_id=_dec_subject(getattr(payload, "subject_id", None)) if hasattr(payload, "subject_id") else None,
        platform_id=_dec_ref(payload.platform_id) if hasattr(payload, "platform_id") else None,
        platform_other=getattr(payload, "platform_other", None),
        notes=getattr(payload, "notes", None),
        url=getattr(payload, "url", None),
        status_id=_dec_ref(getattr(payload, "status_id", None)) if hasattr(payload, "status_id") else None,
        investigated_id=_dec_ref(getattr(payload, "investigated_id", None)) if hasattr(payload, "investigated_id") else None,
        rule_out=bool(getattr(payload, "rule_out", False)) if hasattr(payload, "rule_out") else False,
    )
    
    db.add(row)
    await db.commit()

    return {"ok": True}


class SocialMediaPartial(BaseModel):
    subject_id: Optional[str] = None
    platform_id: Optional[str] = None
    platform_other: Optional[str] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    status_id: Optional[str] = None
    investigated_id: Optional[str] = None
    rule_out: Optional[bool] = None


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
        sm_db_id = int(decode_id("social_media", social_media_id)) if not str(social_media_id).isdigit() else int(social_media_id)
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

    def _dec_subject(oid: _OptionalForSM[str]):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("subject", s)) if not s.isdigit() else int(s)
        except Exception:
            return None

    fields_set = getattr(payload, "model_fields_set", set())

    if "subject_id" in fields_set:
        row.subject_id = _dec_subject(payload.subject_id)
    if "platform_id" in fields_set:
        row.platform_id = _dec_ref(payload.platform_id)
    if "platform_other" in fields_set:
        row.platform_other = payload.platform_other
    if "notes" in fields_set:
        row.notes = payload.notes
    if "url" in fields_set:
        row.url = payload.url
    if "status_id" in fields_set:
        row.status_id = _dec_ref(payload.status_id)
    if "investigated_id" in fields_set:
        row.investigated_id = _dec_ref(payload.investigated_id)
    if "rule_out" in fields_set:
        row.rule_out = bool(payload.rule_out)

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

    # Resolve alias_status_id; if not provided, default to SM_ALIAS "NF" (Waiting),
    # or fall back to the first SM_ALIAS ref value by sort_order/id.
    status_id = _dec_ref(payload.alias_status_id)
    if status_id is None:
        from app.db.models.ref_type import RefType
        # Try preferred code 'NF' under SM_ALIAS
        res = await db.execute(
            select(RefValue.id)
            .join(RefType, RefType.id == RefValue.ref_type_id)
            .where(RefType.code == "SM_ALIAS", RefValue.code == "NF")
        )
        status_id = res.scalar_one_or_none()
        if status_id is None:
            # Fallback: pick the first by sort_order then id
            res2 = await db.execute(
                select(RefValue.id)
                .join(RefType, RefType.id == RefValue.ref_type_id)
                .where(RefType.code == "SM_ALIAS")
                .order_by(asc(RefValue.sort_order), asc(RefValue.id))
                .limit(1)
            )
            status_id = res2.scalar_one_or_none()
        if status_id is None:
            raise HTTPException(status_code=400, detail="Alias status reference values (SM_ALIAS) are not configured")

    row = SocialMediaAlias(
        social_media_id=int(sm_db_id),
        alias_status_id=int(status_id),
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
