from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Body, UploadFile, File as UploadFileParam, Form
from sqlalchemy import select
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db.models.app_user import AppUser
from app.db.models.person import Person as PersonModel
from app.db.models.person_case import PersonCase
from app.db.models.rfi import Rfi
from app.db.models.file import File as OtherFile
from app.db.models.subject import Subject
from app.db.models.file_subject import FileSubject
from app.core.id_codec import decode_id, OpaqueIdError, encode_id
from app.services.auth import user_has_permission
from app.services.s3 import get_download_link, create_file
from app.services.image_classifier.image_classifier import predict_photo_probability

from .case_utils import _decode_or_404, can_user_access_case, case_number_or_id

router = APIRouter()


# ---------------- Files (list and upload) ----------------
@router.get("/{case_id}/files", summary="List files for a case")
async def list_files(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):

    pk = await case_number_or_id(db, current_user, case_id)

    P = PersonModel
    R = Rfi
    F = OtherFile
    q = (
        select(
            F.id,
            F.case_id,
            F.file_name,
            F.created_by_id,
            F.source,
            F.where,
            F.notes,
            F.rfi_id,
            F.created_at,
            F.updated_at,
            F.mime_type,
            F.is_image,
            F.is_video,
            F.is_document,
            (P.first_name + sa.literal(" ") + P.last_name).label("created_by_name"),
            R.name.label("rfi_name"),
        )
        .select_from(F)
        .join(P, P.id == F.created_by_id, isouter=True)
        .join(R, R.id == F.rfi_id, isouter=True)
        .where(F.case_id == pk)
        .order_by(sa.desc(F.created_at))
    )

    rows = (await db.execute(q)).all()
    items = []
    for r in rows:
        rid = int(r.id)
        is_img = bool(getattr(r, "is_image", False))
        is_vid = bool(getattr(r, "is_video", False))
        items.append({
            "id": rid,
            "case_id": int(r.case_id),
            "file_name": r.file_name,
            "created_by_id": int(r.created_by_id) if r.created_by_id is not None else None,
            "source": r.source,
            "where": r.where,
            "notes": r.notes,
            "rfi_id": int(r.rfi_id) if r.rfi_id is not None else None,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
            "mime_type": r.mime_type,
            "is_image": is_img,
            "is_video": is_vid,
            "is_document": bool(getattr(r, "is_document", False)),
            "url": get_download_link("file", rid, file_type=r.mime_type or None, thumbnail=False, attachment_filename=r.file_name or "download"),
            "thumb": (get_download_link("file", rid, file_type=None, thumbnail=True) if (is_img or is_vid) else None),
            "storage_slug": None,
            "created_by_name": r.created_by_name if getattr(r, "created_by_name", None) else None,
            "rfi_name": r.rfi_name if getattr(r, "rfi_name", None) else None,
        })
    return items


