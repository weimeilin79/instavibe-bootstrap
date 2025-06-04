import json
from google.adk.tools.function_tool import FunctionTool

# --- Placeholder Custom BigQuery Tools ---

async def analyze_query_cost_async(query: str, project_id: str = "default_project") -> str:
    """
    Placeholder tool to simulate BigQuery query cost analysis.
    In a real implementation, this would connect to BigQuery, run a dry-run,
    and fetch cost estimations and execution details.
    """
    print(f"Tool 'analyze_query_cost_async' called with query: '{query[:50]}...', project_id: {project_id}")

    # Simulate some analysis
    estimated_cost_usd = 0.01 * len(query) # Dummy cost based on query length
    bytes_processed = f"{10 * len(query)}MB" # Dummy data processed

    recommendations = []
    if "SELECT *" in query.upper():
        recommendations.append("Consider avoiding 'SELECT *' and specify columns if not all are needed.")
    if "WHERE" not in query.upper() and len(query) > 100: # Arbitrary condition
        recommendations.append("For large tables, ensure you have appropriate filters (WHERE clause) to limit data scanned.")
    if not recommendations:
        recommendations.append("Query structure looks reasonable for a basic analysis. Further optimization might require deeper workload understanding.")

    result = {
        "query": query,
        "project_id": project_id,
        "estimated_cost_usd": round(estimated_cost_usd, 4),
        "estimated_bytes_processed": bytes_processed,
        "recommendations": recommendations,
        "notes": "This is a simulated analysis. Actual costs and performance may vary."
    }
    return json.dumps(result)

async def get_schema_recommendations_async(table_id: str, project_id: str = "default_project", dataset_id: str = "default_dataset") -> str:
    """
    Placeholder tool to simulate providing schema recommendations for a BigQuery table.
    A real tool would inspect table metadata, clustering, partitioning, etc.
    """
    print(f"Tool 'get_schema_recommendations_async' called for table: {project_id}.{dataset_id}.{table_id}")

    recommendations = []
    if "customer" in table_id.lower():
        recommendations.append(f"For table '{table_id}', consider partitioning by a date/timestamp column if time-based queries are frequent.")
        recommendations.append(f"If '{table_id}' is often joined with an orders table, consider clustering by 'customer_id'.")
    else:
        recommendations.append("No specific schema recommendations for this table based on simple name analysis. Review query patterns for optimization opportunities.")

    result = {
        "table_id": f"{project_id}.{dataset_id}.{table_id}",
        "recommendations": recommendations,
        "notes": "These are generic schema recommendations based on simulated analysis."
    }
    return json.dumps(result)

# --- Wrap them with FunctionTool for the MCP Server ---

# Instantiating the FunctionTool directly with the async function
analyze_query_cost_tool = FunctionTool(
    fn=analyze_query_cost_async,
    name="analyze_query_cost", # Explicit name, otherwise it's analyze_query_cost_async
    description="Analyzes a BigQuery query string and provides estimated cost, bytes processed, and optimization recommendations. Requires 'query' (string) and optional 'project_id' (string)."
)

get_schema_recommendations_tool = FunctionTool(
    fn=get_schema_recommendations_async,
    name="get_schema_recommendations",
    description="Provides schema optimization recommendations for a given BigQuery table. Requires 'table_id' (string), optional 'project_id' (string), and 'dataset_id' (string)."
)

# List of all custom tools for easy import by the MCP server
custom_bq_tools = [
    analyze_query_cost_tool,
    get_schema_recommendations_tool,
]

if __name__ == '__main__':
    # Example of how to test the tools locally (optional)
    import asyncio

    async def test_tools():
        print("Testing analyze_query_cost_tool...")
        cost_result_json = await analyze_query_cost_tool.run_async(args={"query": "SELECT * FROM my_dataset.my_table WHERE event_date = '2024-01-15'"})
        print(json.loads(cost_result_json))

        print("\nTesting get_schema_recommendations_tool...")
        schema_result_json = await get_schema_recommendations_tool.run_async(args={"table_id": "customer_transactions", "dataset_id": "sales"})
        print(json.loads(schema_result_json))

    asyncio.run(test_tools())
