from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from app import auth

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    password: str


@router.post("/login")
def login(body: LoginIn, response: Response):
    if not auth.password_configured():
        raise HTTPException(503, "APP_PASSWORD_HASH isn't set on the server")
    if not auth.check_password(body.password):
        raise HTTPException(401, "Wrong password")
    auth.start_session(response)
    return {"ok": True}


@router.post("/logout")
def logout(response: Response):
    auth.end_session(response)
    return {"ok": True}


@router.get("/me")
def me(request: Request):
    return {"logged_in": auth.is_logged_in(request)}
