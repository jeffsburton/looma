from pydantic import BaseModel, ConfigDict


class RolePermissionRead(BaseModel):
    role_id: int
    permission_id: int

    model_config = ConfigDict(from_attributes=True)


class RolePermissionUpsert(BaseModel):
    role_id: str
    permission_id: str
