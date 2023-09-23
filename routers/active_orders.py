import os

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from models.sql_connector import OrdersDAO

router = APIRouter()
templates = Jinja2Templates(directory=f"{os.getcwd()}/templates")


@router.get("/active_orders", response_class=HTMLResponse)
async def sales_report_page(request: Request):
    active_orders = await OrdersDAO.get_active()
    data = []
    counter = 1
    status_dict = {
        "new": "🟥 Новое",
        "confirm": "🟨 На сборке",
        "complete": "🟩 В доставке",
        "waiting": "🟥 Ожидается",
        "sorted": "🟨 Отсортировано",
        "ready_for_pickup": "🟩 Готово к выдаче",
        "---": ""
    }
    for order in active_orders:
        item_data = {
            "counter": counter,
            "number": f"{order['order_id']} от {order['create_dtime'].strftime('%d-%m-%Y %H:%M')}",
            "article": order["article"],
            "delivery_type": order["delivery_type"].upper(),
            "destination": order["destination"],
            "seller_price": order["seller_price"],
            "client_price": order["client_price"],
            "seller_status": status_dict[order['seller_status']],
            "client_status": status_dict[order['client_status']],
        }
        data.append(item_data)
        counter += 1
    return templates.TemplateResponse("active_orders.html", {"request": request, "data": data})
