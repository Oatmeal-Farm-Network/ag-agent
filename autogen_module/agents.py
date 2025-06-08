# autogen_setup.py
# Defines AutoGen agents and their configurations.

#configures all the specialized AI agents (e.g., User Proxy, Searcher, Experts)
#  that participate in the automated conversation workflow using the AutoGen framework.

import autogen
import streamlit as st # For session state access if needed, though direct use is minimized
import pandas as pd

# Import from other modules
from config import autogen_llm_config_list
from config import USER_PROXY_NAME, SEARCHER_NAME, PROCESSOR_NAME, SOIL_NAME, NUTRITION_NAME, EXPERT_ADVISOR_NAME
from database_module.cosmos_retriever import retrieve_semantic_chunks_tool # The tool function
from config import (
    autogen_llm_config_list, USER_PROXY_NAME, SEARCHER_NAME, PROCESSOR_NAME,
    SOIL_NAME, NUTRITION_NAME, EXPERT_ADVISOR_NAME, LIVESTOCK_BREED_NAME,WEATHER_NAME 
)
from database_module.cosmos_retriever import (
    retrieve_semantic_chunks_tool,
    retrieve_livestock_breed_info_tool # Import new tool
)
from external_apis.weather_api import get_lat_lon_from_zip, hourly_weather_data, fetch_weather_data


# --- User Proxy Agent ---
# Represents the user in the AutoGen workflow.
user_proxy = autogen.UserProxyAgent(
    name=USER_PROXY_NAME,
    human_input_mode="NEVER",       # Input is handled via Streamlit
    max_consecutive_auto_reply=0,   # Must hand off after its message
    is_termination_msg=lambda x: x.get("content", "").strip().upper().endswith("TERMINATE"),
    code_execution_config=False,    # No code execution needed for this agent
    llm_config={"config_list": autogen_llm_config_list, "temperature": 0.0},
    system_message=(
        f"You are the {USER_PROXY_NAME}. Your role is to receive the farmer's query "
        "(initial or follow-up). State the query clearly. "
        f"Then, you *MUST* end your response with 'NEXT_SPEAKER: {SEARCHER_NAME}'. "
        f"Example: 'The farmer asks: [farmer's exact query here]\\nNEXT_SPEAKER: {SEARCHER_NAME}'"
        "Do not add any other information or engage in conversation beyond this."
    )
)

# --- Semantic Search Agent ---
# Uses a tool to retrieve information from a knowledge base.
semantic_search_agent = autogen.AssistantAgent(
    name=SEARCHER_NAME,
    llm_config={
        "config_list": autogen_llm_config_list,
        "temperature": 0.1,
        "tools": [{
            "type": "function",
            "function": {
                "name": "retrieve_semantic_chunks_tool",
                "description": "Retrieves relevant text chunks from a knowledge base based on semantic similarity to the input query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_text": {"type": "string", "description": "The farmer's query to search for. This should be the specific question asked in the current turn."},
                        "k": {"type": "integer", "description": "Number of top chunks to retrieve.", "default": 3}
                    },
                    "required": ["query_text"]
                }
            }
        }]
    },
    system_message=(
        "You are a semantic search specialist. You will receive the farmer's current query from the chat history. "
        "Your task is to use the `retrieve_semantic_chunks_tool` with that *specific current query*. "
        "Focus on the latest query for the tool call. "
        "After calling the tool and receiving its output, present this output *exactly* as received. "
        f"Then, you *MUST* end your response with 'NEXT_SPEAKER: {PROCESSOR_NAME}'."
    )
)
# Register the function for the search agent
semantic_search_agent.register_function(
    function_map={"retrieve_semantic_chunks_tool": retrieve_semantic_chunks_tool}
)

