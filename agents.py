# from asyncio import tasks
# from multiprocessing import process
# from multiprocessing.connection import Client
import os
# from re import search
import sys
from dotenv import load_dotenv
# from tabnanny import verbose
from crewai import LLM
from typing  import Type
from pydantic import BaseModel, Field
from linkup import LinkupClient
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool

# loading envirionment variables for linkup setup 
load_dotenv()

def get_llm_cleint():
# to initialize the llm client and return it
    return LLM(
        model = "ollama/deepseek-r1:8b",
        base_url = "http://localhost:11434",
        temperature = 0.4,
        max_tokens = 1000,
    )

# Defining the linkup search tool 

class LinkupSearchTool(BaseTool):
    query: str = Field(desciption = "Which Search query you want to perform on linkup" )
    depth: str = Field(default = "standard" , description = "How deep you want to search on linkup 'standard' or 'deep' ")
    output_type : str = Field(
        default = "search_results", # search_results or search_results_with_details
        description="Output type: 'searchResults', 'sourcedAnswer', or 'structured'"
    )
    
    def __init__(self):
        super().__init__()

# Actually writing the code for the tool

class LinkupSearchTool(BaseTool):
    name: str = "linkup_search"
    description: str = "Search for information on Linkup"
    args_schema: Type[BaseModel] = LinkupSearchTool
    
    def __init__(self):
        super().__init__()
        
    def _run(self, query: str, depth: str = "standard", output_type: str = "search_results") -> str:
        # to initialize the linkup client and perform the search finally return the results
        try :
            linkup_client = LinkupClient(api_key = os.getenv("LINKUP_API_KEY"))
            # Search initialization
            search = linkup_client.search(
                query = query,
                depth = depth,
                output_type = output_type
                )
            # Process the search results and return the results
            # if output_type == "search_results":
            #     return search.results
            # elif output_type == "sourced_answer":
            #     return search.sourced_answer
            # elif output_type == "structured":
            #     return search.structured_answer
            # else:
            #     raise ValueError(f"Invalid output type: {output_type}")
            return search.results
        except Exception as e:
            return f"! There was an error in the linkup search tool: {e}"
# creating a crew to perform the search 

def create_research_crew(query:str):
    
    """
    This function creates a crew to perform the search
    create and configure the crew with all the agents and tasks
    """
    # Initialize the tool 
    linkup_search_tool = LinkupSearchTool()
    
    # Get LLM cleint
    
    llm_client = get_llm_cleint()
    
    # web searcher agent
    web_searcher_agent = Agent(
        role = "Web Searcher",
        goal = "Search the web for the most relevant information about the query along with the sources and the links (urls) to the sources ",
        backstory = "An expert at curating the search querries and retreiving relevant content and infirmation. Passes on the results to the 'Research Analyst' only.",
        verbose = True,
        allow_delegation = True,
        tools = [linkup_search_tool],
        llm = llm_client
    )
    
    # making a Research Analyst agent 
    research_analyst_agent = Agent(
        role = "Research Analyst",
        goal = "Analyze and synthesize raw information into structured insights, along with source links (urls) as citations.",
        backstory="An expert at analyzing information, identifying patterns, and extracting key insights. If required, can delagate the task of fact checking/verification to 'Web Searcher' only. Passes the final results to the 'Technical Writer' only.",
        verbose = True,
        allow_delegation = True,
        llm = llm_client
    )
    
    # making a Technical Writer agent
    technical_writer_agent = Agent(
        role = "Technical Writer",
        goal = "Analyze and synthesize raw information into structured insights, along with source links (urls) as citations.",
        backstory = "Expert at communicating and explaining xomplex topics and information in a simple manner for general uninformed masses",
        verbose = True,
        allow_delegation = True,
        llm = llm_client
    )
    
    # Defining Tasks for each and every agent 
    search_task = Task(
        description = f"search for comprehensive information about the {query}",
        agent = web_searcher_agent,
        expected_output = "Raw results with their corresponding links (urls).",
        tools = [linkup_search_tool]
    )
    
    # for the analysis task 
    analysis_task = Task(
        description="Analyze the raw search results, identify key information, verify facts and prepare a structured analysis.",
        agent=research_analyst_agent,
        expected_output="A structured analysis of the information with verified facts and key insights, along with source links",
        context=[search_task]
    )

    writing_task = Task(
        description="Create a comprehensive, well-organized response based on the research analysis.",
        agent=technical_writer_agent,
        expected_output="A clear, comprehensive response that directly answers the query with proper citations/source links (urls).",
        context=[analysis_task]
    )
    
    # defining the Crew
    crew = Crew(
        agents = [research_analyst_agent,research_analyst_agent,technical_writer_agent],
        tasks = [search_task,analysis_task,writing_task],
        verbose = True,
        process = Process.sequential
    )
    
    return crew

def run_research(query : str):
    """
    Run the research and return the analysed report about the same
    """
    try:
        crew = create_research_crew(query=query)
        results = crew.kickoff()
        return results.raw
    except Exception as e:
        return f"Some unexpected error: {str(e)} happned while processing the query" 