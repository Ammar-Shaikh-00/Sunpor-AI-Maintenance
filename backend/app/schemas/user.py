from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class UserBase(BaseModel):

    first_name: str
    last_name: str
    email: str
    is_active: bool = True


class UserCreate(UserBase):

    password: str


class UserUpdate(BaseModel):

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    password: str | None = None
    is_active: bool | None = None


class UserResponse(UserBase):

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdate(BaseModel):

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
