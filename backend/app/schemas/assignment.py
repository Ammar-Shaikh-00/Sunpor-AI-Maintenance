from pydantic import BaseModel


class RoleAssignmentRequest(BaseModel):

    role_ids: list[int]
