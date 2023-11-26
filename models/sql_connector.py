import asyncio
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import MetaData, DateTime, Column, Integer, String, select, insert, delete, update, null, func, asc, \
    desc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, as_declarative

from config import load_config


config = load_config(".env")

DATABASE_URL = f'postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}:5432/{config.db.database}'

engine = create_async_engine(DATABASE_URL)

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@as_declarative()
class Base:
    metadata = MetaData()


class ProductsDB(Base):
    __tablename__ = "products"

    id = Column(Integer, nullable=False, autoincrement=True, primary_key=True)
    article = Column(String, nullable=False)
    title = Column(String, nullable=True)
    wb_id = Column(String, nullable=True)
    sku = Column(String, nullable=True)
    purchase_price = Column(Integer, nullable=True)
    sale_price = Column(Integer, nullable=True)


class OrdersDB(Base):
    __tablename__ = "orders"

    id = Column(Integer, nullable=False, autoincrement=True, primary_key=True)
    order_id = Column(String, nullable=False, unique=True)
    article = Column(String, nullable=False)
    seller_price = Column(Integer, nullable=False)
    client_price = Column(Integer, nullable=False)
    create_dtime = Column(DateTime, nullable=False)
    seller_status = Column(String, nullable=False)
    client_status = Column(String, nullable=False)
    finish_dtime = Column(DateTime, nullable=True)
    rid = Column(String)
    delivery_type = Column(String)
    destination = Column(String)
    warehouse_name = Column(String)


class StocksDB(Base):
    __tablename__ = "stocks"

    id = Column(Integer, nullable=False, autoincrement=True, primary_key=True)
    article = Column(String, nullable=False)
    barcode = Column(String, nullable=False)
    warehouse = Column(String, nullable=False)
    to_client = Column(Integer, nullable=True)
    from_client = Column(Integer, nullable=True)
    quantity = Column(Integer, nullable=True)


class BaseDAO:
    """Класс взаимодействия с БД"""
    model = None

    @classmethod
    async def get_one_or_none(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model.__table__.columns).filter_by(**filter_by).limit(1)
            result = await session.execute(query)
            return result.mappings().one_or_none()

    @classmethod
    async def get_many(cls, **filter_by) -> list:
        async with async_session_maker() as session:
            query = select(cls.model.__table__.columns).filter_by(**filter_by).order_by(cls.model.id.asc())
            result = await session.execute(query)
            return result.mappings().all()

    @classmethod
    async def create(cls, **data):
        async with async_session_maker() as session:
            stmt = insert(cls.model).values(**data)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def create_many(cls, data: List[dict]):
        async with async_session_maker() as session:
            stmt = insert(cls.model).values(data)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def delete(cls, **data):
        async with async_session_maker() as session:
            stmt = delete(cls.model).filter_by(**data)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def update_by_id(cls, item_id: int, **data):
        async with async_session_maker() as session:
            stmt = update(cls.model).values(**data).filter_by(id=item_id)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def test(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(func.count(cls.model.id)).filter_by(**filter_by).limit(1)
            result = await session.execute(query)
            return result.mappings().one_or_none()


class ProductsDAO(BaseDAO):
    model = ProductsDB

    @classmethod
    async def update_by_article(cls, article: str, **data):
        async with async_session_maker() as session:
            stmt = update(cls.model).values(**data).filter_by(article=article)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def get_many_by_articles_list(cls, articles: List[str]) -> List[dict]:
        async with async_session_maker() as session:
            query = select(cls.model.__table__.columns).where(cls.model.article.in_(articles)).\
                order_by(cls.model.id.asc())
            result = await session.execute(query)
            return result.mappings().all()


class OrdersDAO(BaseDAO):
    model = OrdersDB

    @classmethod
    async def update_by_order_id(cls, order_id: str, **data):
        async with async_session_maker() as session:
            stmt = update(cls.model).values(**data).filter_by(order_id=order_id)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def get_active(cls, with_last_2_week: bool = False) -> list:
        async with async_session_maker() as session:
            query = select(cls.model.__table__.columns).filter(cls.model.finish_dtime.is_(null())).\
                order_by(cls.model.id.asc())
            result = await session.execute(query)
            result = result.mappings().all()
            if with_last_2_week:
                last_2_week = datetime.utcnow() - timedelta(days=14)
                query = select(cls.model.__table__.columns).where(cls.model.finish_dtime > last_2_week)
                last_result = await session.execute(query)
                last_result = last_result.mappings().all()
                last_result.extend(result)
                return last_result
            return result

    @classmethod
    async def get_last_week(cls, is_new: bool) -> list:
        async with async_session_maker() as session:
            last_week = datetime.utcnow() - timedelta(days=7, hours=9)
            if is_new:
                query = select(cls.model.__table__.columns).where(cls.model.create_dtime > last_week)
            else:
                query = select(cls.model.__table__.columns).where(cls.model.finish_dtime > last_week)
            result = await session.execute(query)
            return result.mappings().all()

    @classmethod
    async def get_orders_by_client_status(cls, is_all: bool = False) -> list:
        async with async_session_maker() as session:
            status_list = ["sold"]
            if is_all:
                status_list.extend(["sorted", "ready_for_pickup", "canceled_by_client", "defect"])
            query = select(cls.model.__table__.columns).where(cls.model.client_status.in_(status_list)).\
                order_by(cls.model.id)
            result = await session.execute(query)
            return result.mappings().all()

    @classmethod
    async def get_weekly_report(cls) -> list:
        async with async_session_maker() as session:
            last_week = datetime.utcnow() - timedelta(days=7, hours=9)
            this_week = datetime.utcnow() - timedelta(hours=9)
            query = select(OrdersDB.article, func.sum(OrdersDB.seller_price), func.count(OrdersDB.article)).\
                group_by(OrdersDB.article).filter_by(client_status="sold").\
                where(OrdersDB.finish_dtime > last_week, OrdersDB.finish_dtime < this_week)
            result = await session.execute(query)
            return result.mappings().all()

    @classmethod
    async def get_total_report_by_articles(cls) -> list:
        async with async_session_maker() as session:
            query = select(
                OrdersDB.article,
                func.count().filter(OrdersDB.seller_status == 'complete').label('loaded_positions'),
                func.sum(OrdersDB.seller_price).filter(OrdersDB.seller_status == 'complete').label('loaded_sum'),
                func.count().filter(OrdersDB.client_status == 'sold').label('sold_positions'),
                func.sum(OrdersDB.seller_price).filter(OrdersDB.client_status == 'sold').label('sold_sum'),
                (func.count().filter(OrdersDB.seller_status == 'complete') -
                 func.count().filter(OrdersDB.client_status == 'sold')).label('in_system_positions'),
                (func.sum(OrdersDB.seller_price).filter(OrdersDB.seller_status == 'complete') -
                 func.sum(OrdersDB.seller_price).filter(OrdersDB.client_status == 'sold')).label('in_system_sum')
            ).group_by(OrdersDB.article).order_by(desc('loaded_positions'))
            result = await session.execute(query)
            return result.mappings().all()

    @classmethod
    async def get_total_report(cls, **filter_by) -> dict:
        async with async_session_maker() as session:
            query = select(func.sum(OrdersDB.seller_price), func.count(OrdersDB.article)).filter_by(**filter_by).\
                limit(1)
            result = await session.execute(query)
            return result.mappings().one_or_none()


class StocksDAO(BaseDAO):
    model = StocksDB


async def test():
    a = await OrdersDAO.get_total_report_by_articles()
    print(a)

if __name__ == "__main__":
    asyncio.run(test())
