# app.py
# Main Streamlit application for the AI-Powered Agricultural Advisor.

import streamlit as st
import autogen
import time
import threading
import traceback
from dotenv import load_dotenv


# Import configurations, agents, and UI components
from config import autogen_llm_config_list, EXPERT_ADVISOR_NAME, USER_PROXY_NAME # Import necessary configs
from autogen_module.agents import all_agents, user_proxy, expert_advisor_agent # Import agent list and specific agents
from ui_module.ui_components import display_conversation_messages
# utils.py and cosmos_utils.py are used by autogen_setup and config, so not directly imported here unless needed.




# --- Streamlit Page Setup ---
st.set_page_config(page_title="Agricultural Advisory Agent", layout="wide")
st.title("🌾 AI-Powered Agricultural Advisor")
st.markdown("Welcome to the Farm Hub! Drop your farm questions or ask away—let’s grow answers together!")

# --- Initialize Session State ---
# For Streamlit chat message display
if "user_query_history" not in st.session_state:
    st.session_state.user_query_history = []
# For AutoGen group chat persistence across Streamlit reruns
if "autogen_chat_history" not in st.session_state:
    st.session_state.autogen_chat_history = []
# For tracking errors from the conversation thread
if "thread_error" not in st.session_state:
    st.session_state.thread_error = None
# No longer need displayed_message_count globally as ui_components handles its scope

# --- Display Past Chat Messages (Streamlit UI) ---
for msg_obj in st.session_state.user_query_history:
    with st.chat_message(msg_obj["role"]):
        st.markdown(msg_obj["content"])

# --- Handle User Input ---
if prompt := st.chat_input("Describe your farm problem or ask a follow-up (e.g., 'My maize has yellowing leaves...'):"):
    # Add user's new query to Streamlit's display history
    st.session_state.user_query_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Use st.status for displaying agent thinking process
    with st.status("👩‍🌾 Consulting AI agricultural experts... (Scroll down to see thinking process)", expanded=True) as status_widget:
        
        # Initialize GroupChat with persisted history for this new turn
        # AutoGen's GroupChat messages are appended to, so we pass the current history.
        groupchat = autogen.GroupChat(
            agents=all_agents,
            messages=st.session_state.autogen_chat_history, # Load history
            max_round=15,                                  # Max rounds for this specific prompt
            speaker_selection_method="auto",               # Relies on "NEXT_SPEAKER"
            allow_repeat_speaker=False
        )
        manager = autogen.GroupChatManager(
            groupchat=groupchat,
            llm_config={"config_list": autogen_llm_config_list, "temperature": 0.0}
        )

        try:
            status_widget.markdown("---")
            status_widget.markdown(f"#### 🗣️ **User Query (Initiating/Continuing Agent Chat)**")
            status_widget.markdown(f"**Question:** {prompt}")
            status_widget.markdown("---")

            conversation_completed_flag = [False] # Mutable flag for the thread
            st.session_state.thread_error = None  # Clear previous errors

            # Record length of AutoGen history *before* this turn's processing
            # This will help identify messages added *during* this turn.
            history_len_before_initiate_chat = len(st.session_state.autogen_chat_history)


            def run_agent_conversation():
                """Runs the AutoGen conversation in a separate thread."""
                try:
                    # User_proxy initiates the conversation FOR THIS TURN with the new prompt.
                    # The groupchat object (and thus its .messages list) already contains prior history.
                    # The user_proxy's system message dictates it will format the prompt
                    # and then suggest the next speaker.
                    user_proxy.initiate_chat(
                        manager,
                        message=prompt # Pass the new user prompt for this turn
                    )
                except Exception as e:
                    print(f"Error during agent conversation thread: {e}") # Server-side log
                    detailed_tb = traceback.format_exc()
                    print(detailed_tb) # Server-side log
                    st.session_state.thread_error = f"Error in conversation: {e}\nTrace:\n{detailed_tb}"
                finally:
                    conversation_completed_flag[0] = True # Signal completion

            # Start the conversation in a new thread
            conversation_thread = threading.Thread(target=run_agent_conversation)
            conversation_thread.start()

            # Monitor thread and update UI with new messages
            # groupchat.messages is updated by the running thread.
            # We compare its length with history_len_before_initiate_chat to get new messages.
            # st.session_state.autogen_chat_history is the master record, updated at the end.
            
            # Loop to update UI while the thread is running
            # In your app.py, inside the `if prompt:` block and `with st.status(...) as status_widget:`

