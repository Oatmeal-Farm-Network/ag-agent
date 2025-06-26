# app.py
# Simplified Agricultural Advisory Application
# This version removes the main() function for a more direct script flow.

import streamlit as st
import autogen
import time
import threading
import traceback
import re
import uuid
import datetime




# --- STEP 1: SET PAGE CONFIG AS THE VERY FIRST COMMAND ---
st.set_page_config(
    page_title="Charlie 1.0 - Agricultural Advisor",
    layout="wide",
    initial_sidebar_state="auto"
)



# --- Local Imports ---
# These must be correct and point to your project's structure
from config import (
    autogen_llm_config_list, EXPERT_ADVISOR_NAME, USER_PROXY_NAME, 
    SEARCHER_NAME, PROCESSOR_NAME, SOIL_NAME, NUTRITION_NAME, 
    WEATHER_NAME, LIVESTOCK_BREED_NAME
)
from autogen_module.agents import all_agents
from database_module.cosmos_retriever import add_memory_to_cosmos
from streamlit_cookies_manager import CookieManager

# <<< --- FIX: Importing UI components at the top level --- >>>
from ui_module.ui_components import display_conversation_messages, create_chat_input_with_upload

# --- Helper Functions ---
def extract_final_advice(autogen_messages):
    """Extract the final advice from Expert Advisor"""
    if not autogen_messages:
        return None
    
    for msg_data in reversed(autogen_messages):
        if isinstance(msg_data, dict) and msg_data.get("name") == EXPERT_ADVISOR_NAME:
            content = msg_data.get("content", "").strip()
            if content:
                # Remove any trailing "TERMINATE" string for a cleaner output
                cleaned_advice = re.sub(r'\s*TERMINATE\s*$', '', content, flags=re.IGNORECASE).strip()
                if cleaned_advice:
                    return cleaned_advice
    return None

def custom_speaker_selection(last_speaker, groupchat):
    """
    Handles the conversation flow. It first checks for a NEXT_SPEAKER directive.
    If none is found, it uses a predefined workflow as a fallback.
    """
    print(f"\n--- Speaker Selection Triggered. Last speaker: '{last_speaker.name}' ---")

    last_message = groupchat.messages[-1]
    
    # If the last message was a tool call, the agent that made the call should speak next to process the result.
    if last_message.get("tool_calls"):
        print(f"Tool call detected from '{last_speaker.name}'. Forcing reply from the same agent to process results.")
        return last_speaker

    # Check for an explicit "NEXT_SPEAKER:" directive in the last message content.
    last_content = last_message.get('content', '')
    match = re.search(r"NEXT_SPEAKER:\s*(\w+)", last_content, re.IGNORECASE)
    if match:
        next_speaker_name = match.group(1).strip()
        print(f"Found directive: NEXT_SPEAKER: '{next_speaker_name}'")
        next_speaker = groupchat.agent_by_name(next_speaker_name)
        if next_speaker:
            print(f"SUCCESS: Following directive to '{next_speaker_name}'.")
            return next_speaker
        else:
            print(f"ERROR: Directive found, but agent '{next_speaker_name}' does not exist.")
            return None # End conversation if the directed agent is not found

    print("No directive found. Using fallback workflow.")
    
    # Predefined conversation flow if no directive is given
    fallback_workflow = {
        USER_PROXY_NAME: SEARCHER_NAME,
        SEARCHER_NAME: PROCESSOR_NAME,
        PROCESSOR_NAME: SOIL_NAME, 
        SOIL_NAME: NUTRITION_NAME,
        NUTRITION_NAME: EXPERT_ADVISOR_NAME,
        WEATHER_NAME: EXPERT_ADVISOR_NAME,
        LIVESTOCK_BREED_NAME: EXPERT_ADVISOR_NAME
    }
    
    next_speaker_name = fallback_workflow.get(last_speaker.name)

    if next_speaker_name:
        print(f"Fallback: After '{last_speaker.name}', next is '{next_speaker_name}'.")
        next_speaker = groupchat.agent_by_name(next_speaker_name)
        if next_speaker:
            return next_speaker
        else:
            print(f"ERROR: Fallback workflow error. Agent '{next_speaker_name}' does not exist.")
            return None
    else:
        print(f"End of fallback workflow for '{last_speaker.name}'. Terminating if possible.")
        return None # No more speakers in the predefined flow

# --- STEP 3: INITIALIZE SESSION AND COOKIES ---

# --- Initialize Cookie Manager ---
cookies = CookieManager()
if not cookies.ready():
    # Stop the script if cookies are not enabled in the browser or cannot be initialized.
    st.stop()

# --- User ID Initialization ---
if "user_id" not in st.session_state:
    try:
        user_id_from_cookie = cookies.get('user_id')
        if user_id_from_cookie:
            st.session_state.user_id = user_id_from_cookie
        else:
            # Generate a new user ID if one doesn't exist in cookies
            new_user_id = str(uuid.uuid4())
            st.session_state.user_id = new_user_id
            # Set a far-future expiration date for the cookie
            cookies.set('user_id', new_user_id, expires_at=datetime.datetime(year=2030, month=1, day=1))
    except Exception as e:
        # Fallback for environments where cookies might fail (e.g., some iframes)
        if '_user_id_fallback' not in st.session_state:
            st.session_state._user_id_fallback = str(uuid.uuid4())
        st.session_state.user_id = st.session_state._user_id_fallback
        st.warning(f"Could not initialize cookies. Using temporary user ID. Error: {e}")

# --- Initialize Session State for Chat History and Controls ---
if "user_query_history" not in st.session_state:
    st.session_state.user_query_history = []
if "autogen_chat_history" not in st.session_state:
    st.session_state.autogen_chat_history = []
