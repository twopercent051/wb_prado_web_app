from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from create_app import templates
from models.sql_connector import OrdersDAO, ProductsDAO
from routers.auth import SUserAuth, get_current_user

router = APIRouter()


@router.get("/sales_report", response_class=HTMLResponse)
async def sales_report_page(request: Request, user: SUserAuth = Depends(get_current_user)):
    data = await OrdersDAO.get_total_report_by_articles()
    products = await ProductsDAO.get_many()
    result = []
    for item in data:
        for product in products:
            if item["article"] == product["article"]:
                loaded_sum = item["loaded_sum"] if item["loaded_sum"] else 0
                sold_sum = item["sold_sum"] if item["sold_sum"] else 0
                result.append(dict(article=item["article"],
                                   loaded_positions=item["loaded_positions"],
                                   loaded_sum=loaded_sum,
                                   sold_positions=item["sold_positions"],
                                   sold_sum=sold_sum,
                                   in_system_positions=item["in_system_positions"],
                                   in_system_sum=item["in_system_positions"] * product["purchase_price"]))

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
            "data": result,
            "loaded_total_data": loaded_total_data,
            "sold_total_data": sold_total_data,
            "in_system_total_data": in_system_total_data
        },
    )