# --- tool for the Weather Agent ---
def get_weather_report_for_zipcode(zipcode: str) -> str:
    """
    Fetches and summarizes the current weather, today's forecast, and a 3-day forecast for a given US zip code.
    Returns a formatted string with the weather report.
    """
    try:
        lat, lon, city, state = get_lat_lon_from_zip(zipcode)
        
        # Get hourly data for today and daily data for the next 3 days
        hourly_df, _ = hourly_weather_data(lat, lon) # We only need the hourly part here
        daily_forecast_df = fetch_weather_data(lat, lon, forecast_days=3)

        # --- Summarize the data into a concise string for the agent ---
        # Current conditions (approximated from the first hour available)
        current_temp = hourly_df.iloc[0]['temperature_2m']
        current_humidity = hourly_df.iloc[0]['relative_humidity_2m']
        
        # Today's high and low
        today_high = daily_forecast_df.iloc[0]['temperature_2m_max']
        today_low = daily_forecast_df.iloc[0]['temperature_2m_min']
        
        report = (
            f"Weather Report for {city}, {state} (Zip: {zipcode}):\n"
            f"- Current Conditions: Temperature: {current_temp:.1f}°F, Humidity: {current_humidity:.0f}%\n"
            f"- Today's Forecast: High of {today_high:.1f}°F, Low of {today_low:.1f}°F.\n\n"
            "3-Day Forecast:\n"
        )
        
        for _, row in daily_forecast_df.iterrows():
            date_str = pd.to_datetime(row['date']).strftime('%A, %b %d')
            report += (
                f"- {date_str}: High {row['temperature_2m_max']:.1f}°F, "
                f"Low {row['temperature_2m_min']:.1f}°F, "
                f"Max Wind {row['wind_speed_10m_max']:.1f} mph.\n"
            )
            
        return report
    except Exception as e:
        print(f"Error in get_weather_report_for_zipcode: {e}")
        return f"Could not retrieve weather for zip code {zipcode}. The zip code may be invalid or the weather service is unavailable."

# --- Context Processor Agent ---
# Synthesizes information from retrieved chunks.
context_processor_agent = autogen.AssistantAgent(
    name=PROCESSOR_NAME,
    llm_config={"config_list": autogen_llm_config_list, "temperature": 0.3},
    system_message=(
        "You are a context processing specialist and query router. You receive the full conversation history and raw context snippets. "
        "First, synthesize key information into a concise summary. "
        "Second, based on the farmer's query, decide which specialist is the most appropriate next speaker. "
        "- If the query is about weather, forecast, rain, or temperature, hand off to the WeatherSpecialist. "
        "- If the query is about livestock, cattle, or animal breeds, hand off to the LivestockBreedSpecialist. "
        "- If the query is about soil, farming practices, or crop health, hand off to the SoilScienceSpecialist. "
        "Your response *MUST* end with 'NEXT_SPEAKER: [agent_name]', where agent_name is one of 'WeatherSpecialist', 'LivestockBreedSpecialist', or 'SoilScienceSpecialist'."
    )
)
# --- Soil Science Specialist Agent ---
soil_agent = autogen.AssistantAgent(
    name=SOIL_NAME,
    llm_config={"config_list": autogen_llm_config_list, "temperature": 0.5},
    system_message=(
        "You are a soil science specialist. You will receive the farmer's problem description "
        "and a contextual summary from the ContextProcessor. "
        "Analyze the problem and context, focusing *ONLY* on potential soil-related issues "
        "(e.g., pH, compaction, drainage, structure) based *strictly* on provided chat history. "
        "Do *NOT* use external knowledge or make assumptions. "
        "Report identified soil problems. If none can be inferred, state that. "
        f"You *MUST* end your response with 'NEXT_SPEAKER: {NUTRITION_NAME}'."
    )
)

