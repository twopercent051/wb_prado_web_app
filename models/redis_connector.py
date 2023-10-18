from datetime import datetime

import redis

from create_app import config, logger


class RedisConnector:

    def __init__(self):
        self.r = redis.Redis(host=config.redis.host, port=config.redis.port, db=config.redis.database)
        self.db = "last_stock_event"

    def redis_start(self):
        response = self.r.get(self.db)
        if not response:
            self.r.set(self.db, 0)
        logger.info('Redis connected OKK')

    def update(self, new_timestamp: int | float):
        self.r.set(self.db, new_timestamp)

    def get(self) -> int:
        response = self.r.get(self.db)
        if not response:
            return
        return float(response)


def test():
    red = RedisConnector()
    red.redis_start()
    # red.get()


if __name__ == "__main__":
    test()