@router.post("/{case_id}/files/upload", summary="Upload a file for a case")
async def upload_file(
    case_id: str,
    file: UploadFile = UploadFileParam(...),
    thumbnail: Optional[UploadFile] = UploadFileParam(None),
    source: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    rfi_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):

    pk = await case_number_or_id(db, current_user, case_id)

    # Decode optional rfi_id if provided
    rid: Optional[int] = None
    if rfi_id:
        try:
            rid = decode_id("rfi", rfi_id)
        except OpaqueIdError:
            rid = None

    # Resolve current user's person.id via Person.app_user_id; fallback to any person linked to the case
    person_id: Optional[int] = None
    try:
        res = await db.execute(select(PersonModel.id).where(PersonModel.app_user_id == current_user.id))
        person_id = res.scalar()
    except Exception:
        person_id = None

    if person_id is None:
        try:
            pc = (
                await db.execute(
                    select(PersonCase.person_id)
                    .where(PersonCase.case_id == pk)
                    .order_by(sa.asc(PersonCase.id))
                    .limit(1)
                )
            ).scalar_one_or_none()
            if pc is not None:
                person_id = int(pc)
        except Exception:
            person_id = None

    if person_id is None:
        raise HTTPException(status_code=400, detail="No person available to attribute file upload")

    # Determine content type and flags
    content_type = file.content_type or "application/octet-stream"
    is_img = content_type.startswith("image/")
    is_vid = content_type.startswith("video/")

    # Read bytes once (needed for optional classification and upload)
    file.file.seek(0)
    data_bytes = file.file.read()

    # Document heuristic via classifier for images
    is_doc = False if is_img or is_vid else True
    if is_img:
        try:
            prob = float(predict_photo_probability(data_bytes))
            if prob < 0.5:
                is_doc = True
        except Exception:
            # If classifier fails, do not mark as document
            pass

    row = OtherFile(
        case_id=pk,
        file_name=file.filename or "upload",
        created_by_id=int(person_id) if person_id is not None else None,
        source=source,
        notes=notes,
        rfi_id=rid,
        mime_type=content_type,
        is_image=is_img,
        is_video=is_vid,
        is_document=is_doc,
    )
    db.add(row)
    await db.flush()

    # Upload main file using the same bytes
    await create_file("file", row.id, data_bytes, content_type=content_type)

    # Optional: store thumbnail alongside original under -thumbnail key
    if thumbnail is not None:
        try:
            thumbnail.file.seek(0)
            await create_file("file", row.id, thumbnail.file, content_type="image/jpeg", is_thumbnail=True)
        except Exception:
            # Non-fatal if thumbnail upload fails
            pass

    await db.commit()
    await db.refresh(row)

    return {
        "id": int(row.id),
        "case_id": int(row.case_id),
        "file_name": row.file_name,
        "created_by_id": int(row.created_by_id) if row.created_by_id is not None else None,
        "source": row.source,
        "notes": row.notes,
        "rfi_id": int(row.rfi_id) if row.rfi_id is not None else None,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "mime_type": row.mime_type,
        "url": get_download_link("file", int(row.id), file_type=row.mime_type or None, thumbnail=False, attachment_filename=row.file_name or "download"),
        "storage_slug": None,
    }


# ---------------- File Subjects ----------------
from pydantic import BaseModel as _BaseModel_FS
from typing import Optional as _Optional_FS

class FileSubjectCreate(_BaseModel_FS):
    subject_id: str


@router.get("/{case_id}/files/{file_id}/subjects", summary="List subjects linked to a file")
async def list_file_subjects(
    case_id: str,
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):

    pk = await case_number_or_id(db, current_user, case_id)

    # Resolve file id and ensure it belongs to the case
    try:
        fid = decode_id("file", file_id) if not str(file_id).isdigit() else int(file_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="File not found")

    f_row = (await db.execute(select(OtherFile.id).where(OtherFile.id == fid, OtherFile.case_id == pk))).scalar_one_or_none()
    if f_row is None:
        raise HTTPException(status_code=404, detail="File not found")

    FS = FileSubject
    S = Subject
    rows = (
        await db.execute(
            select(
                FS.id,
                S.first_name,
                S.last_name,
                S.nicknames,
                S.id.label("sid"),
                S.profile_pic,
            ).join(S, S.id == FS.subject_id).where(FS.file_id == fid)
        )
    ).all()

    def _name(first: str, last: str, nick: _Optional_FS[str]) -> str:
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


@router.post("/{case_id}/files/{file_id}/subjects", summary="Add a subject to a file")
async def add_file_subject(
    case_id: str,
    file_id: str,
    payload: FileSubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):

    pk = await case_number_or_id(db, current_user, case_id)

    try:
        fid = decode_id("file", file_id) if not str(file_id).isdigit() else int(file_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="File not found")

    f_row = (await db.execute(select(OtherFile.id).where(OtherFile.id == fid, OtherFile.case_id == pk))).scalar_one_or_none()
    if f_row is None:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        sid = decode_id("subject", payload.subject_id) if not str(payload.subject_id).isdigit() else int(payload.subject_id)
    except OpaqueIdError:
        raise HTTPException(status_code=400, detail="Invalid subject_id")

    exists_row = (
        await db.execute(select(FileSubject.id).where(FileSubject.file_id == fid, FileSubject.subject_id == sid).limit(1))
    ).scalar_one_or_none()
    if exists_row is not None:
        return {"id": int(exists_row)}

    link = FileSubject(file_id=fid, subject_id=sid)
    db.add(link)
    await db.commit()
    await db.refresh(link)

    return {"id": int(link.id)}


