from typing import List

from pydantic import BaseModel

from services.wildberries import WildberriesMain


class OrdersWbFbo(BaseModel):
    article: str
    rid: str
    create_dtime: str
    order_id: int
    price: int


class ValidData:

    @classmethod
    async def orders_fbo_wb(cls) -> List[OrdersWbFbo]:
        data = await WildberriesMain.get_fbs_orders()
        result = []
        for order in data["orders"]:
            item = OrdersWbFbo(article=order["article"],
                               rid=order["rid"],
                               )
