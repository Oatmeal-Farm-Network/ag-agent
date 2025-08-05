# autogen_module/userdata_agent_fixed_v5.py
# FIXED VERSION: Parse RECENT CONVERSATION for context understanding

import autogen
import re
import ast
from typing import Dict, Any, Optional, List

from database_module.database_tools import people_tool, PEOPLE_COLUMNS
from config import autogen_llm_config_list, USERDATAAGENT_NAME

# Note: No default PeopleID - user ID must be provided in the enhanced message

class UserDataAgentWrapper:
    def __init__(self):
        # Store context for confirmation flows
        self.pending_update = None  # (field, value, people_id)
        self.pending_delete = None  # (field, people_id)
    
    def parse_enhanced_message(self, full_content):
        """Parse enhanced message to extract user query, conversation history, and user ID"""
        user_input = None
        conversation_history = []
        user_id = None
        
        lines = full_content.split('\n')
        
        # Extract USER ID
        for line in lines:
            if line.strip().startswith('USER ID:'):
                user_id = line.replace('USER ID:', '').strip()
                break
        
        # Extract CURRENT USER QUERY
        for i, line in enumerate(lines):
            if line.strip().startswith('CURRENT USER QUERY:'):
                # Get the content after the colon
                user_input = line.replace('CURRENT USER QUERY:', '').strip()
                # If empty, check the next line
                if not user_input and i + 1 < len(lines):
                    user_input = lines[i + 1].strip()
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
            except Exception as e:
                conversation_history = []
        
        return user_input, conversation_history, user_id
    
    def extract_user_intent(self, user_input, chat_history, default_people_id):
        """Enhanced intent extraction for chatbot-like behavior with context awareness"""
        original_input = user_input  # Keep original for capitalization preservation
        user_input = user_input.lower().strip()
        print(f"🔍 Extracting intent from: '{user_input}' (type: {type(user_input)})")
        
        # Initialize variables
        action = None
        field = None
        value = None
        detected_people_id = None
        
        # Check for PeopleID in the query (e.g., "user 123", "peopleid 456")
        people_id_patterns = [
            r'user\s+(\d+)',
            r'peopleid\s+(\d+)',
            r'people\s+id\s+(\d+)',
            r'id\s+(\d+)',
            r'person\s+(\d+)'
        ]
        
        for pattern in people_id_patterns:
            match = re.search(pattern, user_input)
            if match:
                detected_people_id = int(match.group(1))
                print(f"🔍 Detected PeopleID from query: {detected_people_id}")
                break
        
        # If no specific PeopleID found, check for "my" or "me" queries
        if not detected_people_id and any(word in user_input for word in ['my', 'me', 'i am', 'who am i']):
            # Only use default if it's a valid number (not None or invalid)
            if default_people_id and isinstance(default_people_id, int):
                detected_people_id = default_people_id
                print(f"🔍 Using provided PeopleID for 'my/me' query: {detected_people_id}")
            else:
                print(f"❌ No valid PeopleID available for 'my/me' query")
                return None, None, None, None
        
        # Enhanced action detection with priority
        read_keywords = ['show', 'display', 'get', 'see', 'view', 'what is', 'what\'s', 'whats', 'tell me', 'find', 'search', 'look up', 'know', 'wanted to know']
        update_keywords = ['update', 'change', 'modify', 'set', 'edit', 'alter', 'replace', 'switch']
        delete_keywords = ['delete', 'remove', 'clear', 'erase', 'reset', 'empty']
        create_keywords = ['create', 'add', 'new', 'register', 'sign up']
        
        # Check for actions with priority (delete > update > read > create)
        action = None
        
        # Check for delete actions first (highest priority)
        for keyword in delete_keywords:
            if keyword in user_input:
                action = "delete"
                break
        
        # Check for update actions
        if not action:
            for keyword in update_keywords:
                if keyword in user_input:
                    action = "update"
                    break
        
        # Check for read actions
        if not action:
            for keyword in read_keywords:
                if keyword in user_input:
                    action = "read"
                    break
        
        # Check for create actions last
        if not action:
            for keyword in create_keywords:
                if keyword in user_input:
                    action = "create"
                    break
        
        # Enhanced field detection with synonyms (more specific terms first)
        field_mappings = {
            'username': 'UserName',
            'user name': 'UserName',
            'login': 'UserName',
            'first name': 'PeopleFirstName',
            'firstname': 'PeopleFirstName',
            'last name': 'PeopleLastName',
            'lastname': 'PeopleLastName',
            'surname': 'PeopleLastName',
            'middle initial': 'PeopleMiddleInitial',
            'middle': 'PeopleMiddleInitial',
            'phone': 'PeoplePhone',
            'telephone': 'PeoplePhone',
            'landline': 'PeoplePhone',
            'cell': 'PeopleCell',
            'mobile': 'PeopleCell',
            'cellphone': 'PeopleCell',
            'fax': 'PeopleFax',
            'email': 'PeopleEmail',
            'e-mail': 'PeopleEmail',
            'mail': 'PeopleEmail',
            'bio': 'PeopleBio',
            'biography': 'PeopleBio',
            'about': 'PeopleBio',
            # More general terms last to avoid conflicts
            'first': 'PeopleFirstName',
            'last': 'PeopleLastName',
            'name': 'PeopleFirstName',
            'user': 'UserName',
            'profile': None,  # Special case for full profile
            'info': None,     # Special case for full profile
            'details': None,  # Special case for full profile
            'information': None  # Special case for full profile
        }
        
        # Detect field from current input
        for field_keyword, field_name in field_mappings.items():
            if field_keyword in user_input:
                field = field_name
                print(f"🔍 Found field in current input: {field}")
                break
        
        # If no field found in current input, try to get it from conversation history
        if not field:
            print(f"🔍 No field found in current input, checking conversation history...")
            # Look for the most recent field mentioned in conversation history
            if chat_history:
                recent_messages = chat_history[-5:] if len(chat_history) >= 5 else chat_history  # Check last 5 messages
                for msg in reversed(recent_messages):
                    if msg.get('role') == 'user':
                        msg_content = msg.get('content', '').lower()
                        print(f"🔍 Checking message: '{msg_content}'")
                        for field_keyword, field_name in field_mappings.items():
                            if field_keyword in msg_content:
                                field = field_name
                                print(f"🔍 Found field from conversation history: {field} (from: '{msg_content}')")
                                break
                        if field:
                            break
        
        # Special cases for full profile requests
        if any(word in user_input for word in ['profile', 'info', 'details', 'information', 'all', 'everything']):
            field = None  # Will trigger full profile read
        
        # Extract value for updates and creates - PRESERVE ORIGINAL CAPITALIZATION
        if action in ["update", "create"]:
            # Look for "to" patterns for updates - USE ORIGINAL INPUT FOR VALUE EXTRACTION
            if action == "update":
                to_patterns = [
                    r'to\s+([^,\s]+(?:\s+[^,\s]+)*)',  # Capture everything after "to" until comma or end
                    r'change\s+.+\s+to\s+([^,\s]+(?:\s+[^,\s]+)*)',
                    r'update\s+.+\s+to\s+([^,\s]+(?:\s+[^,\s]+)*)',
                    r'set\s+.+\s+to\s+([^,\s]+(?:\s+[^,\s]+)*)',
                    r'change\s+the\s+.+\s+to\s+([^,\s]+(?:\s+[^,\s]+)*)',
                    r'update\s+the\s+.+\s+to\s+([^,\s]+(?:\s+[^,\s]+)*)'
                ]
                
                for pattern in to_patterns:
                    # Use original input for value extraction to preserve capitalization
                    match = re.search(pattern, original_input, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        # Clean up the value (remove common endings)
                        value = re.sub(r'\s*(?:please|thanks|thank you|\.|,|!|\?)$', '', value, flags=re.IGNORECASE)
                        # PRESERVE ORIGINAL CAPITALIZATION - don't force title() or lower()
                        print(f"🔍 Extracted value: '{value}'")
                        break
            
            # Look for "add" patterns for creates
            elif action == "create":
                add_patterns = [
                    r'add\s+(?:my\s+)?(?:new\s+)?(?:email|phone|cell|bio|username|name)\s*[-:]\s*([^,\s]+(?:\s+[^,\s]+)*)',
                    r'add\s+(?:my\s+)?(?:new\s+)?(?:email|phone|cell|bio|username|name)\s+([^,\s]+(?:\s+[^,\s]+)*)',
                    r'(?:email|phone|cell|bio|username|name)\s*[-:]\s*([^,\s]+(?:\s+[^,\s]+)*)'
                ]
                
                for pattern in add_patterns:
                    match = re.search(pattern, original_input, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        # Clean up the value (remove common endings)
                        value = re.sub(r'\s*(?:please|thanks|thank you|\.|,|!|\?)$', '', value, flags=re.IGNORECASE)
                        # PRESERVE ORIGINAL CAPITALIZATION
                        print(f"🔍 Extracted value: '{value}'")
                        break
        
        print(f"🔍 Extracted intent: action={action}, field={field}, value={value}, people_id={detected_people_id}")
        return action, field, value, detected_people_id

    def get_user_friendly_field_name(self, field):
        """Convert database field names to user-friendly names"""
        field_mappings = {
            'PeopleFirstName': 'first name',
            'PeopleMiddleInitial': 'middle initial',
            'PeopleLastName': 'last name',
            'PeoplePhone': 'phone number',
            'PeopleCell': 'cell number',
            'PeopleFax': 'fax number',
            'PeopleEmail': 'email address',
            'UserName': 'username',
            'PeopleBio': 'bio'
        }
        return field_mappings.get(field, field)

    def generate_reply(self, agent, messages):
        
        # Extract the actual user query from the messages
        user_input = None
        conversation_history = []
        
        # Get the message content
        full_content = messages[-1]['content']
        
        # Check if this is an enhanced message by looking for USER ID first
        if 'USER ID:' in full_content:
            # Parse the enhanced message to get user query, conversation history, and user ID
            user_input, conversation_history, user_id = self.parse_enhanced_message(full_content)
            
            # Check if we have a valid user ID
            if not user_id or not user_id.isdigit():
                return "❌ **User ID not found!** I cannot process user data requests without a valid user ID. Please ensure you're logged in with a valid session."
            
            # Convert user_id to people_id
            people_id = int(user_id)
        else:
            # This is a simple message format (no USER ID found)
            user_input = full_content
            return "❌ **User ID not found!** I cannot process user data requests without a valid user ID. Please ensure you're logged in with a valid session."
        
        # Ensure user_input is a string
        if not isinstance(user_input, str):
            user_input = str(user_input)
        
        # Check if this is a confirmation response BEFORE processing intent
        user_input_lower = user_input.lower().strip()
        is_confirmation = any(word in user_input_lower for word in ['yes', 'confirm', 'ok', 'sure', 'proceed', 'do it', 'update it'])
        is_cancellation = any(word in user_input_lower for word in ['no', 'cancel', 'abort', 'stop', 'nevermind'])
        
        # Handle confirmation responses first
        if is_confirmation:
            if self.pending_update:
                field, value, people_id = self.pending_update
                # Proceed with update
                result = people_tool('update', identifier={'PeopleID': people_id}, data={field: value})
                if "Updated" in result:
                    friendly_field_name = self.get_user_friendly_field_name(field)
                    response = f"✅ **Successfully updated!** Your {friendly_field_name} has been changed to **{value}**"
                    # Clear pending update
                    self.pending_update = None
                    return response
                else:
                    response = f"❌ **Update failed:** {result}"
                    self.pending_update = None
                    return response
            elif self.pending_delete:
                field, people_id = self.pending_delete
                # Proceed with delete
                result = people_tool('update', identifier={'PeopleID': people_id}, data={field: None})
                if "Updated" in result:
                    friendly_field_name = self.get_user_friendly_field_name(field)
                    response = f"✅ **Successfully cleared!** Your {friendly_field_name} has been removed."
                    # Clear pending delete
                    self.pending_delete = None
                    return response
                else:
                    response = f"❌ **Clear failed:** {result}"
                    self.pending_delete = None
                    return response
            else:
                return "❌ I don't have a pending operation to confirm. Please specify what you want to update or clear."
        
        # Handle cancellation responses
        if is_cancellation:
            if self.pending_update:
                self.pending_update = None
                return "❌ **Update cancelled.** Your data remains unchanged."
            elif self.pending_delete:
                self.pending_delete = None
                return "❌ **Clear cancelled.** Your data remains unchanged."
            else:
                return "❌ No operation was pending to cancel."
        
        # Process normal requests with conversation history context
        intent_result = self.extract_user_intent(user_input, conversation_history, people_id)
        
        # Check if intent extraction failed
        if intent_result[0] is None:
            return "❌ **User ID not found!** I cannot process user data requests without a valid user ID. Please ensure you're logged in with a valid session."
        
        action, field, value, detected_people_id = intent_result
        
        # Use the detected PeopleID if available, otherwise use the provided people_id
        target_people_id = detected_people_id if detected_people_id else people_id
        
        # Enhanced chatbot responses with confirmation flow and context preservation
        if action == "read":
            result = people_tool('read', identifier={'PeopleID': target_people_id})
            print(f"[DEBUG] UserDataAgent people_tool result: {result}")
            if result and isinstance(result, list) and len(result) > 0:
                person = result[0]
                if field:
                    # Read specific field - USE USER-FRIENDLY NAMES
                    field_value = person.get(field, 'Not set')
                    if field_value:
                        friendly_field_name = self.get_user_friendly_field_name(field)
                        response = f"✅ Your {friendly_field_name} is **{field_value}**"
                        print(f"[DEBUG] UserDataAgent final response: {response}")
                        return response
                    else:
                        friendly_field_name = self.get_user_friendly_field_name(field)
                        response = f"❌ Your {friendly_field_name} is not set."
                        print(f"[DEBUG] UserDataAgent final response: {response}")
                        return response
                else:
                    # Read all fields - create a nice formatted response with user-friendly names
                    response_lines = [f"👤 **Your Profile Information:**"]
                    response_lines.append("")
                    
                    # Group fields logically
                    name_fields = ['PeopleFirstName', 'PeopleMiddleInitial', 'PeopleLastName']
                    contact_fields = ['PeoplePhone', 'PeopleCell', 'PeopleFax', 'PeopleEmail']
                    account_fields = ['UserName', 'PeopleBio']
                    
                    # Name section
                    name_parts = []
                    for field_name in name_fields:
                        value = person.get(field_name)
                        if value:
                            name_parts.append(value)
                    if name_parts:
                        response_lines.append(f"**Name:** {' '.join(name_parts)}")
                    
                    # Contact section
                    response_lines.append("")
                    response_lines.append("**Contact Information:**")
                    for field_name in contact_fields:
                        value = person.get(field_name)
                        if value:
                            friendly_name = self.get_user_friendly_field_name(field_name)
                            response_lines.append(f"  • {friendly_name.title()}: {value}")
                    
                    # Account section
                    response_lines.append("")
                    response_lines.append("**Account Information:**")
                    for field_name in account_fields:
                        value = person.get(field_name)
                        if value:
                            friendly_name = self.get_user_friendly_field_name(field_name)
                            response_lines.append(f"  • {friendly_name.title()}: {value}")
                        else:
                            friendly_name = self.get_user_friendly_field_name(field_name)
                            response_lines.append(f"  • {friendly_name.title()}: Not set")
                    
                    response = "\n".join(response_lines)
                    print(f"[DEBUG] UserDataAgent final response: {response}")
                    return response
            else:
                response = f"❌ Sorry, I couldn't find user data for PeopleID {target_people_id}. Please check if the ID is correct."
                print(f"[DEBUG] UserDataAgent final response: {response}")
                return response
        
        elif action == "update":
            # Handle new update request
            if not field:
                return "❌ I couldn't understand what field you want to update. Please specify the field name (like 'email', 'phone', 'username', etc.)."
            
            # Get current value to show what to change
            current_data = people_tool('read', identifier={'PeopleID': target_people_id})
            current_value = "Not set"
            if current_data and isinstance(current_data, list) and len(current_data) > 0:
                current_value = current_data[0].get(field, 'Not set')
            
            friendly_field_name = self.get_user_friendly_field_name(field)
            
            if not value:
                return f"📝 **Update {friendly_field_name.title()}**\n\nYour current {friendly_field_name}: **{current_value}**\n\nWhat would you like to change it to? Please specify the new value."
            
            # Store pending update for confirmation
            self.pending_update = (field, value, target_people_id)
            
            # Show confirmation
            confirmation_message = f"🔄 **Confirm Update**\n\n"
            confirmation_message += f"**Field:** {friendly_field_name.title()}\n"
            confirmation_message += f"**Current value:** {current_value}\n"
            confirmation_message += f"**New value:** {value}\n\n"
            confirmation_message += f"Are you sure you want to update your {friendly_field_name}? Please confirm with 'yes' or 'no'."
            return confirmation_message
        
        elif action == "delete":
            # Handle new delete request
            if not field:
                return "❌ I couldn't understand what field you want to clear. Please specify the field name (like 'email', 'phone', 'username', etc.)."
            
            # Get current value to show confirmation
            current_data = people_tool('read', identifier={'PeopleID': target_people_id})
            if not current_data or not isinstance(current_data, list) or len(current_data) == 0:
                return f"❌ Sorry, I couldn't find your current data. Please try again."
            
            current_person = current_data[0]
            current_value = current_person.get(field, 'Not set')
            friendly_field_name = self.get_user_friendly_field_name(field)
            
            # Store pending delete for confirmation
            self.pending_delete = (field, target_people_id)
            
            # Show confirmation
            confirmation_message = f"🗑️ **Confirm Clear**\n\n"
            confirmation_message += f"**Field:** {friendly_field_name.title()}\n"
            confirmation_message += f"**Current value:** {current_value}\n\n"
            confirmation_message += f"Are you sure you want to clear your {friendly_field_name}? Please confirm with 'yes' or 'no'."
            return confirmation_message
        
        else:
            return "I couldn't understand your request. Please try again."

# Create the UserDataAgent with the wrapper
user_data_agent_wrapper = UserDataAgentWrapper()

# Create the actual UserDataAgent
user_data_agent = autogen.AssistantAgent(
    name=USERDATAAGENT_NAME,
    llm_config={
        "config_list": autogen_llm_config_list,
        "temperature": 0.2,
    },
    system_message=(
        "You are a User Data Specialist. You can read, update, or delete user profile fields in the people table. "
        f"You have access to: {', '.join(PEOPLE_COLUMNS)}. Use the provided PeopleID to look up users. "
        "Always ask for confirmation before making changes and provide clear, helpful responses. "
        "Use the people_tool function for all database operations. "
        "IMPORTANT: Maintain context from previous messages. If a user asks about a field and then says 'change it to X', "
        "understand that 'it' refers to the field they just asked about."
    )
)

# Override the generate_reply method to use the wrapper
def generate_reply_with_wrapper(self, messages, sender=None, config=None):
    return user_data_agent_wrapper.generate_reply(self, messages)

# Replace the agent's generate_reply method with our wrapper version
user_data_agent.generate_reply = generate_reply_with_wrapper.__get__(user_data_agent, type(user_data_agent))

# Register the people_tool function with the UserDataAgent
user_data_agent.register_function(
    function_map={
        "people_tool": people_tool
    }
) 