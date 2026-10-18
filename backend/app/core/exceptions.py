from typing import Optional

from fastapi import HTTPException


class ApiError(HTTPException):
    """detail 을 {code, message, ...} 로 통일한다. retry_after 가 있으면 Retry-After 헤더도 보낸다."""

    def __init__(self, status_code: int, code: str, message: str, retry_after: Optional[int] = None, **extra):
        detail = {"code": code, "message": message, **extra}
        headers = None
        if retry_after is not None:
            detail["retry_after"] = retry_after
            headers = {"Retry-After": str(retry_after)}
        super().__init__(status_code=status_code, detail=detail, headers=headers)
