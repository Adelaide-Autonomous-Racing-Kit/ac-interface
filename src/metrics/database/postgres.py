from loguru import logger
import psycopg


class PostgresConnector:
    def __init__(
        self,
        dbname="postgres",
        user="postgres",
        password="postgres",
        host="0.0.0.0",
        port="5432",
        table_name=None,
    ):
        self._table_name = table_name
        self._connect_to_postgres(dbname, user, password, host, port)

    def _connect_to_postgres(
        self,
        dbname: str,
        user: str,
        password: str,
        host: str,
        port: str,
    ):
        self._session = psycopg.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
        )
        logger.success("Connected to Database")

    def close(self):
        self._session.close()
