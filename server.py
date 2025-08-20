import asyncio
from pdb import run 
from agents import run_research
from mcp.server.fastmcp import FastMCP 

# creating a MCP instance

mcp = FastMCP("crew_for_research")

@mcp.tool()
def crew_for_research(query:str) -> str:
    """Run a crew ai based deep researcher 
    where both standard and deep research can be done 
    Args:
        the query for doing deep research
    Returns:
        str : The research response from the pipeline 
    """
    return run_research(query)

if __name__ == "__main__":
    mcp.run(transport = 'stdio')
    