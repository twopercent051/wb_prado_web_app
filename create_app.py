import os

from fastapi import FastAPI
from starlette.templating import Jinja2Templates

from config import load_config

app = FastAPI(title="Prado_64_CRM")

templates = Jinja2Templates(directory=f"{os.getcwd()}/templates")
config = load_config(".env")

DATABASE_URL = f'postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}:5432/{config.db.database}'
