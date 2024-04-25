from typing import Dict

from loguru import logger
import psycopg


class PostgresConnector:
    def __init__(self, postgres_config: Dict):
        self._dbname = postgres_config["dbname"]
        self._user = postgres_config["user"]
        self._password = postgres_config["password"]
        self._host = postgres_config["host"]
        self._port = postgres_config["port"]
        self._table_name = postgres_config["table_name"]
        self._connect_to_postgres()

    def _connect_to_postgres(self):
        self._session = psycopg.connect(
            dbname=self._dbname,
            user=self._user,
            password=self._password,
            host=self._host,
            port=self._port,
        )
        logger.success("Connected to Database")

    def close(self):
        self._session.close()
