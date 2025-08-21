from pydantic import BaseModel, ConfigDict
from typing import Optional


class AppUserRoleRead(BaseModel):
    app_user_id: int
    role_id: int

    model_config = ConfigDict(from_attributes=True)


class AppUserRoleUpsert(BaseModel):
    app_user_id: str
    role_id: str
