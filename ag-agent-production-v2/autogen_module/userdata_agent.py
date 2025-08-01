# autogen_module/userdata_agent_fixed_v5.py
# FIXED VERSION: Parse RECENT CONVERSATION for context understanding
# UPDATED: Extract PeopleID from USER ID section dynamically

import autogen
import re
import ast
from typing import Dict, Any, Optional, List

from database_module.database_tools import people_tool, PEOPLE_COLUMNS
from config import autogen_llm_config_list, USERDATAAGENT_NAME

# Default PeopleID for testing purposes (fallback)
DEFAULT_PEOPLE_ID = 1234  # Generic test ID

class UserDataAgentWrapper:
    def __init__(self):
        # Store context for confirmation flows
        self.pending_update = None  # (field, value, people_id)
        self.pending_delete = None  # (field, people_id)
    
    def extract_people_id_from_context(self, full_content):
        """Extract PeopleID from USER ID section in the enhanced message"""
        lines = full_content.split('\n')
        
        for line in lines:
            if line.strip().startswith('USER ID:'):
                user_id = line.replace('USER ID:', '').strip()
                # If empty, fall back to default
                if not user_id:
                    print(f"⚠️  Empty USER ID found, using default: {DEFAULT_PEOPLE_ID}")
                    return DEFAULT_PEOPLE_ID
                try:
                    # Convert to integer if possible
                    return int(user_id)
                except ValueError:
                    # If not a valid integer, return the string as is
                    return user_id
        
        # Fallback to default if not found
        print(f"⚠️  No USER ID found in context, using default: {DEFAULT_PEOPLE_ID}")
        return DEFAULT_PEOPLE_ID
    
    def parse_enhanced_message(self, full_content):
        """Parse enhanced message to extract user query and conversation history"""
        user_input = None
        conversation_history = []
        
        lines = full_content.split('\n')
        
        # Extract CURRENT USER QUERY
        for line in lines:
            if line.strip().startswith('CURRENT USER QUERY:'):
                user_input = line.replace('CURRENT USER QUERY:', '').strip()
                break
        
        # Extract RECENT CONVERSATION
        in_recent_section = False
        recent_conversation_text = ""
        for line in lines:
            if line.strip().startswith('RECENT CONVERSATION:'):
                in_recent_section = True
                continue
            elif in_recent_section and line.strip().startswith('IMAGE ANALYSIS'):
                break
            elif in_recent_section:
                recent_conversation_text += line.strip()
        
        # Parse the conversation history
        if recent_conversation_text:
            try:
                conversation_history = ast.literal_eval(recent_conversation_text)
                print(f"🔍 Parsed conversation history: {len(conversation_history)} messages")
            except:
                print("⚠️  Could not parse conversation history")
                conversation_history = []
        
        return user_input, conversation_history 