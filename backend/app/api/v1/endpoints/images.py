from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Body, UploadFile, File as UploadFileParam, Form
from sqlalchemy import select
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db.models.app_user import AppUser
from app.db.models.subject import Subject
from app.db.models.person import Person as PersonModel
from app.db.models.rfi import Rfi
from app.db.models.file import File
from app.db.models.file_subject import FileSubject
from app.core.id_codec import decode_id, OpaqueIdError, encode_id
from app.services.auth import user_has_permission
from app.services.s3 import get_download_link, create_file

from .case_utils import _decode_or_404, can_user_access_case

router = APIRouter()


# ---------------- Images (list and upload) ----------------
@router.get("/{case_id}/images", summary="List images for a case")
async def list_images(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    pk = _decode_or_404("case", case_id)
    # Access control (allow admins with CASES.ALL_CASES)
    if not await user_has_permission(db, current_user.id, "CASES.ALL_CASES"):
        if not await can_user_access_case(db, current_user.id, pk):
            raise HTTPException(status_code=404, detail="Case not found")

    # Join to gather creator/rfi names
    P = PersonModel
    R = Rfi
    I = Image
    q = (
        select(
            I.id,
            I.case_id,
            I.file_name,
            I.created_by_id,
            I.source_url,
            I.where,
            I.notes,
            I.rfi_id,
            I.created_at,
            I.updated_at,
            I.mime_type,
            (P.first_name + sa.literal(" ") + P.last_name).label("created_by_name"),
            R.name.label("rfi_name"),
        )
        .select_from(I)
        .join(P, P.id == I.created_by_id, isouter=True)
        .join(R, R.id == I.rfi_id, isouter=True)
        .where(I.case_id == pk)
        .order_by(sa.desc(I.created_at))
    )

    rows = (await db.execute(q)).all()
    items = []
    image_ids: list[int] = []
    for r in rows:
        rid = int(r.id)
        image_ids.append(rid)
        items.append({
            "id": rid,
            "case_id": int(r.case_id),
            "file_name": r.file_name,
            "created_by_id": int(r.created_by_id) if r.created_by_id is not None else None,
            "source_url": r.source_url,
            "where": r.where,
            "notes": r.notes,
            "rfi_id": int(r.rfi_id) if r.rfi_id is not None else None,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
            "mime_type": r.mime_type,
            # presigned links to S3 objects
            "url": get_download_link("image", rid, file_type=None, thumbnail=False, attachment_filename=r.file_name or "download"),
            "thumb": get_download_link("image", rid, file_type=None, thumbnail=True),
            "storage_slug": None,
            # extras for UI display
            "created_by_name": r.created_by_name if getattr(r, "created_by_name", None) else None,
            "rfi_name": r.rfi_name if getattr(r, "rfi_name", None) else None,
        })

    # Attach subjects per image
    if image_ids:
        IS = ImageSubject
        S = Subject
        subj_rows = (
            await db.execute(
                select(
                    IS.image_id,
                    IS.id.label("link_id"),
                    S.id.label("sid"),
                    S.first_name,
                    S.last_name,
                    S.nicknames,
                    S.profile_pic,
                ).join(S, S.id == IS.subject_id).where(IS.image_id.in_(image_ids))
            )
        ).all()

        # Helper to compose display name
        def _name(first: str | None, last: str | None, nick: str | None) -> str:
            first = (first or "").strip()
            last = (last or "").strip()
            nick_part = f' "{nick.strip()}"' if nick and str(nick).strip() else ""
            return f"{first}{nick_part} {last}".strip()

        by_image: dict[int, list[dict]] = {}
        for row in subj_rows:
            img_id = int(row.image_id)
            sid = int(row.sid)
            photo_url = f"/api/v1/media/pfp/subject/{encode_id('subject', sid)}?s=sm" if getattr(row, 'profile_pic', None) else "/images/pfp-generic.png"
            by_image.setdefault(img_id, []).append({
                "id": int(row.link_id),  # link id
                "subject_id": encode_id("subject", sid),
                "name": _name(row.first_name, row.last_name, row.nicknames),
                "photo_url": photo_url,
            })

        # merge back into items
        by_id = {it["id"]: it for it in items}
        for img_id, subs in by_image.items():
            if img_id in by_id:
                by_id[img_id]["subjects"] = subs
        # ensure others have empty list
        for it in items:
            if "subjects" not in it:
                it["subjects"] = []

    return items


@router.post("/{case_id}/images/upload", summary="Upload image for a case")
async def upload_image(
    case_id: str,
    file: UploadFile = UploadFileParam(...),
    thumbnail: Optional[UploadFile] = UploadFileParam(None),
    source_url: Optional[str] = Form(None),
    where: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    rfi_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    pk = _decode_or_404("case", case_id)
    # Access control (allow admins with CASES.ALL_CASES)
    if not await user_has_permission(db, current_user.id, "CASES.ALL_CASES"):
        if not await can_user_access_case(db, current_user.id, pk):
            raise HTTPException(status_code=404, detail="Case not found")

    # Decode optional rfi_id if provided (opaque)
    rid: Optional[int] = None
    if rfi_id:
        try:
            rid = decode_id("rfi", rfi_id)
        except OpaqueIdError:
            rid = None

    # Resolve current user's person.id via Person.app_user_id
    person_id = None
    try:
        res = await db.execute(select(PersonModel.id).where(PersonModel.app_user_id == current_user.id))
        person_id = res.scalar()
    except Exception:
        person_id = None

    # Create DB row first to get the ID
    img = Image(
        case_id=pk,
        file_name=file.filename or "upload",
        created_by_id=int(person_id) if person_id is not None else None,
        source_url=source_url,
        where=where,
        notes=notes,
        rfi_id=rid,
    )
    db.add(img)
    await db.flush()  # assign PK

    # Store file in S3 under key image-<id>
    file.file.seek(0)
    await create_file("image", img.id, file.file, content_type=file.content_type or "application/octet-stream")

    # Optional: store thumbnail alongside
    if thumbnail is not None:
        try:
            thumbnail.file.seek(0)
            # Always JPEG per requirement
            await create_file("image", img.id, thumbnail.file, content_type="image/jpeg", is_thumbnail=True)
        except Exception:
            # Non-fatal if thumbnail upload fails
            pass

    await db.commit()
    await db.refresh(img)

    # Build response payload with presigned URLs
    payload = {
        "id": int(img.id),
        "case_id": int(img.case_id),
        "file_name": img.file_name,
        "created_by_id": int(img.created_by_id) if img.created_by_id is not None else None,
        "source_url": img.source_url,
        "where": img.where,
        "notes": img.notes,
        "rfi_id": int(img.rfi_id) if img.rfi_id is not None else None,
        "created_at": img.created_at,
        "updated_at": img.updated_at,
        "url": get_download_link("image", int(img.id), file_type=file.content_type or None, thumbnail=False, attachment_filename=img.file_name or "download"),
        "thumb": get_download_link("image", int(img.id), file_type=None, thumbnail=True),
        "storage_slug": None,
    }
    return payload


@router.patch("/{case_id}/images/{image_id}", summary="Update image fields for a case")
async def update_image(
    case_id: str,
    image_id: str,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Update editable fields on an image: source_url, where, notes, rfi_id (opaque).
    Returns the updated record in the same shape used by list_images.
    """
    pk = _decode_or_404("case", case_id)
    # Access control
    if not await can_user_access_case(db, current_user.id, pk):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        iid = decode_id("image", image_id) if not str(image_id).isdigit() else int(image_id)
    except OpaqueIdError:
        # Allow numeric IDs as well
        raise HTTPException(status_code=404, detail="Image not found")

    # Fetch image and validate ownership to case
    result = await db.execute(select(Image).where(Image.id == iid, Image.case_id == pk))
    img: Optional[Image] = result.scalars().first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    # Apply updates
    if payload is None:
        payload = {}
    source_url = payload.get("source_url")
    where = payload.get("where")
    notes = payload.get("notes")
    rfi_eid = payload.get("rfi_id")

    # Decode rfi opaque ID if provided
    rid: Optional[int] = img.rfi_id
    if rfi_eid is not None:
        if rfi_eid == "" or rfi_eid is None:
            rid = None
        else:
            try:
                rid = decode_id("rfi", rfi_eid) if not str(rfi_eid).isdigit() else int(rfi_eid)
            except OpaqueIdError:
                rid = None

    # Only set provided fields (allow nulls)
    if "source_url" in payload:
        img.source_url = source_url
    if "where" in payload:
        img.where = where
    if "notes" in payload:
        img.notes = notes
    if "rfi_id" in payload:
        img.rfi_id = rid

    await db.commit()
    await db.refresh(img)

    # Join to get names for response
    P = PersonModel
    R = Rfi
    I = Image
    q = (
        select(
            I.id,
            I.case_id,
            I.file_name,
            I.created_by_id,
            I.source_url,
            I.where,
            I.notes,
            I.rfi_id,
            I.created_at,
            I.updated_at,
            I.mime_type,
            (P.first_name + sa.literal(" ") + P.last_name).label("created_by_name"),
            R.name.label("rfi_name"),
        )
        .select_from(I)
        .join(P, P.id == I.created_by_id, isouter=True)
        .join(R, R.id == I.rfi_id, isouter=True)
        .where(I.id == img.id)
    )
    row = (await db.execute(q)).first()
    if not row:
        raise HTTPException(status_code=500, detail="Failed to load updated image")

    return {
        "id": int(row.id),
        "case_id": int(row.case_id),
        "file_name": row.file_name,
        "created_by_id": int(row.created_by_id) if row.created_by_id is not None else None,
        "source_url": row.source_url,
        "where": row.where,
        "notes": row.notes,
        "rfi_id": int(row.rfi_id) if row.rfi_id is not None else None,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "url": get_download_link("image", int(row.id), file_type=None, thumbnail=False, attachment_filename=row.file_name or "download"),
        "thumb": get_download_link("image", int(row.id), file_type=None, thumbnail=True),
        "mime_type" : row.mime_type,
        "storage_slug": None,
        "created_by_name": row.created_by_name if getattr(row, "created_by_name", None) else None,
        "rfi_name": row.rfi_name if getattr(row, "rfi_name", None) else None,
    }


# ---------------- Image Subjects ----------------
from pydantic import BaseModel as _BaseModel_IS
from typing import Optional as _Optional_IS

class ImageSubjectCreate(_BaseModel_IS):
    subject_id: str


@router.get("/{case_id}/images/{image_id}/subjects", summary="List subjects linked to an image")
async def list_image_subjects(
    case_id: str,
    image_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    pk = _decode_or_404("case", case_id)
    # Access control
    if not await can_user_access_case(db, current_user.id, pk):
        raise HTTPException(status_code=404, detail="Case not found")

    # Resolve image id and ensure it belongs to the case
    try:
        iid = decode_id("image", image_id) if not str(image_id).isdigit() else int(image_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Image not found")

    img_row = (await db.execute(select(Image.id).where(Image.id == iid, Image.case_id == pk))).scalar_one_or_none()
    if img_row is None:
        raise HTTPException(status_code=404, detail="Image not found")

    # Join to Subject for display
    IS = ImageSubject
    S = Subject
    rows = (
        await db.execute(
            select(
                IS.id,
                S.first_name,
                S.last_name,
                S.nicknames,
                S.id.label("sid"),
                S.profile_pic,
            ).join(S, S.id == IS.subject_id).where(IS.image_id == iid)
        )
    ).all()

    def _name(first: str, last: str, nick: _Optional_IS[str]) -> str:
        nick_part = f' "{nick.strip()}"' if nick and str(nick).strip() else ""
        return f"{first}{nick_part} {last}".strip()

    items = []
    for r in rows:
        sid = int(r.sid)
        photo_url = f"/api/v1/media/pfp/subject/{encode_id('subject', sid)}?s=sm" if getattr(r, 'profile_pic', None) else "/images/pfp-generic.png"
        items.append({
            "id": int(r.id),
            "subject_id": encode_id("subject", sid),
            "name": _name(r.first_name, r.last_name, r.nicknames),
            "photo_url": photo_url,
        })
    return items


@router.post("/{case_id}/images/{image_id}/subjects", summary="Add a subject to an image")
async def add_image_subject(
    case_id: str,
    image_id: str,
    payload: ImageSubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    pk = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, pk):
        raise HTTPException(status_code=404, detail="Case not found")

    # Resolve image id and ensure it belongs to the case
    try:
        iid = decode_id("image", image_id) if not str(image_id).isdigit() else int(image_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Image not found")

    img_row = (await db.execute(select(Image.id).where(Image.id == iid, Image.case_id == pk))).scalar_one_or_none()
    if img_row is None:
        raise HTTPException(status_code=404, detail="Image not found")

    # Decode subject id
    try:
        sid = decode_id("subject", payload.subject_id) if not str(payload.subject_id).isdigit() else int(payload.subject_id)
    except OpaqueIdError:
        raise HTTPException(status_code=400, detail="Invalid subject_id")

    # Upsert-like: avoid duplicates
    exists_row = (
        await db.execute(select(ImageSubject.id).where(ImageSubject.image_id == iid, ImageSubject.subject_id == sid).limit(1))
    ).scalar_one_or_none()
    if exists_row is not None:
        return {"id": int(exists_row)}

    link = ImageSubject(image_id=iid, subject_id=sid)
    db.add(link)
    await db.commit()
    await db.refresh(link)

    return {"id": int(link.id)}


@router.delete("/{case_id}/images/{image_id}/subjects/{link_id}", summary="Remove a subject from an image")
async def delete_image_subject(
    case_id: str,
    image_id: str,
    link_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    pk = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, pk):
        raise HTTPException(status_code=404, detail="Case not found")

    # Resolve image id and ensure it belongs to the case
    try:
        iid = decode_id("image", image_id) if not str(image_id).isdigit() else int(image_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Image not found")

    img_row = (await db.execute(select(Image.id).where(Image.id == iid, Image.case_id == pk))).scalar_one_or_none()
    if img_row is None:
        raise HTTPException(status_code=404, detail="Image not found")

    # Delete the link constrained to this image
    try:
        lid = int(link_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Link not found")

    await db.execute(sa.delete(ImageSubject).where(ImageSubject.id == lid, ImageSubject.image_id == iid))
    await db.commit()

    return {"ok": True}
