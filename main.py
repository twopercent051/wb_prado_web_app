from fastapi.staticfiles import StaticFiles

from create_app import app, scheduler
from routers.index import router as index_router
from routers.sales_report import router as sales_report_router
from routers.active_orders import router as active_orders_router
from routers.products import router as products_router
from routers.auth import router as auth_router
from services.scheduler import CreateTask

app.include_router(index_router)
app.include_router(sales_report_router)
app.include_router(active_orders_router)
app.include_router(products_router)
app.include_router(auth_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

create_task = CreateTask()


@app.on_event("startup")
async def in_startup():
    scheduler.remove_all_jobs()
    await create_task.create_task()
    scheduler.start()
