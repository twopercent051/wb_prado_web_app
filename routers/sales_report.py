from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from create_app import templates
from models.sql_connector import OrdersDAO
from routers.auth import SUserAuth, get_current_user

router = APIRouter()


@router.get("/sales_report", response_class=HTMLResponse)
async def sales_report_page(request: Request, user: SUserAuth = Depends(get_current_user)):
    data = await OrdersDAO.get_total_report_by_articles()
    loaded_total_data = await OrdersDAO.get_total_report(seller_status="complete")
    sold_total_data = await OrdersDAO.get_total_report(client_status="sold")
    in_system_total_data = {
        "sum": loaded_total_data["sum"] - sold_total_data["sum"],
        "count": loaded_total_data["count"] - sold_total_data["count"]
    }
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
