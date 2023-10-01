import os
from datetime import datetime, timedelta

from jose import jwt, JWTError
from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from starlette.status import HTTP_302_FOUND

from create_app import config, app
from exceptions import JWTIsFailException

router = APIRouter()
templates = Jinja2Templates(directory=f"{os.getcwd()}/templates")


class SUserAuth(BaseModel):
    login: str
    password: str


def verify_user(user: SUserAuth) -> bool:
    return config.auth.login == user.login and config.auth.password == user.password


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=10)
    to_encode.update({"exp": expire})
    return jwt.encode(claims=to_encode, key=config.auth.secret_key, algorithm=config.auth.algorithm)


async def authenticate_user(user: SUserAuth):
    if not verify_user(user=user):
        return False
    return True


def get_token(request: Request):
    token = request.cookies.get("prado_app_access_token")
    if not token:
        raise JWTIsFailException
    return token


async def get_current_user(token: str = Depends(get_token)):
    try:
        payload = jwt.decode(token=token, key=config.auth.secret_key, algorithms=config.auth.algorithm)
    except JWTError:
        raise JWTIsFailException
    login: str = payload.get("sub")
    if not login:
        raise JWTIsFailException
    if login != config.auth.login:
        raise JWTIsFailException
    return login


@router.get("/login", response_class=HTMLResponse)
async def auth_page(request: Request, is_start: bool = True):
    return templates.TemplateResponse("auth.html", {"request": request, "is_start": is_start})


@router.get("/incorrect_auth", response_class=HTMLResponse)
async def incorrect_auth_page(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request, "is_start": False})


@router.post("/auth_action", response_class=HTMLResponse)
async def auth_page(request: Request, login: str = Form(), password: str = Form()):
    is_verified = await authenticate_user(user=SUserAuth(login=login, password=password))
    if is_verified:
        access_token = create_access_token({"sub": str(login)})
        response = RedirectResponse(url="/", status_code=HTTP_302_FOUND)
        response.set_cookie("prado_app_access_token", access_token, httponly=True)
    else:
        response = RedirectResponse(url="/incorrect_auth", status_code=HTTP_302_FOUND)
    return response


@app.exception_handler(JWTIsFailException)
async def not_correct_auth_data(request: Request, exc: JWTIsFailException):
    response = RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    return response
