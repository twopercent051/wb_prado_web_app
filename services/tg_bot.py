import aiohttp

from config import load_config

config = load_config(".env")
token = config.tg_bot.bot_token
admin = config.tg_bot.admin_group


async def send_message(text: str):
    params = dict(chat_id=admin, text=text, parse_mode="HTML", disable_web_page_preview="true")
    async with aiohttp.ClientSession() as session:
        await session.get(f'https://api.telegram.org/bot{token}/sendMessage', params=params)