if "thread_error" not in st.session_state:
    st.session_state.thread_error = None
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False

# --- STEP 4: RENDER THE UI AND HANDLE LOGIC ---

# --- Application Header ---
st.title("🌾 Charlie 1.0 - Agricultural Advisor")
st.markdown("*Get expert advice for your farming challenges*")

# --- Sidebar Controls ---
with st.sidebar:
    st.header("🔧 Controls")
    
    st.session_state.debug_mode = st.checkbox("Enable Debug Mode", value=st.session_state.debug_mode)
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.user_query_history = []
        st.session_state.autogen_chat_history = []
        st.rerun()
    
    st.text(f"User ID: {st.session_state.user_id[:8]}...")
    st.text(f"Messages: {len(st.session_state.user_query_history)}")

# --- Display Past Chat Messages ---
for msg_obj in st.session_state.user_query_history:
    with st.chat_message(msg_obj["role"]):
        st.markdown(msg_obj["content"])

# --- Handle New User Input ---
# Calling the function from ui_components to create the input bar with the '+' icon
prompt = create_chat_input_with_upload()

# The rest of the logic triggers only if the user entered text in the input box
if prompt:
    st.session_state.user_query_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # This is the main agent workflow logic
    with st.status("👩‍🌾 Consulting AI agricultural experts...", expanded=True) as status_widget:
        final_advice = None
        try:
            all_agents_for_chat = all_agents
            user_proxy = next((agent for agent in all_agents_for_chat if agent.name == USER_PROXY_NAME), None)

            if not user_proxy:
                raise ValueError(f"User Proxy Agent named '{USER_PROXY_NAME}' not found.")

            if st.session_state.debug_mode:
                status_widget.write(f"🔍 Debug: Starting with {len(st.session_state.autogen_chat_history)} existing messages")
                status_widget.write(f"🔍 Debug: User ID: {st.session_state.user_id}")

            groupchat = autogen.GroupChat(
                agents=all_agents_for_chat,
                messages=st.session_state.autogen_chat_history,
                max_round=20,
                speaker_selection_method=custom_speaker_selection
            )

            manager = autogen.GroupChatManager(
                groupchat=groupchat,
                llm_config={"config_list": autogen_llm_config_list, "temperature": 0.0}
            )

            conversation_completed_flag = [False]
            conversation_error = [None]

            def run_agent_conversation(user_id, current_prompt):
                """This function runs in a background thread and does NOT access st.session_state."""
                try:
                    initial_message = f"user_id: {user_id}\nquery_text: {current_prompt}"
                    user_proxy.initiate_chat(manager, message=initial_message)
                except Exception as e:
                    tb_str = traceback.format_exc()
                    conversation_error[0] = f"Error in conversation thread: {e}\nTrace:\n{tb_str}"
                finally:
                    conversation_completed_flag[0] = True

            conversation_thread = threading.Thread(
                target=run_agent_conversation,
                args=(st.session_state.user_id, prompt)
            )
            conversation_thread.start()

            last_displayed_count = len(st.session_state.autogen_chat_history)
            max_timeout = 300  # 5 minutes
            
            # Loop to update the UI while the thread is running
            for _ in range(max_timeout):
                if conversation_completed_flag[0] and len(groupchat.messages) <= last_displayed_count:
                    break
                
                if conversation_error[0]:
                    status_widget.error(conversation_error[0])
                    break
                
                current_total_messages = len(groupchat.messages)
                if current_total_messages > last_displayed_count:
                    new_messages = groupchat.messages[last_displayed_count:]
                    display_conversation_messages(new_messages, status_widget)
                    last_displayed_count = current_total_messages

                time.sleep(1)
            else:
                st.error("Conversation timed out. Please try again.")

            conversation_thread.join(timeout=30)

            st.session_state.autogen_chat_history = groupchat.messages.copy()

            if st.session_state.debug_mode:
                status_widget.write(f"🔍 Debug: Conversation ended with {len(groupchat.messages)} total messages")

            if conversation_error[0]:
                status_widget.update(label="❌ Workflow Failed!", state="error", expanded=True)
                final_advice_to_display = "I apologize, but an error occurred. The expert agents could not complete the consultation."
            else:
                status_widget.update(label="✅ Workflow Complete!", state="complete", expanded=True)
                final_advice = extract_final_advice(groupchat.messages)
                
                if final_advice:
                    final_advice_to_display = final_advice
                else:
                    final_advice_to_display = "The expert agents concluded their discussion, but a final recommendation was not formulated. Please try rephrasing."
        
        except Exception as e:
            tb_str = traceback.format_exc()
            status_widget.update(label="⚠️ Critical Error!", state="error", expanded=True)
            st.error(f"An error occurred in the main application workflow: {e}")
            if st.session_state.debug_mode:
                status_widget.error(f"Traceback:\n```\n{tb_str}\n```")
            final_advice_to_display = "A critical technical error occurred. Please contact support or try again later."

    # --- Display the final response and save to memory ---
    with st.chat_message("assistant"):
        st.markdown(final_advice_to_display)
        st.session_state.user_query_history.append({"role": "assistant", "content": final_advice_to_display})

        # Save to memory only if the advice was successful
        if final_advice and not ("apologize" in final_advice_to_display.lower() or "error" in final_advice_to_display.lower()):
            try:
                memory_summary = f"""User Query: {prompt}\n\nConcluded Advice: {final_advice}"""
                add_memory_to_cosmos(memory_summary, st.session_state.user_id)
                if st.session_state.debug_mode:
                    st.write("🔍 Debug: Successfully saved to memory.")
            except Exception as e:
                st.warning(f"Failed to save to memory: {e}")

