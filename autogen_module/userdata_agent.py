# autogen_module/userdata_agent_fixed_v5.py
# FIXED VERSION: Parse RECENT CONVERSATION for context understanding

import autogen
import re
import ast
from typing import Dict, Any, Optional, List


from database_module.database_tools import (
    people_tool, PEOPLE_COLUMNS,
    animals_tool, ANIMALS_COLUMNS,
    ancestors_tool, ANCESTORS_COLUMNS,
    ancestrypercents_tool, ANCESTRYPERCENTS_COLUMNS,
    animalregistration_tool, ANIMALREGISTRATION_COLUMNS,
    animalstats_tool, ANIMALSTATS_COLUMNS,
    awards_tool, AWARDS_COLUMNS,
    associations_tool, ASSOCIATIONS_COLUMNS,
    associationmembers_tool, ASSOCIATIONMEMBERS_COLUMNS,
    business_tool, BUSINESS_COLUMNS,
    colorlookup_tool, COLORLOOKUP_COLUMNS,
    colors_tool, COLORS_COLUMNS,
    country_tool, COUNTRY_COLUMNS,
    fiber_tool, FIBER_COLUMNS,
    peopletitlelookup_tool, PEOPLETITLELOOKUP_COLUMNS,
    sire_tool, SIRE_COLUMNS,
    speciesbreedlookuptable_tool, SPECIESBREEDLOOKUPTABLE_COLUMNS,
    speciescategory_tool, SPECIESCATEGORY_COLUMNS,
    speciescolorlookuptable_tool, SPECIESCOLORLOOKUPTABLE_COLUMNS,
    speciesregistrationtypelookuptable_tool, SPECIESREGISTRATIONTYPELOOKUPTABLE_COLUMNS,
    state_province_tool, STATE_PROVINCE_COLUMNS,
    states_tool, STATES_COLUMNS,
    maledata_tool, MALEDATA_COLUMNS,
    
)

from config import autogen_llm_config_list, USERDATAAGENT_NAME


