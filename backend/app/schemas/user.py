from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class RoleSummary(BaseModel):

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):

    first_name: str
    last_name: str
    email: str
    is_active: bool = True
    email_notifications_enabled: bool = True


class UserCreate(UserBase):

    password: str


class UserUpdate(BaseModel):

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    password: str | None = None
    is_active: bool | None = None
    email_notifications_enabled: bool | None = None


class UserResponse(UserBase):

    id: int
    roles: list[RoleSummary] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserMeResponse(UserResponse):

    permissions: list[str] = []


class ProfileUpdate(BaseModel):

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
