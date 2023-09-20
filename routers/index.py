import os

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from models.sql_connector import OrdersDAO

router = APIRouter()
templates = Jinja2Templates(directory=f"{os.getcwd()}/templates")


@router.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/sales_report", response_class=HTMLResponse)
async def sales_report_page(request: Request):
    data = await OrdersDAO.get_total_report_by_articles()
    loaded_total_data = await OrdersDAO.get_total_report(seller_status="complete")
    sold_total_data = await OrdersDAO.get_total_report(client_status="sold")
    in_system_total_data = {
        "sum": loaded_total_data["sum"] - sold_total_data["sum"],
        "count": loaded_total_data["count"] - sold_total_data["count"]
    }
    print(data)
    return templates.TemplateResponse(
        "sales_report.html",
        {
            "request": request,
            "data": data,
            "loaded_total_data": loaded_total_data,
            "sold_total_data": sold_total_data,
            "in_system_total_data": in_system_total_data
        },
    )
