from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

import config


@lru_cache(maxsize=1)
def get_engine():

    url = URL.create(
        drivername="oracle+oracledb",
        username=config.ORACLE_USER,
        password=config.ORACLE_PASSWORD,
        host=config.ORACLE_HOST,
        port=config.ORACLE_PORT,
        query={
            "service_name": config.ORACLE_SERVICE_NAME
        }
    )

    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
        future=True
    )

    return engine


def test_connection():

    with get_engine().connect() as connection:

        result = connection.execute(
            text("SELECT 1 FROM DUAL")
        )

        return result.scalar_one()


def get_schema_text():

    if not config.ALLOWED_TABLES:
        return "No allowed tables configured."

    table_names = list(
        sorted(config.ALLOWED_TABLES)
    )

    bind_names = []

    params = {}

    for index, table in enumerate(table_names):

        parameter_name = f"table_{index}"

        bind_names.append(
            f":{parameter_name}"
        )

        params[parameter_name] = table

    sql = f"""
        SELECT
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE,
            NULLABLE,
            COLUMN_ID
        FROM USER_TAB_COLUMNS
        WHERE TABLE_NAME IN (
            {", ".join(bind_names)}
        )
        ORDER BY
            TABLE_NAME,
            COLUMN_ID
    """

    rows = []

    with get_engine().connect() as connection:

        result = connection.execute(
            text(sql),
            params
        )

        for row in result.mappings():

            rows.append({
                "table": row["TABLE_NAME"],
                "column": row["COLUMN_NAME"],
                "data_type": row["DATA_TYPE"],
                "nullable": row["NULLABLE"]
            })

    if not rows:

        return (
            "No table metadata found. "
            "Check Oracle user/schema/table names."
        )

    tables = {}

    for row in rows:

        tables.setdefault(
            row["table"],
            []
        ).append(row)

    output = []

    for table_name, columns in tables.items():

        output.append(
            f"TABLE {table_name}"
        )

        for column in columns:

            output.append(
                "  - "
                f"{column['column']} "
                f"({column['data_type']}, "
                f"nullable={column['nullable']})"
            )

    return "\n".join(output)


def execute_readonly_sql(sql):

    cleaned_sql = (
        sql
        .strip()
        .rstrip(";")
        .strip()
    )

    upper_sql = cleaned_sql.upper()

    # --------------------------------------------------------
    # Only SELECT and WITH are allowed.
    # --------------------------------------------------------

    if not (
        upper_sql.startswith("SELECT ")
        or upper_sql.startswith("WITH ")
    ):

        raise ValueError(
            "Only SELECT and WITH SQL statements are allowed."
        )

    # --------------------------------------------------------
    # Block dangerous SQL
    # --------------------------------------------------------

    blocked_keywords = [
        "INSERT ",
        "UPDATE ",
        "DELETE ",
        "MERGE ",
        "DROP ",
        "ALTER ",
        "TRUNCATE ",
        "CREATE ",
        "GRANT ",
        "REVOKE ",
        "BEGIN ",
        "DECLARE ",
        "EXECUTE ",
        "CALL ",
        "COMMIT",
        "ROLLBACK",
        "DBMS_"
    ]

    padded_sql = " " + upper_sql + " "

    for keyword in blocked_keywords:

        if keyword in padded_sql:

            raise ValueError(
                f"Blocked SQL operation: "
                f"{keyword.strip()}"
            )

    # --------------------------------------------------------
    # Execute
    # --------------------------------------------------------

    with get_engine().connect() as connection:

        result = connection.execute(
            text(cleaned_sql)
        )

        columns = list(
            result.keys()
        )

        rows = []

        for row in result.mappings().fetchmany(100):

            rows.append(
                dict(row)
            )

    return columns, rows