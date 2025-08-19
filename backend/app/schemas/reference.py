from pydantic import BaseModel, ConfigDict


class StateRead(BaseModel):
    id: int
    name: str
    code: str

    model_config = ConfigDict(from_attributes=True)
