from pydantic import BaseModel
from pydantic import ConfigDict


class PermissionResponse(BaseModel):

    id: int
    code: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PermissionCreate(BaseModel):

    code: str
    description: str | None = None


class PermissionUpdate(BaseModel):

    code: str | None = None
    description: str | None = None


class PermissionAssignmentRequest(BaseModel):

    permission_ids: list[int]