class UserDataAgentWrapper:
    def __init__(
        self, 
        *,
        id_field: str = "PeopleID",
        id_label: str = "USER ID",
        table_name: str = "people",
        columns: Optional[List[str]] = None,
        tool_func=None,
        field_synonyms: Optional[Dict[str, str]] = None,
    ):
        self.id_field = id_field
        self.id_label = id_label
        self.table_name = table_name
        self.columns = columns or PEOPLE_COLUMNS
        self.tool_func = tool_func or people_tool
        self.field_synonyms = field_synonyms or {}
        
        # Store context for confirmation flows (people)
        self.pending_create = None  # (field, value)
        self.pending_update = None  # (field, value, people_id)
        self.pending_delete = None  # (field, people_id)

        # Store context for confirmation flows (animals)
        self.pending_create_animal = None  # (field, value, identifier_dict)
        self.pending_update_animal = None  # (field, value, identifier_dict)
        self.pending_delete_animal = None  # (field, identifier_dict)
        
        # Store context for confirmation flows (ancestors)
        self.pending_create_ancestor = None  # (field, value, identifier_dict)
        self.pending_update_ancestor = None  # (field, value, identifier_dict)
        self.pending_delete_ancestor = None  # (field, identifier_dict)
       
        # Store context for confirmation flows (ancestry percents)
        self.pending_create_ancestrypercent = None  # (field, value, identifier_dict)
        self.pending_update_ancestrypercent = None  # (field, value, identifier_dict)
        self.pending_delete_ancestrypercent = None  # (field, identifier_dict)
        
        # Store context for confirmation flows (animal registration)
        self.pending_create_animalregistration = None  # (field, value, identifier_dict)
        self.pending_update_animalregistration = None  # (field, value, identifier_dict)
        self.pending_delete_animalregistration = None  # (field, identifier_dict)

        # Store context for confirmation flows (animal stats)
        self.pending_create_animalstats = None  # (field, value, identifier_dict)
        self.pending_update_animalstats = None  # (field, value, identifier_dict)
        self.pending_delete_animalstats = None  # (field, identifier_dict)

        # Store context for confirmation flows (awards)
        self.pending_create_awards = None  # (field, value, identifier_dict)
        self.pending_update_awards = None  # (field, value, identifier_dict)
        self.pending_delete_awards = None  # (field, identifier_dict)

        # Store context for confirmation flows (associations)
        self.pending_create_association = None  # (field, value, identifier_dict)
        self.pending_update_association = None  # (field, value, identifier_dict)
        self.pending_delete_association = None  # (field, identifier_dict)

        # Store context for confirmation flows (association members)
        self.pending_create_associationmembers = None  # (field, value, identifier_dict)
        self.pending_update_associationmembers = None  # (field, value, identifier_dict)
        self.pending_delete_associationmembers = None  # (field, identifier_dict)

        # Store context for confirmation flows (business)
        self.pending_create_business = None   # (field, value, identifier_dict)
        self.pending_update_business = None   # (field, value, identifier_dict)
        self.pending_delete_business = None   # (field, identifier_dict)

        # Store context for confirmation flows (color lookup)
        self.pending_create_colorlookup = None   # (field, value, identifier_dict)
        self.pending_update_colorlookup = None   # (field, value, identifier_dict)
        self.pending_delete_colorlookup = None   # (field, identifier_dict)

        # Store context for confirmation flows (colors)
        self.pending_create_colors = None   # (field, value, identifier_dict)
        self.pending_update_colors = None   # (field, value, identifier_dict)
        self.pending_delete_colors = None   # (field, identifier_dict)

        # Store context for confirmation flows (country)
        self.pending_create_country = None  # (field, value, identifier_dict)
        self.pending_update_country = None  # (field, value, identifier_dict)
        self.pending_delete_country = None  # (field, identifier_dict)

        # Store context for confirmation flows (fiber)
        self.pending_create_fiber = None   # (field, value, identifier_dict)
        self.pending_update_fiber = None   # (field, value, identifier_dict)
        self.pending_delete_fiber = None   # (field, identifier_dict)

        # Store context for confirmation flows (people title lookup)
        self.pending_create_peopletitlelookup = None  # (field, value, identifier_dict)
        self.pending_update_peopletitlelookup = None  # (field, value, identifier_dict)
        self.pending_delete_peopletitlelookup = None  # (field, identifier_dict)

        # Store context for confirmation flows (sire)
        self.pending_create_sire = None   # (field, value, identifier_dict)
        self.pending_update_sire = None   # (field, value, identifier_dict)
        self.pending_delete_sire = None   # (field, identifier_dict)

        # Store context for confirmation flows (species category)
        self.pending_create_speciescategory = None  # (field, value, identifier_dict)
        self.pending_update_speciescategory = None  # (field, value, identifier_dict)
        self.pending_delete_speciescategory = None  # (field, identifier_dict)

        # Store context for confirmation flows (species color lookup)
        self.pending_create_speciescolorlookup = None  # (field, value, identifier_dict)
        self.pending_update_speciescolorlookup = None  # (field, value, identifier_dict)
        self.pending_delete_speciescolorlookup = None  # (field, identifier_dict)

        # Store context for confirmation flows (species registration type lookup)
        self.pending_create_speciesregtype = None  # (field, value, identifier_dict)
        self.pending_update_speciesregtype = None  # (field, value, identifier_dict)
        self.pending_delete_speciesregtype = None  # (field, identifier_dict)

        # Store context for confirmation flows (state/province)
        self.pending_create_stateprov = None  # (field, value, identifier_dict)
        self.pending_update_stateprov = None  # (field, value, identifier_dict)
        self.pending_delete_stateprov = None  # (field, identifier_dict)

        # Store context for confirmation flows (states)
        self.pending_create_state = None  # (field, value, identifier_dict)
        self.pending_update_state = None  # (field, value, identifier_dict)
        self.pending_delete_state = None  # (field, identifier_dict)

        # Store context for confirmation flows (male data)
        self.pending_create_maledata = None  # (field, value, identifier_dict)
        self.pending_update_maledata = None  # (field, value, identifier_dict)
        self.pending_delete_maledata = None  # (field, identifier_dict)
    
    # ---------- COMMON PARSERS ----------
    def parse_enhanced_message(self, full_content: str):
        """Parse enhanced message to extract user query, conversation history, and user ID"""
        user_input = None
        conversation_history = []
        user_id = None
        
        lines = full_content.split('\n')
        
        # Extract USER ID
        for line in lines:
            if line.strip().startswith(f'{self.id_label}:'):
                user_id = line.replace(f'{self.id_label}:', '').strip()
                break
        
        # Extract CURRENT USER QUERY
        for i, line in enumerate(lines):
            if line.strip().startswith('CURRENT USER QUERY:'):
                user_input = line.replace('CURRENT USER QUERY:', '').strip()
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
        
        if recent_conversation_text:
            try:
                conversation_history = ast.literal_eval(recent_conversation_text)
            except Exception:
                conversation_history = []
        
        return user_input, conversation_history, user_id
    
    def _extract_action_generic(self, text: str) -> Optional[str]:
        t = text.lower()
        delete_keywords = ['delete', 'remove', 'clear', 'erase', 'reset', 'empty']
        update_keywords = ['update', 'change', 'modify', 'set', 'edit', 'alter', 'replace', 'switch']
        read_keywords = ['show', 'display', 'get', 'see', 'view', 'what is', "what's", 'whats', 'tell me', 'find', 'search', 'look up', 'know', 'wanted to know']
        create_keywords = ['create', 'add', 'new', 'register', 'sign up']
        for k in delete_keywords:
            if k in t: return 'delete'
        for k in update_keywords:
            if k in t: return 'update'
        for k in read_keywords:
            if k in t: return 'read'
        for k in create_keywords:
            if k in t: return 'create'
        return None

    def _extract_update_value_generic(self, original_text: str) -> Optional[str]:
        to_patterns = [
            r'to\s+(.+?)(?:\s*(?:please|thanks|thank you)[\.\!\,]?$|[\.\!\,]?$)',
            r'change\s+.+\s+to\s+(.+?)(?:\s*(?:please|thanks|thank you)[\.\!\,]?$|[\.\!\,]?$)',
            r'update\s+.+\s+to\s+(.+?)(?:\s*(?:please|thanks|thank you)[\.\!\,]?$|[\.\!\,]?$)',
            r'set\s+.+\s+to\s+(.+?)(?:\s*(?:please|thanks|thank you)[\.\!\,]?$|[\.\!\,]?$)',
        ]
        for p in to_patterns:
            m = re.search(p, original_text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None


    # ---------- PEOPLE ----------
    def extract_user_intent(self, user_input, chat_history, default_people_id):
        """Enhanced intent extraction for chatbot-like behavior with context awareness (PEOPLE)"""
        original_input = user_input
        user_input = user_input.lower().strip()
        
        action = None
        field = None
        value = None
        detected_people_id = None
        
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
                break
        
        if not detected_people_id and any(word in user_input for word in ['my', 'me', 'i am', 'who am i']):
            if default_people_id and isinstance(default_people_id, int):
                detected_people_id = default_people_id
            else:
                return None, None, None, None
        
        read_k = ['show','display','get','see','view','what is','what\'s','whats','tell me','find','search','look up','know','wanted to know']
        update_k = ['update','change','modify','set','edit','alter','replace','switch']
        delete_k = ['delete','remove','clear','erase','reset','empty']
        create_k = ['create','add','new','register','sign up']

        for k in delete_k:
            if k in user_input: action="delete"; break
        if not action:
            for k in update_k:
                if k in user_input: action="update"; break
        if not action:
            for k in read_k:
                if k in user_input: action="read"; break
        if not action:
            for k in create_k:
                if k in user_input: action="create"; break
        
        field_mappings = {
            'username':'UserName','user name':'UserName','login':'UserName',
            'first name':'PeopleFirstName','firstname':'PeopleFirstName',
            'last name':'PeopleLastName','lastname':'PeopleLastName','surname':'PeopleLastName',
            'middle initial':'PeopleMiddleInitial','middle':'PeopleMiddleInitial',
            'phone':'PeoplePhone','telephone':'PeoplePhone','landline':'PeoplePhone',
            'cell':'PeopleCell','mobile':'PeopleCell','cellphone':'PeopleCell',
            'fax':'PeopleFax','email':'PeopleEmail','e-mail':'PeopleEmail','mail':'PeopleEmail',
            'bio':'PeopleBio','biography':'PeopleBio','about':'PeopleBio',
            'first':'PeopleFirstName','last':'PeopleLastName','name':'PeopleFirstName',
            'user':'UserName','profile':None,'info':None,'details':None,'information':None
        }
        for fk, fn in field_mappings.items():
            if fk in user_input:
                field = fn
                break

        if not field and chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    msg_content = msg.get('content','').lower()
                    for fk, fn in field_mappings.items():
                        if fk in msg_content:
                            field = fn
                            break
                if field: break

        if any(word in user_input for word in ['profile','info','details','information','all','everything']):
            field = None

        if action in ["update","create"]:
            if action=="update":
                to_patterns = [
                    r'to\s+([^,\s]+(?:\s+[^,\s]+)*)',
                    r'change\s+.+\s+to\s+([^,\s]+(?:\s+[^,\s]+)*)',
                    r'update\s+.+\s+to\s+([^,\s]+(?:\s+[^,\s]+)*)',
                    r'set\s+.+\s+to\s+([^,\s]+(?:\s+[^,\s]+)*)',
                    r'change\s+the\s+.+\s+to\s+([^,\s]+(?:\s+[^,\s]+)*)',
                    r'update\s+the\s+.+\s+to\s+([^,\s]+(?:\s+[^,\s]+)*)'
                ]
                for pattern in to_patterns:
                    m = re.search(pattern, original_input, re.IGNORECASE)
                    if m:
                        value = re.sub(r'\s*(?:please|thanks|thank you|\.|,|!|\?)$','', m.group(1).strip(), flags=re.IGNORECASE)
                        break
            else:
                add_patterns = [
                    r'add\s+(?:my\s+)?(?:new\s+)?(?:email|phone|cell|bio|username|name)\s*[-:]\s*([^,\s]+(?:\s+[^,\s]+)*)',
                    r'add\s+(?:my\s+)?(?:new\s+)?(?:email|phone|cell|bio|username|name)\s+([^,\s]+(?:\s+[^,\s]+)*)',
                    r'(?:email|phone|cell|bio|username|name)\s*[-:]\s*([^,\s]+(?:\s+[^,\s]+)*)'
                ]
                for pattern in add_patterns:
                    m = re.search(pattern, original_input, re.IGNORECASE)
                    if m:
                        value = re.sub(r'\s*(?:please|thanks|thank you|\.|,|!|\?)$','', m.group(1).strip(), flags=re.IGNORECASE)
                        break

        return action, field, value, detected_people_id

    def get_user_friendly_field_name(self, field):
        mapping = {
            'PeopleFirstName':'first name','PeopleMiddleInitial':'middle initial','PeopleLastName':'last name',
            'PeoplePhone':'phone number','PeopleCell':'cell number','PeopleFax':'fax number',
            'PeopleEmail':'email address','UserName':'username','PeopleBio':'bio'
        }
        return mapping.get(field, field)

    # ---------- ANIMALS ----------
    def get_user_friendly_field_name_animal(self, field: str) -> str:
        mapping = {
            'FullName':'full name','ShortName':'short name','Breed':'breed','Horns':'horns','Category':'category',
            'LotNumber':'lot number','MicrochipNumber':'microchip number','Description':'description',
            'StudDescription':'stud description','Owner':'owner','Weight':'weight','Height':'height',
            'Temperment':'temperament','Skills':'skills','AgeClass':'age class','Gaited':'gaited',
            'Warmblooded':'warm-blooded','Markings':'markings','WhyOnABH':'why on ABH'
        }
        return mapping.get(field, field)

    def _extract_animal_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        m = re.search(r'\blot\s+([A-Za-z0-9\-_/\.]+)\b', original_text, re.IGNORECASE)
        if m:
            return {'LotNumber': m.group(1)}
        m = re.search(r'\b(?:microchip|chip)\s*(?:number)?\s*([A-Za-z0-9\-_/\.]+)\b', original_text, re.IGNORECASE)
        if m:
            return {'MicrochipNumber': m.group(1)}
        m = re.search(r'\banimal\s+["“]?([^"\n\r]+?)["”]?(?:$|[,\.\?\! ]+)', original_text, re.IGNORECASE)
        if m:
            cand = m.group(1).strip()
            if cand:
                return {'FullName': cand}
        m = re.search(r'\b(?:animal\s+)?id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            return {'ID': int(m.group(1))}
        return None

    def _extract_animal_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        candidates = {
            'fullname':'FullName','full name':'FullName','shortname':'ShortName','short name':'ShortName',
            'breed':'Breed','horns':'Horns','category':'Category','lot':'LotNumber','lot number':'LotNumber',
            'microchip':'MicrochipNumber','microchip number':'MicrochipNumber','description':'Description',
            'stud description':'StudDescription','owner':'Owner','weight':'Weight','height':'Height',
            'temperament':'Temperment','temperment':'Temperment','skills':'Skills','age class':'AgeClass',
            'gaited':'Gaited','warmblooded':'Warmblooded','markings':'Markings','why on abh':'WhyOnABH'
        }
        t = text.lower()
        for k, v in candidates.items():
            if k in t and v in ANIMALS_COLUMNS:
                return v
        if chat_history:
            recent = chat_history[-5:] if len(chat_history)>=5 else chat_history
            for msg in reversed(recent):
                if msg.get('role')=='user':
                    t2 = msg.get('content','').lower()
                    for k, v in candidates.items():
                        if k in t2 and v in ANIMALS_COLUMNS:
                            return v
        if any(w in t for w in ['profile','info','details','information','all','everything','record']):
            return None
        return None

    # ---------- ANCESTORS ----------
    def get_user_friendly_field_name_ancestor(self, field: str) -> str:
        mapping = {
            'dam':'Dam', 'Dam Color': 'DamColor','Dam Ari': 'DamARI','Dam CLAA': 'DamCLAA','Dam Link': 'DamLink','Dam dam': 'DamDam','Dam Dam Color': 'DamDamColor','Dam Dam ARI': 'DamDamARI',
            'Dam Dam CLAA': 'DamDamCLAA','Dam Dam Link': 'DamDamLink','Dam sire': 'Damsire','Dam Sire ARI': 'DamsireARI','Dam Sire CLAA': 'DamsireCLAA','Dam Sire Color': 'DamsireColor',
            'Dam Sire Link': 'DamsireLink','Dam Dam Dam': 'DamDamDam','Dam Dam Dam ARI': 'DamDamDamARI','Dam Dam Dam CLAA': 'DamDamDamCLAA','Dam Dam Dam Color': 'DamDamDamColor',
            'Dam Dam Dam Link': 'DamDamDamLink','Dam Dam Sire': 'DamDamSire','Dam Dam Sire ARI': 'DamDamSireARI','Dam Dam Sire CLAA': 'DamDamSireCLAA','Dam Dam Sire Color': 'DamDamSireColor',
            'Dam Dam Sire Link': 'DamDamSireLink','Dam Sire Dam': 'DamSireDam','Dam Sire Dam ARI': 'DamSireDamARI','Dam Sire Dam CLAA': 'DamSireDamCLAA','Dam Sire Dam Color': 'DamSireDamColor',
            'Dam Sire Dam Link': 'DamSireDamLink','Dam Sire Sire': 'DamSireSire','Dam Sire Sire ARI': 'DamSireSireARI','Dam Sire Sire CLAA': 'DamSireSireCLAA','Dam Sire Sire Color': 'DamSireSireColor',
            'Dam Sire Sire Link': 'DamSireSireLink','Sire': 'Sire','Sire Color': 'SireColor','Sire ARI': 'SireARI','Sire CLAA': 'SireCLAA','Sire Link': 'SireLink','Sire dam': 'Siredam',
            'Sire dam Color': 'SiredamColor','Sire dam ARI': 'SiredamARI','Sire dam CLAA': 'SiredamCLAA','Sire dam Link': 'SiredamLink','Sire Sire': 'SireSire','Sire Sire Color': 'SireSireColor',
            'Sire Sire ARI': 'SireSireARI','Sire Sire CLAA': 'SireSireCLAA','Sire Sire Link': 'SireSireLink','Sire Dam Dam': 'SireDamDam','Sire Dam Dam Color': 'SireDamDamColor',
            'Sire Dam Dam ARI': 'SireDamDamARI','Sire Dam Dam CLAA': 'SireDamDamCLAA','Sire Dam Dam Link': 'SireDamDamLink','Sire Dam Sire': 'SireDamSire','Sire Dam Sire Color': 'SireDamSireColor',
            'Sire Dam Sire ARI': 'SireDamSireARI','Sire Dam Sire CLAA': 'SireDamSireCLAA','Sire Dam Sire Link': 'SireDamSireLink','Sire Sire Dam': 'SireSireDam','Sire Sire Dam Color': 'SireSireDamColor',
            'Sire Sire Dam ARI': 'SireSireDamARI','Sire Sire Dam CLAA': 'SireSireDamCLAA','Sire Sire Dam Link': 'SireSireDamLink','Sire Sire Sire': 'SireSireSire','Sire Sire Sire Color': 'SireSireSireColor',
            'Sire Sire Sire ARI': 'SireSireSireARI','Sire Sire Sire CLAA': 'SireSireSireCLAA','Sire Sire Sire Link': 'SireSireSireLink'
        }
        return mapping.get(field, field)

    def _extract_ancestor_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        m = re.search(r'\b(?:ancestor\s+)?id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            return {'ID': int(m.group(1))}
        m = re.search(r'\baddress\s*id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            return {'AddressID': int(m.group(1))}
        m = re.search(r'\bfor\s+animal\s+["“]?([^"\n\r]+?)["”]?(?:$|[\.!,])', original_text, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            if name:
                animals = animals_tool('read', {'FullName': name})
                if animals and isinstance(animals, list) and len(animals) > 0 and 'ID' in animals[0]:
                    return {'ID': animals[0]['ID']}
        return None

    def _extract_ancestor_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        variants = {col.lower(): col for col in ANCESTORS_COLUMNS}
        friendly = {
            'dam':'Dam', 'Dam Color': 'DamColor','Dam Ari': 'DamARI','Dam CLAA': 'DamCLAA','Dam Link': 'DamLink','Dam dam': 'DamDam','Dam Dam Color': 'DamDamColor','Dam Dam ARI': 'DamDamARI',
            'Dam Dam CLAA': 'DamDamCLAA','Dam Dam Link': 'DamDamLink','Dam sire': 'Damsire','Dam Sire ARI': 'DamsireARI','Dam Sire CLAA': 'DamsireCLAA','Dam Sire Color': 'DamsireColor',
            'Dam Sire Link': 'DamsireLink','Dam Dam Dam': 'DamDamDam','Dam Dam Dam ARI': 'DamDamDamARI','Dam Dam Dam CLAA': 'DamDamDamCLAA','Dam Dam Dam Color': 'DamDamDamColor',
            'Dam Dam Dam Link': 'DamDamDamLink','Dam Dam Sire': 'DamDamSire','Dam Dam Sire ARI': 'DamDamSireARI','Dam Dam Sire CLAA': 'DamDamSireCLAA','Dam Dam Sire Color': 'DamDamSireColor',
            'Dam Dam Sire Link': 'DamDamSireLink','Dam Sire Dam': 'DamSireDam','Dam Sire Dam ARI': 'DamSireDamARI','Dam Sire Dam CLAA': 'DamSireDamCLAA','Dam Sire Dam Color': 'DamSireDamColor',
            'Dam Sire Dam Link': 'DamSireDamLink','Dam Sire Sire': 'DamSireSire','Dam Sire Sire ARI': 'DamSireSireARI','Dam Sire Sire CLAA': 'DamSireSireCLAA','Dam Sire Sire Color': 'DamSireSireColor',
            'Dam Sire Sire Link': 'DamSireSireLink','Sire': 'Sire','Sire Color': 'SireColor','Sire ARI': 'SireARI','Sire CLAA': 'SireCLAA','Sire Link': 'SireLink','Sire dam': 'Siredam',
            'Sire dam Color': 'SiredamColor','Sire dam ARI': 'SiredamARI','Sire dam CLAA': 'SiredamCLAA','Sire dam Link': 'SiredamLink','Sire Sire': 'SireSire','Sire Sire Color': 'SireSireColor',
            'Sire Sire ARI': 'SireSireARI','Sire Sire CLAA': 'SireSireCLAA','Sire Sire Link': 'SireSireLink','Sire Dam Dam': 'SireDamDam','Sire Dam Dam Color': 'SireDamDamColor',
            'Sire Dam Dam ARI': 'SireDamDamARI','Sire Dam Dam CLAA': 'SireDamDamCLAA','Sire Dam Dam Link': 'SireDamDamLink','Sire Dam Sire': 'SireDamSire','Sire Dam Sire Color': 'SireDamSireColor',
            'Sire Dam Sire ARI': 'SireDamSireARI','Sire Dam Sire CLAA': 'SireDamSireCLAA','Sire Dam Sire Link': 'SireDamSireLink','Sire Sire Dam': 'SireSireDam','Sire Sire Dam Color': 'SireSireDamColor',
            'Sire Sire Dam ARI': 'SireSireDamARI','Sire Sire Dam CLAA': 'SireSireDamCLAA','Sire Sire Dam Link': 'SireSireDamLink','Sire Sire Sire': 'SireSireSire','Sire Sire Sire Color': 'SireSireSireColor',
            'Sire Sire Sire ARI': 'SireSireSireARI','Sire Sire Sire CLAA': 'SireSireSireCLAA','Sire Sire Sire Link': 'SireSireSireLink'
        }
        t = text.lower()
        for k, v in variants.items():
            if k in t:
                return v
        for k, v in friendly.items():
            if k in t and v in ANCESTORS_COLUMNS:
                return v
        if chat_history:
            recent = chat_history[-5:] if len(chat_history)>=5 else chat_history
            for msg in reversed(recent):
                if msg.get('role')=='user':
                    t2 = msg.get('content','').lower()
                    for k, v in variants.items():
                        if k in t2:
                            return v
                    for k, v in friendly.items():
                        if k in t2 and v in ANCESTORS_COLUMNS:
                            return v
        if any(w in t for w in ['all','everything','details','info','record','lineage','ancestry']):
            return None
        return None

    # ---------- ANCESTRY PERCENTS ----------
    def get_user_friendly_field_name_percent(self, field: str) -> str:
        mapping = {
            'PercentPeruvian': 'percent Peruvian',
            'PercentBolivian': 'percent Bolivian',
            'PercentChilean': 'percent Chilean',
            'PercentAccoyo': 'percent Accoyo',
            'PercentUnknownOther': 'percent Unknown/Other',
            'OwnerID': 'owner id',
            'PercentID': 'percent id',
            'ID': 'animal id'
        }
        return mapping.get(field, field)

    def _extract_percent_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        m = re.search(r'\bpercent\s*id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            return {'PercentID': int(m.group(1))}
        m = re.search(r'\b(?:animal\s+)?id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            return {'ID': int(m.group(1))}
        m = re.search(r'\bowner\s*id\s*[:\s]+([A-Za-z0-9\-_\.]+)\b', original_text, re.IGNORECASE)
        if m:
            return {'OwnerID': m.group(1)}
        m = re.search(r'\bfor\s+animal\s+["“]?([^"\n\r]+?)["”]?(?:$|[\.!,])', original_text, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            if name:
                animals = animals_tool('read', {'FullName': name})
                if animals and isinstance(animals, list) and len(animals) > 0 and 'ID' in animals[0]:
                    return {'ID': animals[0]['ID']}
        return None

    def _extract_percent_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        candidates = {
            'peruvian': 'PercentPeruvian',
            'bolivian': 'PercentBolivian',
            'chilean': 'PercentChilean',
            'accoyo': 'PercentAccoyo',
            'unknown': 'PercentUnknownOther',
            'unknown/other': 'PercentUnknownOther',
            'owner id': 'OwnerID'
        }
        t = text.lower()
        for col in ANCESTRYPERCENTS_COLUMNS:
            if col.lower() in t:
                return col
        for k, v in candidates.items():
            if k in t and v in ANCESTRYPERCENTS_COLUMNS:
                return v
        if chat_history:
            recent = chat_history[-5:] if len(chat_history)>=5 else chat_history
            for msg in reversed(recent):
                if msg.get('role')=='user':
                    t2 = msg.get('content','').lower()
                    for col in ANCESTRYPERCENTS_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in candidates.items():
                        if k in t2 and v in ANCESTRYPERCENTS_COLUMNS:
                            return v
        if any(w in t for w in ['percent','percents','ancestry percent','ancestry percents','all','everything','details','info','record']):
            return None
        return None

    # ---------- ANIMAL REGISTRATION ----------
    def get_user_friendly_field_name_registration(self, field: str) -> str:
        mapping = {
            'AnimalRegistrationID': 'animal registration id',
            'AnimalID': 'animal id',
            'RegType': 'registration type',
            'RegNumber': 'registration number'
        }
        return mapping.get(field, field)

    def _extract_registration_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        m = re.search(r'\b(?:animal\s*)?registration\s*id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            return {'AnimalRegistrationID': int(m.group(1))}
        m = re.search(r'\banimal\s*id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            return {'AnimalID': int(m.group(1))}
        m = re.search(r'\bfor\s+animal\s+["“]?([^"\n\r]+?)["”]?(?:$|[\.!,])', original_text, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            if name:
                animals = animals_tool('read', {'FullName': name})
                if animals and isinstance(animals, list) and len(animals) > 0 and 'ID' in animals[0]:
                    return {'AnimalID': animals[0]['ID']}
        return None

    def _extract_registration_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        candidates = {
            'registration type': 'RegType',
            'reg type': 'RegType',
            'type': 'RegType',
            'registration number': 'RegNumber',
            'reg number': 'RegNumber',
            'reg no': 'RegNumber',
            'number': 'RegNumber'
        }
        t = text.lower()
        for col in ANIMALREGISTRATION_COLUMNS:
            if col.lower() in t:
                return col
        for k, v in candidates.items():
            if k in t and v in ANIMALREGISTRATION_COLUMNS:
                return v
        if chat_history:
            recent = chat_history[-5:] if len(chat_history)>=5 else chat_history
            for msg in reversed(recent):
                if msg.get('role')=='user':
                    t2 = msg.get('content','').lower()
                    for col in ANIMALREGISTRATION_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in candidates.items():
                        if k in t2 and v in ANIMALREGISTRATION_COLUMNS:
                            return v
        if any(w in t for w in ['register','registration','reg','papers','paperwork','all','everything','details','info','record']):
            return None
        return None

    # ---------- ANIMAL STATS ----------
    def get_user_friendly_field_name_stats(self, field: str) -> str:
        mapping = {
            'Animalsstatid': 'animal stats id',
            'AnimalID': 'animal id',
            'StatDate': 'stat date',
            'WebsiteID': 'website id',
            'AnimalName': 'animal name',
            'PeopleID': 'people id',
            'Websitename': 'website name'
        }
        return mapping.get(field, field)

    def _extract_stats_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        m = re.search(r'\b(?:animal\s*)?stats?\s*id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            return {'Animalsstatid': int(m.group(1))}
        m = re.search(r'\banimal\s*id\s+(\d+)\b', original_text, re.IGNORECASE)
        id_dict: Dict[str, Any] = {}
        if m:
            id_dict['AnimalID'] = int(m.group(1))
        m = re.search(r'\b(?:on|for)?\s*stat\s*date\s*[:\s]+([0-9]{4}-[0-9]{2}-[0-9]{2}(?:\s+[0-9]{2}:[0-9]{2}:[0-9]{2})?)\b', original_text, re.IGNORECASE)
        if m:
            id_dict['StatDate'] = m.group(1)
        m = re.search(r'\bwebsite\s*id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            id_dict['WebsiteID'] = int(m.group(1))
        if 'AnimalID' not in id_dict:
            m = re.search(r'\bfor\s+animal\s+["“]?([^"\n\r]+?)["”]?(?:$|[\.!,])', original_text, re.IGNORECASE)
            if m:
                name = m.group(1).strip()
                if name:
                    animals = animals_tool('read', {'FullName': name})
                    if animals and isinstance(animals, list) and len(animals) > 0 and 'ID' in animals[0]:
                        id_dict['AnimalID'] = animals[0]['ID']
        return id_dict if id_dict else None

    def _extract_stats_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        candidates = {
            'animal name': 'AnimalName',
            'website name': 'Websitename',
            'stat date': 'StatDate',
            'website id': 'WebsiteID',
            'people id': 'PeopleID',
        }
        t = text.lower()
        for col in ANIMALSTATS_COLUMNS:
            if col.lower() in t:
                return col
        for k, v in candidates.items():
            if k in t and v in ANIMALSTATS_COLUMNS:
                return v
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in ANIMALSTATS_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in candidates.items():
                        if k in t2 and v in ANIMALSTATS_COLUMNS:
                            return v
        if any(w in t for w in ['stats', 'stat', 'statistics', 'views', 'traffic', 'all', 'everything', 'details', 'info', 'record']):
            return None
        return None

    # ---------- AWARDS ----------
    def get_user_friendly_field_name_awards(self, field: str) -> str:
        mapping = {
            'AwardsID': 'awards id',
            'ID': 'animal id',
            'ShowName': 'show name',
            'AwardYear': 'award year',
            'Type': 'type',
            'PlacingNumber': 'placing number',
            'Placing': 'placing',
            'Class': 'class',
            'Judge': 'judge',
            'ShowYear': 'show year',
            'Awardcomments': 'award comments',
            'ShowLevel': 'show level'
        }
        return mapping.get(field, field)

    def _extract_awards_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        m = re.search(r'\bawards?\s*id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            return {'AwardsID': int(m.group(1))}
        ident: Dict[str, Any] = {}
        m = re.search(r'\banimal\s*id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            ident['ID'] = int(m.group(1))
        m = re.search(r'\bshow\s*name\s*[:\s]+"?([A-Za-z0-9 \-_&]+)"?\b', original_text, re.IGNORECASE)
        if m:
            ident['ShowName'] = m.group(1).strip()
        m = re.search(r'\b(?:award\s*year|show\s*year)\s+(\d{4})\b', original_text, re.IGNORECASE)
        if m:
            ident['AwardYear'] = int(m.group(1))
        if 'ID' not in ident:
            m = re.search(r'\bfor\s+animal\s+["“]?([^"\n\r]+?)["”]?(?:$|[\.!,])', original_text, re.IGNORECASE)
            if m:
                name = m.group(1).strip()
                if name:
                    animals = animals_tool('read', {'FullName': name})
                    if animals and isinstance(animals, list) and len(animals) > 0 and 'ID' in animals[0]:
                        ident['ID'] = animals[0]['ID']
        return ident if ident else None

    def _extract_awards_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        candidates = {
            'show name': 'ShowName',
            'award year': 'AwardYear',
            'type': 'Type',
            'placing number': 'PlacingNumber',
            'placing': 'Placing',
            'class': 'Class',
            'judge': 'Judge',
            'show year': 'ShowYear',
            'comments': 'Awardcomments',
            'show level': 'ShowLevel',
        }
        t = text.lower()
        for col in AWARDS_COLUMNS:
            if col.lower() in t:
                return col
        for k, v in candidates.items():
            if k in t and v in AWARDS_COLUMNS:
                return v
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in AWARDS_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in candidates.items():
                        if k in t2 and v in AWARDS_COLUMNS:
                            return v
        if any(w in t for w in ['award', 'awards', 'show', 'placing', 'judge', 'class', 'all', 'everything', 'details', 'record']):
            return None
        return None

    # ---------- ASSOCIATIONS ----------
    def get_user_friendly_field_name_association(self, field: str) -> str:
        mapping = {
            'AssociationID': 'association id',
            'PeopleId': 'people id',
            'SpeciesID': 'species id',
            'Position': 'position',
            'AddressID': 'address id',
            'Registry': 'registry',
            'AssociationName': 'association name',
            'AssociationAcronym': 'association acronym',
            'Associationwebsite': 'website',
            'AssociationEmailaddress': 'email address',
            'AssociationStreet1': 'street 1',
            'AssociationStreet2': 'street 2',
            'AssociationCity': 'city',
            'AssociationState': 'state',
            'AssociationCountry': 'country',
            'AssociationZip': 'zip',
            'AssociationPhone': 'phone',
            'SentWelcomeEmail': 'sent welcome email',
            'OfferedFreeMembership': 'offered free membership',
            'AcceptedFreeMemeberhip': 'accepted free membership',
            'OfferFreeAssciationwebsite': 'offered free association website',
            'AcceptedFreeMembershipWebsite': 'accepted free membership website',
            'AssociationLogo': 'logo',
            'AssociationDescription': 'description',
            'AssociationPassword': 'password',
            'AssociationContactName': 'contact name',
            'AssociationContactPosition': 'contact position',
            'AssociationContactEmail': 'contact email',
            'AssociationActivationCode': 'activation code',
            'AssociationShowaddress': 'show address',
            'country_id': 'country id',
            'AssociationType': 'association type',
            'FarmersMarket': 'farmers market',
            'FoodHub': 'food hub',
            'CSA': 'csa',
            'Livestock': 'livestock',
            'FarmAg': 'farm/ag',
            'AssociationFacebook': 'facebook',
            'AssociationX': 'x',
            'AssociationInstagram': 'instagram',
            'AssociationTruthSocial': 'truth social',
            'AssociationBlog': 'blog',
            'AssociationYouTube': 'youtube',
            'AssociationOtherSocial1': 'other social 1',
            'AssociationOtherSocial2': 'other social 2',
            'AssociationPinterest': 'pinterest',
            'AssociationLinkedIn': 'linkedin',
            'AssociationTollFreePhone': 'toll-free phone',
            'AssociationFax': 'fax',
            'AssociationTypeID': 'association type id'
        }
        return mapping.get(field, field)

    def _extract_association_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Identify an association row by:
          - AssociationID (PK)
          - AssociationName
          - AssociationAcronym
          - Registry + Position + PeopleId (as hints)
        """
        m = re.search(r'\bassociation\s*id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            return {'AssociationID': int(m.group(1))}
        ident: Dict[str, Any] = {}
        m = re.search(r'\bassociation\s*name\s*[:\s]+"?([^"\n\r]+?)"?\b', original_text, re.IGNORECASE)
        if m:
            ident['AssociationName'] = m.group(1).strip()
        m = re.search(r'\bacronym\s*[:\s]+"?([A-Za-z0-9\-_]+)"?\b', original_text, re.IGNORECASE)
        if m:
            ident['AssociationAcronym'] = m.group(1).strip()
        m = re.search(r'\bpeople\s*id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            ident['PeopleId'] = int(m.group(1))
        m = re.search(r'\bregistry\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            ident['Registry'] = int(m.group(1))
        return ident if ident else None

    def _extract_association_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        t = text.lower()
        # explicit column mentions
        for col in ASSOCIATIONS_COLUMNS:
            if col.lower() in t:
                return col
        # friendly aliases
        friendly = {
            'association name': 'AssociationName',
            'name': 'AssociationName',
            'acronym': 'AssociationAcronym',
            'website': 'Associationwebsite',
            'email': 'AssociationEmailaddress',
            'street 1': 'AssociationStreet1',
            'street 2': 'AssociationStreet2',
            'city': 'AssociationCity',
            'state': 'AssociationState',
            'country': 'AssociationCountry',
            'zip': 'AssociationZip',
            'phone': 'AssociationPhone',
            'toll free': 'AssociationTollFreePhone',
            'fax': 'AssociationFax',
            'facebook': 'AssociationFacebook',
            'instagram': 'AssociationInstagram',
            'twitter': 'AssociationX',
            'x': 'AssociationX',
            'linkedin': 'AssociationLinkedIn',
            'pinterest': 'AssociationPinterest',
            'youtube': 'AssociationYouTube',
            'blog': 'AssociationBlog',
            'truth social': 'AssociationTruthSocial',
            'other social 1': 'AssociationOtherSocial1',
            'other social 2': 'AssociationOtherSocial2',
            'description': 'AssociationDescription',
            'logo': 'AssociationLogo',
            'contact name': 'AssociationContactName',
            'contact position': 'AssociationContactPosition',
            'contact email': 'AssociationContactEmail',
            'activation code': 'AssociationActivationCode',
            'show address': 'AssociationShowaddress',
            'association type': 'AssociationType',
            'type id': 'AssociationTypeID',
            'farmers market': 'FarmersMarket',
            'food hub': 'FoodHub',
            'csa': 'CSA',
            'livestock': 'Livestock',
            'farmag': 'FarmAg',
            'position': 'Position',
            'registry': 'Registry',
        }
        for k, v in friendly.items():
            if k in t and v in ASSOCIATIONS_COLUMNS:
                return v
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in ASSOCIATIONS_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in friendly.items():
                        if k in t2 and v in ASSOCIATIONS_COLUMNS:
                            return v
        if any(w in t for w in ['association','registry','acronym','website','email','social','address','phone','all','everything','details','info','record']):
            return None
        return None

    # ---------- ASSOCIATION MEMBERS ----------
    def get_user_friendly_field_name_associationmember(self, field: str) -> str:
        mapping = {
            'associationmemberID': 'association member id',
            'PeopleID': 'people id',
            'AssociationID': 'association id',
            'MemberPosition': 'member position',
            'AccessLevel': 'access level',
            'Favorite': 'favorite',
            'BusinessID': 'business id'
        }
        return mapping.get(field, field)

    def _extract_associationmember_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Identify an association member row by:
          - associationmemberID (PK)
          - PeopleID + AssociationID combo
        """
        m = re.search(r'\bassociation\s*member\s*id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            return {'associationmemberID': int(m.group(1))}
        ident: Dict[str, Any] = {}
        m = re.search(r'\bmember\s*id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            ident['associationmemberID'] = int(m.group(1))
        m = re.search(r'\bpeople\s*id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            ident['PeopleID'] = int(m.group(1))
        m = re.search(r'\bassociation\s*id\s+(\d+)\b', original_text, re.IGNORECASE)
        if m:
            ident['AssociationID'] = int(m.group(1))
        return ident if ident else None

    def _extract_associationmember_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        t = text.lower()
        for col in ASSOCIATIONMEMBERS_COLUMNS:
            if col.lower() in t:
                return col
        friendly = {
            'member position': 'MemberPosition',
            'position': 'MemberPosition',
            'access level': 'AccessLevel',
            'favorite': 'Favorite',
            'business id': 'BusinessID',
            'people id': 'PeopleID',
            'association id': 'AssociationID'
        }
        for k, v in friendly.items():
            if k in t and v in ASSOCIATIONMEMBERS_COLUMNS:
                return v
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in ASSOCIATIONMEMBERS_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in friendly.items():
                        if k in t2 and v in ASSOCIATIONMEMBERS_COLUMNS:
                            return v
        if any(w in t for w in ['member','membership','association member','access','favorite','business','all','everything','details','info','record']):
            return None
        return None
    
    
    # ---------- BUSINESS ----------
    def get_user_friendly_field_name_business(self, field: str) -> str:
        mapping = {
            'BusinessID': 'business id',
            'BusinessTypeID': 'business type id',
            'BusinessName': 'business name',
            'BusinessWebsiteID': 'business website id',
            'BusinessEmail': 'business email',
            'BusinessHours': 'business hours',
            'PhoneID': 'phone id',
            'AddressID': 'address id',
            'EventID': 'event id',
            'BusinessLogo': 'business logo',
            'Contact1PeopleID': 'primary contact (people id)',
            'GGWebsite': 'gg website',
            'BusinessLinkedIn': 'linkedin',
            'BusinessFacebook': 'facebook',
            'BusinessX': 'x',
            'BusinessInstagram': 'instagram',
            'BusinessPinterest': 'pinterest',
            'BusinessTruthSocial': 'truth social',
            'BusinessBlog': 'blog',
            'BusinessYouTube': 'youtube',
            'BusinessOtherSocial1': 'other social 1',
            'BusinessOtherSocial2': 'other social 2',
            'AccessLevel': 'access level',
            'PreferedBreed': 'preferred breed',
            'SubscriptionLevel': 'subscription level',
            'BusinessPhone': 'business phone',
            'WebsitesID': 'websites id',
            'Cell': 'cell',
            'Fax': 'fax',
            'Preferedspecies': 'preferred species',
            'RanchHomeText': 'ranch home text',
            'RanchHomeHeading': 'ranch home heading',
            'RanchHomeText2': 'ranch home text 2',
            'Logo': 'logo',
            'Header': 'header',
            'FavoriteAssocitaionID': 'favorite association id',
            'BusinessAcronym': 'business acronym',
        }
        return mapping.get(field, field)

    def _extract_business_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Identify a business row by one (or more) of:
          - BusinessID
          - BusinessName
          - BusinessAcronym
          - Contact1PeopleID (via 'people id' or 'user id' cues)
          - BusinessWebsiteID / WebsitesID
          - AddressID / PhoneID
        """
        t = original_text

        # Primary IDs
        m = re.search(r'\bbusiness\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            return {'BusinessID': int(m.group(1))}

        ident: Dict[str, Any] = {}

        # Name / Acronym
        m = re.search(r'\bbusiness\s*name\s*[:\s]+"?([^"\n\r]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['BusinessName'] = m.group(1).strip()

        m = re.search(r'\bacronym\s*[:\s]+"?([A-Za-z0-9\-_]+)"?\b', t, re.IGNORECASE)
        if m:
            ident['BusinessAcronym'] = m.group(1).strip()

        # People link (treat “people id” or “user id” as Contact1PeopleID)
        m = re.search(r'\bpeople\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            ident['Contact1PeopleID'] = int(m.group(1))
        else:
            m = re.search(r'\buser\s*id\s+(\d+)\b', t, re.IGNORECASE)
            if m:
                ident['Contact1PeopleID'] = int(m.group(1))

        # Website IDs
        m = re.search(r'\bbusiness\s*website\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            ident['BusinessWebsiteID'] = int(m.group(1))
        m = re.search(r'\bwebsites?\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            ident['WebsitesID'] = int(m.group(1))

        # Address / Phone links
        m = re.search(r'\baddress\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            ident['AddressID'] = int(m.group(1))
        m = re.search(r'\bphone\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            ident['PhoneID'] = int(m.group(1))

        return ident if ident else None

    def _extract_business_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        """
        Try explicit column mentions, then friendly aliases. Falls back to None (meaning "show full record").
        """
        t = text.lower()

        # 1) direct column mentions
        for col in BUSINESS_COLUMNS:
            if col.lower() in t:
                return col

        # 2) friendly aliases
        friendly = {
            'name': 'BusinessName',
            'business name': 'BusinessName',
            'email': 'BusinessEmail',
            'business email': 'BusinessEmail',
            'hours': 'BusinessHours',
            'business hours': 'BusinessHours',
            'logo': 'BusinessLogo',
            'website id': 'BusinessWebsiteID',
            'business website id': 'BusinessWebsiteID',
            'websites id': 'WebsitesID',
            'phone id': 'PhoneID',
            'address id': 'AddressID',
            'event id': 'EventID',
            'linkedin': 'BusinessLinkedIn',
            'facebook': 'BusinessFacebook',
            'x': 'BusinessX',
            'twitter': 'BusinessX',
            'instagram': 'BusinessInstagram',
            'pinterest': 'BusinessPinterest',
            'truth social': 'BusinessTruthSocial',
            'blog': 'BusinessBlog',
            'youtube': 'BusinessYouTube',
            'other social 1': 'BusinessOtherSocial1',
            'other social 2': 'BusinessOtherSocial2',
            'access level': 'AccessLevel',
            'preferred breed': 'PreferedBreed',
            'subscription level': 'SubscriptionLevel',
            'business phone': 'BusinessPhone',
            'cell': 'Cell',
            'fax': 'Fax',
            'preferred species': 'Preferedspecies',
            'ranch home text': 'RanchHomeText',
            'ranch home heading': 'RanchHomeHeading',
            'ranch home text 2': 'RanchHomeText2',
            'header': 'Header',
            'favorite association id': 'FavoriteAssocitaionID',
            'acronym': 'BusinessAcronym',
            'type id': 'BusinessTypeID',
            'gg website': 'GGWebsite',
            'contact people id': 'Contact1PeopleID',
        }
        for k, v in friendly.items():
            if k in t and v in BUSINESS_COLUMNS:
                return v

        # 3) look back into chat history
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in BUSINESS_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in friendly.items():
                        if k in t2 and v in BUSINESS_COLUMNS:
                            return v

        # 4) if user asked generically for “business info/details/all”, return None to show full record
        if any(w in t for w in ['business', 'company', 'brand', 'store']) and any(
            g in t for g in ['info', 'details', 'record', 'profile', 'all', 'everything']
        ):
            return None

        return None

    # ---------- COLORLOOKUP ----------
    def get_user_friendly_field_name_color(self, field: str) -> str:
        mapping = {
            'ColorID': 'color id',
            'Color': 'color',
            'Abbreviation': 'abbreviation',
            'ColorGroup': 'color group',
            'JudgingType': 'judging type',
            'Breed': 'breed',
        }
        return mapping.get(field, field)

    def _extract_color_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Identify a Colorlookup row by:
          - ColorID (PK)
          - Color (exact), Abbreviation (exact), or a combination (fallbacks)
        """
        t = original_text

        # ColorID
        m = re.search(r'\b(?:color|colour)\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            return {'ColorID': int(m.group(1))}

        ident: Dict[str, Any] = {}

        # Color (quoted or plain)
        m = re.search(r'\b(?:color|colour)\s*[:\s]+"?([A-Za-z0-9 \-_/]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['Color'] = m.group(1).strip()

        # Abbreviation
        m = re.search(r'\babbrev(?:iation)?\s*[:\s]+"?([A-Za-z0-9\-_]+)"?\b', t, re.IGNORECASE)
        if m:
            ident['Abbreviation'] = m.group(1).strip()

        # ColorGroup
        m = re.search(r'\bcolor\s*group\s*[:\s]+"?([A-Za-z0-9 \-_/]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['ColorGroup'] = m.group(1).strip()

        # JudgingType
        m = re.search(r'\bjudging\s*type\s*[:\s]+"?([A-Za-z0-9 \-_/]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['JudgingType'] = m.group(1).strip()

        # Breed
        m = re.search(r'\bbreed\s*[:\s]+"?([A-Za-z0-9 \-_/]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['Breed'] = m.group(1).strip()

        return ident if ident else None

    def _extract_color_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        t = text.lower()
        # direct column name mentions
        for col in COLORLOOKUP_COLUMNS:
            if col.lower() in t:
                return col
        # friendly aliases
        friendly = {
            'color': 'Color',
            'colour': 'Color',
            'abbrev': 'Abbreviation',
            'abbreviation': 'Abbreviation',
            'color group': 'ColorGroup',
            'colour group': 'ColorGroup',
            'group': 'ColorGroup',
            'judging type': 'JudgingType',
            'judging': 'JudgingType',
            'breed': 'Breed',
            'color id': 'ColorID',
            'colour id': 'ColorID',
        }
        for k, v in friendly.items():
            if k in t and v in COLORLOOKUP_COLUMNS:
                return v

        # fall back to recent user message context
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in COLORLOOKUP_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in friendly.items():
                        if k in t2 and v in COLORLOOKUP_COLUMNS:
                            return v

        # read-all queries
        if any(w in t for w in ['color', 'colour', 'abbreviation', 'group', 'judging', 'breed', 'all', 'everything', 'details', 'info', 'record', 'lookup']):
            return None

        return None

    # ---------- COLORS ----------
    def get_user_friendly_field_name_colors(self, field: str) -> str:
        mapping = {
            'ColorID': 'color id',
            'ID': 'id',
            'Color1': 'color 1',
            'Color2': 'color 2',
            'Color3': 'color 3',
            'Color4': 'color 4',
            'Color5': 'color 5',
        }
        return mapping.get(field, field)

    def _extract_colors_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Identify a Colors row by:
          - ColorID (PK), or
          - ID (foreign key to parent entity, if applicable)
        """
        t = original_text

        # ColorID
        m = re.search(r'\bcolors?\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            return {'ColorID': int(m.group(1))}

        # ID (generic)
        m = re.search(r'\b(?:entity|parent|animal)?\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            return {'ID': int(m.group(1))}

        return None

    def _extract_colors_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        t = text.lower()

        # direct column references
        for col in COLORS_COLUMNS:
            if col.lower() in t:
                return col

        # friendly aliases / soft matches
        friendly = {
            'color 1': 'Color1', 'colour 1': 'Color1', 'color1': 'Color1', 'colour1': 'Color1',
            'color 2': 'Color2', 'colour 2': 'Color2', 'color2': 'Color2', 'colour2': 'Color2',
            'color 3': 'Color3', 'colour 3': 'Color3', 'color3': 'Color3', 'colour3': 'Color3',
            'color 4': 'Color4', 'colour 4': 'Color4', 'color4': 'Color4', 'colour4': 'Color4',
            'color 5': 'Color5', 'colour 5': 'Color5', 'color5': 'Color5', 'colour5': 'Color5',
            'colors id': 'ColorID', 'colours id': 'ColorID',
            'id': 'ID'
        }
        for k, v in friendly.items():
            if k in t and v in COLORS_COLUMNS:
                return v

        # try recent user messages
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in COLORS_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in friendly.items():
                        if k in t2 and v in COLORS_COLUMNS:
                            return v

        # if the user asks for the whole record
        if any(w in t for w in ['colors', 'colours', 'palette', 'swatch', 'all', 'everything', 'details', 'info', 'record']):
            return None

        return None
    
    # ---------- COUNTRY ----------
    def get_user_friendly_field_name_country(self, field: str) -> str:
        mapping = {
            'country_id': 'country id',
            'name': 'name',
            'iso_code': 'ISO code',
            'Currency': 'currency',
            'CurrencyCode': 'currency code',
            'Active': 'active',
            'Paycode': 'pay code',
            'region': 'region',
            'ProvinceTitle': 'province title',
        }
        return mapping.get(field, field)

    def _extract_country_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Identify a Country row by:
          - country_id (PK), or
          - iso_code, or
          - name (exact/quoted), with optional region/Paycode hints
        """
        t = original_text

        # country_id
        m = re.search(r'\bcountry\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            return {'country_id': int(m.group(1))}

        ident: Dict[str, Any] = {}

        # iso_code
        m = re.search(r'\biso\s*code\s*[:\s]+"?([A-Za-z]{2,3})"?\b', t, re.IGNORECASE)
        if m:
            ident['iso_code'] = m.group(1).upper().strip()

        # name
        m = re.search(r'\bname\s*[:\s]+"?([A-Za-z0-9 \-\'\(\)&\.]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['name'] = m.group(1).strip()

        # region (hint)
        m = re.search(r'\bregion\s*[:\s]+"?([A-Za-z0-9 \-\'\(\)&\.]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['region'] = m.group(1).strip()

        # Paycode (hint)
        m = re.search(r'\bpay\s*code\s*[:\s]+"?([A-Za-z0-9\-_]+)"?\b', t, re.IGNORECASE)
        if m:
            ident['Paycode'] = m.group(1).strip()

        return ident if ident else None

    def _extract_country_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        t = text.lower()

        # direct column name mentions
        for col in COUNTRY_COLUMNS:
            if col.lower() in t:
                return col

        # friendly aliases
        friendly = {
            'country id': 'country_id',
            'iso code': 'iso_code',
            'iso': 'iso_code',
            'currency': 'Currency',
            'currency code': 'CurrencyCode',
            'pay code': 'Paycode',
            'paycode': 'Paycode',
            'region': 'region',
            'province title': 'ProvinceTitle',
            'name': 'name',
        }
        for k, v in friendly.items():
            if k in t and v in COUNTRY_COLUMNS:
                return v

        # recent user context fallback
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in COUNTRY_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in friendly.items():
                        if k in t2 and v in COUNTRY_COLUMNS:
                            return v

        # asking for full record
        if any(w in t for w in ['country', 'iso', 'currency', 'paycode', 'region', 'province', 'all', 'everything', 'details', 'info', 'record']):
            return None

        return None

    # ---------- FIBER ----------
    def get_user_friendly_field_name_fiber(self, field: str) -> str:
        mapping = {
            'FiberID': 'fiber id',
            'ID': 'id',
            'SampleDate': 'sample date',
            'SampleDateMonth': 'sample date month',
            'SampleDateDay': 'sample date day',
            'SampleDateYear': 'sample date year',
            'SampleAge': 'sample age',
            'Average': 'average',
            'StandardDev': 'standard deviation',
            'COV': 'cov',
            'GreaterThan30': 'greater than 30',
            'CF': 'comfort factor',
            'Curve': 'curve',
            'Shearweight': 'shear weight',
            'BlanketWeight': 'blanket weight',
            'Length': 'length',
            'CrimpPerInch': 'crimp per inch',
            'LargeHistogram': 'large histogram',
            'SmallHistogram': 'small histogram',
            'StapleLength': 'staple length',
        }
        return mapping.get(field, field)

    def _extract_fiber_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Identify a Fiber row by:
          - FiberID (PK), or
          - ID (foreign key to animal/entity), optionally with date hints
        """
        t = original_text

        # FiberID
        m = re.search(r'\bfiber\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            return {'FiberID': int(m.group(1))}

        ident: Dict[str, Any] = {}

        # Generic ID (e.g., animal ID that fiber row is linked to)
        m = re.search(r'\b(?:entity|animal)?\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            ident['ID'] = int(m.group(1))

        # SampleDate (any string; accept quoted or unquoted up to punctuation)
        m = re.search(r'\bsample\s*date\s*[:\s]+"?([0-9A-Za-z \-_/.:]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['SampleDate'] = m.group(1).strip()

        # Month / Day / Year components (optional)
        m = re.search(r'\bmonth\s*[:\s]+(\d{1,2})\b', t, re.IGNORECASE)
        if m:
            ident['SampleDateMonth'] = int(m.group(1))
        m = re.search(r'\bday\s*[:\s]+(\d{1,2})\b', t, re.IGNORECASE)
        if m:
            ident['SampleDateDay'] = int(m.group(1))
        m = re.search(r'\byear\s*[:\s]+(\d{4})\b', t, re.IGNORECASE)
        if m:
            ident['SampleDateYear'] = int(m.group(1))

        return ident if ident else None

    def _extract_fiber_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        t = text.lower()

        # exact column mentions
        for col in FIBER_COLUMNS:
            if col.lower() in t:
                return col

        # friendly aliases
        friendly = {
            'fiber id': 'FiberID',
            'sample date': 'SampleDate',
            'month': 'SampleDateMonth',
            'day': 'SampleDateDay',
            'year': 'SampleDateYear',
            'sample age': 'SampleAge',
            'average': 'Average',
            'std': 'StandardDev',
            'standard deviation': 'StandardDev',
            'cov': 'COV',
            '>30': 'GreaterThan30',
            'greater than 30': 'GreaterThan30',
            'comfort factor': 'CF',
            'cf': 'CF',
            'curve': 'Curve',
            'shear weight': 'Shearweight',
            'blanket weight': 'BlanketWeight',
            'length': 'Length',
            'crimp per inch': 'CrimpPerInch',
            'large histogram': 'LargeHistogram',
            'small histogram': 'SmallHistogram',
            'staple length': 'StapleLength',
        }
        for k, v in friendly.items():
            if k in t and v in FIBER_COLUMNS:
                return v

        # recent user context
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in FIBER_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in friendly.items():
                        if k in t2 and v in FIBER_COLUMNS:
                            return v

        # reading a whole record
        if any(w in t for w in ['fiber', 'fibre', 'sample', 'sample date', 'histogram', 'staple', 'crimp', 'all', 'everything', 'details', 'info', 'record']):
            return None

        return None

    # ---------- PEOPLETITLELOOKUP ----------
    def get_user_friendly_field_name_peopletitle(self, field: str) -> str:
        mapping = {
            'PeopletitleID': 'people title id',
            'PeopleTitle': 'people title',
            'PeopleTitleDescription': 'people title description',
        }
        return mapping.get(field, field)

    def _extract_peopletitle_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Identify a Peopletitlelookup row by:
          - PeopletitleID (PK), or
          - PeopleTitle (exact/quoted)
        """
        t = original_text

        # PeopletitleID
        m = re.search(r'\bpeople\s*title\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            return {'PeopletitleID': int(m.group(1))}

        ident: Dict[str, Any] = {}

        # PeopleTitle (quoted or simple)
        m = re.search(r'\bpeople\s*title\s*[:\s]+"?([A-Za-z0-9 \-\'&\.]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['PeopleTitle'] = m.group(1).strip()

        return ident if ident else None

    def _extract_peopletitle_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        t = text.lower()

        # direct column mentions
        for col in PEOPLETITLELOOKUP_COLUMNS:
            if col.lower() in t:
                return col

        # friendly aliases
        friendly = {
            'people title id': 'PeopletitleID',
            'title id': 'PeopletitleID',
            'people title': 'PeopleTitle',
            'title': 'PeopleTitle',
            'description': 'PeopleTitleDescription',
            'people title description': 'PeopleTitleDescription',
        }
        for k, v in friendly.items():
            if k in t and v in PEOPLETITLELOOKUP_COLUMNS:
                return v

        # recent user context fallback
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in PEOPLETITLELOOKUP_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in friendly.items():
                        if k in t2 and v in PEOPLETITLELOOKUP_COLUMNS:
                            return v

        # whole-record reads
        if any(w in t for w in ['people title', 'title', 'titles', 'lookup', 'all', 'everything', 'details', 'info', 'record']):
            return None

        return None
    
    # ---------- SIRE ----------
    def get_user_friendly_field_name_sire(self, field: str) -> str:
        mapping = {
            'SireID': 'sire id',
            'SiresName': 'sire name',
            'SiresRegistration': 'sire registration',
            'SiresColor': 'sire color',
        }
        return mapping.get(field, field)

    def _extract_sire_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Identify a Sire row by:
          - SireID (PK), or
          - SiresName, or
          - SiresRegistration
        """
        t = original_text

        # SireID
        m = re.search(r'\bsire\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            return {'SireID': int(m.group(1))}

        ident: Dict[str, Any] = {}

        # SiresName (quoted or simple)
        m = re.search(r'\bsire(?:s)?\s*name\s*[:\s]+"?([A-Za-z0-9 \-\'&\.]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['SiresName'] = m.group(1).strip()

        # SiresRegistration
        m = re.search(r'\b(?:sire(?:s)?\s*)?registration\s*[:\s]+"?([A-Za-z0-9\-_\/\.]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['SiresRegistration'] = m.group(1).strip()

        return ident if ident else None

    def _extract_sire_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        t = text.lower()

        # direct column mentions
        for col in SIRE_COLUMNS:
            if col.lower() in t:
                return col

        # friendly aliases
        friendly = {
            'sire id': 'SireID',
            'sire name': 'SiresName',
            'sires name': 'SiresName',
            'registration': 'SiresRegistration',
            'sire registration': 'SiresRegistration',
            'color': 'SiresColor',
            'colour': 'SiresColor',
            'sire color': 'SiresColor',
            'sire colour': 'SiresColor',
        }
        for k, v in friendly.items():
            if k in t and v in SIRE_COLUMNS:
                return v

        # recent user context fallback
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in SIRE_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in friendly.items():
                        if k in t2 and v in SIRE_COLUMNS:
                            return v

        # whole-record reads
        if any(w in t for w in ['sire', 'sires', 'sire table', 'sire record', 'registration', 'color', 'colour', 'all', 'everything', 'details', 'info', 'record']):
            return None

        return None

    # ---------- SPECIESBREEDLOOKUP ----------
    def get_user_friendly_field_name_speciesbreed(self, field: str) -> str:
        mapping = {
            'BreedLookupID': 'breed lookup id',
            'breedavailable': 'breed available',
            'SpeciesID': 'species id',
            'Breed': 'breed',
            'Breeddescription': 'breed description',
            'BreedImage': 'breed image',
            'Breedvideo': 'breed video',
            'BreedAnimalID': 'breed animal id',
            'BreedImageCaption': 'breed image caption',
            'BreedImageOrientation': 'breed image orientation',
            'SpeciesRegistrationTypeID': 'species registration type id',
            'MeatBreed': 'meat breed',
            'MilkBreed': 'milk breed',
            'WoolBreed': 'wool breed',
            'EggBreed': 'egg breed',
            'Working': 'working',
            'HoneyBreed': 'honey breed',
        }
        return mapping.get(field, field)

    def _extract_speciesbreed_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Identify a Speciesbreedlookuptable row by:
          - BreedLookupID (PK), or
          - Breed (name) optionally with SpeciesID / SpeciesRegistrationTypeID hints, or
          - BreedAnimalID
        """
        t = original_text

        # Primary key
        m = re.search(r'\bbreed\s*lookup\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            return {'BreedLookupID': int(m.group(1))}

        ident: Dict[str, Any] = {}

        # Breed (quoted or plain)
        m = re.search(r'\bbreed\s*[:\s]+"?([A-Za-z0-9 \-\'&\.]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['Breed'] = m.group(1).strip()

        # SpeciesID
        m = re.search(r'\bspecies\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            ident['SpeciesID'] = int(m.group(1))

        # SpeciesRegistrationTypeID
        m = re.search(r'\bspecies\s*registration\s*type\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            ident['SpeciesRegistrationTypeID'] = int(m.group(1))

        # BreedAnimalID
        m = re.search(r'\bbreed\s*animal\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            ident['BreedAnimalID'] = int(m.group(1))

        return ident if ident else None

    def _extract_speciesbreed_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        t = text.lower()

        # exact column mentions
        for col in SPECIESBREEDLOOKUPTABLE_COLUMNS:
            if col.lower() in t:
                return col

        # friendly aliases
        friendly = {
            'breed lookup id': 'BreedLookupID',
            'available': 'breedavailable',
            'breed available': 'breedavailable',
            'species id': 'SpeciesID',
            'breed': 'Breed',
            'description': 'Breeddescription',
            'breed description': 'Breeddescription',
            'breed image': 'BreedImage',
            'image': 'BreedImage',
            'breed video': 'Breedvideo',
            'video': 'Breedvideo',
            'breed animal id': 'BreedAnimalID',
            'image caption': 'BreedImageCaption',
            'image orientation': 'BreedImageOrientation',
            'species registration type id': 'SpeciesRegistrationTypeID',
            'meat breed': 'MeatBreed',
            'milk breed': 'MilkBreed',
            'wool breed': 'WoolBreed',
            'egg breed': 'EggBreed',
            'working': 'Working',
            'honey breed': 'HoneyBreed',
        }
        for k, v in friendly.items():
            if k in t and v in SPECIESBREEDLOOKUPTABLE_COLUMNS:
                return v

        # look back into recent user messages
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in SPECIESBREEDLOOKUPTABLE_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in friendly.items():
                        if k in t2 and v in SPECIESBREEDLOOKUPTABLE_COLUMNS:
                            return v

        # full-record hints
        if any(w in t for w in ['breed lookup', 'species breed', 'breed image', 'breed video', 'meat breed', 'milk breed', 'wool breed', 'egg breed', 'honey breed', 'all', 'everything', 'details', 'info', 'record']):
            return None

        return None

    # ---------- SPECIESCATEGORY ----------
    def get_user_friendly_field_name_speciescategory(self, field: str) -> str:
        mapping = {
            'SpeciesID': 'species id',
            'SpeciesCategory': 'species category',
            'SpeciesCategoryOrder': 'species category order',
            'SpeciesCategoryID': 'species category id',
            'SpeciesCategoryPlural': 'species category (plural)',
            'QuantityType': 'quantity type',
        }
        return mapping.get(field, field)

    def _extract_speciescategory_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Identify a Speciescategory row by:
          - SpeciesCategoryID (PK), or
          - SpeciesCategory (name) with optional SpeciesID, or
          - SpeciesID alone (may return multiple; your tool should handle)
        """
        t = original_text

        # Primary key
        m = re.search(r'\bspecies\s*category\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            return {'SpeciesCategoryID': int(m.group(1))}

        ident: Dict[str, Any] = {}

        # SpeciesCategory (quoted or simple)
        m = re.search(r'\bspecies\s*category\s*[:\s]+"?([A-Za-z0-9 \-\'&\.]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['SpeciesCategory'] = m.group(1).strip()

        # SpeciesID
        m = re.search(r'\bspecies\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            ident['SpeciesID'] = int(m.group(1))

        return ident if ident else None

    def _extract_speciescategory_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        t = text.lower()

        # exact column mentions
        for col in SPECIESCATEGORY_COLUMNS:
            if col.lower() in t:
                return col

        # friendly aliases
        friendly = {
            'species category id': 'SpeciesCategoryID',
            'category id': 'SpeciesCategoryID',
            'species id': 'SpeciesID',
            'species category': 'SpeciesCategory',
            'category': 'SpeciesCategory',
            'category order': 'SpeciesCategoryOrder',
            'order': 'SpeciesCategoryOrder',
            'plural': 'SpeciesCategoryPlural',
            'category plural': 'SpeciesCategoryPlural',
            'quantity type': 'QuantityType',
        }
        for k, v in friendly.items():
            if k in t and v in SPECIESCATEGORY_COLUMNS:
                return v

        # recent user context fallback
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in SPECIESCATEGORY_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in friendly.items():
                        if k in t2 and v in SPECIESCATEGORY_COLUMNS:
                            return v

        # full-record reads
        if any(w in t for w in ['species category', 'category', 'category order', 'category plural', 'quantity type', 'all', 'everything', 'details', 'info', 'record']):
            return None

        return None

    # ---------- SPECIESCOLORLOOKUP ----------
    def get_user_friendly_field_name_speciescolor(self, field: str) -> str:
        mapping = {
            'SpeciesColorID': 'species color id',
            'SpeciesID': 'species id',
            'SpeciesColor': 'species color',
        }
        return mapping.get(field, field)

    def _extract_speciescolor_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Identify a Speciescolorlookuptable row by:
          - SpeciesColorID (PK), or
          - SpeciesID + SpeciesColor (name)
        """
        t = original_text

        # Primary key
        m = re.search(r'\bspecies\s*color\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            return {'SpeciesColorID': int(m.group(1))}

        ident: Dict[str, Any] = {}

        # SpeciesID
        m = re.search(r'\bspecies\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            ident['SpeciesID'] = int(m.group(1))

        # SpeciesColor (quoted or simple)
        m = re.search(r'\bspecies\s*color\s*[:\s]+"?([A-Za-z0-9 \-\'&\.]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['SpeciesColor'] = m.group(1).strip()

        return ident if ident else None

    def _extract_speciescolor_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        t = text.lower()

        # direct column mentions
        for col in SPECIESCOLORLOOKUPTABLE_COLUMNS:
            if col.lower() in t:
                return col

        # friendly aliases
        friendly = {
            'species color id': 'SpeciesColorID',
            'species id': 'SpeciesID',
            'species color': 'SpeciesColor',
            'color': 'SpeciesColor',   # be careful: may collide with generic Colors domain
            'colour': 'SpeciesColor',
        }
        for k, v in friendly.items():
            if k in t and v in SPECIESCOLORLOOKUPTABLE_COLUMNS:
                return v

        # recent user context fallback
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in SPECIESCOLORLOOKUPTABLE_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in friendly.items():
                        if k in t2 and v in SPECIESCOLORLOOKUPTABLE_COLUMNS:
                            return v

        # whole-record reads
        if any(w in t for w in ['species color', 'species colours', 'species colour', 'all', 'everything', 'details', 'info', 'record']):
            return None

        return None

    # ---------- SPECIESREGISTRATIONTYPELOOKUP ----------
    def get_user_friendly_field_name_speciesregtype(self, field: str) -> str:
        mapping = {
            'SpeciesRegistrationTypeID': 'species registration type id',
            'SpeciesID': 'species id',
            'SpeciesRegistrationType': 'species registration type',
            'country_id': 'country id',
        }
        return mapping.get(field, field)

    def _extract_speciesregtype_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Identify a Speciesregistrationtypelookuptable row by:
          - SpeciesRegistrationTypeID (PK), or
          - SpeciesRegistrationType (name) with optional SpeciesID and/or country_id, or
          - SpeciesID + country_id combo
        """
        t = original_text

        # Primary key
        m = re.search(r'\bspecies\s*registration\s*type\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            return {'SpeciesRegistrationTypeID': int(m.group(1))}

        ident: Dict[str, Any] = {}

        # SpeciesRegistrationType (quoted or simple)
        m = re.search(r'\bspecies\s*registration\s*type\s*[:\s]+"?([A-Za-z0-9 \-\'&\.]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['SpeciesRegistrationType'] = m.group(1).strip()

        # SpeciesID
        m = re.search(r'\bspecies\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            ident['SpeciesID'] = int(m.group(1))

        # country_id
        m = re.search(r'\bcountry\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            ident['country_id'] = int(m.group(1))

        return ident if ident else None

    def _extract_speciesregtype_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        t = text.lower()

        # exact column mentions
        for col in SPECIESREGISTRATIONTYPELOOKUPTABLE_COLUMNS:
            if col.lower() in t:
                return col

        # friendly aliases
        friendly = {
            'registration type id': 'SpeciesRegistrationTypeID',
            'species registration type id': 'SpeciesRegistrationTypeID',
            'species id': 'SpeciesID',
            'registration type': 'SpeciesRegistrationType',
            'species registration type': 'SpeciesRegistrationType',
            'country id': 'country_id',
        }
        for k, v in friendly.items():
            if k in t and v in SPECIESREGISTRATIONTYPELOOKUPTABLE_COLUMNS:
                return v

        # recent user context fallback
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in SPECIESREGISTRATIONTYPELOOKUPTABLE_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in friendly.items():
                        if k in t2 and v in SPECIESREGISTRATIONTYPELOOKUPTABLE_COLUMNS:
                            return v

        # whole-record reads
        if any(w in t for w in ['species registration type', 'registration type', 'reg type', 'all', 'everything', 'details', 'info', 'record']):
            return None

        return None

    # ---------- STATE_PROVINCE ----------
    def get_user_friendly_field_name_stateprov(self, field: str) -> str:
        mapping = {
            'StateIndex': 'state/province id',
            'name': 'state/province name',
            'abbreviation': 'abbreviation',
            'country_id': 'country id',
        }
        return mapping.get(field, field)

    def _extract_stateprov_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Identify a State_province row by:
          - StateIndex (PK), or
          - name (string), optionally with country_id, or
          - abbreviation (string), optionally with country_id
        """
        t = original_text

        # Primary key
        m = re.search(r'\b(?:state|province)\s*index\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            return {'StateIndex': int(m.group(1))}

        ident: Dict[str, Any] = {}

        # name (quoted or simple)
        m = re.search(r'\b(?:state|province)\s*name\s*[:\s]+"?([A-Za-z0-9 \-\'.]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['name'] = m.group(1).strip()
        else:
            m = re.search(r'\b(?:state|province)\s*[:\s]+"?([A-Za-z0-9 \-\'.]+?)"?\b', t, re.IGNORECASE)
            if m:
                ident['name'] = m.group(1).strip()

        # abbreviation
        m = re.search(r'\b(?:state|province)?\s*(?:abbr|abbrev|abbreviation|code)\s*[:\s]+"?([A-Za-z0-9\-]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['abbreviation'] = m.group(1).strip()

        # country_id (varchar, keep as string)
        m = re.search(r'\bcountry\s*id\s*[:\s]+"?([A-Za-z0-9\-_]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['country_id'] = m.group(1).strip()

        return ident if ident else None

    def _extract_stateprov_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        t = text.lower()

        # direct column mentions
        for col in STATE_PROVINCE_COLUMNS:
            if col.lower() in t:
                return col

        # friendly aliases
        friendly = {
            'state index': 'StateIndex',
            'province index': 'StateIndex',
            'state id': 'StateIndex',
            'province id': 'StateIndex',
            'state name': 'name',
            'province name': 'name',
            'name': 'name',
            'abbrev': 'abbreviation',
            'abbreviation': 'abbreviation',
            'state code': 'abbreviation',
            'province code': 'abbreviation',
            'code': 'abbreviation',
            'country id': 'country_id',
            'country': 'country_id',
        }
        for k, v in friendly.items():
            if k in t and v in STATE_PROVINCE_COLUMNS:
                return v

        # recent user context
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in STATE_PROVINCE_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in friendly.items():
                        if k in t2 and v in STATE_PROVINCE_COLUMNS:
                            return v

        # whole-record reads
        if any(w in t for w in ['state', 'province', 'state/province', 'state code', 'province code', 'all', 'everything', 'details', 'info', 'record']):
            return None

        return None

    # ---------- STATES ----------
    def get_user_friendly_field_name_state(self, field: str) -> str:
        mapping = {
            'StateID': 'state id',
            'StateName': 'state name',
            'StateAbbreviation': 'state abbreviation',
            'StateHeaderImage': 'state header image',
            'StateDescription': 'state description',
            'StateFlag': 'state flag',
            'Statebird': 'state bird',
            'StateSeal': 'state seal',
            'Moto': 'motto',
            'Nicknames': 'nicknames',
            'Weatherlink': 'weather link',
            'Governor': 'governor',
            'Senator1': 'senator 1',
            'Senator2': 'senator 2',
        }
        # Rep1..Rep58 -> "representative N"
        if field and field.lower().startswith('rep'):
            try:
                n = int(field[3:])
                return f"representative {n}"
            except Exception:
                pass
        return mapping.get(field, field)

    def _extract_states_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Identify a States row by:
          - StateID (PK), or
          - StateName, or
          - StateAbbreviation
        """
        t = original_text

        # StateID
        m = re.search(r'\bstate\s*id\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            return {'StateID': int(m.group(1))}

        ident: Dict[str, Any] = {}

        # StateAbbreviation (e.g., "CA")
        m = re.search(r'\bstate\s*(?:abbr|abbrev|abbreviation|code)\s*[:\s]+"?([A-Za-z]{2,3})"?\b', t, re.IGNORECASE)
        if m:
            ident['StateAbbreviation'] = m.group(1).strip().upper()

        # StateName
        m = re.search(r'\bstate\s*name\s*[:\s]+"?([A-Za-z \-\'\.]+?)"?\b', t, re.IGNORECASE)
        if m:
            ident['StateName'] = m.group(1).strip()
        else:
            # looser: `state "California"`
            m = re.search(r'\bstate\s*[:\s]+"?([A-Za-z \-\'\.]+?)"?\b', t, re.IGNORECASE)
            if m:
                ident['StateName'] = m.group(1).strip()

        return ident if ident else None

    def _extract_states_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        t = text.lower()

        # direct column mentions
        for col in STATES_COLUMNS:
            if col.lower() in t:
                return col

        # support Rep1..Rep58 via "rep 12", "representative 12"
        m = re.search(r'\brep(?:resentative)?\s*(\d{1,2})\b', t, re.IGNORECASE)
        if m:
            n = int(m.group(1))
            key = f"Rep{n}"
            if key in STATES_COLUMNS:
                return key

        friendly = {
            'state id': 'StateID',
            'state name': 'StateName',
            'name': 'StateName',
            'state abbreviation': 'StateAbbreviation',
            'state code': 'StateAbbreviation',
            'abbrev': 'StateAbbreviation',
            'header image': 'StateHeaderImage',
            'description': 'StateDescription',
            'flag': 'StateFlag',
            'state bird': 'Statebird',
            'bird': 'Statebird',
            'seal': 'StateSeal',
            'motto': 'Moto',
            'nicknames': 'Nicknames',
            'weather link': 'Weatherlink',
            'governor': 'Governor',
            'senator1': 'Senator1',
            'senator 1': 'Senator1',
            'senator2': 'Senator2',
            'senator 2': 'Senator2',
        }
        for k, v in friendly.items():
            if k in t and v in STATES_COLUMNS:
                return v

        # recent user context fallback
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in STATES_COLUMNS:
                        if col.lower() in t2:
                            return col
                    m2 = re.search(r'\brep(?:resentative)?\s*(\d{1,2})\b', t2, re.IGNORECASE)
                    if m2:
                        n2 = int(m2.group(1))
                        key2 = f"Rep{n2}"
                        if key2 in STATES_COLUMNS:
                            return key2
                    for k, v in friendly.items():
                        if k in t2 and v in STATES_COLUMNS:
                            return v

        # whole-record reads
        if any(w in t for w in ['state name', 'state abbreviation', 'state flag', 'governor', 'senator', 'representative', 'states table', 'all', 'everything', 'details', 'info', 'record']):
            return None

        return None

    # ---------- MALEDATA ----------
    def get_user_friendly_field_name_maledata(self, field: str) -> str:
        mapping = {
            'ID': 'male/animal id',
            'StudFee': 'stud fee',
            'Herdsire': 'herdsire',
            'JrHerdsire': 'junior herdsire',
            'JuvenileMale': 'juvenile male',
            'Comments': 'comments',
        }
        return mapping.get(field, field)

    def _extract_maledata_identifier(self, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Identify a Maledata row by:
          - ID (PK) — often the Animal ID this male data belongs to
        """
        t = original_text

        # Accept "male id", "male data id", or generic "id" with male context
        m = re.search(r'\b(?:male\s*data\s*id|male\s*id|animal\s*id|id)\s+(\d+)\b', t, re.IGNORECASE)
        if m:
            return {'ID': int(m.group(1))}

        return None

    def _extract_maledata_field(self, text: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        t = text.lower()

        # direct column mentions
        for col in MALEDATA_COLUMNS:
            if col.lower() in t:
                return col

        # friendly aliases
        friendly = {
            'stud fee': 'StudFee',
            'herdsire': 'Herdsire',
            'jr herdsire': 'JrHerdsire',
            'junior herdsire': 'JrHerdsire',
            'juvenile male': 'JuvenileMale',
            'comments': 'Comments',
        }
        for k, v in friendly.items():
            if k in t and v in MALEDATA_COLUMNS:
                return v

        # recent user context fallback
        if chat_history:
            recent = chat_history[-5:] if len(chat_history) >= 5 else chat_history
            for msg in reversed(recent):
                if msg.get('role') == 'user':
                    t2 = msg.get('content', '').lower()
                    for col in MALEDATA_COLUMNS:
                        if col.lower() in t2:
                            return col
                    for k, v in friendly.items():
                        if k in t2 and v in MALEDATA_COLUMNS:
                            return v

        # whole-record reads
        if any(w in t for w in ['male data', 'stud fee', 'herdsire', 'jr herdsire', 'junior herdsire', 'juvenile male', 'all', 'everything', 'details', 'info', 'record']):
            return None

        return None

    
    # ---------- MAIN ROUTER ----------
    def generate_reply(self, agent, messages):
        user_input = None
        conversation_history = []
        full_content = messages[-1]['content']
        
        if f'{self.id_label}:' in full_content:
            user_input, conversation_history, user_id = self.parse_enhanced_message(full_content)
            if not user_id or not user_id.isdigit():
                return "❌ **User ID not found!** I cannot process user data requests without a valid user ID. Please ensure you're logged in with a valid session."
            people_id = int(user_id)
        else:
            user_input = full_content
            return "❌ **User ID not found!** I cannot process user data requests without a valid user ID. Please ensure you're logged in with a valid session."
        
        if not isinstance(user_input, str):
            user_input = str(user_input)
        
        user_input_lower = user_input.lower().strip()
        is_confirmation = any(word in user_input_lower for word in ['yes','confirm','ok','sure','proceed','do it','update it'])
        is_cancellation = any(word in user_input_lower for word in ['no','cancel','abort','stop','nevermind','never mind'])
        
        # ----- Confirmations -----
        if is_confirmation:
            # PEOPLE
            if self.pending_create:
                data = self.pending_create
                result = people_tool('create', data=data)
                self.pending_create = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Profile created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
                 
            if self.pending_update:
                field, value, pid = self.pending_update
                result = people_tool('update', identifier={'PeopleID': pid}, data={field: value})
                self.pending_update = None
                if "Updated" in str(result):
                    return f"✅ **Successfully updated!** Your {self.get_user_friendly_field_name(field)} has been changed to **{value}**"
                return f"❌ **Update failed:** {result}"
                
            if self.pending_delete:
                field, pid = self.pending_delete
                result = people_tool('update', identifier={'PeopleID': pid}, data={field: None})
                self.pending_delete = None
                if "Updated" in str(result):
                    return f"✅ **Successfully cleared!** Your {self.get_user_friendly_field_name(field)} has been removed."
                return f"❌ **Clear failed:** {result}"

            # ANIMALS
            if self.pending_create_animal:
                data = self.pending_create_animal
                result = animals_tool('create', data=data)
                self.pending_create_animal = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Animal profile created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_animal:
                field, value, identifier = self.pending_update_animal
                result = animals_tool('update', identifier=identifier, data={field: value})
                self.pending_update_animal = None
                if "Updated" in str(result):
                    return f"✅ **Animal updated!** {self.get_user_friendly_field_name_animal(field).title()} set to **{value}**."
                return f"❌ **Animal update failed:** {result}"
                
            if self.pending_delete_animal:
                field, identifier = self.pending_delete_animal
                result = animals_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_animal = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Animal field cleared!** {self.get_user_friendly_field_name_animal(field).title()} removed."
                return f"❌ **Animal clear failed:** {result}"

            # ANCESTORS
            if self.pending_create_ancestor:
                data = self.pending_create_ancestor
                result = ancestors_tool('create', data=data)
                self.pending_create_ancestor = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Ancestor profile created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_ancestor:
                field, value, identifier = self.pending_update_ancestor
                result = ancestors_tool('update', identifier=identifier, data={field: value})
                self.pending_update_ancestor = None
                if "Updated" in str(result):
                    return f"✅ **Ancestor updated!** {self.get_user_friendly_field_name_ancestor(field).title()} set to **{value}**."
                return f"❌ **Ancestor update failed:** {result}"
                
            if self.pending_delete_ancestor:
                field, identifier = self.pending_delete_ancestor
                result = ancestors_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_ancestor = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Ancestor field cleared!** {self.get_user_friendly_field_name_ancestor(field).title()} removed."
                return f"❌ **Ancestor clear failed:** {result}"

            # ANCESTRY PERCENTS
            if self.pending_create_ancestry_percent:
                data = self.pending_create_ancestry_percent
                result = ancestrypercents_tool('create', data=data)
                self.pending_create_ancestry_percent = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Ancestry percent created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_percent:
                field, value, identifier = self.pending_update_percent
                result = ancestrypercents_tool('update', identifier=identifier, data={field: value})
                self.pending_update_percent = None
                if "Updated" in str(result):
                    return f"✅ **Ancestry percent updated!** {self.get_user_friendly_field_name_percent(field).title()} set to **{value}**."
                return f"❌ **Ancestry percent update failed:** {result}"
                
            if self.pending_delete_percent:
                field, identifier = self.pending_delete_percent
                result = ancestrypercents_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_percent = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Ancestry percent cleared!** {self.get_user_friendly_field_name_percent(field).title()} removed."
                return f"❌ **Ancestry percent clear failed:** {result}"

            # ANIMAL REGISTRATION
            if self.pending_create_animal_registration:
                data = self.pending_create_animal_registration
                result = animalregistration_tool('create', data=data)
                self.pending_create_animal_registration = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Animal Registration profile created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_registration:
                field, value, identifier = self.pending_update_registration
                result = animalregistration_tool('update', identifier=identifier, data={field: value})
                self.pending_update_registration = None
                if "Updated" in str(result):
                    return f"✅ **Registration updated!** {self.get_user_friendly_field_name_registration(field).title()} set to **{value}**."
                return f"❌ **Registration update failed:** {result}"
                
            if self.pending_delete_registration:
                field, identifier = self.pending_delete_registration
                result = animalregistration_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_registration = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Registration field cleared!** {self.get_user_friendly_field_name_registration(field).title()} removed."
                return f"❌ **Registration clear failed:** {result}"

            # ANIMAL STATS
            if self.pending_create_animal_stats:
                data = self.pending_create_animal_stats
                result = animalstats_tool('create', data=data)
                self.pending_create_animal_stats = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Animal Stats profile created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_stats:
                field, value, identifier = self.pending_update_stats
                result = animalstats_tool('update', identifier=identifier, data={field: value})
                self.pending_update_stats = None
                if "Updated" in str(result):
                    return f"✅ **Animal stats updated!** {self.get_user_friendly_field_name_stats(field).title()} set to **{value}**."
                return f"❌ **Animal stats update failed:** {result}"
                
            if self.pending_delete_stats:
                field, identifier = self.pending_delete_stats
                result = animalstats_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_stats = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Animal stats field cleared!** {self.get_user_friendly_field_name_stats(field).title()} removed."
                return f"❌ **Animal stats clear failed:** {result}"

            # AWARDS
            if self.pending_create_awards:
                data = self.pending_create_awards
                result = awards_tool('create', data=data)
                self.pending_create_awards = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Awards profile created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_awards:
                field, value, identifier = self.pending_update_awards
                result = awards_tool('update', identifier=identifier, data={field: value})
                self.pending_update_awards = None
                if "Updated" in str(result):
                    return f"✅ **Awards updated!** {self.get_user_friendly_field_name_awards(field).title()} set to **{value}**."
                return f"❌ **Awards update failed:** {result}"
                
            if self.pending_delete_awards:
                field, identifier = self.pending_delete_awards
                result = awards_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_awards = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Awards field cleared!** {self.get_user_friendly_field_name_awards(field).title()} removed."
                return f"❌ **Awards clear failed:** {result}"

            # ASSOCIATIONS
            if self.pending_create_associations:
                data = self.pending_create_associations
                result = associations_tool('create', data=data)
                self.pending_create_associations = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Association created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_association:
                field, value, identifier = self.pending_update_association
                result = associations_tool('update', identifier=identifier, data={field: value})
                self.pending_update_association = None
                if "Updated" in str(result):
                    return f"✅ **Association updated!** {self.get_user_friendly_field_name_association(field).title()} set to **{value}**."
                return f"❌ **Association update failed:** {result}"
                
            if self.pending_delete_association:
                field, identifier = self.pending_delete_association
                result = associations_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_association = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Association field cleared!** {self.get_user_friendly_field_name_association(field).title()} removed."
                return f"❌ **Association clear failed:** {result}"

            # ASSOCIATION MEMBERS
            if self.pending_create_associationmembers:
                data = self.pending_create_associationmembers
                result = associationmembers_tool('create', data=data)
                self.pending_create_associationmembers = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Association member created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_associationmember:
                field, value, identifier = self.pending_update_associationmember
                result = associationmembers_tool('update', identifier=identifier, data={field: value})
                self.pending_update_associationmember = None
                if "Updated" in str(result):
                    return f"✅ **Association member updated!** {self.get_user_friendly_field_name_associationmember(field).title()} set to **{value}**."
                return f"❌ **Association member update failed:** {result}"
                
            if self.pending_delete_associationmember:
                field, identifier = self.pending_delete_associationmember
                result = associationmembers_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_associationmember = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Association member field cleared!** {self.get_user_friendly_field_name_associationmember(field).title()} removed."
                return f"❌ **Association member clear failed:** {result}"
                        
            # PEOPLETITLELOOKUP
            if self.pending_create_peopletitle:
                data = self.pending_create_peopletitle
                result = people_tool('create', data=data)
                self.pending_create_peopletitle = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Profile created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
            
            if self.pending_update_peopletitle:
                field, value, identifier = self.pending_update_peopletitle
                result = peopletitlelookup_tool('update', identifier=identifier, data={field: value})
                self.pending_update_peopletitle = None
                if "Updated" in str(result):
                    return f"✅ **People title updated!** {self.get_user_friendly_field_name_peopletitle(field).title()} set to **{value}**."
                return f"❌ **People title update failed:** {result}"

            if self.pending_delete_peopletitle:
                field, identifier = self.pending_delete_peopletitle
                result = peopletitlelookup_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_peopletitle = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **People title field cleared!** {self.get_user_friendly_field_name_peopletitle(field).title()} removed."
                return f"❌ **People title clear failed:** {result}"

            # BUSINESS
            if self.pending_create_business:
                data = self.pending_create_business
                result = business_tool('create', data=data)
                self.pending_create_business = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Business created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_business:
                field, value, identifier = self.pending_update_business
                result = business_tool('update', identifier=identifier, data={field: value})
                self.pending_update_business = None
                if "Updated" in str(result):
                    return f"✅ **Business updated!** {self.get_user_friendly_field_name_business(field).title()} set to **{value}**."
                return f"❌ **Business update failed:** {result}"
                
            if self.pending_delete_business:
                field, identifier = self.pending_delete_business
                result = business_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_business = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Business field cleared!** {self.get_user_friendly_field_name_business(field).title()} removed."
                return f"❌ **Business clear failed:** {result}"
        
            # COLORLOOKUP
            if self.pending_create_colorlookup:
                data = self.pending_create_colorlookup
                result = colorlookup_tool('create', data=data)
                self.pending_create_colorlookup = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Color lookup created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_color:
                field, value, identifier = self.pending_update_color
                result = colorlookup_tool('update', identifier=identifier, data={field: value})
                self.pending_update_color = None
                if "Updated" in str(result):
                    return f"✅ **Color lookup updated!** {self.get_user_friendly_field_name_color(field).title()} set to **{value}**."
                return f"❌ **Color lookup update failed:** {result}"
                
            if self.pending_delete_color:
                field, identifier = self.pending_delete_color
                result = colorlookup_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_color = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Color lookup field cleared!** {self.get_user_friendly_field_name_color(field).title()} removed."
                return f"❌ **Color lookup clear failed:** {result}"

            # COLORS
            if self.pending_create_colors:
                data = self.pending_create_colors
                result = colors_tool('create', data=data)
                self.pending_create_colors = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Colors created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_colors:
                field, value, identifier = self.pending_update_colors
                result = colors_tool('update', identifier=identifier, data={field: value})
                self.pending_update_colors = None
                if "Updated" in str(result):
                    return f"✅ **Colors updated!** {self.get_user_friendly_field_name_colors(field).title()} set to **{value}**."
                return f"❌ **Colors update failed:** {result}"

            if self.pending_delete_colors:
                field, identifier = self.pending_delete_colors
                result = colors_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_colors = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Colors field cleared!** {self.get_user_friendly_field_name_colors(field).title()} removed."
                return f"❌ **Colors clear failed:** {result}"

            # COUNTRY
            if self.pending_create_country:
                data = self.pending_create_country
                result = country_tool('create', data=data)
                self.pending_create_country = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Country created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_country:
                field, value, identifier = self.pending_update_country
                # Coerce boolean-ish inputs for Active
                if field == 'Active':
                    if isinstance(value, str):
                        value_norm = value.strip().lower()
                        value = 1 if value_norm in ['1', 'true', 'yes', 'y', 'on', 'active'] else 0 if value_norm in ['0','false','no','n','off','inactive'] else value
                result = country_tool('update', identifier=identifier, data={field: value})
                self.pending_update_country = None
                if "Updated" in str(result):
                    return f"✅ **Country updated!** {self.get_user_friendly_field_name_country(field).title()} set to **{value}**."
                return f"❌ **Country update failed:** {result}"

            if self.pending_delete_country:
                field, identifier = self.pending_delete_country
                result = country_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_country = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Country field cleared!** {self.get_user_friendly_field_name_country(field).title()} removed."
                return f"❌ **Country clear failed:** {result}"

            # FIBER
            if self.pending_create_fiber:
                data = self.pending_create_fiber
                result = fiber_tool('create', data=data)
                self.pending_create_fiber = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Fiber created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_fiber:
                field, value, identifier = self.pending_update_fiber

                # Optional coercions for numeric date parts
                if field in ['SampleDateMonth', 'SampleDateDay', 'SampleDateYear']:
                    try:
                        value = int(value)
                    except Exception:
                        pass

                result = fiber_tool('update', identifier=identifier, data={field: value})
                self.pending_update_fiber = None
                if "Updated" in str(result):
                    return f"✅ **Fiber updated!** {self.get_user_friendly_field_name_fiber(field).title()} set to **{value}**."
                return f"❌ **Fiber update failed:** {result}"

            if self.pending_delete_fiber:
                field, identifier = self.pending_delete_fiber
                result = fiber_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_fiber = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Fiber field cleared!** {self.get_user_friendly_field_name_fiber(field).title()} removed."
                return f"❌ **Fiber clear failed:** {result}"

            # SIRE
            if self.pending_create_sire:
                data = self.pending_create_sire
                result = sire_tool('create', data=data)
                self.pending_create_sire = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Sire created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_sire:
                field, value, identifier = self.pending_update_sire
                result = sire_tool('update', identifier=identifier, data={field: value})
                self.pending_update_sire = None
                if "Updated" in str(result):
                    return f"✅ **Sire updated!** {self.get_user_friendly_field_name_sire(field).title()} set to **{value}**."
                return f"❌ **Sire update failed:** {result}"

            if self.pending_delete_sire:
                field, identifier = self.pending_delete_sire
                result = sire_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_sire = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Sire field cleared!** {self.get_user_friendly_field_name_sire(field).title()} removed."
                return f"❌ **Sire clear failed:** {result}"
 
            # SPECIESBREEDLOOKUP
            if self.pending_create_speciesbreed:
                data = self.pending_create_speciesbreed
                result = speciesbreedlookuptable_tool('create', data=data)
                self.pending_create_speciesbreed = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Species breed created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_speciesbreed:
                field, value, identifier = self.pending_update_speciesbreed

                # Coerce likely numeric/boolean-ish fields
                int_fields = {'BreedLookupID','SpeciesID','BreedAnimalID','SpeciesRegistrationTypeID','Working'}
                tiny_fields = {'breedavailable','MeatBreed','MilkBreed','WoolBreed','EggBreed','HoneyBreed'}
                if field in int_fields:
                    try: value = int(value)
                    except Exception: pass
                if field in tiny_fields and isinstance(value, str):
                    v = value.strip().lower()
                    value = 1 if v in ['1','true','yes','y','on','available','meat','milk','wool','egg','honey','working'] else 0 if v in ['0','false','no','n','off','unavailable'] else value

                result = speciesbreedlookuptable_tool('update', identifier=identifier, data={field: value})
                self.pending_update_speciesbreed = None
                if "Updated" in str(result):
                    return f"✅ **Species breed updated!** {self.get_user_friendly_field_name_speciesbreed(field).title()} set to **{value}**."
                return f"❌ **Species breed update failed:** {result}"

            if self.pending_delete_speciesbreed:
                field, identifier = self.pending_delete_speciesbreed
                result = speciesbreedlookuptable_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_speciesbreed = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Species breed field cleared!** {self.get_user_friendly_field_name_speciesbreed(field).title()} removed."
                return f"❌ **Species breed clear failed:** {result}"

            # SPECIESCATEGORY
            if self.pending_create_speciescategory:
                data = self.pending_create_speciescategory
                result = speciescategory_tool('create', data=data)
                self.pending_create_speciescategory = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Species category created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_speciescategory:
                field, value, identifier = self.pending_update_speciescategory

                # Coerce ints where sensible
                if field in ['SpeciesID', 'SpeciesCategoryOrder', 'SpeciesCategoryID']:
                    try:
                        value = int(value)
                    except Exception:
                        pass

                result = speciescategory_tool('update', identifier=identifier, data={field: value})
                self.pending_update_speciescategory = None
                if "Updated" in str(result):
                    return f"✅ **Species category updated!** {self.get_user_friendly_field_name_speciescategory(field).title()} set to **{value}**."
                return f"❌ **Species category update failed:** {result}"

            if self.pending_delete_speciescategory:
                field, identifier = self.pending_delete_speciescategory
                result = speciescategory_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_speciescategory = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Species category field cleared!** {self.get_user_friendly_field_name_speciescategory(field).title()} removed."
                return f"❌ **Species category clear failed:** {result}"

            # SPECIESCOLORLOOKUP
            if self.pending_create_speciescolor:
                data = self.pending_create_speciescolor
                result = speciescolorlookuptable_tool('create', data=data)
                self.pending_create_speciescolor = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Species color created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_speciescolor:
                field, value, identifier = self.pending_update_speciescolor
                if field in ['SpeciesColorID', 'SpeciesID']:
                    try:
                        value = int(value)
                    except Exception:
                        pass
                result = speciescolorlookuptable_tool('update', identifier=identifier, data={field: value})
                self.pending_update_speciescolor = None
                if "Updated" in str(result):
                    return f"✅ **Species color updated!** {self.get_user_friendly_field_name_speciescolor(field).title()} set to **{value}**."
                return f"❌ **Species color update failed:** {result}"

            if self.pending_delete_speciescolor:
                field, identifier = self.pending_delete_speciescolor
                result = speciescolorlookuptable_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_speciescolor = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Species color field cleared!** {self.get_user_friendly_field_name_speciescolor(field).title()} removed."
                return f"❌ **Species color clear failed:** {result}"

            # SPECIESREGISTRATIONTYPELOOKUP
            if self.pending_create_speciesregtype:
                data = self.pending_create_speciesregtype
                result = speciesregistrationtypelookuptable_tool('create', data=data)
                self.pending_create_speciesregtype = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Species registration type created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_speciesregtype:
                field, value, identifier = self.pending_update_speciesregtype

                # Coerce ints where appropriate
                if field in ['SpeciesRegistrationTypeID', 'SpeciesID', 'country_id']:
                    try:
                        value = int(value)
                    except Exception:
                        pass

                result = speciesregistrationtypelookuptable_tool('update', identifier=identifier, data={field: value})
                self.pending_update_speciesregtype = None
                if "Updated" in str(result):
                    return f"✅ **Species registration type updated!** {self.get_user_friendly_field_name_speciesregtype(field).title()} set to **{value}**."
                return f"❌ **Species registration type update failed:** {result}"

            if self.pending_delete_speciesregtype:
                field, identifier = self.pending_delete_speciesregtype
                result = speciesregistrationtypelookuptable_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_speciesregtype = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Species registration type field cleared!** {self.get_user_friendly_field_name_speciesregtype(field).title()} removed."
                return f"❌ **Species registration type clear failed:** {result}"

            # STATE_PROVINCE
            if self.pending_create_stateprov:
                data = self.pending_create_stateprov
                result = state_province_tool('create', data=data)
                self.pending_create_stateprov = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **State/Province created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
            
            if self.pending_update_stateprov:
                field, value, identifier = self.pending_update_stateprov

                # Coerce integers for PK if needed
                if field in ['StateIndex']:
                    try:
                        value = int(value)
                    except Exception:
                        pass  # leave as-is if user provided non-numeric

                result = state_province_tool('update', identifier=identifier, data={field: value})
                self.pending_update_stateprov = None
                if "Updated" in str(result):
                    return f"✅ **State/Province updated!** {self.get_user_friendly_field_name_stateprov(field).title()} set to **{value}**."
                return f"❌ **State/Province update failed:** {result}"

            if self.pending_delete_stateprov:
                field, identifier = self.pending_delete_stateprov
                result = state_province_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_stateprov = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **State/Province field cleared!** {self.get_user_friendly_field_name_stateprov(field).title()} removed."
                return f"❌ **State/Province clear failed:** {result}"

            # STATES
            if self.pending_create_state:
                data = self.pending_create_state
                result = states_tool('create', data=data)
                self.pending_create_state = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **State created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_state:
                field, value, identifier = self.pending_update_state
                if field == 'StateID':
                    try:
                        value = int(value)
                    except Exception:
                        pass
                result = states_tool('update', identifier=identifier, data={field: value})
                self.pending_update_state = None
                if "Updated" in str(result):
                    return f"✅ **State updated!** {self.get_user_friendly_field_name_state(field).title()} set to **{value}**."
                return f"❌ **State update failed:** {result}"

            if self.pending_delete_state:
                field, identifier = self.pending_delete_state
                result = states_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_state = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **State field cleared!** {self.get_user_friendly_field_name_state(field).title()} removed."
                return f"❌ **State clear failed:** {result}"

            # MALEDATA
            if self.pending_create_maledata:
                data = self.pending_create_maledata
                result = maledata_tool('create', data=data)
                self.pending_create_maledata = None
                if "Created" in str(result) or "Inserted" in str(result) or "OK" in str(result):
                    return "✅ **Male profile created!** Your record has been added."
                return f"❌ **Create failed:** {result}"
        
            if self.pending_update_maledata:
                field, value, identifier = self.pending_update_maledata

                # Coerce boolean-ish smallints (0/1) for status flags
                flag_fields = {'Herdsire', 'JrHerdsire', 'JuvenileMale'}
                if field in flag_fields and isinstance(value, str):
                    v = value.strip().lower()
                    if v in ['1','true','yes','y','on','enabled']:
                        value = 1
                    elif v in ['0','false','no','n','off','disabled']:
                        value = 0
                    elif v.isdigit():
                        value = int(v)

                # ID can be int when updating (rare)
                if field == 'ID':
                    try: value = int(value)
                    except Exception: pass

                result = maledata_tool('update', identifier=identifier, data={field: value})
                self.pending_update_maledata = None
                if "Updated" in str(result):
                    return f"✅ **Male data updated!** {self.get_user_friendly_field_name_maledata(field).title()} set to **{value}**."
                return f"❌ **Male data update failed:** {result}"

            if self.pending_delete_maledata:
                field, identifier = self.pending_delete_maledata
                result = maledata_tool('update', identifier=identifier, data={field: None})
                self.pending_delete_maledata = None
                if "Updated" in str(result) or "Deleted" in str(result):
                    return f"✅ **Male data field cleared!** {self.get_user_friendly_field_name_maledata(field).title()} removed."
                return f"❌ **Male data clear failed:** {result}"

            return "❌ I don't have a pending operation to confirm. Please specify what you want to update or clear."

           
        # ----- Cancellations -----
        if is_cancellation:
            cleared = False
            if self.pending_update: self.pending_update=None; cleared=True
            if self.pending_delete: self.pending_delete=None; cleared=True
            if self.pending_update_animal: self.pending_update_animal=None; cleared=True
            if self.pending_delete_animal: self.pending_delete_animal=None; cleared=True
            if self.pending_update_ancestor: self.pending_update_ancestor=None; cleared=True
            if self.pending_delete_ancestor: self.pending_delete_ancestor=None; cleared=True
            if self.pending_update_percent: self.pending_update_percent=None; cleared=True
            if self.pending_delete_percent: self.pending_delete_percent=None; cleared=True
            if self.pending_update_registration: self.pending_update_registration=None; cleared=True
            if self.pending_delete_registration: self.pending_delete_registration=None; cleared=True
            if self.pending_update_stats: self.pending_update_stats=None; cleared=True
            if self.pending_delete_stats: self.pending_delete_stats=None; cleared=True
            if self.pending_update_awards: self.pending_update_awards=None; cleared=True
            if self.pending_delete_awards: self.pending_delete_awards=None; cleared=True
            if self.pending_update_association: self.pending_update_association=None; cleared=True
            if self.pending_delete_association: self.pending_delete_association=None; cleared=True
            if self.pending_update_associationmember: self.pending_update_associationmember=None; cleared=True
            if self.pending_delete_associationmember: self.pending_delete_associationmember=None; cleared=True
            if self.pending_update_business: self.pending_update_business=None; cleared=True
            if self.pending_delete_business: self.pending_delete_business=None; cleared=True
            if self.pending_update_color: self.pending_update_color=None; cleared=True
            if self.pending_delete_color: self.pending_delete_color=None; cleared=True
            if self.pending_update_colors: self.pending_update_colors = None; cleared = True
            if self.pending_delete_colors: self.pending_delete_colors = None; cleared = True
            if self.pending_update_country: self.pending_update_country = None; cleared = True
            if self.pending_delete_country: self.pending_delete_country = None; cleared = True
            if self.pending_update_fiber: self.pending_update_fiber = None; cleared = True
            if self.pending_delete_fiber: self.pending_delete_fiber = None; cleared = True
            if self.pending_update_peopletitle: self.pending_update_peopletitle = None; cleared = True
            if self.pending_delete_peopletitle: self.pending_delete_peopletitle = None; cleared = True
            if self.pending_update_sire: self.pending_update_sire = None; cleared = True
            if self.pending_delete_sire: self.pending_delete_sire = None; cleared = True
            if self.pending_update_speciesbreed: self.pending_update_speciesbreed = None; cleared = True
            if self.pending_delete_speciesbreed: self.pending_delete_speciesbreed = None; cleared = True
            if self.pending_update_speciescategory: self.pending_update_speciescategory = None; cleared = True
            if self.pending_delete_speciescategory: self.pending_delete_speciescategory = None; cleared = True
            if self.pending_update_speciescolor: self.pending_update_speciescolor = None; cleared = True
            if self.pending_delete_speciescolor: self.pending_delete_speciescolor = None; cleared = True
            if self.pending_update_speciesregtype: self.pending_update_speciesregtype = None; cleared = True
            if self.pending_delete_speciesregtype: self.pending_delete_speciesregtype = None; cleared = True
            if self.pending_update_stateprov: self.pending_update_stateprov = None; cleared = True
            if self.pending_delete_stateprov: self.pending_delete_stateprov = None; cleared = True
            if self.pending_update_state: self.pending_update_state = None; cleared = True
            if self.pending_delete_state: self.pending_delete_state = None; cleared = True
            if self.pending_update_maledata: self.pending_update_maledata = None; cleared = True
            if self.pending_delete_maledata: self.pending_delete_maledata = None; cleared = True
            return "❌ **Operation cancelled.** No changes made." if cleared else "❌ No operation was pending to cancel."
        
        # ----- Domain routing -----
        t = user_input.lower()
        # cues
        associationmembers_cues = ['association member', 'member position', 'access level', 'favorite', 'membership', 'member id']
        association_cues = ['association', 'acronym', 'registry', 'association name', 'facebook', 'instagram', 'linkedin', 'pinterest', 'youtube', 'truth social', 'website', 'email', 'address', 'toll free', 'fax', 'association type']
        awards_cues = ['award', 'awards', 'show', 'placing', 'judge', 'class', 'show level', 'award year', 'show year']
        animalstats_cues = ['stats', 'stat ', 'stat date', 'statistics', 'traffic', 'views', 'page views', 'website name', 'website id']
        animalregistration_cues = ['registration', 'reg number', 'registration number', 'regtype', 'reg type', 'papers', 'paperwork']
        ancestrypercents_cues = ['percent', 'peruvian', 'bolivian', 'chilean', 'accoyo', 'unknown other', 'unknown/other', 'ancestry percent', 'percents']
        ancestor_cues = ['ancestor','ancestors','lineage','pedigree','sire','dam','claa','ari','bloodline']
        animal_cues = ['animal','breed','lot','microchip','stud','herd','gaited','warmblooded','temperment','temperament','owner','stallion','mare','markings']
        business_cues = ['business', 'company', 'brand', 'store', 'business name', 'business email', 'business hours', 'business website', 'business logo', 'business phone', 'acronym']
        colorlookup_cues = ['color', 'colour', 'abbrev', 'abbreviation', 'color group', 'colour group', 'judging', 'judging type', 'breed', 'lookup']
        colors_cues = ['colors', 'colours', 'palette', 'swatch', 'color1', 'color 1', 'colour1', 'colour 1', 'color2', 'color 2', 'colour2', 'colour 2', 'color3', 'color 3', 'colour3', 'colour 3','color4', 'color 4', 'colour4', 'colour 4', 'color5', 'color 5', 'colour5', 'colour 5']
        country_cues = ['country', 'iso code', 'currency', 'currency code', 'paycode', 'pay code', 'region', 'province title']
        fiber_cues = ['fiber', 'fibre', 'sample date', 'staple length', 'crimp', 'histogram', 'shear weight', 'blanket weight', 'average', 'standard deviation', 'cov', 'comfort factor']
        peopletitle_cues = ['people title', 'title', 'title id', 'peopletitle']
        sire_cues = ['sire table', 'sire record', 'sire id', 'sire name', 'sire registration', 'siresname', 'sires registration']
        speciesbreedlookup_cues = [ 'breed lookup', 'species breed', 'breed image', 'breed video', 'meat breed', 'milk breed', 'wool breed', 'egg breed', 'honey breed', 'breed available', 'breedlookupid']
        speciescategory_cues = ['species category', 'category plural', 'category order', 'quantity type', 'species category id']
        speciescolor_cues = ['species color', 'species colours', 'species colour', 'species color id']
        speciesregtype_cues = [
            'species registration type', 'registration type id', 'species reg type', 'reg type'
        ]
        stateprov_cues = [
            'state index', 'province index', 'state name', 'province name',
            'state code', 'province code', 'state/province', 'state_province'
        ]
        states_cues = [
            'states table', 'state id', 'state name', 'state abbreviation', 'state code',
            'state flag', 'state header image', 'state description', 'state bird', 'state seal',
            'governor', 'senator', 'representative', 'weather link'
        ]
        maledata_cues = ['male data', 'stud fee', 'herdsire', 'jr herdsire', 'junior herdsire', 'juvenile male']

        is_maledata = any(c in t for c in maledata_cues) and not (
            is_awards or is_animalstats or is_animalregistration or is_ancestrypercents or is_ancestor
            or is_association or is_associationmembers or is_animal
        )
        is_states = any(c in t for c in states_cues) and not (
            is_awards or is_animalstats or is_animalregistration or is_ancestrypercents or is_ancestor
            or is_association or is_associationmembers or is_animal
        )
        is_stateprov = any(c in t for c in stateprov_cues) and not (
            is_awards or is_animalstats or is_animalregistration or is_ancestrypercents or is_ancestor
            or is_association or is_associationmembers or is_animal
        )
        is_speciesregtype = any(c in t for c in speciesregtype_cues) and not (
            is_awards or is_animalstats or is_animalregistration or is_ancestrypercents or is_ancestor
            or is_association or is_associationmembers or is_animal
        )
        is_speciescolor = any(c in t for c in speciescolor_cues) and not (
            is_awards or is_animalstats or is_animalregistration or is_ancestrypercents or is_ancestor
            or is_association or is_associationmembers or is_animal
        )
        is_speciescategory = any(c in t for c in speciescategory_cues) and not (is_awards or is_animalstats or is_animalregistration or is_ancestrypercents or is_ancestor or is_association or is_associationmembers or is_animal)
        is_speciesbreedlookup = any(c in t for c in speciesbreedlookup_cues) and not (is_awards or is_animalstats or is_animalregistration or is_ancestrypercents or is_ancestor or is_association or is_associationmembers or is_animal)
        is_sire = any(c in t for c in sire_cues) and not (is_awards or is_animalstats or is_animalregistration or is_ancestrypercents or is_association or is_associationmembers or is_animal)
        is_peopletitle = any(c in t for c in peopletitle_cues) and not (is_awards or is_animalstats or is_animalregistration or is_ancestrypercents or is_ancestor or is_association or is_associationmembers or is_animal)
        is_fiber = any(c in t for c in fiber_cues) and not (is_awards or is_animalstats or is_animalregistration or is_ancestrypercents or is_ancestor or is_association or is_associationmembers or is_animal)
        is_country = any(c in t for c in country_cues) and not (is_awards or is_animalstats or is_animalregistration or is_ancestrypercents or is_ancestor or is_association or is_associationmembers or is_animal)
        is_colors = any(c in t for c in colors_cues) and not (is_awards or is_animalstats or is_animalregistration or is_ancestrypercents or is_ancestor or is_association or is_associationmembers or is_animal)
        is_colorlookup = any(c in t for c in colorlookup_cues) and not (is_awards or is_animalstats or is_animalregistration or is_ancestrypercents or is_ancestor or is_association or is_associationmembers or is_animal)
        is_business = any(c in t for c in business_cues) and not (is_association or is_associationmembers or is_awards or is_animalstats or is_animalregistration or is_ancestrypercents or is_ancestor or is_animal)
        is_associationmembers = any(c in t for c in associationmembers_cues)
        is_association = (any(c in t for c in association_cues) and not is_associationmembers)
        is_awards = any(c in t for c in awards_cues) and not (is_association or is_associationmembers)
        is_animalstats = any(c in t for c in animalstats_cues) and not (is_awards or is_association or is_associationmembers)
        is_animalregistration = any(c in t for c in animalregistration_cues) and not (is_awards or is_animalstats or is_association or is_associationmembers)
        is_ancestrypercents = any(c in t for c in ancestrypercents_cues) and not (is_awards or is_animalstats or is_animalregistration or is_association or is_associationmembers)
        is_ancestor = any(c in t for c in ancestor_cues) and not (is_awards or is_animalstats or is_animalregistration or is_ancestrypercents or is_association or is_associationmembers)
        is_animal = any(c in t for c in animal_cues) and not (is_awards or is_animalstats or is_animalregistration or is_ancestrypercents or is_ancestor or is_association or is_associationmembers)

        # ----- Maledata flow -----
        if is_maledata:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_maledata_identifier(user_input)
            field = self._extract_maledata_field(user_input, conversation_history)

            if action == "create":
                maledata_field_map = {
                    'male id': 'MaleID', 'bull id': 'MaleID', 'id': 'MaleID',
                    'name': 'MaleName', 'male name': 'MaleName', 'bull name': 'MaleName',
                    'registration': 'Registration', 'reg number': 'Registration',
                    'registration number': 'Registration', 'reg': 'Registration',
                    'birthdate': 'BirthDate', 'dob': 'BirthDate', 'date of birth': 'BirthDate',
                    'color': 'Color', 'colour': 'Color','status': 'Status','breed id': 'BreedID', 'breed': 'BreedID',
                    'business id': 'BusinessID', 'owner business id': 'BusinessID'
                    }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=maledata_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                        "📝 *Create new Male (Bull) record*\n\n"
                        "Tell me the fields to add — for example:\n"
                        "create male name: Rocky, registration: 112255, color: black, breed id: 5\n\n"
                        "You can also paste JSON/Python dict like:\n"
                        "{\"MaleName\": \"Rocky\", \"Registration\": \"112255\", \"Color\": \"Black\"}"
                      )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                       data[k] = data[k].strip()

                preview = "\n".join(f"- *{self.get_user_friendly_field_name(k).title()}*: {v}"
                    for k, v in data.items())

                self.pending_create_maledata = data

                return (
                     "🆕 *Confirm Create (MaleData)*\n\n"
                     f"You’re about to create a new male record with:\n{preview}\n\n"
                      "Confirm with *'yes'* or cancel with *'no'*."
                    )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which male data record (e.g., 'male id 42' or 'animal id 42')."
                result = maledata_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_maledata(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in ['ID','StudFee','Herdsire','JrHerdsire','JuvenileMale','Comments'] if k in MALEDATA_COLUMNS]
                        lines = ["🧬 **Male Data Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None, ""]:
                                label = self.get_user_friendly_field_name_maledata(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in MALEDATA_COLUMNS if k not in show_keys and record.get(k) not in [None,""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching male data record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which male data row to update. Include 'male id <n>' or 'animal id <n>'."
                if not field:
                    return "❌ I couldn't understand which male data field you want to update. Try 'set StudFee to $1500' or 'update Herdsire to yes'."

                current = maledata_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)

                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_maledata(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"

                # same coercions as in confirmations
                flag_fields = {'Herdsire', 'JrHerdsire', 'JuvenileMale'}
                if field in flag_fields and isinstance(new_value, str):
                    v = new_value.strip().lower()
                    new_value = 1 if v in ['1','true','yes','y','on','enabled'] else 0 if v in ['0','false','no','n','off','disabled'] else new_value
                    if isinstance(new_value, str) and new_value.isdigit():
                        new_value = int(new_value)
                if field == 'ID' and isinstance(new_value, str) and new_value.isdigit():
                    new_value = int(new_value)

                self.pending_update_maledata = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Male Data Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which male data row to modify. Include an identifier (e.g., 'male id 42')."
                if not field:
                    return "❌ Please specify which field to clear (e.g., 'Comments' or 'StudFee')."
                current = maledata_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current male data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_maledata(field)
                self.pending_delete_maledata = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Male Data)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- States flow -----
        if is_states:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_states_identifier(user_input)
            field = self._extract_states_field(user_input, conversation_history)

            if action == "create":
                states_field_map = {
                   'state id': 'StateID', 'id': 'StateID',
                   'state': 'StateName', 'state name': 'StateName',
                   'abbrev': 'StateAbbreviation', 'abbreviation': 'StateAbbreviation', 'short code': 'StateAbbreviation',
                   'country': 'Country', 'country name': 'Country'
                }
                                
                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=states_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                        "📝 *Create new State record*\n\n"
                        "Tell me the fields to add — for example:\n"
                        "create state name: California, abbreviation: CA, country: USA\n\n"
                        "You can also paste JSON/Python dict like:\n"
                        "{\"StateName\": \"California\", \"StateAbbreviation\": \"CA\", \"Country\": \"USA\"}"
                      )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                    f"- *{self.get_user_friendly_field_name(k).title()}*: {v}"
                    for k, v in data.items()
                    )

                self.pending_create_states = data

                return (
                     "🆕 *Confirm Create (States)*\n\n"
                     f"You’re about to create a new state record with:\n{preview}\n\n"
                     "Confirm with *'yes'* or cancel with *'no'*."
                   )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which state record (e.g., 'state id 5', 'state name \"California\"', or 'state abbreviation \"CA\"')."
                result = states_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_state(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in [
                            'StateID','StateName','StateAbbreviation','Governor','Senator1','Senator2',
                            'StateFlag','Statebird','StateSeal','Moto','Nicknames','Weatherlink'
                        ] if k in STATES_COLUMNS]
                        lines = ["🏛️ **State Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None, ""]:
                                label = self.get_user_friendly_field_name_state(k).title()
                                lines.append(f"- {label}: {record.get(k)}")

                        # summary of representatives present
                        rep_count = len([c for c in STATES_COLUMNS if c.startswith('Rep') and record.get(c)])
                        if rep_count:
                            lines.append(f"- Representatives present: {rep_count} entries")

                        # extras
                        others = [k for k in STATES_COLUMNS if k not in show_keys and not k.startswith('Rep') and record.get(k)]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching state record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which state row to update. Include 'state id <n>', 'state name \"...\"', or 'state abbreviation \"...\"'."
                if not field:
                    return "❌ I couldn't understand which state field you want to update. Try 'set Governor to Jane Doe' or 'update StateFlag to https://…'."
                current = states_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)

                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_state(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"

                if field == 'StateID' and isinstance(new_value, str) and new_value.isdigit():
                    new_value = int(new_value)

                self.pending_update_state = (field, new_value, identifier)
                return (
                    "🔄 **Confirm State Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which state row to modify. Include an identifier (e.g., 'state id 10' or 'state abbreviation \"CA\"')."
                if not field:
                    return "❌ Please specify which state field to clear (e.g., 'Weatherlink', 'StateHeaderImage', 'Nicknames', or 'Rep12')."
                current = states_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current state data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_state(field)
                self.pending_delete_state = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (State)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- State_province flow -----
        if is_stateprov:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_stateprov_identifier(user_input)
            field = self._extract_stateprov_field(user_input, conversation_history)

            if action == "create":
                state_province_field_map = {
                    'stateprov id': 'StateProvID', 'state province id': 'StateProvID', 'id': 'StateProvID',
                    'state': 'State', 'state name': 'State',
                    'province': 'Province', 'province name': 'Province',
                    'country': 'Country', 'country name': 'Country',
                    'code': 'Code', 'short code': 'Code', 'abbrev': 'Code',
                    'region': 'Region'
                                       }
                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=state_province_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                         "📝 *Create new State_Province record*\n\n"
                         "Tell me the fields to add — for example:\n"
                         "create state_province state: Texas, province: NA, country: USA, code: TX\n\n"
                         "You can also paste JSON/Python dict like:\n"
                         "{\"State\": \"Texas\", \"Province\": \"NA\", \"Country\": \"USA\", \"Code\": \"TX\"}"
                       )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                                f"- *{self.get_user_friendly_field_name(k).title()}*: {v}"
                                for k, v in data.items()
                               )

                self.pending_create_state_province = data

                return (
                     "🆕 *Confirm Create (State_Province)*\n\n"
                     f"You’re about to create a new State_Province record with:\n{preview}\n\n"
                     "Confirm with *'yes'* or cancel with *'no'*."
                    )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which state/province record (e.g., 'state index 12', 'state name \"California\"', or 'abbreviation \"CA\" country id \"US\"')."
                result = state_province_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_stateprov(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in ['StateIndex','name','abbreviation','country_id'] if k in STATE_PROVINCE_COLUMNS]
                        lines = ["🗺️ **State/Province Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None, ""]:
                                label = self.get_user_friendly_field_name_stateprov(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in STATE_PROVINCE_COLUMNS if k not in show_keys and record.get(k) not in [None, ""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching state/province record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which state/province row to update. Include 'state index <n>' or identify by 'state name \"...\"' or 'abbreviation \"...\"' (optionally with country id)."
                if not field:
                    return "❌ I couldn't understand which field you want to update. Try 'set abbreviation to CA' or 'update country_id to US'."
                current = state_province_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_stateprov(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                if field in ['StateIndex'] and isinstance(new_value, str) and new_value.isdigit():
                    new_value = int(new_value)
                self.pending_update_stateprov = (field, new_value, identifier)
                return (
                    "🔄 **Confirm State/Province Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which state/province row to modify. Include an identifier (e.g., 'state index 10')."
                if not field:
                    return "❌ Please specify which field to clear (e.g., 'abbreviation' or 'country_id')."
                current = state_province_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current state/province data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_stateprov(field)
                self.pending_delete_stateprov = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (State/Province)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Speciesregistrationtypelookuptable flow -----
        if is_speciesregtype:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_speciesregtype_identifier(user_input)
            field = self._extract_speciesregtype_field(user_input, conversation_history)

            if action == "create":
                speciesregtype_field_map = {
                                         'type id': 'SpeciesRegistrationTypeID',
                                         'registration type id': 'SpeciesRegistrationTypeID',
                                         'species registration type id': 'SpeciesRegistrationTypeID',
                                         'type': 'SpeciesRegistrationType',
                                         'registration type': 'SpeciesRegistrationType',
                                         'species registration type': 'SpeciesRegistrationType',
                                         'description': 'Description',
                                         'details': 'Description',
                                         'info': 'Description'
                                         }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=speciesregtype_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                         "📝 *Create new Species Registration Type*\n\n"
                         "Tell me the fields to add — for example:\n"
                         "create species registration type: Purebred, description: Fully verified line\n\n"
                         "You can also paste JSON/Python dict like:\n"
                         "{\"SpeciesRegistrationType\": \"Purebred\", \"Description\": \"Verified\"}"
                       )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                                f"- *{self.get_user_friendly_field_name(k).title()}*: {v}"
                                 for k, v in data.items()
                               )

                self.pending_create_speciesregtype = data

                return (
                     "🆕 *Confirm Create (SpeciesRegistrationTypeLookupTable)*\n\n"
                     f"You’re about to create a new species registration type record with:\n{preview}\n\n"
                     "Confirm with *'yes'* or cancel with *'no'*."
                   )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which species registration type record (e.g., 'registration type id 5', 'species registration type \"CLAA\" species id 3', or 'species id 3 country id 1')."
                result = speciesregistrationtypelookuptable_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_speciesregtype(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in ['SpeciesRegistrationTypeID','SpeciesID','SpeciesRegistrationType','country_id'] if k in SPECIESREGISTRATIONTYPELOOKUPTABLE_COLUMNS]
                        lines = ["🧾 **Species Registration Type Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None, ""]:
                                label = self.get_user_friendly_field_name_speciesregtype(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in SPECIESREGISTRATIONTYPELOOKUPTABLE_COLUMNS if k not in show_keys and record.get(k) not in [None, ""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching species registration type record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which species registration type row to update. Include 'registration type id <n>' or 'species registration type \"...\"' (optionally with species id / country id)."
                if not field:
                    return "❌ I couldn't understand which field you want to update. Try 'set SpeciesRegistrationType to CLAA' or 'update country_id to 1'."
                current = speciesregistrationtypelookuptable_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_speciesregtype(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                if field in ['SpeciesRegistrationTypeID','SpeciesID','country_id'] and isinstance(new_value, str) and new_value.isdigit():
                    new_value = int(new_value)
                self.pending_update_speciesregtype = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Species Registration Type Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which species registration type row to modify. Include an identifier (e.g., 'registration type id 10')."
                if not field:
                    return "❌ Please specify which field to clear (e.g., 'SpeciesRegistrationType')."
                current = speciesregistrationtypelookuptable_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current species registration type data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_speciesregtype(field)
                self.pending_delete_speciesregtype = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Species Registration Type)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Speciescolorlookuptable flow -----
        if is_speciescolor:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_speciescolor_identifier(user_input)
            field = self._extract_speciescolor_field(user_input, conversation_history)

            if action == "create":
                speciescolor_field_map = {
                                        'color id': 'SpeciesColorID',
                                        'species color id': 'SpeciesColorID',
                                        'id': 'SpeciesColorID',
                                        'color': 'Color',
                                        'colour': 'Color',
                                        'color name': 'Color',
                                        'species color': 'Color',
                                        'description': 'Description',
                                        'details': 'Description',
                                        'info': 'Description'
                                       }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=speciescolor_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                        "📝 *Create new Species Color*\n\n"
                        "Tell me the fields to add — for example:\n"
                        "create species color: Red Brindle, description: Reddish coat with brindle pattern\n\n"
                        "You can also paste JSON/Python dict like:\n"
                      "{\"Color\": \"Red\", \"Description\": \"Reddish coat\"}"
                       )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                                 f"- *{self.get_user_friendly_field_name(k).title()}*: {v}"
                                 for k, v in data.items()
                                )

                self.pending_create_speciescolor = data

                return (
                      "🆕 *Confirm Create (SpeciesColor)*\n\n"
                      f"You’re about to create a new species color record with:\n{preview}\n\n"
                      "Confirm with *'yes'* or cancel with *'no'*."
                    )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which species color record (e.g., 'species color id 5', 'species id 3 species color \"Fawn\"')."
                result = speciescolorlookuptable_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_speciescolor(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in ['SpeciesColorID','SpeciesID','SpeciesColor'] if k in SPECIESCOLORLOOKUPTABLE_COLUMNS]
                        lines = ["🌈 **Species Color Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None, ""]:
                                label = self.get_user_friendly_field_name_speciescolor(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in SPECIESCOLORLOOKUPTABLE_COLUMNS if k not in show_keys and record.get(k) not in [None, ""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching species color record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which species color row to update. Include 'species color id <n>' or 'species id <n> species color \"...\"'."
                if not field:
                    return "❌ I couldn't understand which species color field you want to update. Try 'set SpeciesColor to Fawn' or 'update SpeciesID to 3'."
                current = speciescolorlookuptable_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_speciescolor(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                if field in ['SpeciesColorID', 'SpeciesID'] and isinstance(new_value, str) and new_value.isdigit():
                    new_value = int(new_value)
                self.pending_update_speciescolor = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Species Color Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which species color row to modify. Include an identifier (e.g., 'species color id 10')."
                if not field:
                    return "❌ Please specify which field to clear (e.g., 'SpeciesColor')."
                current = speciescolorlookuptable_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current species color data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_speciescolor(field)
                self.pending_delete_speciescolor = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Species Color)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Speciescategory flow -----
        if is_speciescategory:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_speciescategory_identifier(user_input)
            field = self._extract_speciescategory_field(user_input, conversation_history)

            if action == "create":
                speciescategory_field_map = {
                                          'category id': 'SpeciesCategoryID',
                                          'species category id': 'SpeciesCategoryID',
                                          'id': 'SpeciesCategoryID',
                                          'category': 'Category',
                                          'species category': 'Category',
                                          'type': 'Category',
                                          'name': 'Category',
                                          'category name': 'Category',
                                          'description': 'Description',
                                          'details': 'Description',
                                          'info': 'Description'
                                        }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=speciescategory_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                          "📝 *Create new Species Category*\n\n"
                          "Tell me the fields to add — for example:\n"
                          "create species category: Dairy, description: Cattle used for milk production\n\n"
                          "You can also paste JSON/Python dict like:\n"
                          "{\"Category\": \"Dairy\", \"Description\": \"Milk-producing cattle\"}"
                        )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                                 f"- *{self.get_user_friendly_field_name(k).title()}*: {v}"
                                 for k, v in data.items()
                                )

                self.pending_create_speciescategory = data

                return (
                     "🆕 *Confirm Create (SpeciesCategory)*\n\n"
                     f"You’re about to create a new species category with:\n{preview}\n\n"
                     "Confirm with *'yes'* or cancel with *'no'*."
                    )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which species category record (e.g., 'species category id 7', 'species category \"Camelids\"', or 'species id 3')."
                result = speciescategory_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_speciescategory(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in [
                            'SpeciesCategoryID','SpeciesID','SpeciesCategory','SpeciesCategoryPlural',
                            'SpeciesCategoryOrder','QuantityType'
                        ] if k in SPECIESCATEGORY_COLUMNS]
                        lines = ["🧭 **Species Category Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None, ""]:
                                label = self.get_user_friendly_field_name_speciescategory(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in SPECIESCATEGORY_COLUMNS if k not in show_keys and record.get(k) not in [None, ""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching species category record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which species category row to update. Include 'species category id <n>' or 'species category \"...\"' (optionally with species id)."
                if not field:
                    return "❌ I couldn't understand which species category field you want to update. Try 'set SpeciesCategoryPlural to Camelids' or 'update QuantityType to Head'."
                current = speciescategory_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_speciescategory(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                if field in ['SpeciesID', 'SpeciesCategoryOrder', 'SpeciesCategoryID'] and isinstance(new_value, str) and new_value.isdigit():
                    new_value = int(new_value)
                self.pending_update_speciescategory = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Species Category Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which species category row to modify. Include an identifier (e.g., 'species category id 10')."
                if not field:
                    return "❌ Please specify which field to clear (e.g., 'SpeciesCategoryPlural', 'QuantityType')."
                current = speciescategory_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current species category data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_speciescategory(field)
                self.pending_delete_speciescategory = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Species Category)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Speciesbreedlookuptable flow -----
        if is_speciesbreedlookup:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_speciesbreed_identifier(user_input)
            field = self._extract_speciesbreed_field(user_input, conversation_history)

            if action == "create":
                speciesbreed_field_map = {
                    'breed id': 'SpeciesBreedID', 'id': 'SpeciesBreedID',
                    'breed name': 'SpeciesBreedName', 'name': 'SpeciesBreedName',
                    'species id': 'SpeciesID', 'species': 'SpeciesID',
                    'description': 'Description', 'details': 'Description'
                }                                     

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=speciesbreed_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                         "📝 *Create a new Species Breed*\n\n"
                         "Tell me the fields to add — example:\n"
                         "create species breed name: Jersey, species id: 12, description: dairy breed\n\n"
                         "You may also paste JSON/Python dict like:\n"
                         "{\"SpeciesBreedName\": \"Jersey\", \"SpeciesID\": 12, \"Description\": \"Dairy breed\"}"
                      )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                                 f"- *{self.get_user_friendly_field_name(k).title()}*: {v}"
                                 for k, v in data.items()
                               )

                self.pending_create_speciesbreed = data

                return (
                     "🆕 *Confirm Create (Species Breed)*\n\n"
                     f"You’re about to create a new species breed with:\n{preview}\n\n"
                     "Confirm with *'yes'* or cancel with *'no'*."
                   )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which breed lookup record (e.g., 'breed lookup id 12', 'breed \"Merino\" species id 4')."
                result = speciesbreedlookuptable_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_speciesbreed(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in [
                            'BreedLookupID','breedavailable','SpeciesID','Breed','Breeddescription','BreedImage','Breedvideo',
                            'BreedAnimalID','BreedImageCaption','BreedImageOrientation','SpeciesRegistrationTypeID',
                            'MeatBreed','MilkBreed','WoolBreed','EggBreed','Working','HoneyBreed'
                        ] if k in SPECIESBREEDLOOKUPTABLE_COLUMNS]
                        lines = ["🐾 **Species Breed Lookup Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None,""]:
                                label = self.get_user_friendly_field_name_speciesbreed(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in SPECIESBREEDLOOKUPTABLE_COLUMNS if k not in show_keys and record.get(k) not in [None,""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching species breed lookup record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which species breed row to update. Include 'breed lookup id <n>' or 'breed \"...\" species id <n>'."
                if not field:
                    return "❌ I couldn't understand which species breed field you want to update. Try 'set breedavailable to yes' or 'update BreedImage to https://…'."
                current = speciesbreedlookup_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_speciesbreed(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"

                # Coercions (same as in confirmations)
                int_fields = {'BreedLookupID','SpeciesID','BreedAnimalID','SpeciesRegistrationTypeID','Working'}
                tiny_fields = {'breedavailable','MeatBreed','MilkBreed','WoolBreed','EggBreed','HoneyBreed'}
                if field in int_fields and isinstance(new_value, str) and new_value.isdigit():
                    new_value = int(new_value)
                if field in tiny_fields and isinstance(new_value, str):
                    v = new_value.strip().lower()
                    new_value = 1 if v in ['1','true','yes','y','on','available'] else 0 if v in ['0','false','no','n','off','unavailable'] else new_value

                self.pending_update_speciesbreed = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Species Breed Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which species breed row to modify. Include an identifier (e.g., 'breed lookup id 10')."
                if not field:
                    return "❌ Please specify which field to clear (e.g., 'BreedImageCaption', 'Breeddescription')."
                current = speciesbreedlookuptable_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current species breed data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_speciesbreed(field)
                self.pending_delete_speciesbreed = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Species Breed)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Sire flow -----
        if is_sire:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_sire_identifier(user_input)
            field = self._extract_sire_field(user_input, conversation_history)

            if action == "create":
                sire_field_map = {
                                 'sire id': 'SireID', 'id': 'SireID',
                                 'sire name': 'SireName', 'name': 'SireName',
                                 'registration': 'Registration',
                                 'registration number': 'Registration',
                                 'reg number': 'Registration',
                                 'reg': 'Registration',
                                 'birthdate': 'BirthDate', 'dob': 'BirthDate', 'date of birth': 'BirthDate',
                                 'color': 'Color', 'colour': 'Color',
                                 'status': 'Status',
                                 'breed id': 'BreedID', 'breed': 'BreedID',
                                 'species breed id': 'BreedID',
                                 'business id': 'BusinessID', 'owner business id': 'BusinessID'
                             }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=sire_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                          "📝 *Create new Sire (Bull Father) record*\n\n"
                          "Tell me the fields to add — for example:\n"
                          "create sire name: Thunder, registration: 554433, color: brown, breed id: 7\n\n"
                          "Or paste a JSON/Python dict like:\n"
                          "{\"SireName\": \"Thunder\", \"Registration\": \"554433\", \"Color\": \"Brown\"}"
                       )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                                 f"- *{self.get_user_friendly_field_name(k).title()}*: {v}"
                                 for k, v in data.items()
                               )

                self.pending_create_sire = data

                return (
                     "🆕 *Confirm Create (Sire)*\n\n"
                     f"You’re about to create a new sire record with:\n{preview}\n\n"
                     "Confirm with *'yes'* or cancel with *'no'*."
                   )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which sire record (e.g., 'sire id 12', 'sire name \"Snowmass\"', or 'registration \"CLAA-12345\"')."
                result = sire_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_sire(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in ['SireID','SiresName','SiresRegistration','SiresColor'] if k in SIRE_COLUMNS]
                        lines = ["🧬 **Sire Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None,""]:
                                label = self.get_user_friendly_field_name_sire(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in SIRE_COLUMNS if k not in show_keys and record.get(k) not in [None,""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching sire record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which sire row to update. Include 'sire id <n>' or 'sire name \"...\"' or 'registration \"...\"'."
                if not field:
                    return "❌ I couldn't understand which sire field you want to update. Try 'set SiresColor to Fawn' or 'update SiresRegistration to CLAA-12345'."
                current = sire_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_sire(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                self.pending_update_sire = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Sire Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which sire row to modify. Include an identifier (e.g., 'sire id 10' or 'registration \"...\"')."
                if not field:
                    return "❌ Please specify which sire field to clear (e.g., 'SiresColor' or 'SiresRegistration')."
                current = sire_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current sire data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_sire(field)
                self.pending_delete_sire = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Sire)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Peopletitlelookup flow -----
        if is_peopletitle:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_peopletitle_identifier(user_input)
            field = self._extract_peopletitle_field(user_input, conversation_history)

            if action == "create":
                peopletitle_field_map = {
                    'people title id': 'PeopletitleID', 'peopletitle id': 'PeopletitleID', 'title id': 'PeopletitleID',
                    'people title': 'PeopleTitle', 'title': 'PeopleTitle', 'name': 'PeopleTitle',
                    'people title description': 'PeopleTitleDescription', 'description': 'PeopleTitleDescription', 'desc': 'PeopleTitleDescription',
                }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=peopletitle_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                        "📝 **Create new people title**\n\n"
                        "Tell me the fields to add — for example:\n"
                        "`create people title title: Herd Manager, description: Oversees daily herd operations`\n"
                        "You can also paste a Python/JSON dict like:\n"
                        "`{\"PeopleTitle\": \"Herd Manager\", \"PeopleTitleDescription\": \"Oversees daily herd operations\"}`"
                )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                    f"- **{self.get_user_friendly_field_name_peopletitle(k).title()}**: {v}"
                    for k, v in data.items()
                )

                self.pending_create_peopletitlelookup = data

                return (
                    "🆕 **Confirm Create (People Title)**\n\n"
                    f"You’re about to create a new people title with:\n{preview}\n\n"
                    "Confirm with **'yes'** or cancel with **'no'**."
                )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which people title record (e.g., 'people title id 3' or 'people title \"Dr\"')."
                result = peopletitlelookup_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_peopletitle(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in ['PeopletitleID','PeopleTitle','PeopleTitleDescription'] if k in PEOPLETITLELOOKUP_COLUMNS]
                        lines = ["👔 **People Title Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None,""]:
                                label = self.get_user_friendly_field_name_peopletitle(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in PEOPLETITLELOOKUP_COLUMNS if k not in show_keys and record.get(k) not in [None,""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching people title record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which people title row to update. Include 'people title id <n>' or 'people title \"...\"'."
                if not field:
                    return "❌ I couldn't understand which people title field you want to update. Try 'set PeopleTitle to Prof' or 'update PeopleTitleDescription to Academic rank'."
                current = peopletitlelookup_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_peopletitle(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                self.pending_update_peopletitle = (field, new_value, identifier)
                return (
                    "🔄 **Confirm People Title Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which people title row to modify. Include an identifier (e.g., 'people title id 10' or 'people title \"Ms\"')."
                if not field:
                    return "❌ Please specify which people title field to clear (e.g., 'PeopleTitleDescription')."
                current = peopletitlelookup_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current people title data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_peopletitle(field)
                self.pending_delete_peopletitle = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (People Title)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."
      
        # ----- Fiber flow -----
        if is_fiber:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_fiber_identifier(user_input)
            field = self._extract_fiber_field(user_input, conversation_history)

            if action == "create":
                fiber_field_map = {
                    'fiber id': 'FiberID', 'fibers id': 'FiberID',
                    'animal id': 'AnimalID', 'animal': 'AnimalID', 'id (animal)': 'AnimalID',
                    'people id': 'PeopleID', 'owner id': 'PeopleID',
                    'sample date': 'SampleDate', 'date': 'SampleDate', 'testing date': 'SampleDate',
                    'test lab': 'FiberTestLab', 'lab': 'FiberTestLab',
                    'test method': 'TestMethod',
                    'afd': 'AFD', 'micron': 'AFD', 'mean micron': 'AFD', 'mean fiber diameter': 'AFD', 'mfd': 'AFD',
                    'sd': 'SD', 'stdev': 'SD', 'standard deviation': 'SD',
                    'cv': 'CV', 'coefficient of variation': 'CV',
                    'cf': 'ComfortFactor', 'comfort factor': 'ComfortFactor',
                    'spin fineness': 'SpinFineness', 'sf': 'SpinFineness',
                    'curvature': 'Curvature', 'crv': 'Curvature',
                    'staple length': 'StapleLength', 'staple': 'StapleLength', 'sl': 'StapleLength',
                    'medulation': 'Medulation', 'med': 'Medulation',
                    'yield': 'Yield',
                    'mean curvature': 'MeanCurvature',
                    'fleece weight': 'FleeceWeight', 'fiber weight': 'FleeceWeight', 'shear weight': 'FleeceWeight',
                    'blanket weight': 'BlanketWeight',
                    'shoulder micron': 'ShoulderMicron', 'mid micron': 'MidMicron', 'hip micron': 'HipMicron',
                    'sample color id': 'ColorID', 'color id': 'ColorID',
                    'notes': 'Notes', 'comments': 'Notes', 'remark': 'Notes'
                }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=fiber_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                        "📝 **Create new fiber record**\n\n"
                        "Tell me the fields to add — for example:\n"
                        "`create fiber animal id: 42, sample date: 2025-04-15, afd: 18.6, sd: 3.7, cv: 19.9, cf: 99.1, staple length: 85, curvature: 48`\n"
                        "You can also paste a Python/JSON dict like:\n"
                        "`{\"AnimalID\": 42, \"SampleDate\": \"2025-04-15\", \"AFD\": 18.6, \"SD\": 3.7, \"CV\": 19.9, \"ComfortFactor\": 99.1, \"StapleLength\": 85, \"Curvature\": 48, \"SpinFineness\": 18.8}`"
                )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                    f"- **{self.get_user_friendly_field_name_fiber(k).title()}**: {v}"
                   for k, v in data.items()
                )

                self.pending_create_fiber = data

                return (
                    "🆕 **Confirm Create (Fiber)**\n\n"
                    f"You’re about to create a new fiber record with:\n{preview}\n\n"
                    "Confirm with **'yes'** or cancel with **'no'**."
                )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which fiber record (e.g., 'fiber id 9', 'id 42 sample date \"2024-05-01\"', or 'id 42 month 5 year 2024')."
                result = fiber_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_fiber(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in [
                            'FiberID','ID','SampleDate','SampleDateMonth','SampleDateDay','SampleDateYear',
                            'SampleAge','Average','StandardDev','COV','GreaterThan30','CF','Curve',
                            'Shearweight','BlanketWeight','Length','CrimpPerInch','LargeHistogram',
                            'SmallHistogram','StapleLength'
                        ] if k in FIBER_COLUMNS]
                        lines = ["🧶 **Fiber Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None,""]:
                                label = self.get_user_friendly_field_name_fiber(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in FIBER_COLUMNS if k not in show_keys and record.get(k) not in [None,""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching fiber record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which fiber row to update. Include 'fiber id <n>' or 'id <n>' with optional date hints."
                if not field:
                    return "❌ I couldn't understand which fiber field you want to update. Try 'set Average to 20.5' or 'update SampleDate to 2024-05-01'."
                current = fiber_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_fiber(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                # Coerce numeric for date parts if user typed a number
                if field in ['SampleDateMonth', 'SampleDateDay', 'SampleDateYear'] and isinstance(new_value, str) and new_value.isdigit():
                    new_value = int(new_value)
                self.pending_update_fiber = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Fiber Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which fiber row to modify. Include an identifier (e.g., 'fiber id 10' or 'id 42 sample date \"2023-04-01\"')."
                if not field:
                    return "❌ Please specify which fiber field to clear (e.g., 'Average', 'StandardDev', 'LargeHistogram')."
                current = fiber_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current fiber data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_fiber(field)
                self.pending_delete_fiber = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Fiber)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Country flow -----
        if is_country:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_country_identifier(user_input)
            field = self._extract_country_field(user_input, conversation_history)

            if action == "create":
                country_field_map = {
                    'country id': 'CountryID', 'id': 'CountryID',
                    'country': 'Country', 'country name': 'Country', 'name': 'Country',
                    'country code': 'CountryCode', 'code': 'CountryCode', 'iso2': 'CountryCode',
                    'iso3': 'ISO3',
                    'phone code': 'PhoneCode', 'dial code': 'PhoneCode',
                    'capital': 'Capital',
                    'continent': 'Continent',
                    'region': 'Region',
                    'subregion': 'Subregion',
                    'latitude': 'Latitude', 'lat': 'Latitude',
                    'longitude': 'Longitude', 'lon': 'Longitude', 'lng': 'Longitude',
                    'currency': 'Currency',
                    'currency code': 'CurrencyCode',
                    'notes': 'Notes', 'comments': 'Notes',
            }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=country_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                        "📝 **Create new country**\n\n"
                        "Tell me the fields to add — for example:\n"
                        "`create country name: United States, country code: US, iso3: USA, phone code: +1, capital: Washington D.C., region: Americas`\n"
                        "You can also paste a Python/JSON dict like:\n"
                        "`{\"Country\": \"United States\", \"CountryCode\": \"US\", \"ISO3\": \"USA\", \"PhoneCode\": \"+1\", \"Capital\": \"Washington D.C.\", \"Region\": \"Americas\"}`"
                    )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                    f"- **{self.get_user_friendly_field_name_country(k).title()}**: {v}"
                    for k, v in data.items()
                )

                self.pending_create_country = data

                return (
                    "🆕 **Confirm Create (Country)**\n\n"
                    f"You’re about to create a new country record with:\n{preview}\n\n"
                    "Confirm with **'yes'** or cancel with **'no'**."
                )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which country record (e.g., 'country id 5', 'iso code \"US\"', or 'name \"United States\"')."
                result = country_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_country(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in ['country_id','name','iso_code','Currency','CurrencyCode','Active','Paycode','region','ProvinceTitle'] if k in COUNTRY_COLUMNS]
                        lines = ["🌍 **Country Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None,""]:
                                label = self.get_user_friendly_field_name_country(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in COUNTRY_COLUMNS if k not in show_keys and record.get(k) not in [None,""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching country record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which country row to update. Include 'country id <n>', 'iso code \"XX\"', or 'name \"...\"'."
                if not field:
                    return "❌ I couldn't understand which country field you want to update. Try 'set currency to USD' or 'update region to EMEA'."
                current = country_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_country(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                # Coerce Active to 0/1 if user typed yes/no/true/false
                if field == 'Active' and isinstance(new_value, str):
                    nv = new_value.strip().lower()
                    new_value = 1 if nv in ['1','true','yes','y','on','active'] else 0 if nv in ['0','false','no','n','off','inactive'] else new_value
                self.pending_update_country = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Country Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which country row to modify. Include an identifier (e.g., 'country id 10', 'iso code \"CA\"', or 'name \"Canada\"')."
                if not field:
                    return "❌ Please specify which country field to clear (e.g., 'CurrencyCode', 'Paycode', 'ProvinceTitle')."
                current = country_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current country data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_country(field)
                self.pending_delete_country = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Country)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Colors flow -----
        if is_colors:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_colors_identifier(user_input)
            field = self._extract_colors_field(user_input, conversation_history)

            if action == "create":
                colors_field_map = {
                    'colors id': 'ColorsID', 'color record id': 'ColorsID', 'color id (record)': 'ColorsID',
                    'animal id': 'ID', 'animal': 'ID', 'id': 'ID',
                    'color id': 'ColorID', 'lookup color id': 'ColorID',    
                    'color': 'Color', 'colour': 'Color', 'name': 'Color',
                    'abbrev': 'Abbreviation', 'abbreviation': 'Abbreviation', 'abbr': 'Abbreviation',
                    'color group': 'ColorGroup', 'colour group': 'ColorGroup', 'group': 'ColorGroup',
                    'judging type': 'JudgingType', 'judging': 'JudgingType',
                    'breed': 'Breed',
                    'rank': 'ColorRank', 'primary': 'Primary', 'is primary': 'Primary',
                    'notes': 'ColorNotes', 'comments': 'ColorNotes',
                }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=colors_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                        "📝 **Create new color record**\n\n"
                        "Tell me the fields to add — for example:\n"
                        "`create colors animal id: 42, color id: 17, color: Rose Grey, abbreviation: RG, color group: Grey`\n"
                        "You can also paste a Python/JSON dict like:\n"
                        "`{\"ID\": 42, \"ColorID\": 17, \"Color\": \"Rose Grey\", \"Abbreviation\": \"RG\", \"ColorGroup\": \"Grey\"}`"
                    )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                    f"- **{self.get_user_friendly_field_name_colors(k).title()}**: {v}"
                    for k, v in data.items()
                )

                self.pending_create_colors = data

                return (
                    "🆕 **Confirm Create (Colors)**\n\n"
                    f"You’re about to create a new colors record with:\n{preview}\n\n"
                    "Confirm with **'yes'** or cancel with **'no'**."
                )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which colors record (e.g., 'colors id 7' or 'id 42')."
                result = colors_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_colors(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in ['ColorID','ID','Color1','Color2','Color3','Color4','Color5'] if k in COLORS_COLUMNS]
                        lines = ["🎨 **Colors Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None, ""]:
                                label = self.get_user_friendly_field_name_colors(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in COLORS_COLUMNS if k not in show_keys and record.get(k) not in [None, ""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching colors record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which colors row to update. Include 'colors id <n>' or 'id <n>'."
                if not field:
                    return "❌ I couldn't understand which colors field you want to update. Try 'set Color1 to Fawn' or 'update Color3 to Silver Grey'."
                current = colors_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_colors(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                self.pending_update_colors = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Colors Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which colors row to modify. Include an identifier (e.g., 'colors id 10' or 'id 42')."
                if not field:
                    return "❌ Please specify which colors field to clear (e.g., 'Color4', 'Color2')."
                current = colors_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current colors data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_colors(field)
                self.pending_delete_colors = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Colors)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Colorlookup flow -----
        if is_colorlookup:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_color_identifier(user_input)
            field = self._extract_color_field(user_input, conversation_history)

            if action == "create":
                colorlookup_field_map = {
                    'color id': 'ColorID', 'colour id': 'ColorID', 'id': 'ColorID',
                    'color': 'Color', 'colour': 'Color', 'name': 'Color',
                    'abbrev': 'Abbreviation', 'abbreviation': 'Abbreviation', 'abbr': 'Abbreviation',
                    'color group': 'ColorGroup', 'colour group': 'ColorGroup', 'group': 'ColorGroup',
                    'judging type': 'JudgingType', 'judging': 'JudgingType',
                    'breed': 'Breed',
                }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=colorlookup_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                        "📝 **Create new color lookup**\n\n"
                        "Tell me the fields to add — for example:\n"
                        "`create color color: Rose Grey, abbreviation: RG, color group: Grey, judging type: Halter, breed: Alpaca`\n"
                        "You can also paste a Python/JSON dict like:\n"
                        "`{\"Color\": \"Rose Grey\", \"Abbreviation\": \"RG\", \"ColorGroup\": \"Grey\", \"JudgingType\": \"Halter\", \"Breed\": \"Alpaca\"}`"
                    )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                    f"- **{self.get_user_friendly_field_name_color(k).title()}**: {v}"
                    for k, v in data.items()
                )

                self.pending_create_colorlookup = data

                return (
                    "🆕 **Confirm Create (Color Lookup)**\n\n"
                    f"You’re about to create a new color lookup record with:\n{preview}\n\n"
                    "Confirm with **'yes'** or cancel with **'no'**."
                )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which color record (e.g., 'color id 12', 'color \"Rose Grey\"', 'abbreviation \"RG\"', or 'color group \"Grey\"')."
                result = colorlookup_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_color(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in ['ColorID','Color','Abbreviation','ColorGroup','JudgingType','Breed'] if k in COLORLOOKUP_COLUMNS]
                        lines = ["🎨 **Color Lookup Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None,""]:
                                label = self.get_user_friendly_field_name_color(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in COLORLOOKUP_COLUMNS if k not in show_keys and record.get(k) not in [None,""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching color record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which color row to update. Include 'color id <n>' or key fields like 'color \"...\"' or 'abbreviation \"...\"'."
                if not field:
                    return "❌ I couldn't understand which color field you want to update. Try 'set Abbreviation to RG' or 'update ColorGroup to Grey'."
                current = colorlookup_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_color(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                self.pending_update_color = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Color Lookup Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which color row to modify. Include an identifier (e.g., 'color id 10', or 'color \"Fawn\"')."
                if not field:
                    return "❌ Please specify which color field to clear (e.g., 'Abbreviation', 'ColorGroup', 'JudgingType', 'Breed')."
                current = colorlookup_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current color data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_color(field)
                self.pending_delete_color = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Color Lookup)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Business flow -----
        if is_business:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_business_identifier(user_input)
            field = self._extract_business_field(user_input, conversation_history)

            if action == "create":
                business_field_map = {
                    'business id': 'BusinessID', 'id': 'BusinessID',
                    'business type id': 'BusinessTypeID', 'type id': 'BusinessTypeID',
                    'business name': 'BusinessName', 'name': 'BusinessName',
                    'business acronym': 'BusinessAcronym', 'acronym': 'BusinessAcronym',
                    'business email': 'BusinessEmail', 'email': 'BusinessEmail',
                    'business phone': 'BusinessPhone', 'phone': 'BusinessPhone',
                    'business hours': 'BusinessHours', 'hours': 'BusinessHours',
                    'business website id': 'BusinessWebsiteID', 'website id': 'BusinessWebsiteID',
                    'websites id': 'WebsitesID',
                    'address id': 'AddressID',
                    'phone id': 'PhoneID',
                    'event id': 'EventID',
                    'people id': 'Contact1PeopleID', 'user id': 'Contact1PeopleID', 'primary contact id': 'Contact1PeopleID',
                    'linkedin': 'BusinessLinkedIn',
                    'facebook': 'BusinessFacebook',
                    'x': 'BusinessX', 'twitter': 'BusinessX',
                    'instagram': 'BusinessInstagram',
                    'pinterest': 'BusinessPinterest',
                    'truth social': 'BusinessTruthSocial',
                    'blog': 'BusinessBlog',
                    'youtube': 'BusinessYouTube',
                    'other social 1': 'BusinessOtherSocial1',
                    'other social 2': 'BusinessOtherSocial2',
                    'gg website': 'GGWebsite',
                    'preferred breed': 'PreferredBreed',
                    'preferred species': 'Preferedspecies',
                    'subscription level': 'SubscriptionLevel',
                    'access level': 'AccessLevel',
                    'business logo': 'BusinessLogo', 'logo': 'Logo', 'header': 'Header',
                    'ranch home text': 'RanchHomeText',
                    'ranch home heading': 'RanchHomeHeading',
                    'ranch home text 2': 'RanchHomeText2',
                    'cell': 'Cell',
                    'fax': 'Fax',
                    'favorite association id': 'FavoriteAssociationID',
            }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=business_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                        "📝 **Create new business**\n\n"
                        "Tell me the fields to add — for example:\n"
                        "`create business business name: Silver Sky Ranch, business acronym: SSR, business email: hello@ssr.com, business phone: 555-0100, people id: 77`\n"
                        "You can also paste a Python/JSON dict like:\n"
                        "`{\"BusinessName\": \"Silver Sky Ranch\", \"BusinessAcronym\": \"SSR\", \"BusinessEmail\": \"hello@ssr.com\", \"BusinessPhone\": \"555-0100\", \"Contact1PeopleID\": 77, \"BusinessFacebook\": \"https://facebook.com/ssr\"}`"
                    )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                    f"- **{self.get_user_friendly_field_name_business(k).title()}**: {v}"
                    for k, v in data.items()
                )

                self.pending_create_business = data

                return (
                    "🆕 **Confirm Create (Business)**\n\n"
                    f"You’re about to create a new business with:\n{preview}\n\n"
                    "Confirm with **'yes'** or cancel with **'no'**."
                )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which business (e.g., 'business id 7', 'business name \"Acme Ranch\"', 'acronym \"ACME\"', or 'people id 12')."
                result = business_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_business(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in [
                            'BusinessID','BusinessName','BusinessAcronym','BusinessEmail','BusinessPhone',
                            'BusinessHours','BusinessWebsiteID','WebsitesID','BusinessLogo',
                            'BusinessFacebook','BusinessInstagram','BusinessX','BusinessLinkedIn',
                        ] if k in BUSINESS_COLUMNS]
                        lines = ["🏢 **Business Record:**", ""]
                        for k in show_keys:
                            if record.get(k) not in [None, ""]:
                                label = self.get_user_friendly_field_name_business(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in BUSINESS_COLUMNS if k not in show_keys and record.get(k) not in [None,""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching business record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which business row to update. Include 'business id <n>', or 'business name \"...\"', or 'acronym \"...\"', or 'people id <n>'."
                if not field:
                    return "❌ I couldn't understand which business field you want to update. Try 'set BusinessEmail to x@y.com' or 'update BusinessHours to 9–5'."
                current = business_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_business(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return (
                        f"📝 **Update {friendly.title()}**\n\n"
                        f"Current value: **{cur}**\n\n"
                        f"What should it be changed to?"
                    )
                self.pending_update_business = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Business Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which business row to modify. Include an identifier (e.g., 'business id 10')."
                if not field:
                    return "❌ Please specify which business field to clear (e.g., 'BusinessLogo', 'BusinessEmail')."
                current = business_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current business data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_business(field)
                self.pending_delete_business = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Business)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Association Members flow -----
        if is_associationmembers:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_associationmember_identifier(user_input)
            field = self._extract_associationmember_field(user_input, conversation_history)

            if action == "create":
                associationmembers_field_map = {
                'association member id': 'AssociationMemberID', 'assoc member id': 'AssociationMemberID',
                'member id': 'AssociationMemberID',
                'association id': 'AssociationID', 'assoc id': 'AssociationID',
                'people id': 'PeopleId', 'person id': 'PeopleId', 'owner id': 'PeopleId', 'user id': 'PeopleId',
                'role': 'Role', 'position': 'Role', 'title': 'Role',
                'member type': 'MemberType', 'type': 'MemberType', 'membership type': 'MemberType',
                'status': 'Status', 'membership status': 'Status',
                'active': 'Active', 'is active': 'Active',
                'start date': 'StartDate', 'join date': 'StartDate', 'joined': 'StartDate',
                'end date': 'EndDate', 'leave date': 'EndDate', 'left': 'EndDate',
                'notes': 'Notes', 'comments': 'Notes', 'remark': 'Notes'
            }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=associationmembers_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                        "📝 **Create new association member**\n\n"
                        "Tell me the fields to add — for example:\n"
                        "`create association member association id: 10, people id: 77, role: Treasurer, member type: Individual, status: Active, start date: 2024-06-01`\n"
                        "You can also paste a Python/JSON dict like:\n"
                        "`{\"AssociationID\": 10, \"PeopleId\": 77, \"Role\": \"Treasurer\", \"MemberType\": \"Individual\", \"Status\": \"Active\", \"StartDate\": \"2024-06-01\"}`"
                    )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                    f"- **{self.get_user_friendly_field_name_associationmembers(k).title()}**: {v}"
                    for k, v in data.items()
                    )

                self.pending_create_associationmembers = data

                return (
                    "🆕 **Confirm Create (Association Members)**\n\n"
                    f"You’re about to create a new association member with:\n{preview}\n\n"
                    "Confirm with **'yes'** or cancel with **'no'**."
                )
            
            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which association member record (e.g., 'association member id 12', 'people id 7 and association id 3')."
                result = associationmembers_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_associationmember(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in ['associationmemberID','PeopleID','AssociationID','MemberPosition','AccessLevel','Favorite','BusinessID'] if k in ASSOCIATIONMEMBERS_COLUMNS]
                        lines = ["👥 **Association Member Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None,""]:
                                label = self.get_user_friendly_field_name_associationmember(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in ASSOCIATIONMEMBERS_COLUMNS if k not in show_keys and record.get(k) not in [None,""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching association member record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which association member row to update. Include 'association member id <n>' or both 'people id <n>' and 'association id <n>'."
                if not field:
                    return "❌ I couldn't understand which association member field you want to update. Try 'set access level to 3' or 'update member position to Treasurer'."
                current = associationmembers_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_associationmember(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                self.pending_update_associationmember = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Association Member Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which association member row to modify. Include an identifier (e.g., 'association member id 10')."
                if not field:
                    return "❌ Please specify which association member field to clear (e.g., 'MemberPosition', 'Favorite')."
                current = associationmembers_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current association member data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_associationmember(field)
                self.pending_delete_associationmember = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Association Member)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Associations flow -----
        if is_association:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_association_identifier(user_input)
            field = self._extract_association_field(user_input, conversation_history)

            if action == "create":
                association_field_map = {
                    'association id': 'AssociationID', 'assoc id': 'AssociationID',
                    'people id': 'PeopleId', 'person id': 'PeopleId', 'owner id': 'PeopleId',
                    'species id': 'SpeciesID',
                    'address id': 'AddressID',
                    'association name': 'AssociationName', 'name': 'AssociationName',
                    'acronym': 'AssociationAcronym',
                    'registry': 'Registry',
                    'association type': 'AssociationType', 'type': 'AssociationType',
                    'association type id': 'AssociationTypeID', 'type id': 'AssociationTypeID',
                    'website': 'Associationwebsite', 'site': 'Associationwebsite', 'url': 'Associationwebsite',
                    'email': 'AssociationEmailaddress', 'email address': 'AssociationEmailaddress',
                    'phone': 'AssociationPhone', 'toll-free phone': 'AssociationTollFreePhone', 'toll free phone': 'AssociationTollFreePhone',
                    'fax': 'AssociationFax',
                    'street 1': 'AssociationStreet1', 'street1': 'AssociationStreet1',
                    'street 2': 'AssociationStreet2', 'street2': 'AssociationStreet2',
                    'city': 'AssociationCity', 'state': 'AssociationState', 'country': 'AssociationCountry',
                    'zip': 'AssociationZip', 'postal': 'AssociationZip', 'postal code': 'AssociationZip',
                    'sent welcome email': 'SentWelcomeEmail',
                    'offered free membership': 'OfferedFreeMembership',
                    'accepted free membership': 'AcceptedFreeMembership',
                    'offered free association website': 'OfferedFreeAssociationWebsite',
                    'accepted free membership website': 'AcceptedFreeMembershipWebsite',
                    'show address': 'AssociationShowAddress',
                    'farmers market': 'FarmersMarket',
                    'food hub': 'FoodHub',
                    'csa': 'CSA',
                    'livestock': 'Livestock',
                    'farmag': 'FarmAg',
                    'facebook': 'AssociationFacebook',
                    'instagram': 'AssociationInstagram',
                    'twitter': 'AssociationX', 'x': 'AssociationX',
                    'linkedin': 'AssociationLinkedIn',
                    'pinterest': 'AssociationPinterest',
                    'youtube': 'AssociationYouTube',
                    'blog': 'AssociationBlog',
                    'truth social': 'AssociationTruthSocial',
                    'other social 1': 'AssociationOtherSocial1',
                    'other social 2': 'AssociationOtherSocial2',
                    'description': 'AssociationDescription',
                    'logo': 'AssociationLogo',
                    'password': 'AssociationPassword',
                    'contact name': 'AssociationContactName',
                    'contact position': 'AssociationContactPosition',
                    'contact email': 'AssociationContactEmail',
                    'activation code': 'AssociationActivationCode',
                    'position': 'Position',
                    'country id': 'country_id',
                }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=association_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                        "📝 **Create new association**\n\n"
                        "Tell me the fields to add — for example:\n"
                        "`create association association name: Alpaca Breeders Hub, acronym: ABH, website: https://abh.org, email: hello@abh.org, phone: 800-555-0100, city: Denver, state: CO`\n"
                        "You can also paste a Python/JSON dict like:\n"
                        "`{\"AssociationName\": \"Alpaca Breeders Hub\", \"AssociationAcronym\": \"ABH\", \"Associationwebsite\": \"https://abh.org\", \"AssociationEmailaddress\": \"hello@abh.org\", \"AssociationPhone\": \"800-555-0100\", \"AssociationCity\": \"Denver\", \"AssociationState\": \"CO\", \"AssociationCountry\": \"USA\"}`"
                    )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                    f"- **{self.get_user_friendly_field_name_association(k).title()}**: {v}"
                    for k, v in data.items()
                )

                self.pending_create_associations = data

                return (
                    "🆕 **Confirm Create (Association)**\n\n"
                    f"You’re about to create a new association with:\n{preview}\n\n"
                    "Confirm with **'yes'** or cancel with **'no'**."
            )
            
            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which association record (e.g., 'association id 5', 'association name \"Alpaca Breeders\"', or 'acronym \"ABH\"')."
                result = associations_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_association(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in [
                            'AssociationID','AssociationName','AssociationAcronym','Associationwebsite','AssociationEmailaddress',
                            'AssociationPhone','AssociationCity','AssociationState','AssociationCountry','AssociationType',
                            'AssociationFacebook','AssociationInstagram','AssociationX','AssociationLinkedIn','AssociationYouTube',
                            'AssociationTollFreePhone','AssociationFax'
                        ] if k in ASSOCIATIONS_COLUMNS]
                        lines = ["🏢 **Association Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None,""]:
                                label = self.get_user_friendly_field_name_association(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in ASSOCIATIONS_COLUMNS if k not in show_keys and record.get(k) not in [None,""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching association record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which association row to update. Include 'association id <n>', or 'association name \"...\"', or 'acronym \"...\"'."
                if not field:
                    return "❌ I couldn't understand which association field you want to update. Try 'set website to https://…' or 'update facebook to …'."
                current = associations_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_association(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                self.pending_update_association = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Association Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which association row to modify. Include an identifier (e.g., 'association id 10')."
                if not field:
                    return "❌ Please specify which association field to clear (e.g., 'AssociationWebsite', 'AssociationFacebook')."
                current = associations_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current association data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_association(field)
                self.pending_delete_association = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Association)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Awards flow -----
        if is_awards:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_awards_identifier(user_input)
            field = self._extract_awards_field(user_input, conversation_history)

            if action == "create":
                awards_field_map = {
                    'awards id': 'AwardsID', 'award id': 'AwardsID',
                    'animal id': 'ID', 'animal': 'ID', 'id': 'ID',
                    'show name': 'ShowName', 'show': 'ShowName', 'event': 'ShowName',
                   'award year': 'AwardYear', 'year': 'AwardYear',
                    'type': 'Type', 'award type': 'Type',
                    'placing number': 'PlacingNumber', 'place number': 'PlacingNumber', 'placing #': 'PlacingNumber',
                    'placing': 'Placing', 'place': 'Placing', 'rank': 'Placing',
                    'class': 'Class', 'class name': 'Class',
                    'judge': 'Judge',
                    'show year': 'ShowYear',
                    'comments': 'Awardcomments', 'award comments': 'Awardcomments', 'notes': 'Awardcomments',
                    'show level': 'ShowLevel', 'level': 'ShowLevel',
                }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=awards_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                        "📝 **Create new award record**\n\n"
                        "Tell me the fields to add — for example:\n"
                        "`create award animal id: 42, show name: National Fleece Show, award year: 2024, type: Color Champion, placing: 1st`\n"
                        "You can also paste a Python/JSON dict like:\n"
                        "`{\"ID\": 42, \"ShowName\": \"National Fleece Show\", \"AwardYear\": 2024, \"Type\": \"Color Champion\", \"Placing\": \"1st\", \"Class\": \"Fleece\", \"Judge\": \"J. Doe\", \"ShowLevel\": \"National\"}`"
                 )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                    f"- **{self.get_user_friendly_field_name_awards(k).title()}**: {v}"
                    for k, v in data.items()
                )

                self.pending_create_awards = data

                return (
                    "🆕 **Confirm Create (Awards)**\n\n"
                    f"You’re about to create a new awards record with:\n{preview}\n\n"
                    "Confirm with **'yes'** or cancel with **'no'**."
            )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which awards record (e.g., 'awards id 12', 'animal id 42', 'show name \"National Fleece\" award year 2023', or 'for animal \"Storm Runner\"')."
                result = awards_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_awards(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in ['AwardsID','ID','ShowName','AwardYear','Type','PlacingNumber','Placing','Class','Judge','ShowYear','Awardcomments','ShowLevel'] if k in AWARDS_COLUMNS]
                        lines = ["🏆 **Awards Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None,""]:
                                label = self.get_user_friendly_field_name_awards(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in AWARDS_COLUMNS if k not in show_keys and record.get(k) not in [None,""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching awards record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which awards row to update. Include 'awards id <n>', or combine keys like 'animal id <n> show name \"XYZ\" award year 2024'."
                if not field:
                    return "❌ I couldn't understand which awards field you want to update. Try 'set Placing to 1st' or 'update Judge to Jane Doe'."
                current = awards_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_awards(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                self.pending_update_awards = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Awards Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which awards row to modify. Include an identifier (e.g., 'awards id 10')."
                if not field:
                    return "❌ Please specify which awards field to clear (e.g., 'Placing', 'Judge', 'Class')."
                current = awards_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current awards data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_awards(field)
                self.pending_delete_awards = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Awards)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Animal Stats flow -----
        if is_animalstats:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_stats_identifier(user_input)
            field = self._extract_stats_field(user_input, conversation_history)

            if action == "create":
                stats_field_map = {
                    'stats id': 'Animalsstatid', 'stat id': 'Animalsstatid', 'animal stats id': 'Animalsstatid',
                    'animal id': 'AnimalID', 'animal': 'AnimalID', 'id': 'AnimalID',
                    'stat date': 'StatDate', 'date': 'StatDate',
                    'website id': 'WebsiteID', 'site id': 'WebsiteID',
                    'website name': 'Websitename', 'site name': 'Websitename',
                    'animal name': 'AnimalName', 'name': 'AnimalName',
                    'people id': 'PeopleID', 'owner id': 'PeopleID',
                }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=stats_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                        "📝 **Create new animal stats**\n\n"
                        "Tell me the fields to add — for example:\n"
                        "`create animal stats animal id: 42, stat date: 2025-01-15, website id: 3, website name: Main Site`\n"
                        "You can also paste a Python/JSON dict like:\n"
                        "`{\"AnimalID\": 42, \"StatDate\": \"2025-01-15\", \"WebsiteID\": 3, \"Websitename\": \"Main Site\", \"AnimalName\": \"Storm Runner\", \"PeopleID\": 101}`"
                    )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                    f"- **{self.get_user_friendly_field_name_stats(k).title()}**: {v}"
                    for k, v in data.items()
                )

                self.pending_create_animal_stats = data

                return (
                    "🆕 **Confirm Create (Animal Stats)**\n\n"
                    f"You’re about to create a new animal stats record with:\n{preview}\n\n"
                    "Confirm with **'yes'** or cancel with **'no'**."
                )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which stats record (e.g., 'stats id 9', 'animal id 42 on stat date 2024-05-01', 'website id 3', or 'for animal \"Storm Runner\"')."
                result = animalstats_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_stats(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in ['Animalsstatid','AnimalID','AnimalName','StatDate','WebsiteID','Websitename','PeopleID'] if k in ANIMALSTATS_COLUMNS]
                        lines = ["📈 **Animal Stats Record:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None,""]:
                                label = self.get_user_friendly_field_name_stats(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in ANIMALSTATS_COLUMNS if k not in show_keys and record.get(k) not in [None,""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching animal stats record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which stats row to update. Include 'stats id <n>' or combine keys like 'animal id <n> on stat date YYYY-MM-DD'."
                if not field:
                    return "❌ I couldn't understand which stats field you want to update. Try 'set WebsiteID to 3' or 'update WebsiteName to Main Site'."
                current = animalstats_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_stats(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                self.pending_update_stats = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Animal Stats Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which stats row to modify. Include an identifier (e.g., 'stats id 10', or 'animal id <n> on stat date YYYY-MM-DD')."
                if not field:
                    return "❌ Please specify which stats field to clear (e.g., 'WebsiteName', 'AnimalName')."
                current = animalstats_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current stats data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_stats(field)
                self.pending_delete_stats = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Animal Stats)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Animal Registration flow -----
        if is_animalregistration:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_registration_identifier(user_input)
            field = self._extract_registration_field(user_input, conversation_history)

            if action == "create":
                registration_field_map = {
                    'animal registration id': 'AnimalRegistrationID', 'registration id': 'AnimalRegistrationID', 'reg id': 'AnimalRegistrationID',
                    'animal id': 'AnimalID', 'animal': 'AnimalID', 'id': 'AnimalID', 'animalid': 'AnimalID',
                    'registration type': 'RegType', 'reg type': 'RegType', 'type': 'RegType',
                    'registration number': 'RegNumber', 'reg number': 'RegNumber', 'reg no': 'RegNumber', 'reg#': 'RegNumber', 'number': 'RegNumber',
                }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=registration_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                        "📝 **Create new animal registration**\n\n"
                        "Tell me the fields to add — for example:\n"
                        "`create animal registration animal id: 42, registration type: AOA, registration number: 12345`\n"
                        "You can also paste a Python/JSON dict like:\n"
                        "`{\"AnimalID\": 42, \"RegType\": \"AOA\", \"RegNumber\": \"12345\"}`"
                )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                    f"- **{self.get_user_friendly_field_name_registration(k).title()}**: {v}"
                    for k, v in data.items()
                )

                self.pending_create_animalregistration = data

                return (
                    "🆕 **Confirm Create (Animal Registration)**\n\n"
                    f"You’re about to create a new registration record with:\n{preview}\n\n"
                    "Confirm with **'yes'** or cancel with **'no'**."
                )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which registration record (e.g., 'registration id 5', 'animal id 42', or 'for animal \"Storm Runner\"')."
                result = animalregistration_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_registration(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in ['AnimalRegistrationID','AnimalID','RegType','RegNumber'] if k in ANIMALREGISTRATION_COLUMNS]
                        lines = ["📄 **Animal Registration:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None,""]:
                                label = self.get_user_friendly_field_name_registration(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in ANIMALREGISTRATION_COLUMNS if k not in show_keys and record.get(k) not in [None,""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching registration record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which registration row to update. Include 'registration id <n>', 'animal id <n>', or 'for animal \"<Full Name>\"'."
                if not field:
                    return "❌ I couldn't understand which registration field you want to update. Try 'set RegNumber to ABC123' or 'update RegType to CLAA'."
                current = animalregistration_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_registration(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                self.pending_update_registration = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Registration Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which registration row to modify. Include an identifier (e.g., 'registration id 7')."
                if not field:
                    return "❌ Please specify which registration field to clear (e.g., 'RegNumber', 'RegType')."
                current = animalregistration_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current registration data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_registration(field)
                self.pending_delete_registration = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Registration)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Ancestry Percents flow -----
        if is_ancestrypercents:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_percent_identifier(user_input)
            field = self._extract_percent_field(user_input, conversation_history)

            if action == "create":
                percent_field_map = {
                'peruvian': 'PercentPeruvian', 'percent peruvian': 'PercentPeruvian',
                'bolivian': 'PercentBolivian', 'percent bolivian': 'PercentBolivian',
                'chilean': 'PercentChilean', 'percent chilean': 'PercentChilean',
                'accoyo': 'PercentAccoyo', 'percent accoyo': 'PercentAccoyo',
                'unknown': 'PercentUnknownOther', 'unknown/other': 'PercentUnknownOther',
                'percent unknown': 'PercentUnknownOther', 'percent unknown/other': 'PercentUnknownOther',
                'animal id': 'ID', 'animal': 'ID', 'id': 'ID', 'animalid': 'ID',
                'owner id': 'OwnerID', 'ownerid': 'OwnerID', 'owner': 'OwnerID',
                'percent id': 'PercentID', 'percentid': 'PercentID'
            }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=percent_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                    "📝 **Create new ancestry percents**\n\n"
                    "Tell me the fields to add — for example:\n"
                    "`create ancestry percents animal id: 123, peruvian: 50, bolivian: 25, chilean: 25`\n"
                    "You can also paste a Python/JSON dict like:\n"
                    "`{\"ID\": 123, \"PercentPeruvian\": 50, \"PercentBolivian\": 25, \"PercentChilean\": 25, \"PercentAccoyo\": 0, \"PercentUnknownOther\": 0}`"
                )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                    f"- **{self.get_user_friendly_field_name_percent(k).title()}**: {v}"
                    for k, v in data.items()
                )

                self.pending_create_ancestry_percent = data

                return (
                "🆕 **Confirm Create (Ancestry Percents)**\n\n"
                f"You’re about to create a new ancestry percents record with:\n{preview}\n\n"
                "Confirm with **'yes'** or cancel with **'no'**."
                )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which ancestry percents row (e.g., 'percent id 10', 'animal id 42', 'owner id ABC123', or 'for animal \"Storm Runner\"')."
                result = ancestrypercents_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_percent(field)
                        if val not in [None, ""]:
                            return f"✅ {friendly.title()} is **{val}**."
                        else:
                            return f"❌ {friendly.title()} is not set."
                    else:
                        show_keys = [k for k in ['PercentPeruvian','PercentBolivian','PercentChilean','PercentAccoyo','PercentUnknownOther','OwnerID','ID','PercentID'] if k in ANCESTRYPERCENTS_COLUMNS]
                        lines = ["📊 **Ancestry Percents:**",""]
                        for k in show_keys:
                            if record.get(k) not in [None,""]:
                                label = self.get_user_friendly_field_name_percent(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in ANCESTRYPERCENTS_COLUMNS if k not in show_keys and record.get(k) not in [None,""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching ancestry percents record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which ancestry percents row to update. Include 'percent id <n>', 'animal id <n>', or 'owner id <code>'."
                if not field:
                    return "❌ I couldn't understand which ancestry percent field you want to update. Try 'set Peruvian to 50%' or 'update PercentBolivian to 25'."
                current = ancestrypercents_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_percent(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                self.pending_update_percent = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Ancestry Percent Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which ancestry percents row to modify. Include an identifier (e.g., 'percent id 10')."
                if not field:
                    return "❌ Please specify which ancestry percent field to clear (e.g., 'PercentPeruvian', 'PercentUnknownOther')."
                current = ancestrypercents_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current ancestry percents data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_percent(field)
                self.pending_delete_percent = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Ancestry Percents)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )
            else:
                return "I couldn't understand your request. Please try again."

        # ----- Ancestors flow -----
        if is_ancestor:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_ancestor_identifier(user_input)
            field = self._extract_ancestor_field(user_input, conversation_history)

            if action == "create":
                # ---------- ANCESTORS: create ----------
                ancestor_field_map = {    
                    'name': 'AncestorName', 'full name': 'AncestorName', 'fullname': 'AncestorName',
                    'sire': 'Sire', 'dam': 'Dam', 'bloodline': 'Bloodline', 'lineage': 'Bloodline',
                    'pedigree': 'Pedigree',
                    'ari': 'ARINumber', 'ari number': 'ARINumber',
                    'claa': 'CLAANumber', 'claa number': 'CLAANumber',
                    'registration': 'RegistrationNumber', 'registration number': 'RegistrationNumber',
                    'sex': 'Sex', 'gender': 'Sex', 'generation': 'Generation',
                    'notes': 'Notes', 'comment': 'Notes', 'comments': 'Notes'
                }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=ancestor_field_map)

                if not data and field and value:
                    data = {field: value}

                if not data:
                    return (
                        "📝 **Create new ancestor**\n\n"
                        "Tell me the fields to add — for example:\n"
                        "`create ancestor name: Highland Prince, sire: Snowmass Elite, dam: Andean Rose, ARI: 35012345`\n"
                        "You can also paste a Python/JSON dict like:\n"
                        "`{\"AncestorName\": \"Highland Prince\", \"Sire\": \"Snowmass Elite\", \"Dam\": \"Andean Rose\", \"ARINumber\": \"35012345\"}`"
                    )

                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                    f"- **{self.get_user_friendly_field_name_ancestor(k).title()}**: {v}"
                    for k, v in data.items()
                )

                self.pending_create_ancestor = data
                return (
                    "🆕 **Confirm Create (Ancestors)**\n\n"
                    f"You’re about to create a new ancestor with:\n{preview}\n\n"
                    "Confirm with **'yes'** or cancel with **'no'**."
            )

            if action == "read":
                if not identifier:
                    return "🛈 Please specify which ancestor record (e.g., 'ancestor id 42', 'address id 7', or 'for animal \"Storm Runner\"')."
                result = ancestors_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_ancestor(field)
                        if val not in [None, ""]:
                            return f"✅ Ancestor {friendly} is **{val}**."
                        else:
                            return f"❌ Ancestor {friendly} is not set."
                    else:
                        keys_to_show = [k for k in ANCESTORS_COLUMNS if k in record and record.get(k) not in [None,""]]
                        lines = ["🌳 **Ancestor / Lineage Record:**",""]
                        preview = 0
                        for k in keys_to_show:
                            if preview >= 20: break
                            label = self.get_user_friendly_field_name_ancestor(k).title()
                            lines.append(f"- {label}: {record.get(k)}")
                            preview += 1
                        rem = max(0, len(keys_to_show)-preview)
                        if rem:
                            lines.append(f"…and {rem} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching ancestor record."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which ancestor record you want to update. Include 'ancestor id <n>' or 'for animal \"<Full Name>\"'."
                if not field:
                    return "❌ I couldn't understand which ancestor field you want to update. Try 'update Sire to X' or 'set Dam CLAA to …'."
                current = ancestors_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_ancestor(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update Ancestor {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                self.pending_update_ancestor = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Ancestor Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which ancestor record you want to modify. Include 'ancestor id <n>' or 'for animal \"<Full Name>\"'."
                if not field:
                    return "❌ I couldn't understand which ancestor field you want to clear. Please specify a field (e.g., 'Sire', 'Dam', 'Dam CLAA')."
                current = ancestors_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current ancestor data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_ancestor(field)
                self.pending_delete_ancestor = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Ancestor)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- Animals flow -----
        if action is None:
            return "❌ **User ID not found!** I cannot process user data requests without a valid user ID. Please ensure you're logged in with a valid session."
        
        if is_animal:
            action = self._extract_action_generic(user_input)
            identifier = self._extract_animal_identifier(user_input)
            field = self._extract_animal_field(user_input, conversation_history)
            
            if action == "create":
                animal_field_map = {
                    'name': 'FullName', 'full name': 'FullName', 'fullname': 'FullName',
                    'short': 'ShortName', 'short name': 'ShortName', 'shortname': 'ShortName',
                    'breed': 'Breed', 'category': 'Category', 'horns': 'Horns',
                    'lot': 'LotNumber', 'lot number': 'LotNumber', 'microchip': 'MicrochipNumber', 
                    'chip': 'MicrochipNumber',
                    'microchip number': 'MicrochipNumber', 'chip number': 'MicrochipNumber',
                    'description': 'Description', 'desc': 'Description',
                    'stud description': 'StudDescription', 'studdesc': 'StudDescription',
                    'owner': 'Owner',
                    'weight': 'Weight', 'height': 'Height',
                    'temperament': 'Temperament', 'temperment': 'Temperament',
                    'skills': 'Skills', 'age class': 'AgeClass',
                    'gaited': 'Gaited', 'warmblooded': 'Warmblooded',
                    'markings': 'Markings',
                    'why on abh': 'WhyOnABH'
                }

                raw_pairs = self._parse_create_kv_pairs(user_input)
                data = self._normalize_fields(raw_pairs, field_map=animal_field_map)

                if not data and field and value:
                    # allow explicit single field/value create path
                    data = {field: value}

                if not data:
                    return (
                        "📝 **Create new animal**\n\n"
                        "Tell me the fields to add — for example:\n"
                        "`create animal full name: Starfire, breed: Huacaya, lot number: L-102, microchip: 985141000123456`\n"
                        "You can also paste a Python/JSON dict like:\n"
                        "`{\"FullName\": \"Starfire\", \"Breed\": \"Huacaya\", \"LotNumber\": \"L-102\", \"MicrochipNumber\": \"985141000123456\"}`"
                )

                # tidy strings
                for k in list(data.keys()):
                    if isinstance(data[k], str):
                        data[k] = data[k].strip()

                preview = "\n".join(
                    f"- **{self.get_user_friendly_field_name_animal(k).title()}**: {v}"
                    for k, v in data.items()
                )

                self.pending_create_animal = data
                return (
                    "🆕 **Confirm Create (Animals)**\n\n"
                    f"You’re about to create a new animal with:\n{preview}\n\n"
                    "Confirm with **'yes'** or cancel with **'no'**."
                )

            elif action == "read":
                if not identifier:
                    return "🛈 Please specify which animal (e.g., 'lot 12', 'microchip ABC123', or `animal \"Storm Runner\"`)."
                result = animals_tool('read', identifier)
                if result and isinstance(result, list) and len(result) > 0:
                    record = result[0]
                    if field:
                        val = record.get(field, None)
                        friendly = self.get_user_friendly_field_name_animal(field)
                        if val not in [None, ""]:
                            return f"✅ Animal {friendly} is **{val}**."
                        else:
                            return f"❌ Animal {friendly} is not set."
                    else:
                        show_keys = [
                            'FullName','ShortName','Breed','Category','Horns','LotNumber','MicrochipNumber',
                            'Owner','Weight','Height','Temperment','Skills','Description','StudDescription',
                            'AgeClass','Gaited','Warmblooded','Markings','WhyOnABH'
                        ]
                        lines = ["🦙 **Animal Record:**",""]
                        for k in show_keys:
                            if k in ANIMALS_COLUMNS and record.get(k) not in [None, ""]:
                                label = self.get_user_friendly_field_name_animal(k).title()
                                lines.append(f"- {label}: {record.get(k)}")
                        others = [k for k in ANIMALS_COLUMNS if k not in show_keys and record.get(k) not in [None,""]]
                        if others:
                            lines.append("")
                            lines.append(f"…and {len(others)} more fields present.")
                        return "\n".join(lines)
                else:
                    return "❌ Sorry, I couldn't find any matching animal with that reference."

            elif action == "update":
                if not identifier:
                    return "❌ I couldn't determine which animal you want to update. Include 'lot <id>', 'microchip <id>', 'animal \"<Full Name>\"', or 'id <n>'."
                if not field:
                    return "❌ I couldn't understand which animal field you want to update. Try 'update breed to X' or 'set description to …'."
                current = animals_tool('read', identifier)
                current_val = None
                if current and isinstance(current, list) and len(current) > 0:
                    current_val = current[0].get(field, None)
                new_value = self._extract_update_value_generic(user_input)
                friendly = self.get_user_friendly_field_name_animal(field)
                if not new_value:
                    cur = current_val if current_val else 'Not set'
                    return f"📝 **Update Animal {friendly.title()}**\n\nCurrent value: **{cur}**\n\nWhat should it be changed to?"
                self.pending_update_animal = (field, new_value, identifier)
                return (
                    "🔄 **Confirm Animal Update**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val if current_val else 'Not set'}\n"
                    f"**New value:** {new_value}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            elif action == "delete":
                if not identifier:
                    return "❌ I couldn't determine which animal you want to modify. Include an animal reference (e.g., 'lot 12')."
                if not field:
                    return "❌ I couldn't understand which animal field you want to clear. Please specify a field (e.g., 'description', 'owner', 'breed')."
                current = animals_tool('read', identifier)
                if not current or not isinstance(current, list) or len(current) == 0:
                    return "❌ Sorry, I couldn't find the current animal data."
                current_val = current[0].get(field, 'Not set')
                friendly = self.get_user_friendly_field_name_animal(field)
                self.pending_delete_animal = (field, identifier)
                return (
                    "🗑️ **Confirm Clear (Animal)**\n\n"
                    f"**Field:** {friendly.title()}\n"
                    f"**Current value:** {current_val}\n\n"
                    "Confirm with 'yes' or cancel with 'no'."
                )

            else:
                return "I couldn't understand your request. Please try again."

        # ----- People flow -----
        action, field, value, detected_people_id = self.extract_user_intent(user_input, conversation_history, people_id)
        if action is None:
            return "❌ **User ID not found!** I cannot process user data requests without a valid user ID. Please ensure you're logged in with a valid session."
        
        target_people_id = detected_people_id if detected_people_id else people_id

        if action == "create":
            people_field_map = {
                'username': 'UserName', 'user name': 'UserName', 'login': 'UserName',
                'first name': 'PeopleFirstName', 'firstname': 'PeopleFirstName',
                'last name': 'PeopleLastName', 'lastname': 'PeopleLastName', 'surname': 'PeopleLastName',
                'middle initial': 'PeopleMiddleInitial', 'middle': 'PeopleMiddleInitial',
                'phone': 'PeoplePhone', 'telephone': 'PeoplePhone', 'landline': 'PeoplePhone',
                'cell': 'PeopleCell', 'mobile': 'PeopleCell', 'cellphone': 'PeopleCell',
                'fax': 'PeopleFax', 'email': 'PeopleEmail', 'e-mail': 'PeopleEmail', 'mail': 'PeopleEmail',
                'bio': 'PeopleBio', 'biography': 'PeopleBio', 'about': 'PeopleBio',
                'first': 'PeopleFirstName', 'last': 'PeopleLastName', 'name': 'PeopleFirstName',
                'user': 'UserName'
            }

            raw_pairs = self._parse_create_kv_pairs(user_input)
            data = self._normalize_fields(raw_pairs, field_map=people_field_map)

            if not data and field and value:
                data = {field: value}

            if not data:
                return (
                    "📝 **Create new profile**\n\n"
                    "Tell me the fields to add — for example:\n"
                    "`create user first name: John, last name: Doe, email: john@doe.com`\n"
                    "You can also paste a Python/JSON dict like:\n"
                    "`{\"PeopleFirstName\": \"John\", \"PeopleLastName\": \"Doe\", \"PeopleEmail\": \"john@doe.com\"}`"
            )

            for k in list(data.keys()):
                if isinstance(data[k], str):
                    data[k] = data[k].strip()

            preview = "\n".join(f"- **{self.get_user_friendly_field_name(k).title()}**: {v}" for k, v in data.items())
            self.pending_create = data
            return (
                "🆕 **Confirm Create (People)**\n\n"
                f"You’re about to create a new profile with:\n{preview}\n\n"
                "Confirm with **'yes'** or cancel with **'no'**."
            )
        
        elif action == "read":
            result = people_tool('read', identifier={'PeopleID': target_people_id})
            if result and isinstance(result, list) and len(result) > 0:
                person = result[0]
                if field:
                    field_value = person.get(field, 'Not set')
                    if field_value:
                        return f"✅ Your {self.get_user_friendly_field_name(field)} is **{field_value}**"
                    else:
                        return f"❌ Your {self.get_user_friendly_field_name(field)} is not set."
                else:
                    lines = ["👤 **Your Profile Information:**",""]
                    name_fields = ['PeopleFirstName','PeopleMiddleInitial','PeopleLastName']
                    contact_fields = ['PeoplePhone','PeopleCell','PeopleFax','PeopleEmail']
                    account_fields = ['UserName','PeopleBio']
                    name_parts = [person.get(n) for n in name_fields if person.get(n)]
                    if name_parts:
                        lines.append(f"**Name:** {' '.join(name_parts)}")
                    lines.append("")
                    lines.append("**Contact Information:**")
                    for f in contact_fields:
                        v = person.get(f)
                        if v:
                            lines.append(f"  • {self.get_user_friendly_field_name(f).title()}: {v}")
                    lines.append("")
                    lines.append("**Account Information:**")
                    for f in account_fields:
                        v = person.get(f)
                        lines.append(f"  • {self.get_user_friendly_field_name(f).title()}: {v if v else 'Not set'}")
                    return "\n".join(lines)
            else:
                return f"❌ Sorry, I couldn't find user data for PeopleID {target_people_id}. Please check if the ID is correct."
        
        elif action == "update":
            if not field:
                return "❌ I couldn't understand what field you want to update. Please specify the field name (like 'email', 'phone', 'username', etc.)."
            current_data = people_tool('read', identifier={'PeopleID': target_people_id})
            current_value = "Not set"
            if current_data and isinstance(current_data, list) and len(current_data) > 0:
                current_value = current_data[0].get(field, 'Not set')
            if not value:
                return (
                    f"📝 **Update {self.get_user_friendly_field_name(field).title()}**\n\n"
                    f"Your current {self.get_user_friendly_field_name(field)}: **{current_value}**\n\n"
                    f"What would you like to change it to?"
                )
            self.pending_update = (field, value, target_people_id)
            return (
                "🔄 **Confirm Update**\n\n"
                f"**Field:** {self.get_user_friendly_field_name(field).title()}\n"
                f"**Current value:** {current_value}\n"
                f"**New value:** {value}\n\n"
                "Are you sure you want to update? Reply 'yes' to confirm or 'no' to cancel."
            )
        
        elif action == "delete":
            if not field:
                return "❌ I couldn't understand what field you want to clear. Please specify the field name (like 'email', 'phone', 'username', etc.)."
            current_data = people_tool('read', identifier={'PeopleID': target_people_id})
            if not current_data or not isinstance(current_data, list) or len(current_data) == 0:
                return f"❌ Sorry, I couldn't find your current data. Please try again."
            current_person = current_data[0]
            current_value = current_person.get(field, 'Not set')
            self.pending_delete = (field, target_people_id)
            return (
                "🗑️ **Confirm Clear**\n\n"
                f"**Field:** {self.get_user_friendly_field_name(field).title()}\n"
                f"**Current value:** {current_value}\n\n"
                "Are you sure you want to clear this field? Reply 'yes' to confirm or 'no' to cancel."
            )
        
        else:
            return "I couldn't understand your request. Please try again."


# Create the UserDataAgent with the wrapper
user_data_agent_wrapper = UserDataAgentWrapper(
    id_field="PeopleID",
    id_label="USER ID",
    table_name="people",
    columns=PEOPLE_COLUMNS,
    tool_func=people_tool,
    field_synonyms=None
)

# Create the actual UserDataAgent
user_data_agent = autogen.AssistantAgent(
    name=USERDATAAGENT_NAME,
    llm_config={
        "config_list": autogen_llm_config_list,
        "temperature": 0.2,
    },
    system_message=(
        "You are a Data Specialist. You can read, update, or delete user profile fields in the people table, "
        "and you can also read/update/clear fields on animal, ancestor (lineage), ancestry percents, animal registration, "
        "animal stats, awards, associations, and association members records. "
        f"For people you have access to: {', '.join(PEOPLE_COLUMNS)}. Use the provided PeopleID to look up users. "
        f"For animals you can use keys like LotNumber, MicrochipNumber, FullName, or ID. Available animal fields include: {', '.join(ANIMALS_COLUMNS)} "
        f"For ancestors you can use keys like ID (animal ID) or AddressID; available fields include: {', '.join(ANCESTORS_COLUMNS)} "
        f"For ancestry percents you can use keys like PercentID, ID (animal id), or OwnerID; available fields include: {', '.join(ANCESTRYPERCENTS_COLUMNS)}. "
        f"For animal registrations you can use keys like AnimalRegistrationID or AnimalID; available fields include: {', '.join(ANIMALREGISTRATION_COLUMNS)}. "
        f"For animal stats you can use keys like Animalsstatid, AnimalID, StatDate, or WebsiteID; available fields include: {', '.join(ANIMALSTATS_COLUMNS)}. "
        f"For awards you can use keys like AwardsID, ID (animal id), ShowName, or AwardYear; available fields include: {', '.join(AWARDS_COLUMNS)}. "
        f"For associations you can use keys like AssociationID, AssociationName, or AssociationAcronym; available fields include: {', '.join(ASSOCIATIONS_COLUMNS[:25])} ... "
        f"For association members you can use keys like associationmemberID or PeopleID+AssociationID; available fields include: {', '.join(ASSOCIATIONMEMBERS_COLUMNS)}. "
        f"For businesses you can use keys like BusinessID, BusinessName, BusinessAcronym, Contact1PeopleID (people id), BusinessWebsiteID, WebsitesID, AddressID, or PhoneID; available fields include: {', '.join(BUSINESS_COLUMNS[:25])} ... "
        f"For color lookup you can use keys like ColorID, Color, or Abbreviation; available fields include: {', '.join(COLORLOOKUP_COLUMNS)}. "
        f"For colors you can use keys like ColorID or ID; available fields include: {', '.join(COLORS_COLUMNS)}. "
        f"For country you can use keys like country_id, iso_code, or name; available fields include: {', '.join(COUNTRY_COLUMNS)}. "
        f"For fiber you can use keys like FiberID, ID, and optionally SampleDate/Month/Day/Year; available fields include: {', '.join(FIBER_COLUMNS)}. "
        f"For people title lookup you can use keys like PeopletitleID or PeopleTitle; available fields include: {', '.join(PEOPLETITLELOOKUP_COLUMNS)}. "
        f"For sire you can use keys like SireID, SiresName, or SiresRegistration; available fields include: {', '.join(SIRE_COLUMNS)}. "
        f"For species breed lookup you can use keys like BreedLookupID, Breed (+ optional SpeciesID), or BreedAnimalID; available fields include: {', '.join(SPECIESBREEDLOOKUPTABLE_COLUMNS)}. "
        f"For species category you can use keys like SpeciesCategoryID or SpeciesCategory (optionally with SpeciesID); available fields include: {', '.join(SPECIESCATEGORY_COLUMNS)}. "
        f"For species color lookup you can use keys like SpeciesColorID, or SpeciesID + SpeciesColor; available fields include: {', '.join(SPECIESCOLORLOOKUPTABLE_COLUMNS)}. "
        f"For species registration type lookup you can use keys like SpeciesRegistrationTypeID, SpeciesRegistrationType (optionally with SpeciesID and/or country_id); available fields include: {', '.join(SPECIESREGISTRATIONTYPELOOKUPTABLE_COLUMNS)}. "
        f"For state/province you can use keys like StateIndex, name (optionally with country_id), or abbreviation (optionally with country_id); available fields include: {', '.join(STATE_PROVINCE_COLUMNS)}. "
        f"For states you can use keys like StateID, StateName, or StateAbbreviation; available fields include: {', '.join(STATES_COLUMNS[:20])} ... ",
        f"For male data you can use key ID (animal/male id); available fields include: {', '.join(MALEDATA_COLUMNS)}. "
        "Always ask for confirmation before making changes and provide clear, helpful responses. "
        "Use the people_tool, animals_tool, ancestors_tool, ancestrypercents_tool, animalregistration_tool, animalstats_tool, awards_tool, associations_tool, and associationmembers_tool functions for database operations. "
        "IMPORTANT: Maintain context from previous messages. If a user asks about a field and then says 'change it to X', "
        "understand that 'it' refers to the field they just asked about."
    )
)

# Override the generate_reply method to use the wrapper
def generate_reply_with_wrapper(self, messages, sender=None, config=None):
    return user_data_agent_wrapper.generate_reply(self, messages)

# Replace the agent's generate_reply method with our wrapper version
user_data_agent.generate_reply = generate_reply_with_wrapper.__get__(user_data_agent, type(user_data_agent))

# Register the tools with the UserDataAgent
user_data_agent.register_function(
    function_map={
        "people_tool": people_tool,
        "animals_tool": animals_tool,
        "ancestors_tool": ancestors_tool,
        "ancestrypercents_tool": ancestrypercents_tool,
        "animalregistration_tool": animalregistration_tool,
        "animalstats_tool": animalstats_tool,
        "awards_tool": awards_tool,
        "associations_tool": associations_tool,
        "associationmember_tool": associationmembers_tool,
        "business_tool": business_tool,
        "colorlookup_tool": colorlookup_tool,
        "colors_tool": colors_tool,
        "colors_tool": colors_tool,
        "country_tool": country_tool,
        "fiber_tool": fiber_tool,
        "peopletitlelookup_tool": peopletitlelookup_tool,
        "sire_tool": sire_tool,
        "speciesbreedlookuptable_tool": speciesbreedlookuptable_tool,
        "speciescategory_tool": speciescategory_tool,
        "speciescolorlookuptable_tool": speciescolorlookuptable_tool,
        "speciesregistrationtypelookuptable_tool": speciesregistrationtypelookuptable_tool,
        "state_province_tool": state_province_tool,
        "states_tool": states_tool,
        "maledata_tool": maledata_tool,        
    }
)
