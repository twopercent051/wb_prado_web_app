import logging
import os
import betterlogging as bl

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from starlette.templating import Jinja2Templates

from config import load_config

app = FastAPI(title="Prado_64_CRM")

templates = Jinja2Templates(directory=f"{os.getcwd()}/templates")
config = load_config(".env")

DATABASE_URL = f'postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}:5432/{config.db.database}'

logger = logging.getLogger(__name__)
log_level = logging.INFO
bl.basic_colorized_config(level=log_level)

scheduler = AsyncIOScheduler(timezone="UTC")
