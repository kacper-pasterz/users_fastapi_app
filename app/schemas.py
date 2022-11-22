"""Imported modules"""
from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import BaseModel


class UserEvent(BaseModel):
    action_type: str
    user: dict


class UserBase(SQLModel):
    __tablename__ = "users"
    email: Optional[str] = Field(index=True)
    nickname: Optional[str] = Field(index=True)


class User(UserBase, table=True):
    id: int = Field(primary_key=True, default=None)


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: int


class UserUpdate(SQLModel):
    __tablename__ = "users"
    email: Optional[str] = Field(index=True)
    nickname: Optional[str] = Field(index=True)


responses = {400: {"description": "Invalid ID"},
             404: {"description": "User not found"},
             500: {"description": "Internal server error"}}
