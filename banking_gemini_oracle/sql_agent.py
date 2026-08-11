import re

from db import (
    execute_readonly_sql,
    get_schema_text
)

from gemini import get_llm


SQL_PROMPT = """
You are an expert Oracle SQL developer
working for a banking chatbot.

DATABASE SCHEMA
================

{schema}


USER QUESTION
=============

{question}


RULES
=====

1. Generate exactly ONE Oracle SQL statement.

2. Only SELECT or WITH statements are allowed.

3. Never generate:

   INSERT
   UPDATE
   DELETE
   MERGE
   DROP
   ALTER
   TRUNCATE
   CREATE
   GRANT
   REVOKE
   BEGIN
   DECLARE
   EXECUTE
   CALL
   COMMIT
   ROLLBACK

4. Use ONLY tables available in the schema.

5. Use ONLY columns available in the schema.

6. Never invent a column.

7. Do not access any table that is not shown.

8. Do not use DBMS packages.

9. Prefer simple readable SQL.

10. Return ONLY SQL.

11. Do not use Markdown.

12. If the question cannot be answered from the schema,
    return exactly:

CANNOT_ANSWER


Return SQL now.
"""


def clean_sql(response):

    sql = response.strip()

    # Remove Markdown fences if Gemini accidentally adds them.

    sql = re.sub(
        r"^```sql\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )

    sql = re.sub(
        r"^```\s*",
        "",
        sql
    )

    sql = re.sub(
        r"\s*```$",
        "",
        sql
    )

    return sql.strip()


def generate_sql(question):

    schema = get_schema_text()

    prompt = SQL_PROMPT.format(
        schema=schema,
        question=question
    )

    response = get_llm().invoke(
        prompt
    )

    sql = clean_sql(
        response.content
    )

    if sql.upper() == "CANNOT_ANSWER":

        raise ValueError(
            "The Oracle database cannot answer "
            "this question from the configured tables."
        )

    return sql


def ask_oracle(question):

    sql = generate_sql(
        question
    )

    columns, rows = execute_readonly_sql(
        sql
    )

    return {
        "sql": sql,
        "columns": columns,
        "rows": rows
    }


def format_oracle_context(result):

    if not result["rows"]:

        return (
            "Oracle query returned no rows."
        )

    output = []

    output.append(
        f"SQL: {result['sql']}"
    )

    output.append(
        "RESULTS:"
    )

    for row in result["rows"]:

        values = []

        for key, value in row.items():

            values.append(
                f"{key}={value}"
            )

        output.append(
            " | ".join(values)
        )

    return "\n".join(output)