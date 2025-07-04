# agents.py
# Defines AutoGen agents and their configurations.
# FINAL CORRECTED VERSION: Enhanced final agent prompt for beautiful, structured output.

import autogen
import pandas as pd
import re

# Import from other modules
from config import (
    autogen_llm_config_list, USER_PROXY_NAME, SEARCHER_NAME, PROCESSOR_NAME,
    SOIL_NAME, NUTRITION_NAME, EXPERT_ADVISOR_NAME, LIVESTOCK_BREED_NAME, WEATHER_NAME 
)
from database_module.cosmos_retriever import (
    retrieve_semantic_chunks_tool, 
    retrieve_livestock_breed_info_tool, 
    retrieve_from_chat_history
)
from external_apis.weather_api import get_lat_lon_from_zip, hourly_weather_data, fetch_weather_data


# --- User Proxy Agent ---
user_proxy = autogen.UserProxyAgent(
    name=USER_PROXY_NAME,
    human_input_mode="NEVER",
    max_consecutive_auto_reply=0,
    is_termination_msg=lambda x: x.get("content", "").strip().upper().endswith("TERMINATE"),
    code_execution_config=False
)

# --- Enhanced Semantic Search Agent ---
semantic_search_agent = autogen.AssistantAgent(
    name=SEARCHER_NAME,
    llm_config={
        "config_list": autogen_llm_config_list,
        "temperature": 0.1,
        "tools": [{
            "type": "function",
            "function": {
                "name": "retrieve_semantic_chunks_tool",
                "description": "Retrieves relevant text chunks from a knowledge base about crop health and farming.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_text": {"type": "string", "description": "The farmer's query to search for."},
                        "user_id": {"type": "string", "description": "The unique ID of the current user."} 
                    },
                    "required": ["query_text", "user_id"]
                }
            }
        }, {
            "type": "function",
            "function": {
                "name": "retrieve_from_chat_history",
                "description": "Retrieves relevant information from the user's past chat history.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_text": {"type": "string", "description": "The user's query that implies recalling past information."},
                        "user_id": {"type": "string", "description": "The unique ID of the current user."}
                    },
                    "required": ["query_text", "user_id"]
                }
            }
        }]
    },
    system_message=(
        "You are a search specialist. Your job is to call the correct tool and present its results.\n"
        "1. **Parse Input:** Extract 'user_id' and 'query_text'.\n"
        "2. **Choose Tool:** If the query mentions past conversations ('remember', 'recall', etc.), use `retrieve_from_chat_history`. Otherwise, use `retrieve_semantic_chunks_tool`.\n"
        "3. **Call Tool:** Execute the chosen tool with the correct arguments.\n"
        "4. **Present Results:** After the tool runs, your ONLY job is to state the results clearly. Do not add any other text or directives."
    )
)

# Register functions for the search agent
semantic_search_agent.register_function(
    function_map={
        "retrieve_semantic_chunks_tool": retrieve_semantic_chunks_tool,
        "retrieve_from_chat_history": retrieve_from_chat_history
    }
)

# --- Weather Tool Function ---
def get_weather_report_for_zipcode(zipcode: str) -> str:
    """Fetches and summarizes weather data for a given US zip code."""
    try:
        lat, lon, city, state = get_lat_lon_from_zip(zipcode)
        hourly_df, _ = hourly_weather_data(lat, lon)
        daily_forecast_df = fetch_weather_data(lat, lon, forecast_days=3)
        current_temp = hourly_df.iloc[0]['temperature_2m']
        current_humidity = hourly_df.iloc[0]['relative_humidity_2m']
        today_high = daily_forecast_df.iloc[0]['temperature_2m_max']
        today_low = daily_forecast_df.iloc[0]['temperature_2m_min']
        report = (
            f"Weather Report for {city}, {state} (Zip: {zipcode}):\n"
            f"- Current: {current_temp:.1f}°F, {current_humidity:.0f}% Humidity\n"
            f"- Today: High {today_high:.1f}°F, Low {today_low:.1f}°F\n\n3-Day Forecast:\n"
        )
        for _, row in daily_forecast_df.iterrows():
            date_str = pd.to_datetime(row['date']).strftime('%A, %b %d')
            report += f"- {date_str}: High {row['temperature_2m_max']:.1f}°F, Low {row['temperature_2m_min']:.1f}°F\n"
        return report
    except Exception as e:
        return f"Could not retrieve weather for zip code {zipcode}. Error: {str(e)}"

# --- Enhanced Context Processor Agent ---
context_processor_agent = autogen.AssistantAgent(
    name=PROCESSOR_NAME,
    llm_config={"config_list": autogen_llm_config_list, "temperature": 0.3},
    system_message=(
        "You are a context processor and router. Your job is to review the search results and decide which specialist should speak next. "
        f"Based on the query and context, you must state 'NEXT_SPEAKER: [agent_name]', choosing one of: "
        f"'{WEATHER_NAME}', '{LIVESTOCK_BREED_NAME}', or '{SOIL_NAME}'."
    )
)

# --- Soil Science Specialist Agent ---
soil_agent = autogen.AssistantAgent(
    name=SOIL_NAME,
    llm_config={"config_list": autogen_llm_config_list, "temperature": 0.5},
    system_message=(
        "You are a Soil Science and Crop Health Specialist. Analyze the provided context and identify potential soil and crop health issues. "
        f"After your analysis, you MUST end your response with 'NEXT_SPEAKER: {NUTRITION_NAME}'."
    )
)

# --- Plant Nutrition Expert Agent ---
nutrition_agent = autogen.AssistantAgent(
    name=NUTRITION_NAME,
    llm_config={"config_list": autogen_llm_config_list, "temperature": 0.5},
    system_message=(
        "You are a Plant Nutrition Expert. Review all prior analysis and identify potential nutrient issues. "
        f"After your analysis, you MUST end your response with 'NEXT_SPEAKER: {EXPERT_ADVISOR_NAME}'."
    )
)

# --- Livestock Breed Specialist Agent ---
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
        "You are a Livestock Breed Specialist. Use your tools to find information and provide analysis on livestock queries. "
        f"After your analysis, you MUST end your response with 'NEXT_SPEAKER: {EXPERT_ADVISOR_NAME}'."
    )
)
livestock_breed_agent.register_function(function_map={"retrieve_livestock_breed_info_tool": retrieve_livestock_breed_info_tool})

# --- Weather Specialist Agent ---
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
        "You are a Weather Specialist. Use your tools to fetch weather data and provide an agricultural interpretation. "
        f"After your analysis, you MUST end your response with 'NEXT_SPEAKER: {EXPERT_ADVISOR_NAME}'."
    )
)
weather_agent.register_function(function_map={"get_weather_report_for_zipcode": get_weather_report_for_zipcode})

# --- <<< ENHANCED LEAD AGRICULTURAL ADVISOR FOR BEAUTIFUL FORMATTING >>> ---
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



# --- List of all agents for the group chat ---
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

print("All agents properly configured ✓")
