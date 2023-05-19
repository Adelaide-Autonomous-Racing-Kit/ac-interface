from src.metrics.database.postgres import PostgresConnector


class EvaluationMonitor(PostgresConnector):
    def __init__(
        self,
        dbname="postgres",
        user="postgres",
        password="postgres",
        host="0.0.0.0",
        port="5432",
        table_name=None,
    ):
        super().__init__(dbname, user, password, host, port, table_name)
