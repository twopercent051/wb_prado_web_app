from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from create_app import templates
from routers.auth import SUserAuth, get_current_user

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index_page(request: Request, user: SUserAuth = Depends(get_current_user)):
    return templates.TemplateResponse("index.html", {"request": request})
