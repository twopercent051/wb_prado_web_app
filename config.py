from dataclasses import dataclass

from environs import Env


@dataclass
class TgBotConfig:
    bot_token: str
    admin_group: str


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str


@dataclass
class RedisConfig:
    host: str
    port: int
    database: int


@dataclass
class AuthConfig:
    login: str
    password: str
    secret_key: str
    algorithm: str


@dataclass
class WBConfig:
    main_token: str
    statistic_token: str


@dataclass
class Config:
    tg_bot: TgBotConfig
    db: DbConfig
    redis: RedisConfig
    auth: AuthConfig
    wb: WBConfig


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBotConfig(
            bot_token=env.str("BOT_TOKEN"),
            admin_group=env.str("ADMIN_GROUP")
        ),
        db=DbConfig(
            host=env.str('DB_HOST'),
            password=env.str('DB_PASS'),
            user=env.str('DB_USER'),
            database=env.str('DB_NAME')
        ),
        redis=RedisConfig(
            host=env.str("REDIS_HOST"),
            port=env.int("REDIS_PORT"),
            database=env.int("REDIS_DB")
        ),
        auth=AuthConfig(
            login=env.str("LOGIN"),
            password=env.str("PASS"),
            secret_key=env.str("SECRET_KEY"),
            algorithm=env.str("ALGORITHM"),
        ),
        wb=WBConfig(
            main_token=env.str("MAIN_TOKEN"),
            statistic_token=env.str("STATISTIC_TOKEN"),
        )
    )
