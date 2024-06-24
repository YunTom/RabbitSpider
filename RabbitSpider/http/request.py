import warnings
from typing import Callable, Optional, Union
from pydantic import BaseModel, field_validator

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")


class Request(BaseModel):
    url: Optional[str] = None
    params: Optional[dict] = None
    data: Union[dict, str, bytes, None] = None
    json: Optional[dict] = None
    method: Optional[str] = 'get'
    headers: Optional[dict] = {}
    timeout: Optional[int] = None
    cookies: Optional[dict] = None
    proxy: Optional[str] = None
    allow_redirects: Optional[bool] = True
    callback: Union[Callable, str] = 'parse'
    retry: Optional[int] = 0
    meta: Optional[dict] = {}

    @field_validator('callback')
    def call(cls, key):
        if callable(key):
            return key.__name__
        else:
            return key
