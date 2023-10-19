import asyncio
from datetime import timedelta, datetime
from typing import List

from dateutil.parser import parse

from create_app import scheduler
from models.redis_connector import RedisConnector
from models.sql_connector import ProductsDAO, OrdersDAO, StocksDAO
from services.tg_bot import send_message
from services.wildberries import WildberriesMain, WildberriesStatistics


class CreateTask:

    def __init__(self):
        self.red = RedisConnector()

    @staticmethod
    def __parse_dtime(wb_dtime: str) -> datetime:
        create_dtime = parse(wb_dtime) + timedelta(hours=3)
        return datetime(year=create_dtime.year,
                        month=create_dtime.month,
                        day=create_dtime.day,
                        hour=create_dtime.hour,
                        minute=create_dtime.minute)

    async def update_fbs_orders(self, fbo_orders: List[dict]):
        orders = await WildberriesMain.get_fbs_orders()
        fbo_rids = [i["srid"] for i in fbo_orders]
        for order in orders["orders"]:
            product = await ProductsDAO.get_one_or_none(article=order["article"])
            if not product:
                continue
            check_order = await OrdersDAO.get_one_or_none(order_id=str(order["id"]))
            if not check_order and order["rid"] in fbo_rids:
                destination = ""
                for fbo_order in fbo_orders:
                    if fbo_order["srid"] == order["rid"]:
                        destination = fbo_order["oblast"]
                        break
                create_dtime = self.__parse_dtime(wb_dtime=order['createdAt'])
                await OrdersDAO.create(order_id=str(order["id"]),
                                       create_dtime=create_dtime,
                                       article=order["article"],
                                       seller_price=product["purchase_price"],
                                       client_price=int(int(order["convertedPrice"]) / 100),
                                       seller_status="new",
                                       client_status="waiting",
                                       rid=order["rid"],
                                       delivery_type="fbs",
                                       warehouse_name="Маркетплейс",
                                       destination=destination)
                item_text = [
                    "⚠️ Новый заказ FBS",
                    "-" * 5,
                    f"<b>Внутренний артикул:</b> <i>{order['article']}</i>",
                    f"<b>Наименование:</b> <i>{product['title']}</i>",
                    f"<b>Цена:</b> <i>{order['convertedPrice'] / 100} ₽</i>",
                    f"<b>Направление:</b> <i>{destination}</i>",
                    f"https://www.wildberries.ru/catalog/{order['nmId']}/detail.aspx"
                ]
                await send_message(text="\n".join(item_text))

    @staticmethod
    async def check_active_fbs_orders():
        orders = await OrdersDAO.get_active(with_last_2_week=True)
        if len(orders) == 0:
            return
        active_orders = [int(i["order_id"]) for i in orders]
        statuses = await WildberriesMain.get_statuses(orders=active_orders)
        status_dict = dict(confirm="📦 Сборка",
                           complete="🚛 Доставка",
                           sorted="🚦 Сортировка",
                           cancel="🤷 Отмена продавцом",
                           sold="✅ Выдача",
                           canceled="😡 Отмена",
                           canceled_by_client="😡 Отмена покупателем",
                           defect="🤬 Брак",
                           ready_for_pickup="⚓️ На ПВЗ")
        for wb_status in statuses["orders"]:
            for order in orders:
                if str(wb_status["id"]) == str(order["order_id"]):
                    date = order["create_dtime"].strftime("%d-%m-%Y")
                    text = [
                        "-" * 5,
                        f"Заказ от {date}",
                        f"Артикул {order['article']}",
                        f"Цена {order['seller_price']}р / {order['client_price']}р",
                        order["destination"]
                    ]
                    if wb_status["supplierStatus"] != order["seller_status"]:
                        await OrdersDAO.update_by_order_id(order_id=str(order["order_id"]),
                                                           seller_status=wb_status["supplierStatus"])
                        if wb_status["supplierStatus"] in ["cancel"]:
                            await OrdersDAO.update_by_order_id(order_id=str(order["order_id"]),
                                                               finish_dtime=datetime.utcnow())
                        status = [status_dict[wb_status["supplierStatus"]]]
                        status.extend(text)
                        await send_message(text="\n".join(status))
                    if wb_status["wbStatus"] != order["client_status"]:
                        await OrdersDAO.update_by_order_id(order_id=str(order["order_id"]),
                                                           client_status=wb_status["wbStatus"])
                        if wb_status["wbStatus"] in ["canceled", "canceled_by_client", "defect", "sold"]:
                            await OrdersDAO.update_by_order_id(order_id=str(order["order_id"]),
                                                               finish_dtime=datetime.utcnow())
                        status = [status_dict[wb_status["wbStatus"]]]
                        status.extend(text)
                        await send_message(text="\n".join(status))

    async def check_fbo_orders(self, fbo_orders: List[dict]):
        sql_orders = await OrdersDAO.get_many()
        rids = [i["rid"] for i in sql_orders]
        for fbo_order in fbo_orders:
            if fbo_order["srid"] in rids:
                if fbo_order["isCancel"]:
                    order = await OrdersDAO.get_one_or_none(rid=fbo_order["srid"])
                    if order["delivery_type"] == "fbo" and order["client_status"] != "canceled":
                        dtime_now = datetime.utcnow()
                        await OrdersDAO.update_by_order_id(order_id=order["order_id"],
                                                           client_status="canceled",
                                                           finish_dtime=dtime_now)
                        date = order["create_dtime"].strftime("%d-%m-%Y")
                        text = [
                            "😡 Отмена",
                            "-" * 5,
                            f"Заказ от {date}",
                            f"Артикул {order['article']}",
                            f"Цена {order['seller_price']}р / {order['client_price']}р",
                            order["destination"]
                        ]
                        await send_message(text="\n".join(text))
            else:
                product = await ProductsDAO.get_one_or_none(article=fbo_order["supplierArticle"])
                if fbo_order["orderType"] == "Клиентский":
                    client_price = int((fbo_order["totalPrice"] * (100 - fbo_order["discountPercent"])) / 100)
                    await OrdersDAO.create(order_id=str(fbo_order["odid"]),
                                           create_dtime=self.__parse_dtime(wb_dtime=fbo_order['date']),
                                           article=fbo_order["supplierArticle"],
                                           seller_price=product["purchase_price"],
                                           client_price=client_price,
                                           seller_status="---",
                                           client_status="sorted",
                                           rid=fbo_order["srid"],
                                           delivery_type="fbo",
                                           warehouse_name=fbo_order["warehouseName"],
                                           destination=fbo_order["oblast"])
                    text = [
                        "💡 Заказ по FBO",
                        f"<b>Внутренний артикул:</b> <i>{product['article']}</i>",
                        f"<b>Цена:</b> <i>{client_price} ₽</i>",
                        f"<b>Склад:</b> <i>{fbo_order['warehouseName']}</i>",
                        f"<b>Направление:</b> <i>{fbo_order['oblast']}</i>",
                    ]
                else:
                    await OrdersDAO.create(order_id=str(fbo_order["odid"]),
                                           create_dtime=self.__parse_dtime(wb_dtime=fbo_order['date']),
                                           article=fbo_order["supplierArticle"],
                                           seller_price=0,
                                           client_price=0,
                                           seller_status="---",
                                           client_status="sorted",
                                           rid=fbo_order["srid"],
                                           delivery_type="fbo",
                                           warehouse_name=fbo_order["warehouseName"],
                                           destination=fbo_order["oblast"])
                    text = [
                        f"💡 {fbo_order['supplierArticle']}",
                        fbo_order["orderType"]
                    ]
                await send_message(text="\n".join(text))

    async def check_sold_fbo_orders(self):
        sold_fbo_orders = await WildberriesStatistics.get_fbo_sold_orders()
        for order in sold_fbo_orders:
            sql_order = await OrdersDAO.get_one_or_none(rid=order["srid"])
            if sql_order["client_status"] == "sorted" and sql_order["delivery_type"] == "fbo":
                await OrdersDAO.update_by_order_id(order_id=sql_order["order_id"],
                                                   client_status="sold",
                                                   finish_dtime=self.__parse_dtime(wb_dtime=order["date"]))
                date = sql_order["create_dtime"].strftime("%d-%m-%Y")
                text = [
                    "✅ Выдача",
                    "-" * 5,
                    f"Заказ от {date}",
                    f"Артикул {order['article']}",
                    f"Цена {order['seller_price']}р / {order['client_price']}р",
                    order["destination"]
                ]
                await send_message(text="\n".join(text))
                await send_message(text=text)

    @staticmethod
    async def check_feedbacks_and_questions():
        new_events = await WildberriesMain.get_feedbacks_and_questions()
        for question in new_events["questions"]:
            text = f"❔ Вопрос по товару {question['article']}\n\n<i>{question['text']}</i>"
            await send_message(text=text)
        for feedback in new_events["feedbacks"]:
            text = f"{'⭐️' * feedback['rating']}\n\nОтзыв на товар {feedback['article']}\n\n<i>{feedback['text']}</i>"
            await send_message(text=text)

    async def get_warehouse(self):
        events = await WildberriesStatistics.get_warehouse()
        timestamps = []
        text = None
        last_timestamp = self.red.get()
        for event in events:
            event_timestamp = self.__parse_dtime(wb_dtime=event["lastChangeDate"]).timestamp()
            if event_timestamp < last_timestamp:
                continue
            timestamps.append(event_timestamp)
            stock = await StocksDAO.get_one_or_none(article=event["supplierArticle"],
                                                    warehouse=event["warehouseName"],
                                                    barcode=event["barcode"])
            if stock:
                stock_diff = event["quantity"] - stock["quantity"]
                await StocksDAO.update_by_id(item_id=stock["id"],
                                             to_client=event["inWayToClient"],
                                             from_client=event["inWayFromClient"],
                                             quantity=event["quantity"])
            else:
                stock_diff = event["quantity"]
                await StocksDAO.create(article=event["supplierArticle"],
                                       warehouse=event["warehouseName"],
                                       barcode=event["barcode"],
                                       to_client=event["inWayToClient"],
                                       from_client=event["inWayFromClient"],
                                       quantity=event["quantity"])
            if stock_diff > 0:
                text = f"📦 На склад {event['warehouseName']} поступило {abs(stock_diff)}шт {event['supplierArticle']}"
            if stock_diff < 0:
                text = f"📦 Со склада {event['warehouseName']} отправлено {abs(stock_diff)}шт {event['supplierArticle']}"
            if text:
                await send_message(text=text)
        latest_timestamp = max(timestamps)
        self.red.update(new_timestamp=latest_timestamp)

    async def short_tasker(self):
        fbo_orders = await WildberriesStatistics.get_fbo_orders()
        await self.update_fbs_orders(fbo_orders=fbo_orders)
        await self.check_active_fbs_orders()
        await self.check_feedbacks_and_questions()
        await self.check_fbo_orders(fbo_orders=fbo_orders)
        await self.check_sold_fbo_orders()
        await self.get_warehouse()

    async def create_task(self):
        scheduler.add_job(func=self.short_tasker,
                          trigger="interval",
                          minutes=5,
                          misfire_grace_time=None)


if __name__ == "__main__":
    a = CreateTask()
    asyncio.run(a.get_warehouse())
