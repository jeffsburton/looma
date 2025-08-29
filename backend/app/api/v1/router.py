from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, core, reference, organizations, admin, case, hospital_er, qualification, rfi_source, persons, event, team, media

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(core.router, prefix="/core", tags=["core"])
api_router.include_router(reference.router, tags=["reference"])  # exposes /states
api_router.include_router(organizations.router, tags=["organizations"])  # exposes /organizations
api_router.include_router(admin.router, tags=["admin"])  # exposes /admin/*
api_router.include_router(case.router, tags=["cases"])  # exposes /cases/*
api_router.include_router(hospital_er.router, tags=["hospital_er"])  # exposes /hospital-ers
api_router.include_router(qualification.router, tags=["qualifications"])  # exposes /qualifications
api_router.include_router(rfi_source.router, tags=["rfi_sources"])  # exposes /rfi-sources
api_router.include_router(persons.router, tags=["persons"])  # exposes /persons
api_router.include_router(event.router, tags=["events"])  # exposes /events
api_router.include_router(team.router, tags=["teams"])  # exposes /teams
api_router.include_router(media.router, tags=["media"])  # exposes /media/*