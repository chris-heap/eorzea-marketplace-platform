import duckdb


class DuckDBConnect:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        self.conn = duckdb.connect(self.db_path, read_only=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

    def get_information_schema(self) -> str:
        return self.conn.sql("""
            SELECT
                c.TABLE_NAME AS TableName,
                c.COLUMN_NAME AS ColumnName,
                c.DATA_TYPE AS DataType
            FROM INFORMATION_SCHEMA.COLUMNS c
            INNER JOIN INFORMATION_SCHEMA.TABLES t
                ON c.TABLE_NAME = t.TABLE_NAME
                AND c.TABLE_SCHEMA = t.TABLE_SCHEMA
            WHERE t.TABLE_TYPE = 'BASE TABLE'
            ORDER BY TableName, c.ORDINAL_POSITION
        """).fetchdf().to_string(index=False)

    def execute(self, sql: str):
        return self.conn.execute(sql)
