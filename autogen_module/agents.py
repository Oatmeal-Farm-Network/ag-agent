# agents.py
# Defines AutoGen agents and their configurations.
# FINAL CORRECTED VERSION: Enhanced final agent prompt for beautiful, structured output.

import autogen
import pandas as pd
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from other modules
from config import (
    autogen_llm_config_list, USER_PROXY_NAME, SEARCHER_NAME, PROCESSOR_NAME,
    SOIL_NAME, NUTRITION_NAME, EXPERT_ADVISOR_NAME, LIVESTOCK_BREED_NAME, WEATHER_NAME,
    memory_client # Import the new mem0 client
)

from external_apis.weather_api import get_lat_lon_from_zip, hourly_weather_data, fetch_weather_data

# --- New Unified Memory Search Tool ---
def unified_memory_search(query_text: str, user_id: str) -> str:
    """
    Searches for relevant information in both the user's chat history and the general knowledge base.
    """
    print(f"--- [Unified Search] Searching memories for user '{user_id}' with query: '{query_text}' ---")
    
    # Search for user-specific memories
    user_memories = memory_client.search(query=query_text, user_id=user_id, limit=3)
    
    # Search the general knowledge base (we use our generic ID here)
    kb_memories = memory_client.search(query=query_text, user_id="knowledge_base_user", limit=2)

    # Combine and format the results
    context_parts = []
    if user_memories and 'results' in user_memories:
        context_parts.append("Recalled from your past conversations:")
        context_parts.extend([m['memory'] for m in reversed(user_memories['results'])])

    if kb_memories and 'results' in kb_memories:
        context_parts.append("\nRecalled from the knowledge base:")
        context_parts.extend([m['memory'] for m in kb_memories['results']])

    if not context_parts:
        return "No relevant information found in memory."
        
    return "\n".join(context_parts)

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
                "name": "unified_memory_search",
                "description": "Searches for relevant information from both past conversations and the general knowledge base.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_text": {"type": "string", "description": "The farmer's query to search for."},
                        "user_id": {"type": "string", "description": "The unique ID of the current user."} 
                    },
                    "required": ["query_text", "user_id"]
                }
            }
        }]
    },
    system_message=(
        "You are a search specialist. Your only job is to call the `unified_memory_search` tool "
        "using the user's query and their user_id. Present the results clearly."
    )
)

# Register the new unified function
semantic_search_agent.register_function(
    function_map={
        "unified_memory_search": unified_memory_search
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
    )
)

# --- Plant Nutrition Expert Agent ---
nutrition_agent = autogen.AssistantAgent(
    name=NUTRITION_NAME,
    llm_config={"config_list": autogen_llm_config_list, "temperature": 0.5},
    system_message=(
        "You are a Plant Nutrition Expert. Review all prior analysis and identify potential nutrient issues. "
    )
)


# --- Livestock Breed Specialist Agent ---
livestock_breed_agent = autogen.AssistantAgent(
    name=LIVESTOCK_BREED_NAME,
    llm_config={
        "config_list": autogen_llm_config_list,
        "temperature": 0.4,
        # The tools and function registration are removed.
    },
    system_message=(
        "You are a Livestock Breed Specialist. Analyze the provided context about livestock "
        "and provide a detailed analysis based on that information."
    )
)

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
    )
)
weather_agent.register_function(function_map={"get_weather_report_for_zipcode": get_weather_report_for_zipcode})

# --- <<< ENHANCED LEAD AGRICULTURAL ADVISOR FOR BEAUTIFUL FORMATTING >>> ---
expert_advisor_agent = autogen.AssistantAgent(
    name=EXPERT_ADVISOR_NAME,
    llm_config={"config_list": autogen_llm_config_list, "temperature": 0.4},
    system_message=(
        "You are the Lead Agricultural Advisor. You have received an analysis from a specialist "
        "(e.g., Soil, Nutrition, Livestock, or Weather specialist). "
        "Synthesize all information from the conversation history to formulate a comprehensive "
        "and actionable piece of advice for the farmer. "
        "Your advice must be based *STRICTLY* on the information provided by the previous agents. "
    )
)

default_agent = autogen.AssistantAgent(
                name="DefaultAgent",
                llm_config={
                    "config_list": autogen_llm_config_list,
                    "temperature": 0.7
                },
                system_message="""
                You are a friendly agricultural advisor assistant. You can only help with:
                
                ✅ ALLOWED:
                - Agriculture and farming questions
                - Livestock and animal husbandry questions
                - General farming advice
                - Greeting customers and conversation starters
                - If the user question is part of the conversation history, you can use the conversation history to help you answer the question.
                
                ❌ NOT ALLOWED:
                - Non-agriculture topics (technology, politics, entertainment, etc.)
                - Medical advice for humans
                - Financial advice beyond farm economics
                - Legal advice
                
                If someone asks about non-agriculture topics, politely redirect them:
                "I'm here to help with agriculture and livestock questions only. How can I assist you with your farming needs?"
                """
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
    expert_advisor_agent,
    default_agent
]

print("All agents properly configured ✓")
