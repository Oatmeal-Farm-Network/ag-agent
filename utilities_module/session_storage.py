# session_storage.py
# Utilities for session-based message storage in CosmosDB
# Implements ChatGPT-like conversation storage with chunking for long conversations

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional
from azure.cosmos import exceptions as CosmosExceptions

from config import conversations_history_container_client 


class SessionStorageManager:
    """Manages session-based message storage in CosmosDB with automatic chunking."""
    
    def __init__(self, container_client=None):
        """Initialize with container client (defaults to chat_history_container_client)."""
        self.container = container_client or conversations_history_container_client
        self.max_messages_per_chunk = 10
    
    def create_session(self, session_id: str, user_id: str) -> Dict:
        """Create a new session document."""
        session_doc = {
            "id": session_id,  # Use UUID directly
            "session_id": session_id,
            "type": "session",  # Disambiguation field
            "user_id": user_id,
            "message_count": 0,
            "chunks": [],
            "current_chunk": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Use upsert to avoid conflicts - will create if not exists, update if exists
        self.container.upsert_item(body=session_doc)
        print(f"Session {session_id} created/updated")
        
        return session_doc
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session document by session ID."""
        try:
            session_doc = self.container.read_item(
                item=session_id,
                partition_key=session_id
            )
            return session_doc
        except CosmosExceptions.CosmosResourceNotFoundError:
            return None
    
    def add_message(self, session_id: str, role: str, content: str, 
                   user_id: str, attachments: List[Dict] = None) -> str:
        """Add a message to a session, always using chunks."""
        
        # Get or create session
        session_doc = self.get_session(session_id)
        if not session_doc:
            session_doc = self.create_session(session_id, user_id)
        
        print(session_doc)
        
        # Create message object with UUID for concurrency safety
        message_id = str(uuid.uuid4())
        new_message = {
            "id": message_id,
            "role": role,  # "user" or "assistant"
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attachments": attachments or []
        }
        
        # Always add to chunks
        self._add_message_to_chunk(session_doc, new_message)
        
        return message_id
    
    def _add_message_to_chunk(self, session_doc: Dict, message: Dict):
        """Add message to chunk, creating first chunk if needed."""
        
        # Create first chunk if it doesn't exist
        if not session_doc['current_chunk']:
            chunk_id = f"{session_doc['id']}_chunk_1"
            chunk_doc = {
                "id": chunk_id,
                "type": "chunk",
                "session_id": session_doc['id'],
                "chunk_number": 1,
                "message_count": 0,
                "message_range": "1-1",
                "messages": []
            }
            
            try:
                self.container.create_item(body=chunk_doc)
            except CosmosExceptions.CosmosResourceExistsError:
                # Chunk already exists, read it instead
                print(f"Chunk {chunk_id} already exists, reading existing chunk")
                chunk_doc = self.container.read_item(
                    item=chunk_id,
                    partition_key=session_doc['id']
                )
            
            # Update session document with retry logic
            try:
                session_doc['chunks'].append(chunk_id)
                session_doc['current_chunk'] = chunk_id
                self.container.replace_item(item=session_doc['id'], body=session_doc)
            except CosmosExceptions.CosmosAccessConditionFailedError:
                # Session was modified by another request, re-read and retry
                print(f"Session {session_doc['id']} was modified, re-reading and retrying...")
                session_doc = self.get_session(session_doc['id'])
                if session_doc and chunk_id not in session_doc['chunks']:
                    session_doc['chunks'].append(chunk_id)
                    session_doc['current_chunk'] = chunk_id
                    self.container.replace_item(item=session_doc['id'], body=session_doc)
        else:
            # Get current chunk
            chunk_doc = self.container.read_item(
                item=session_doc['current_chunk'],
                partition_key=session_doc['id']
            )
        
        # Check if chunk is full
        chunk_message_count = chunk_doc.get('message_count', len(chunk_doc['messages']))
        if chunk_message_count >= self.max_messages_per_chunk:
            # Create new chunk
            new_chunk_number = len(session_doc['chunks']) + 1
            new_chunk_id = f"{session_doc['id']}_chunk_{new_chunk_number}"
            
            new_chunk = {
                "id": new_chunk_id,
                "type": "chunk",
                "session_id": session_doc['id'],
                "chunk_number": new_chunk_number,
                "message_count": 0,
                "message_range": f"{chunk_message_count + 1}-{chunk_message_count + 1}",
                "messages": []
            }
            
            try:
                self.container.create_item(body=new_chunk)
            except CosmosExceptions.CosmosResourceExistsError:
                # New chunk already exists, read it instead
                print(f"New chunk {new_chunk_id} already exists, reading existing chunk")
                new_chunk = self.container.read_item(
                    item=new_chunk_id,
                    partition_key=session_doc['id']
                )
            
            # Update session document with retry logic
            try:
                session_doc['chunks'].append(new_chunk_id)
                session_doc['current_chunk'] = new_chunk_id
                self.container.replace_item(item=session_doc['id'], body=session_doc)
            except CosmosExceptions.CosmosAccessConditionFailedError:
                # Session was modified by another request, re-read and retry
                print(f"Session {session_doc['id']} was modified, re-reading and retrying...")
                session_doc = self.get_session(session_doc['id'])
                if session_doc and new_chunk_id not in session_doc['chunks']:
                    session_doc['chunks'].append(new_chunk_id)
                    session_doc['current_chunk'] = new_chunk_id
                    self.container.replace_item(item=session_doc['id'], body=session_doc)
            
            chunk_doc = new_chunk
        
        # Add message to current chunk
        chunk_doc['messages'].append(message)
        chunk_doc['message_count'] = len(chunk_doc['messages'])  # Update count
        chunk_doc['message_range'] = f"{chunk_doc['message_range'].split('-')[0]}-{chunk_doc['message_count']}"
        
        self.container.replace_item(item=chunk_doc['id'], body=chunk_doc)
        
        # Update session metadata with optimistic concurrency
        session_doc['message_count'] += 1
        session_doc['updated_at'] = datetime.now(timezone.utc).isoformat()
        try:
            self.container.replace_item(item=session_doc['id'], body=session_doc)
        except CosmosExceptions.CosmosAccessConditionFailedError:
            # Retry once if there's a concurrency conflict
            print(f"Concurrency conflict on session {session_doc['id']}, retrying...")
            # Re-read the session and try again
            session_doc = self.get_session(session_doc['id'])
            if session_doc:
                session_doc['message_count'] += 1
                session_doc['updated_at'] = datetime.now(timezone.utc).isoformat()
                self.container.replace_item(item=session_doc['id'], body=session_doc)
    
    def get_conversation(self, session_id: str) -> List[Dict]:
        """Get complete conversation for a session."""
        session_doc = self.get_session(session_id)
        if not session_doc:
            return []
        
        # Always load from chunks
        all_messages = []
        
        for chunk_id in session_doc['chunks']:
            try:
                chunk_doc = self.container.read_item(
                    item=chunk_id,
                    partition_key=session_id
                )
                all_messages.extend(chunk_doc['messages'])
            except CosmosExceptions.CosmosResourceNotFoundError:
                print(f"Chunk {chunk_id} not found, skipping...")
                continue
        
        # Sort by timestamp to ensure correct order
        all_messages.sort(key=lambda x: x.get('timestamp', ''))
        
        print(f"Loaded {len(all_messages)} messages for session {session_id}")
        return all_messages
    

# Convenience functions for easy usage
def store_message(session_id: str, role: str, content: str, 
                 user_id: str, attachments: List[Dict] = None) -> str:
    """Store a message in a session."""
    manager = SessionStorageManager()
    return manager.add_message(session_id, role, content, user_id, attachments)

def load_conversation(session_id: str) -> List[Dict]:
    """Load complete conversation for a session."""
    manager = SessionStorageManager()
    conv = manager.get_conversation(session_id)
    filtered = [{"role": msg["role"], "content": msg["content"]} for msg in conv]
    return filtered


