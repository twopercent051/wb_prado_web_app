from fastapi import FastAPI


from routers.index import router as index_router
from routers.sales_report import router as sales_report_router
from routers.active_orders import router as active_orders_router

app = FastAPI(
    title="Prado_64_CRM",
    # root_path="/app"
)

app.include_router(index_router)
app.include_router(sales_report_router)
app.include_router(active_orders_router)