# ... (other setup code like groupchat, manager, initial status_widget.markdown for the user query) ...

            # This is the length of the conversation history *before* the current turn's processing starts.
            # groupchat.messages is initialized with st.session_state.autogen_chat_history.
            # New messages for the current turn will be appended by AutoGen after these initial messages.
            num_messages_at_turn_start = len(st.session_state.autogen_chat_history)

            # This will track how many messages *from the current turn* have already been passed to display_conversation_messages.
            displayed_current_turn_message_count = 0

          # Display the initial messages that were present before the current turn started.

            # --- DISPLAY LOOP ---
            while not conversation_completed_flag[0]:
                # `groupchat.messages` is the live list being updated by the agent conversation thread.
                # First, identify all messages that belong to the *current turn's processing*.
                # These are messages appended after the initial `st.session_state.autogen_chat_history`.
                if len(groupchat.messages) > num_messages_at_turn_start:
                    all_new_messages_this_turn = groupchat.messages[num_messages_at_turn_start:]

                    # Now, from these new messages, pick only those not yet displayed.
                    if len(all_new_messages_this_turn) > displayed_current_turn_message_count:
                        messages_to_display_now = all_new_messages_this_turn[displayed_current_turn_message_count:]
                        
                        if messages_to_display_now: # Ensure there's something to display
                            display_conversation_messages(messages_to_display_now, status_widget)
                            displayed_current_turn_message_count += len(messages_to_display_now)
                
                time.sleep(0.5)  # Interval to check for new messages

                # Safety break if thread finishes but flag not set (optional, good for robustness)
                if not conversation_thread.is_alive() and not conversation_completed_flag[0]:
                    print("Debug: Conversation thread finished unexpectedly, marking as complete.")
                    conversation_completed_flag[0] = True
            # --- END OF MODIFIED DISPLAY LOOP ---

            conversation_thread.join(timeout=300) # Wait for the thread to complete

            if st.session_state.thread_error:
                status_widget.error(st.session_state.thread_error)
                # Potentially add st.session_state.thread_error to the main chat as well

            # Final display of any messages generated right at the end of the thread
            # that might have been missed by the loop.
            if len(groupchat.messages) > num_messages_at_turn_start:
                all_new_messages_this_turn_final = groupchat.messages[num_messages_at_turn_start:]
                if len(all_new_messages_this_turn_final) > displayed_current_turn_message_count:
                    final_messages_to_display = all_new_messages_this_turn_final[displayed_current_turn_message_count:]
                    if final_messages_to_display:
                        display_conversation_messages(final_messages_to_display, status_widget)

            # Persist the full updated history from this turn
            st.session_state.autogen_chat_history = groupchat.messages.copy()

            status_widget.update(label="✅ Consultation Complete! Review thinking process above.", state="complete", expanded=False)


        except Exception as e:
            status_widget.update(label="⚠️ Error during consultation!", state="error", expanded=True)
            st.error(f"AutoGen Workflow Orchestration Failed: {e}")
            detailed_tb = traceback.format_exc()
            status_widget.error(f"Traceback:\n```\n{detailed_tb}\n```")
            # Add error to Streamlit chat history as well
            st.session_state.user_query_history.append({"role": "assistant", "content": f"An error occurred: {e}"})

    # --- Display Final Advice from Assistant ---
    with st.chat_message("assistant"):
        st.subheader("🌾 Expert Agri-Guidance:")
        final_advice_to_display = "No advice was generated for this query, or the process was interrupted."

        # The final advice is expected to be the last message from the expert_advisor_agent
        # in the *overall* autogen_chat_history.
        if st.session_state.autogen_chat_history:
            # Iterate backwards through the persisted AutoGen history
            for msg_data in reversed(st.session_state.autogen_chat_history):
                if isinstance(msg_data, dict) and msg_data.get("name") == EXPERT_ADVISOR_NAME:
                    content = msg_data.get("content", "").strip()
                    # A simple check: if this is the very last message from the advisor.
                    # This assumes the advisor is the last one to speak to provide the final answer.
                    # This heuristic should generally work given the agent flow.
                    if content and content.upper() != "TERMINATE": # Ensure content exists and isn't just TERMINATE
                        final_advice_to_display = content
                        break
            
            # If no specific advice found from expert, but an error was logged from thread
            if final_advice_to_display.startswith("No advice") and st.session_state.thread_error:
                final_advice_to_display = f"Could not generate advice due to an internal error. Please check logs or try again. Details: {str(st.session_state.thread_error).splitlines()[0]}"


        st.markdown(final_advice_to_display)
        # Add the final advice to Streamlit's display history
        st.session_state.user_query_history.append({"role": "assistant", "content": final_advice_to_display})