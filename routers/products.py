from typing import List

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from starlette import status

from create_app import templates, app
from models.sql_connector import ProductsDAO
from routers.auth import SUserAuth, get_current_user
from services.wildberries import WildberriesMain

router = APIRouter()


def get_warehouse_name(warehouses: List[dict], warehouse_id: int) -> str:
    for item in warehouses:
        if warehouse_id == item["id"]:
            return item["name"]


async def get_fbs_quantity(current_products: List[dict], warehouse_id: int) -> List[dict]:
    current_products_skus = [i["sku"] for i in current_products]
    fbs_quantity = await WildberriesMain.get_fbs_quantity(warehouse_id=warehouse_id, skus=current_products_skus)
    fbs_skus = [i["sku"] for i in fbs_quantity["stocks"]]
    result = []
    for product in current_products:
        product = dict(product)
        if product["sku"] in fbs_skus:
            for item in fbs_quantity["stocks"]:
                if product["sku"] == item["sku"]:
                    product["quantity"] = item["amount"]
        else:
            product["quantity"] = 0
        result.append(product)
    return result


async def get_and_update_products(warehouse_id: int, sql_products: List[dict]) -> List[dict]:
    wb_products = await WildberriesMain.get_all_products()
    sql_products_articles = [i["article"] for i in sql_products]
    new_wb_products_articles = []
    for wb_product in wb_products:
        if wb_product["vendorCode"] not in sql_products_articles:
            new_wb_products_articles.append(wb_product["vendorCode"])
    if len(new_wb_products_articles) > 0:
        new_wb_products = await WildberriesMain.get_cards_by_art(arts=new_wb_products_articles)
        for item in new_wb_products:
            item["purchase_price"] = 0
            item["sale_price"] = 0
        await ProductsDAO.create_many(new_wb_products)
    all_sql_products = await ProductsDAO.get_many()
    current_wb_articles = [i["vendorCode"] for i in wb_products]
    current_products = list(filter(lambda x: x["article"] in current_wb_articles, all_sql_products))
    return await get_fbs_quantity(current_products=current_products, warehouse_id=warehouse_id)


class PricesData(BaseModel):
    wb_id: str
    sale_price: str
    accept: bool


class ProductData(BaseModel):
    article: str
    purchase_price: str
    sale_price: str
    quantity: str
    warehouse_id: str


@router.get("/products", response_class=HTMLResponse)
async def products_page(request: Request, warehouse_id: int, user: SUserAuth = Depends(get_current_user)):
    warehouses = await WildberriesMain.get_seller_warehouses()
    warehouse_name = None
    current_products = None
    sql_products = await ProductsDAO.get_many()
    wb_prices = await WildberriesMain.get_prices()
    non_default_prices = []
    for product in sql_products:
        if product["wb_id"] is None:
            continue
        for item in wb_prices:
            if int(product["wb_id"]) == item["nmId"]:
                real_price = item["price"] * (1 - 0.01 * item["discount"])
                if abs(real_price - product["sale_price"]) > real_price * 0.01:
                    item_dict = dict(article=product["article"],
                                     wb_id=product["wb_id"],
                                     sale_price=product["sale_price"],
                                     real_price=int(real_price))
                    non_default_prices.append(item_dict)
    is_non_default_prices = True if len(non_default_prices) else False
    if warehouse_id != 0:
        warehouse_name = get_warehouse_name(warehouses=warehouses, warehouse_id=warehouse_id)
        current_products = await get_and_update_products(warehouse_id=warehouse_id, sql_products=sql_products)
    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "warehouses": warehouses,
            "warehouse_name": warehouse_name,
            "current_products": current_products,
            "non_default_prices": non_default_prices,
            "is_non_default_prices": is_non_default_prices
        }
    )


@router.post("/update_prices")
async def products_page(prices_data: List[PricesData]):
    prices_list = []
    discount_list = []
    for item in prices_data:
        if item.accept:
            prices_list.append(dict(nmId=int(item.wb_id), price=int(int(item.sale_price) / 0.75)))
            discount_list.append(dict(nm=int(item.wb_id), discount=25))
    if len(prices_list) > 0:
        await WildberriesMain.set_price(prices_list=prices_list, discount_list=discount_list)


@router.post("/update_products", response_class=HTMLResponse)
async def products_page(product_data: List[ProductData]):
    quantity_articles_list = []
    warehouse_id = product_data[-1].warehouse_id
    for product in product_data:
        if product.purchase_price != "" and product.sale_price != "":
            await ProductsDAO.update_by_article(article=product.article,
                                                purchase_price=int(product.purchase_price),
                                                sale_price=int(product.sale_price))
        else:
            if product.purchase_price != "":
                await ProductsDAO.update_by_article(article=product.article, purchase_price=int(product.purchase_price))
            if product.sale_price != "":
                await ProductsDAO.update_by_article(article=product.article, sale_price=int(product.sale_price))
        if product.quantity != "":
            quantity_articles_list.append(product.article)
    if len(quantity_articles_list) > 0:
        products = await ProductsDAO.get_many_by_articles_list(articles=quantity_articles_list)
        warehouse_list = []
        for product in products:
            for item in product_data:
                if product["article"] == item.article:
                    warehouse_data = dict(sku=product["sku"], amount=int(item.quantity))
                    warehouse_list.append(warehouse_data)
        await WildberriesMain.set_fbs_quantity(warehouse_id=warehouse_id, data=warehouse_list)
    return RedirectResponse(url=app.url_path_for('index_page'), status_code=status.HTTP_303_SEE_OTHER)

