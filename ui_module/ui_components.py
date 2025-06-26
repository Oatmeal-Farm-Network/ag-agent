#ui_components.py
# This file contains functions specifically for creating and managing parts of the 
# Streamlit user interface, like displaying the conversation messages between the user and AI agents.

import streamlit as st
from typing import List, Dict, Any

# Assuming config.py contains these names for emoji mapping

from config import (
    USER_PROXY_NAME, SEARCHER_NAME, PROCESSOR_NAME, SOIL_NAME,
    NUTRITION_NAME, EXPERT_ADVISOR_NAME, LIVESTOCK_BREED_NAME,WEATHER_NAME
)

# Placeholder for agent names if config.py is not directly accessible here
# In a real setup, these would ideally come from a shared config or be passed if needed.
USER_PROXY_NAME = "Farmer_Query_Relay"
SEARCHER_NAME = "SemanticSearcher"
PROCESSOR_NAME = "ContextProcessor"
SOIL_NAME = "SoilScienceSpecialist"
NUTRITION_NAME = "PlantNutritionExpert"
EXPERT_ADVISOR_NAME = "LeadAgriculturalAdvisor"


def display_conversation_messages(groupchat_messages: List[Dict[str, Any]], status_widget: st.status):
    """Displays new messages from the AutoGen conversation in the Streamlit status widget."""
    if not groupchat_messages:
        return

    # The calling code in app.py should ensure 'groupchat_messages' contains only new messages for this update.
    # Thus, internal tracking of displayed messages within this function for this specific turn is not needed.

    for msg in groupchat_messages:  # Iterate over the new messages provided for this update
        if isinstance(msg, dict):
            agent_name = msg.get("name", msg.get("sender", "Unknown Agent"))
            content = msg.get("content", "").strip()
            role = msg.get("role", "")

            # Skip system messages or empty content unless it's a tool call/response
            if role == "system" or not content:
                if not msg.get("tool_calls") and role != "tool" and not msg.get("tool_responses"):
                    continue
            
            status_widget.markdown("---")  # Separator for messages within the status box

            # Assign emojis based on agent names
            agent_emoji = "💬"  # Default
            if agent_name == "Admin" or agent_name == USER_PROXY_NAME: agent_emoji = "👤"
            elif agent_name == SEARCHER_NAME: agent_emoji = "🔍"
            elif agent_name == PROCESSOR_NAME: agent_emoji = "📋"
            elif agent_name == SOIL_NAME: agent_emoji = "🌱"
            elif agent_name == NUTRITION_NAME: agent_emoji = "🧪"
            elif agent_name == LIVESTOCK_BREED_NAME: agent_emoji = "🐄" 
            elif agent_name == WEATHER_NAME: agent_emoji = "🌦️" 
            elif agent_name == EXPERT_ADVISOR_NAME: agent_emoji = "👨‍🌾"
            elif role == "user": agent_emoji = "🗣️"
            
            status_widget.markdown(f"#### {agent_emoji} **{agent_name}** ({role})")

            # Display tool calls
            if msg.get("tool_calls"):
                for tool_call in msg.get("tool_calls", []):
                    func_name = tool_call.get("function", {}).get("name", "Unknown tool")
                    func_args = tool_call.get("function", {}).get("arguments", "No arguments")
                    status_widget.markdown(f"🔧 **Calling Tool:** `{func_name}`")
                    status_widget.caption(f"Arguments: {func_args[:300]}{'...' if len(func_args) > 300 else ''}")

            # Display tool responses
            tool_response_content_to_display = None
            if role == "tool":  # 'tool' role indicates a tool response message
                if msg.get("tool_responses"):  # Standard structure for tool responses
                    tool_response_content_to_display = msg.get("tool_responses")[0].get("content", "")
                elif "content" in msg:  # Fallback if content is directly in the message
                    tool_response_content_to_display = msg.get("content", "")
                
                if tool_response_content_to_display is not None:
                    # Try to get the tool name from the message (often matches tool_call_id or a name field)
                    tool_name_display = msg.get('name', msg.get('tool_call_id', 'unknown_tool_invocation'))
                    status_widget.markdown(f"🛠️ **Tool Result for `{tool_name_display}`:**")
                    status_widget.markdown(f"```text\n{tool_response_content_to_display[:1000]}{'...' if len(tool_response_content_to_display) > 1000 else ''}\n```")
            
            # Display regular content, TERMINATE, or NEXT_SPEAKER hints
            elif content.upper() == "TERMINATE" and agent_name != EXPERT_ADVISOR_NAME:
                status_widget.markdown("🛑 **TERMINATE** - Conversation flow ending by non-advisor agent.")
            elif content.upper().startswith("NEXT_SPEAKER:"):
                next_speaker = content.split(":", 1)[1].strip() if ":" in content else "Unknown"
                status_widget.markdown(f"👉 **Handoff to:** `{next_speaker}`")
            elif content:  # Display regular message content from an agent
                status_widget.markdown("**Response:**")
                status_widget.markdown(content)
            elif not msg.get("tool_calls") and role != "tool":  # No textual content and not a tool-related message
                status_widget.caption("(No textual content in this message step)")
            
            status_widget.markdown("")  # Adds a little vertical space for readability

# --- new function which handles both text and image input ---


def create_chat_input_with_upload():
    """
    Creates a custom chat input bar styled to look like the Gemini UI.
    This function structures the elements; the actual styling is handled by CSS in app.py.
    """
    # Create a container that will be targeted and styled by our custom CSS.
    # The 'gemini-input-bar' class is a custom marker for our CSS to find this container.
    with st.container():
        # Use columns to place the button and text input side-by-side.
        # The widths are adjusted for a small button and a large text area.
        col1, col2 = st.columns([0.07, 0.93])

        with col1:
            # For the icon, we use a simple button. The '➕' emoji provides a nice visual.
            # The key is unique to prevent conflicts with other buttons.
            st.button("➕", key="upload_button_gemini", help="Upload an image or file")

        with col2:
            # This is the main text input field.
            prompt = st.text_input(
                "Describe your farm problem or ask a follow-up question...",
                placeholder="Describe your farm problem or ask a follow-up question...",
                # The label is hidden for a cleaner, more modern look.
                label_visibility="collapsed",
                key="chat_input_gemini"
            )
    
    return prompt