# --- Plant Nutrition Expert Agent ---
nutrition_agent = autogen.AssistantAgent(
    name=NUTRITION_NAME,
    llm_config={"config_list": autogen_llm_config_list, "temperature": 0.5},
    system_message=(
        "You are a plant nutrition expert. You receive the farmer's problem, contextual summary, and soil analysis. "
        "Based *ONLY* on these inputs from chat history, identify potential plant nutrient issues. "
        "If possible, suggest general corrective actions (e.g., 'consider nitrogen source') if supported by the provided information. "
        "Do *NOT* use external knowledge or recommend specific products. "
        "If no nutritional issues can be inferred, state that. "
        f"You *MUST* end your response with 'NEXT_SPEAKER: {EXPERT_ADVISOR_NAME}'."
    )
)
#-- Livestock Breed Specialist Agent ---
livestock_breed_agent = autogen.AssistantAgent(
    name=LIVESTOCK_BREED_NAME,
    llm_config={
        "config_list": autogen_llm_config_list,
        "temperature": 0.4,
        "tools": [{
            "type": "function",
            "function": {
                "name": "retrieve_livestock_breed_info_tool",
                "description": "Retrieves information about livestock breeds from a specialized knowledge base.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_text": {"type": "string", "description": "The specific query about livestock breeds."},
                        "k": {"type": "integer", "description": "Number of top chunks to retrieve.", "default": 3}
                    },
                    "required": ["query_text"]
                }
            }
        }]
    },
    system_message=(
        "You are a Livestock Breed Specialist. You will receive a farmer's query. "
        "Your primary task is to use the `retrieve_livestock_breed_info_tool` to find relevant information about livestock from your knowledge base. "
        "After getting the information from the tool, synthesize it into a clear, helpful analysis. "
        "Do not use external knowledge. Base your analysis strictly on the retrieved information. "
        f"You *MUST* end your response with 'NEXT_SPEAKER: {EXPERT_ADVISOR_NAME}'."
    )
)
#  function for the breed agent
livestock_breed_agent.register_function(
    function_map={"retrieve_livestock_breed_info_tool": retrieve_livestock_breed_info_tool}
)
#-- Weather Agent ---
weather_agent = autogen.AssistantAgent(
    name=WEATHER_NAME,
    llm_config={
        "config_list": autogen_llm_config_list,
        "temperature": 0.1,
        "tools": [{
            "type": "function",
            "function": {
                "name": "get_weather_report_for_zipcode",
                "description": "Provides a weather report and forecast for a given US zip code.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "zipcode": {"type": "string", "description": "The 5-digit US zip code, e.g., '94542'."}
                    },
                    "required": ["zipcode"]
                }
            }
        }]
    },
    system_message=(
        "You are a Weather Specialist. You receive a farmer's query about weather. "
        "Use the `get_weather_report_for_zipcode` tool to fetch the required weather data. "
        "After getting the report from the tool, present it clearly to the user. "
        "If the query contains a question about the weather data (e.g., 'is it good for planting?'), provide a brief interpretation. "
        f"You *MUST* end your response with 'NEXT_SPEAKER: {EXPERT_ADVISOR_NAME}'."
    )
)
# function for the weather agent
weather_agent.register_function(
    function_map={"get_weather_report_for_zipcode": get_weather_report_for_zipcode}
)

# --- Lead Agricultural Advisor Agent ---
expert_advisor_agent = autogen.AssistantAgent(
    name=EXPERT_ADVISOR_NAME,
    llm_config={"config_list": autogen_llm_config_list, "temperature": 0.7},
    system_message=(
        "You are the Lead Agricultural Advisor. You have received an analysis from a specialist "
        "(e.g., Soil, Nutrition, Livestock, or Weather specialist). "
        "Synthesize all information from the conversation history to formulate a comprehensive "
        "and actionable piece of advice for the farmer. "
        "Your advice must be based *STRICTLY* on the information provided by the previous agents. "
        "Your response should be *only* the advice itself. Do not add 'TERMINATE' or 'NEXT_SPEAKER'."
    )
)



# List of all agents for the group chat
all_agents = [
    user_proxy,
    semantic_search_agent,
    context_processor_agent,
    soil_agent,
    nutrition_agent,
    livestock_breed_agent,
    weather_agent,
    expert_advisor_agent
]