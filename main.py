from fastapi import FastAPI


from routers.index import router as index_router

app = FastAPI(
    title="Prado_64_CRM",
    # root_path="/app"
)

app.include_router(index_router)

