import asyncio
from datetime import datetime, timedelta
from typing import Optional, List

import aiohttp

from create_app import config


class WildberriesAPI:
    token = None

    @classmethod
    async def _get_request(cls, url: str, data: Optional[dict] = None):
        headers = dict(Authorization=cls.token)
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=headers, params=data) as resp:
                if resp.status < 400:
                    return await resp.json()

    @classmethod
    async def _post_request(cls, url: str, data: dict = None):
        headers = dict(Authorization=cls.token)
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers, json=data) as resp:
                if resp.status < 400:
                    return await resp.json()

    @classmethod
    async def _put_request(cls, url: str, data: dict = None):
        headers = dict(Authorization=cls.token)
        async with aiohttp.ClientSession() as session:
            async with session.put(url=url, headers=headers, json=data) as resp:
                return resp.status


class WildberriesMain(WildberriesAPI):
    token = config.wb.main_token

    @classmethod
    async def get_seller_warehouses(cls):
        url = "https://suppliers-api.wildberries.ru/api/v3/warehouses"
        return await cls._get_request(url=url)

    @classmethod
    async def get_all_products(cls):
        url = "https://suppliers-api.wildberries.ru/content/v1/cards/cursor/list"
        data = {
            "sort": {"cursor": {"limit": 1000},
                     "filter": {"withPhoto": -1}}
        }
        result = await cls._post_request(url=url, data=data)
        return result["data"]["cards"]

    @classmethod
    async def get_cards_by_art(cls, arts: list):
        url = "https://suppliers-api.wildberries.ru/content/v1/cards/filter"
        data = dict(vendorCodes=arts, allowedCategoriesOnly=False)
        response = await cls._post_request(url=url, data=data)
        result = []
        for item in response["data"]:
            article = item["vendorCode"]
            title = ""
            wb_id = item["nmID"]
            sku = item["sizes"][0]["skus"][0]
            for param in item["characteristics"]:
                if param.keys().__contains__("Наименование"):
                    title = param["Наименование"]
                    break
            result.append(dict(article=article, title=title, wb_id=str(wb_id), sku=sku))
        return result

    @classmethod
    async def get_fbs_quantity(cls, warehouse_id: int, skus: List[str]):
        url = f"https://suppliers-api.wildberries.ru/api/v3/stocks/{warehouse_id}"
        data = dict(skus=skus)
        return await cls._post_request(url=url, data=data)

    @classmethod
    async def set_fbs_quantity(cls, warehouse_id: int, data: List[dict]):
        url = f"https://suppliers-api.wildberries.ru/api/v3/stocks/{warehouse_id}"
        data = dict(stocks=data)
        return await cls._put_request(url=url, data=data)

    @classmethod
    async def get_prices(cls):
        url = "https://suppliers-api.wildberries.ru/public/api/v1/info"
        data = dict(quantity="0")
        return await cls._get_request(url=url, data=data)

    @classmethod
    async def set_price(cls, prices_list: List[dict], discount_list: List[dict]):
        url_prices = "https://suppliers-api.wildberries.ru/public/api/v1/prices"
        url_discounts = "https://suppliers-api.wildberries.ru/public/api/v1/updateDiscounts"
        try:
            await cls._post_request(url=url_prices, data=prices_list)
            await asyncio.sleep(1)
            await cls._post_request(url=url_discounts, data=discount_list)
        except Exception as ex:
            print(ex)

    @classmethod
    async def get_fbs_orders(cls):
        date_from = str(int((datetime.utcnow() - timedelta(days=2)).timestamp()))
        url = "https://suppliers-api.wildberries.ru/api/v3/orders"
        data = dict(limit="100", next="0", dateFrom=str(date_from))
        return await cls._get_request(url=url, data=data)

    @classmethod
    async def get_statuses(cls, orders: List[int]):
        url = "https://suppliers-api.wildberries.ru/api/v3/orders/status"
        data = dict(orders=orders)
        return await cls._post_request(url=url, data=data)

    @classmethod
    async def get_feedbacks_and_questions(cls):
        date_from = int((datetime.utcnow() - timedelta(minutes=5)).timestamp())
        questions_url = "https://feedbacks-api.wildberries.ru/api/v1/questions"
        feedbacks_url = "https://feedbacks-api.wildberries.ru/api/v1/feedbacks"
        data = dict(isAnswered="false", take="5000", skip="0", dateFrom=str(date_from))
        questions = await cls._get_request(url=questions_url, data=data)
        feedbacks = await cls._get_request(url=feedbacks_url, data=data)
        questions_data = []
        feedbacks_data = []
        for question in questions["data"]["questions"]:
            question_dict = dict(id=question["id"],
                                 text=question["text"],
                                 article=question["productDetails"]["supplierArticle"])
            questions_data.append(question_dict)
        for feedback in feedbacks["data"]["feedbacks"]:
            feedback_dict = dict(id=feedback["id"],
                                 text=feedback["text"],
                                 rating=feedback["productValuation"],
                                 article=feedback["productDetails"]["supplierArticle"])
            feedbacks_data.append(feedback_dict)
        return dict(questions=questions_data, feedbacks=feedbacks_data)


class WildberriesStatistics(WildberriesAPI):
    token = config.wb.statistic_token

    @classmethod
    async def get_fbo_sold_orders(cls):
        date_from = str((datetime.utcnow() - timedelta(days=20)))
        url = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"
        data = dict(dateFrom=date_from)
        return await cls._get_request(url=url, data=data)

    @classmethod
    async def get_fbo_orders(cls):
        date_from = str((datetime.utcnow() - timedelta(days=2)))
        url = "https://statistics-api.wildberries.ru/api/v1/supplier/orders"
        data = dict(dateFrom=date_from)
        return await cls._get_request(url=url, data=data)

    @classmethod
    async def get_warehouse(cls):
        date_from = str((datetime.utcnow() - timedelta(days=300)))
        url = "https://statistics-api.wildberries.ru/api/v1/supplier/stocks"
        data = dict(dateFrom=date_from)
        return await cls._get_request(url=url, data=data)


async def main_func():
    a = await WildberriesStatistics.get_fbo_sold_orders()
    print(a)


if __name__ == "__main__":
    asyncio.run(main_func())
