import os
import re
import logging
import time

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from eorzea_api.database import DuckDBConnect
from eorzea_api.tools import create_tools
from eorzea_api.telemetry import (
    token_input_counter, token_output_counter, cost_counter,
    tool_call_counter, request_duration, agent_loop_iterations,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an FFXIV Market Board analyst. You answer questions about market data by writing DuckDB SQL queries against the following tables:

{table_schemas}

Rules:
- Use your tools first to look up exact item names, data centers, or price context before writing SQL
- Write a single SQL query to answer the user's question
- Return only the SQL query wrapped in ```sql ... ``` tags
- Use the exact column names shown above
- Limit results to 20 rows unless the user explicitly asks for more
- For item lookups, use item_name (not item_id) when possible
- For world lookups, use world_name (not world_id) when possible
"""

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
    """Extract the SQL out of ```sql ... ``` blocks."""
    match = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


class EorzeaMarketChatAgent:
    def __init__(self, db_path: str):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required.")

        self.db_path = db_path

        self.llm = ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            anthropic_api_key=api_key,
            max_tokens=1024,
        )

        with DuckDBConnect(db_path) as db:
            self.table_schemas = db.get_information_schema()
        logger.info("Loaded table schemas:\n%s", self.table_schemas)

        # Tools for FFXIV domain knowledge
        self.tools = create_tools(db_path)
        self.tools_by_name = {t.name: t for t in self.tools}
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Summary chain doesn't need tools — just plain LLM
        self.summary_chain = (
            ChatPromptTemplate.from_messages([
                ("system", SUMMARY_PROMPT),
                ("human", "Summarize these results for me."),
            ])
            | self.llm
            | StrOutputParser()
        )

    def ask(self, question: str) -> dict:
        """Take a natural language question, optionally call tools, generate SQL, execute, and summarize."""
        start_time = time.time()

        # Build the initial message with system context + user question
        messages = [
            SystemMessage(content=SYSTEM_PROMPT.format(table_schemas=self.table_schemas)),
            HumanMessage(content=question),
        ]
        
        # Loop: let Claude call tools until it gives a text response
        max_iterations = 5
        for i in range(max_iterations):
            response = self.llm_with_tools.invoke(messages)
            messages.append(response)

            usage = response.response_metadata.get("usage", {})
            input_toks = usage.get("input_tokens", 0)
            output_toks = usage.get("output_tokens", 0)
            token_input_counter.add(input_toks)
            token_output_counter.add(output_toks)
            cost_counter.add((input_toks * 1.0 + output_toks * 5.0) / 1_000_000)

            # If no tool calls, Claude is done — it should have SQL in its response
            if not response.tool_calls:
                break

            # Execute each tool call and feed results back
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                logger.info("Tool call: %s(%s)", tool_name, tool_args)
                tool_call_counter.add(1, {"tool_name": tool_name})

                tool_fn = self.tools_by_name.get(tool_name)
                if tool_fn:
                    tool_result = tool_fn.invoke(tool_args)
                    
                else:
                    tool_result = f"Unknown tool: {tool_name}"

                messages.append(ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"],
                ))

        agent_loop_iterations.record(i + 1)

        # Check if Claude responded with SQL or answered directly from tools
        raw_content = response.content
        has_sql = "```sql" in raw_content

        if not has_sql:
            request_duration.record((time.time() - start_time) * 1000)
            logger.info("Agent answered directly from tools (no SQL)")
            return {
                "question": question,
                "sql": "",
                "rows": 0,
                "answer": raw_content,
                "data": [],
            }

        # Extract and run SQL
        sql = _extract_sql(raw_content)
        logger.info("Generated SQL: %s", sql)

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

        # Summarize with plain LLM (no tools needed here)
        summary = self.summary_chain.invoke({
            "question": question,
            "sql": sql,
            "results": results_str,
        })

        request_duration.record((time.time() - start_time) * 1000)

        return {
            "question": question,
            "sql": sql,
            "rows": len(result),
            "answer": summary,
            "data": result.head(20).to_dict(orient="records"),
        }
