from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Meta(BaseModel):
    total: int
    limit: int
    offset: int


class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: str = "OK"
    meta: Optional[Meta] = None
    code: Optional[int] = None
