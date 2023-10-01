from dataclasses import dataclass

from environs import Env


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str


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
    db: DbConfig
    auth: AuthConfig
    wb: WBConfig


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        db=DbConfig(
            host=env.str('DB_HOST'),
            password=env.str('DB_PASS'),
            user=env.str('DB_USER'),
            database=env.str('DB_NAME')
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