@router.delete("/{case_id}/files/{file_id}/subjects/{link_id}", summary="Remove a subject from a file")
async def delete_file_subject(
    case_id: str,
    file_id: str,
    link_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):

    pk = await case_number_or_id(db, current_user, case_id)

    try:
        fid = decode_id("file", file_id) if not str(file_id).isdigit() else int(file_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="File not found")

    f_row = (await db.execute(select(OtherFile.id).where(OtherFile.id == fid, OtherFile.case_id == pk))).scalar_one_or_none()
    if f_row is None:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        lid = int(link_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Link not found")

    await db.execute(sa.delete(FileSubject).where(FileSubject.id == lid, FileSubject.file_id == fid))
    await db.commit()

    return {"ok": True}


@router.patch("/{case_id}/files/{file_id}", summary="Update file fields for a case")
async def update_file(
    case_id: str,
    file_id: str,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):

    pk = await case_number_or_id(db, current_user, case_id)

    try:
        fid = decode_id("file", file_id) if not str(file_id).isdigit() else int(file_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="File not found")

    result = await db.execute(select(OtherFile).where(OtherFile.id == fid, OtherFile.case_id == pk))
    frow: Optional[OtherFile] = result.scalars().first()
    if not frow:
        raise HTTPException(status_code=404, detail="File not found")

    if payload is None:
        payload = {}
    source = payload.get("source")
    where = payload.get("where")
    notes = payload.get("notes")
    rfi_eid = payload.get("rfi_id")

    rid: Optional[int] = frow.rfi_id
    if rfi_eid is not None:
        if rfi_eid == "" or rfi_eid is None:
            rid = None
        else:
            try:
                rid = decode_id("rfi", rfi_eid) if not str(rfi_eid).isdigit() else int(rfi_eid)
            except OpaqueIdError:
                rid = None

    if "source" in payload:
        frow.source = source
    if "where" in payload:
        frow.where = where
    if "notes" in payload:
        frow.notes = notes
    if "rfi_id" in payload:
        frow.rfi_id = rid

    await db.commit()
    await db.refresh(frow)

    P = PersonModel
    R = Rfi
    F = OtherFile
    q = (
        select(
            F.id,
            F.case_id,
            F.file_name,
            F.created_by_id,
            F.source,
            F.where,
            F.notes,
            F.rfi_id,
            F.created_at,
            F.updated_at,
            F.mime_type,
            (P.first_name + sa.literal(" ") + P.last_name).label("created_by_name"),
            R.name.label("rfi_name"),
        )
        .select_from(F)
        .join(P, P.id == F.created_by_id, isouter=True)
        .join(R, R.id == F.rfi_id, isouter=True)
        .where(F.id == frow.id)
    )
    row = (await db.execute(q)).first()
    if not row:
        raise HTTPException(status_code=500, detail="Failed to load updated file")

    return {
        "id": int(row.id),
        "case_id": int(row.case_id),
        "file_name": row.file_name,
        "created_by_id": int(row.created_by_id) if row.created_by_id is not None else None,
        "source": row.source,
        "where": row.where,
        "notes": row.notes,
        "rfi_id": int(row.rfi_id) if row.rfi_id is not None else None,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "url": get_download_link("file", int(row.id), file_type=row.mime_type or None, thumbnail=False, attachment_filename=row.file_name or "download"),
        "mime_type": row.mime_type,
        "storage_slug": None,
        "created_by_name": row.created_by_name if getattr(row, "created_by_name", None) else None,
        "rfi_name": row.rfi_name if getattr(row, "rfi_name", None) else None,
    }
