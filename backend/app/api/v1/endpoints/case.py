from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.id_codec import decode_id, OpaqueIdError

# Models
from app.db.models.subject import Subject
from app.db.models.case import Case
from app.db.models.team_case import TeamCase
from app.db.models.app_user_case import AppUserCase
from app.db.models.ref_relation import RefRelation
from app.db.models.ref_sm_platform import RefSmPlatform
from app.db.models.ref_activity import RefActivity
from app.db.models.ref_file_type import RefFileType
from app.db.models.ref_scope import RefScope
from app.db.models.ref_case_classification import RefCaseClassification
from app.db.models.ref_status import RefStatus
from app.db.models.ref_requested_by import RefRequestedBy
from app.db.models.ref_alive import RefAlive
from app.db.models.ref_ministry import RefMinistry
from app.db.models.ref_actions import RefActions
from app.db.models.ref_found_by import RefFoundBy
from app.db.models.ref_intel_discover import RefIntelDiscover
from app.db.models.ref_exploitation import RefExploitation
from app.db.models.ref_sub_relation import RefSubRelation
from app.db.models.person_case import PersonCase
from app.db.models.social_media import SocialMedia
from app.db.models.timeline import Timeline
from app.db.models.activity import Activity
from app.db.models.message import Message
from app.db.models.file import File
from app.db.models.file_person import FilePerson
from app.db.models.subject_case import SubjectCase

# Schemas
from app.schemas.subject import SubjectRead, SubjectUpsert
from app.schemas.case import CaseRead, CaseUpsert
from app.schemas.team_case import TeamCaseRead, TeamCaseUpsert
from app.schemas.app_user_case import AppUserCaseRead, AppUserCaseUpsert
from app.schemas.ref_relation import RefRelationRead, RefRelationUpsert
from app.schemas.ref_sm_platform import RefSmPlatformRead, RefSmPlatformUpsert
from app.schemas.ref_activity import RefActivityRead, RefActivityUpsert
from app.schemas.ref_file_type import RefFileTypeRead, RefFileTypeUpsert
from app.schemas.ref_scope import RefScopeRead, RefScopeUpsert
from app.schemas.ref_case_classification import (
    RefCaseClassificationRead,
    RefCaseClassificationUpsert,
)
from app.schemas.ref_status import RefStatusRead, RefStatusUpsert
from app.schemas.ref_requested_by import RefRequestedByRead, RefRequestedByUpsert
from app.schemas.ref_alive import RefAliveRead, RefAliveUpsert
from app.schemas.ref_ministry import RefMinistryRead, RefMinistryUpsert
from app.schemas.ref_actions import RefActionsRead, RefActionsUpsert
from app.schemas.ref_found_by import RefFoundByRead, RefFoundByUpsert
from app.schemas.ref_intel_discover import RefIntelDiscoverRead, RefIntelDiscoverUpsert
from app.schemas.ref_exploitation import RefExploitationRead, RefExploitationUpsert
from app.schemas.ref_sub_relation import RefSubRelationRead, RefSubRelationUpsert
from app.schemas.person_case import PersonCaseRead, PersonCaseUpsert
from app.schemas.social_media import SocialMediaRead, SocialMediaUpsert
from app.schemas.timeline import TimelineRead, TimelineUpsert
from app.schemas.activity import ActivityRead, ActivityUpsert
from app.schemas.message import MessageRead, MessageUpsert
from app.schemas.file import FileRead, FileUpsert
from app.schemas.file_person import FilePersonRead, FilePersonUpsert
from app.schemas.subject_case import SubjectCaseRead, SubjectCaseUpsert

router = APIRouter(prefix="/cases")


# ---------- Helper utilities ----------

def _decode_or_404(model: str, opaque_id: str) -> int:
    try:
        return decode_id(model, opaque_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail=f"{model.replace('_', ' ').title()} not found")


# ---------- Subject endpoints ----------

@router.get("/subjects", response_model=List[SubjectRead], summary="List subjects")
async def list_subjects(db: AsyncSession = Depends(get_db)) -> List[SubjectRead]:
    result = await db.execute(select(Subject))
    return result.scalars().all()


