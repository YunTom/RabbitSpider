import warnings
from typing import Callable, Optional
from pydantic import BaseModel, field_validator

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")


class Request(BaseModel):
    url: Optional[str] = None
    params: Optional[dict] = None
    data: Optional[str] = None
    json: Optional[dict] = None
    method: Optional[str] = 'get'
    headers: Optional[dict] = {}
    timeout: Optional[int] = 10
    cookies: Optional[dict] = None
    proxy: Optional[str] = None
    allow_redirects: Optional[bool] = True
    callback: Callable | str = 'parse'
    retry: Optional[int] = 1
    dupe_filter: Optional[bool] = True
    meta: Optional[dict] = {}

    @field_validator('callback')
    def call(cls, key):
        if callable(key):
            return key.__name__
        else:
            return key
