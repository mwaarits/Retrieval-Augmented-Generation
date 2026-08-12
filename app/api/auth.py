from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.core import auth

router = APIRouter(prefix="/auth", tags=["auth"])

_bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    token: str
    user_id: str


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest) -> LoginResponse:
    user = auth.authenticate(req.username, req.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return LoginResponse(token=auth.issue_token(user), user_id=user)


@router.post("/logout")
def logout(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if creds is not None:
        auth.revoke_token(creds.credentials)
    return {"status": "ok"}