@router.post("/subjects", response_model=SubjectRead, summary="Create subject")
async def create_subject(payload: SubjectUpsert, db: AsyncSession = Depends(get_db)) -> SubjectRead:
    obj = Subject(
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        email=payload.email,
    )
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put("/subjects/{subject_id}", response_model=SubjectRead, summary="Update subject")
async def update_subject(subject_id: str, payload: SubjectUpsert, db: AsyncSession = Depends(get_db)) -> SubjectRead:
    pk = _decode_or_404("subject", subject_id)
    obj = await db.get(Subject, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Subject not found")
    obj.first_name = payload.first_name
    obj.last_name = payload.last_name
    obj.phone = payload.phone
    obj.email = payload.email
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/subjects/{subject_id}", summary="Delete subject", status_code=204)
async def delete_subject(subject_id: str, db: AsyncSession = Depends(get_db)) -> None:
    pk = _decode_or_404("subject", subject_id)
    obj = await db.get(Subject, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Subject not found")
    await db.delete(obj)
    await db.commit()
    return None


# ---------- Case endpoints ----------

@router.get("/cases", response_model=List[CaseRead], summary="List cases")
async def list_cases(db: AsyncSession = Depends(get_db)) -> List[CaseRead]:
    result = await db.execute(select(Case))
    return result.scalars().all()


@router.post("/cases", response_model=CaseRead, summary="Create case")
async def create_case(payload: CaseUpsert, db: AsyncSession = Depends(get_db)) -> CaseRead:
    subject_pk = _decode_or_404("subject", payload.subject_id)
    state_pk: Optional[int] = None
    if payload.missing_from_state_id is not None:
        state_pk = _decode_or_404("ref_state", payload.missing_from_state_id)
    obj = Case(
        subject_id=subject_pk,
        date_missing=payload.date_missing,
        time_missing=payload.time_missing,
        number=payload.number,
        missing_from_state_id=state_pk,
        inactive=bool(payload.inactive) if payload.inactive is not None else False,
    )
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put("/cases/{case_id}", response_model=CaseRead, summary="Update case")
async def update_case(case_id: str, payload: CaseUpsert, db: AsyncSession = Depends(get_db)) -> CaseRead:
    pk = _decode_or_404("case", case_id)
    obj = await db.get(Case, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Case not found")
    obj.subject_id = _decode_or_404("subject", payload.subject_id)
    obj.date_missing = payload.date_missing
    obj.time_missing = payload.time_missing
    obj.number = payload.number
    obj.missing_from_state_id = (
        _decode_or_404("ref_state", payload.missing_from_state_id)
        if payload.missing_from_state_id is not None
        else None
    )
    if payload.inactive is not None:
        obj.inactive = bool(payload.inactive)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/cases/{case_id}", summary="Delete case", status_code=204)
async def delete_case(case_id: str, db: AsyncSession = Depends(get_db)) -> None:
    pk = _decode_or_404("case", case_id)
    obj = await db.get(Case, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Case not found")
    await db.delete(obj)
    await db.commit()
    return None


# ---------- TeamCase endpoints ----------

@router.get("/team-cases", response_model=List[TeamCaseRead], summary="List team-case links")
async def list_team_cases(db: AsyncSession = Depends(get_db)) -> List[TeamCaseRead]:
    result = await db.execute(select(TeamCase))
    return result.scalars().all()


@router.post("/team-cases", response_model=TeamCaseRead, summary="Create team-case link")
async def create_team_case(payload: TeamCaseUpsert, db: AsyncSession = Depends(get_db)) -> TeamCaseRead:
    obj = TeamCase(
        team_id=_decode_or_404("team", payload.team_id),
        case_id=_decode_or_404("case", payload.case_id),
    )
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put("/team-cases/{team_case_id}", response_model=TeamCaseRead, summary="Update team-case link")
async def update_team_case(team_case_id: str, payload: TeamCaseUpsert, db: AsyncSession = Depends(get_db)) -> TeamCaseRead:
    pk = _decode_or_404("team_case", team_case_id)
    obj = await db.get(TeamCase, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="TeamCase not found")
    obj.team_id = _decode_or_404("team", payload.team_id)
    obj.case_id = _decode_or_404("case", payload.case_id)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/team-cases/{team_case_id}", summary="Delete team-case link", status_code=204)
async def delete_team_case(team_case_id: str, db: AsyncSession = Depends(get_db)) -> None:
    pk = _decode_or_404("team_case", team_case_id)
    obj = await db.get(TeamCase, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="TeamCase not found")
    await db.delete(obj)
    await db.commit()
    return None


# ---------- AppUserCase endpoints ----------

@router.get("/app-user-cases", response_model=List[AppUserCaseRead], summary="List user-case links")
async def list_app_user_cases(db: AsyncSession = Depends(get_db)) -> List[AppUserCaseRead]:
    result = await db.execute(select(AppUserCase))
    return result.scalars().all()


@router.post("/app-user-cases", response_model=AppUserCaseRead, summary="Create user-case link")
async def create_app_user_case(payload: AppUserCaseUpsert, db: AsyncSession = Depends(get_db)) -> AppUserCaseRead:
    obj = AppUserCase(
        app_user_id=_decode_or_404("app_user", payload.app_user_id),
        case_id=_decode_or_404("case", payload.case_id),
    )
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put("/app-user-cases/{app_user_case_id}", response_model=AppUserCaseRead, summary="Update user-case link")
async def update_app_user_case(app_user_case_id: str, payload: AppUserCaseUpsert, db: AsyncSession = Depends(get_db)) -> AppUserCaseRead:
    pk = _decode_or_404("app_user_case", app_user_case_id)
    obj = await db.get(AppUserCase, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="AppUserCase not found")
    obj.app_user_id = _decode_or_404("app_user", payload.app_user_id)
    obj.case_id = _decode_or_404("case", payload.case_id)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/app-user-cases/{app_user_case_id}", summary="Delete user-case link", status_code=204)
async def delete_app_user_case(app_user_case_id: str, db: AsyncSession = Depends(get_db)) -> None:
    pk = _decode_or_404("app_user_case", app_user_case_id)
    obj = await db.get(AppUserCase, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="AppUserCase not found")
    await db.delete(obj)
    await db.commit()
    return None


# ---------- Reference tables endpoints ----------

# RefRelation
@router.get("/ref/relations", response_model=List[RefRelationRead], summary="List relations")
async def list_relations(db: AsyncSession = Depends(get_db)) -> List[RefRelationRead]:
    result = await db.execute(select(RefRelation))
    return result.scalars().all()


@router.post("/ref/relations", response_model=RefRelationRead, summary="Create relation")
async def create_relation(payload: RefRelationUpsert, db: AsyncSession = Depends(get_db)) -> RefRelationRead:
    obj = RefRelation(name=payload.name)
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put("/ref/relations/{relation_id}", response_model=RefRelationRead, summary="Update relation")
async def update_relation(relation_id: str, payload: RefRelationUpsert, db: AsyncSession = Depends(get_db)) -> RefRelationRead:
    pk = _decode_or_404("ref_relation", relation_id)
    obj = await db.get(RefRelation, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Relation not found")
    obj.name = payload.name
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/ref/relations/{relation_id}", summary="Delete relation", status_code=204)
async def delete_relation(relation_id: str, db: AsyncSession = Depends(get_db)) -> None:
    pk = _decode_or_404("ref_relation", relation_id)
    obj = await db.get(RefRelation, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Relation not found")
    await db.delete(obj)
    await db.commit()
    return None


# RefSmPlatform
@router.get("/ref/sm-platforms", response_model=List[RefSmPlatformRead], summary="List social media platforms")
async def list_sm_platforms(db: AsyncSession = Depends(get_db)) -> List[RefSmPlatformRead]:
    result = await db.execute(select(RefSmPlatform))
    return result.scalars().all()


@router.post("/ref/sm-platforms", response_model=RefSmPlatformRead, summary="Create social media platform")
async def create_sm_platform(payload: RefSmPlatformUpsert, db: AsyncSession = Depends(get_db)) -> RefSmPlatformRead:
    obj = RefSmPlatform(name=payload.name, url=payload.url)
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put("/ref/sm-platforms/{platform_id}", response_model=RefSmPlatformRead, summary="Update social media platform")
async def update_sm_platform(platform_id: str, payload: RefSmPlatformUpsert, db: AsyncSession = Depends(get_db)) -> RefSmPlatformRead:
    pk = _decode_or_404("ref_sm_platform", platform_id)
    obj = await db.get(RefSmPlatform, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Platform not found")
    obj.name = payload.name
    obj.url = payload.url
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/ref/sm-platforms/{platform_id}", summary="Delete social media platform", status_code=204)
async def delete_sm_platform(platform_id: str, db: AsyncSession = Depends(get_db)) -> None:
    pk = _decode_or_404("ref_sm_platform", platform_id)
    obj = await db.get(RefSmPlatform, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Platform not found")
    await db.delete(obj)
    await db.commit()
    return None


# RefActivity
@router.get("/ref/activities", response_model=List[RefActivityRead], summary="List activities")
async def list_activities(db: AsyncSession = Depends(get_db)) -> List[RefActivityRead]:
    result = await db.execute(select(RefActivity))
    return result.scalars().all()


@router.post("/ref/activities", response_model=RefActivityRead, summary="Create activity")
async def create_activity(payload: RefActivityUpsert, db: AsyncSession = Depends(get_db)) -> RefActivityRead:
    obj = RefActivity(name=payload.name)
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put("/ref/activities/{activity_id}", response_model=RefActivityRead, summary="Update activity")
async def update_activity(activity_id: str, payload: RefActivityUpsert, db: AsyncSession = Depends(get_db)) -> RefActivityRead:
    pk = _decode_or_404("ref_activity", activity_id)
    obj = await db.get(RefActivity, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Activity not found")
    obj.name = payload.name
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/ref/activities/{activity_id}", summary="Delete activity", status_code=204)
async def delete_activity(activity_id: str, db: AsyncSession = Depends(get_db)) -> None:
    pk = _decode_or_404("ref_activity", activity_id)
    obj = await db.get(RefActivity, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Activity not found")
    await db.delete(obj)
    await db.commit()
    return None


# RefFileType
@router.get("/ref/file-types", response_model=List[RefFileTypeRead], summary="List file types")
async def list_file_types(db: AsyncSession = Depends(get_db)) -> List[RefFileTypeRead]:
    result = await db.execute(select(RefFileType))
    return result.scalars().all()


@router.post("/ref/file-types", response_model=RefFileTypeRead, summary="Create file type")
async def create_file_type(payload: RefFileTypeUpsert, db: AsyncSession = Depends(get_db)) -> RefFileTypeRead:
    obj = RefFileType(name=payload.name, code=payload.code)
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put("/ref/file-types/{file_type_id}", response_model=RefFileTypeRead, summary="Update file type")
async def update_file_type(file_type_id: str, payload: RefFileTypeUpsert, db: AsyncSession = Depends(get_db)) -> RefFileTypeRead:
    pk = _decode_or_404("ref_file_type", file_type_id)
    obj = await db.get(RefFileType, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="File type not found")
    obj.name = payload.name
    obj.code = payload.code
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/ref/file-types/{file_type_id}", summary="Delete file type", status_code=204)
async def delete_file_type(file_type_id: str, db: AsyncSession = Depends(get_db)) -> None:
    pk = _decode_or_404("ref_file_type", file_type_id)
    obj = await db.get(RefFileType, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="File type not found")
    await db.delete(obj)
    await db.commit()
    return None


# RefScope
@router.get("/ref/scopes", response_model=List[RefScopeRead], summary="List scopes")
async def list_scopes(db: AsyncSession = Depends(get_db)) -> List[RefScopeRead]:
    result = await db.execute(select(RefScope))
    return result.scalars().all()


@router.post("/ref/scopes", response_model=RefScopeRead, summary="Create scope")
async def create_scope(payload: RefScopeUpsert, db: AsyncSession = Depends(get_db)) -> RefScopeRead:
    obj = RefScope(name=payload.name, code=payload.code)
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put("/ref/scopes/{scope_id}", response_model=RefScopeRead, summary="Update scope")
async def update_scope(scope_id: str, payload: RefScopeUpsert, db: AsyncSession = Depends(get_db)) -> RefScopeRead:
    pk = _decode_or_404("ref_scope", scope_id)
    obj = await db.get(RefScope, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Scope not found")
    obj.name = payload.name
    obj.code = payload.code
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/ref/scopes/{scope_id}", summary="Delete scope", status_code=204)
async def delete_scope(scope_id: str, db: AsyncSession = Depends(get_db)) -> None:
    pk = _decode_or_404("ref_scope", scope_id)
    obj = await db.get(RefScope, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Scope not found")
    await db.delete(obj)
    await db.commit()
    return None


# RefCaseClassification
@router.get("/ref/classifications", response_model=List[RefCaseClassificationRead], summary="List case classifications")
async def list_classifications(db: AsyncSession = Depends(get_db)) -> List[RefCaseClassificationRead]:
    result = await db.execute(select(RefCaseClassification))
    return result.scalars().all()


@router.post("/ref/classifications", response_model=RefCaseClassificationRead, summary="Create case classification")
async def create_classification(payload: RefCaseClassificationUpsert, db: AsyncSession = Depends(get_db)) -> RefCaseClassificationRead:
    obj = RefCaseClassification(name=payload.name, code=payload.code)
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put("/ref/classifications/{classification_id}", response_model=RefCaseClassificationRead, summary="Update case classification")
async def update_classification(classification_id: str, payload: RefCaseClassificationUpsert, db: AsyncSession = Depends(get_db)) -> RefCaseClassificationRead:
    pk = _decode_or_404("ref_case_classification", classification_id)
    obj = await db.get(RefCaseClassification, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Case classification not found")
    obj.name = payload.name
    obj.code = payload.code
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/ref/classifications/{classification_id}", summary="Delete case classification", status_code=204)
async def delete_classification(classification_id: str, db: AsyncSession = Depends(get_db)) -> None:
    pk = _decode_or_404("ref_case_classification", classification_id)
    obj = await db.get(RefCaseClassification, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Case classification not found")
    await db.delete(obj)
    await db.commit()
    return None
