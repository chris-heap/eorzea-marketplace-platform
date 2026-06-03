"""
REFERENCE FILE — LangChain + Claude text-to-SQL chat agent for FFXIV market data.
This is not used by the app. It's a reference for building chat.py.
"""

import os
import re
import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from eorzea_api.database import DuckDBConnect

logger = logging.getLogger(__name__)

# This prompt tells Claude what tables exist and how to respond.
# {table_schemas} gets filled in at runtime with the actual DuckDB schema.
SYSTEM_PROMPT = """You are an FFXIV Market Board analyst. You answer questions about market data
by writing DuckDB SQL queries against the following tables:

{table_schemas}

Rules:
- Write a single SQL query to answer the user's question
- Return ONLY the SQL query wrapped in ```sql ... ``` tags
- Use the exact column names shown above
- Limit results to 20 rows unless the user asks for more
- For item lookups, use item_name (not item_id) when possible
- For world lookups, use world_name (not world_id) when possible
"""

# After executing the SQL, this prompt asks Claude to summarize the results.
SUMMARY_PROMPT = """You are an FFXIV Market Board analyst. The user asked: "{question}"

You ran this SQL query:
```sql
{sql}
```

And got these results:
{results}

Summarize the results in a helpful, conversational way. Reference specific item names,
world names, and prices. Keep it concise — 2-4 sentences max."""


def _extract_sql(text: str) -> str:
    """Pull SQL out of ```sql ... ``` blocks."""
    match = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


class MarketChatAgent:
    def __init__(self, db_path: str):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        self.db_path = db_path

        # Initialize the Claude model via LangChain
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=api_key,
            max_tokens=1024,
        )

        # Load table schemas once at startup so we don't re-read every request
        with DuckDBConnect(db_path) as db:
            self.table_schemas = db.get_information_schema()
        logger.info("Loaded table schemas:\n%s", self.table_schemas)

        # Chain 1: question → SQL
        # Pipe operator: fill template → send to Claude → extract text
        self.sql_chain = (
            ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("human", "{question}"),
            ])
            | self.llm
            | StrOutputParser()
        )

        # Chain 2: results → human-readable summary
        self.summary_chain = (
            ChatPromptTemplate.from_messages([
                ("system", SUMMARY_PROMPT),
            ])
            | self.llm
            | StrOutputParser()
        )

    def ask(self, question: str) -> dict:
        """Take a natural language question, generate SQL, execute, summarize."""

        # Step 1: Give Claude the schemas + question, get SQL back
        sql_response = self.sql_chain.invoke({
            "table_schemas": self.table_schemas,
            "question": question,
        })
        sql = _extract_sql(sql_response)
        logger.info("Generated SQL: %s", sql)

        # Step 2: Execute the SQL against DuckDB
        with DuckDBConnect(self.db_path) as db:
            try:
                result = db.execute(sql).fetchdf()
            except Exception as e:
                logger.error("SQL execution failed: %s", e)
                return {
                    "question": question,
                    "sql": sql,
                    "error": str(e),
                    "answer": f"Sorry, the query failed: {e}",
                }

        results_str = result.head(20).to_string(index=False)
        logger.info("Query returned %d rows", len(result))

        # Step 3: Give Claude the results, get a summary back
        summary = self.summary_chain.invoke({
            "question": question,
            "sql": sql,
            "results": results_str,
        })

        return {
            "question": question,
            "sql": sql,
            "rows": len(result),
            "answer": summary,
            "data": result.head(20).to_dict(orient="records"),
        }
