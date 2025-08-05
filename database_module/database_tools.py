# database_module/database_tools.py
import os
import sys
import pyodbc
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database configuration
PEOPLE_COLUMNS = [
    'PeopleFirstName', 'PeopleMiddleInitial', 'PeopleLastName',
    'PeoplePhone', 'PeopleCell', 'PeopleFax', 'PeopleEmail',
    'UserName', 'PeopleBio'
]

# Flag to use mock data instead of real database
USE_MOCK_DATA = False  # Set to False to use real Azure SQL database

# Mock data for testing when database doesn't exist
MOCK_USER_DATA = {
    1234: {
        'PeopleID': 1234,
        'PeopleFirstName': 'Test',
        'PeopleMiddleInitial': 'U',
        'PeopleLastName': 'User',
        'PeoplePhone': '555-123-4567',
        'PeopleCell': '555-987-6543',
        'PeopleFax': '',
        'PeopleEmail': 'test.user@example.com',
        'UserName': 'test_user',
        'PeopleBio': 'Test user for development'
    }
}

class AzureSQLCRUD:
    """Handles CRUD operations for the people table in Azure SQL Database."""
    
    def __init__(self):
        self.connection_string = os.getenv("AZURE_SQL_CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("AZURE_SQL_CONNECTION_STRING environment variable is required")
    
    def _connect(self):
        """Create a database connection."""
        return pyodbc.connect(self.connection_string)
    
    def read_person(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Read person(s) from the database based on filters."""
        sql = f"SELECT PeopleID, {', '.join(PEOPLE_COLUMNS)} FROM people"
        params = []
        
        if filters:
            where_clauses = []
            for col, value in filters.items():
                if col == 'PeopleID':
                    where_clauses.append("PeopleID = ?")
                    params.append(value)
                elif col in PEOPLE_COLUMNS:
                    where_clauses.append(f"{col} = ?")
                    params.append(value)
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
        
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(zip(['PeopleID'] + PEOPLE_COLUMNS, row)) for row in rows]
    
    def update_person(self, identifier: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Update person data in the database."""
        if not identifier or 'PeopleID' not in identifier:
            return "Error: PeopleID is required for updates"
        
        people_id = identifier['PeopleID']
        valid_fields = {k: v for k, v in data.items() if k in PEOPLE_COLUMNS}
        
        if not valid_fields:
            return "Error: No valid fields to update"
        
        set_clauses = [f"{field} = ?" for field in valid_fields.keys()]
        sql = f"UPDATE people SET {', '.join(set_clauses)} WHERE PeopleID = ?"
        params = list(valid_fields.values()) + [people_id]
        
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                return f"Updated {len(valid_fields)} field(s) for PeopleID {people_id}"
        except Exception as e:
            return f"Error updating person: {str(e)}"
    
    def delete_person(self, identifier: Dict[str, Any]) -> str:
        """Delete a person from the database (soft delete by setting fields to NULL)."""
        if not identifier or 'PeopleID' not in identifier:
            return "Error: PeopleID is required for deletion"
        
        people_id = identifier['PeopleID']
        set_clauses = [f"{field} = NULL" for field in PEOPLE_COLUMNS]
        sql = f"UPDATE people SET {', '.join(set_clauses)} WHERE PeopleID = ?"
        
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, [people_id])
                conn.commit()
                return f"Deleted all data for PeopleID {people_id}"
        except Exception as e:
            return f"Error deleting person: {str(e)}"

# Global instance
azure_sql_crud = AzureSQLCRUD()

def people_tool(action: str, identifier: Dict[str, Any], data: Optional[Dict[str, Any]] = None) -> str:
    print(f"[DEBUG] people_tool called with action={action}, identifier={identifier}, data={data}")
    try:
        people_id = identifier.get('PeopleID')
        if not people_id:
            print("[DEBUG] people_tool returning: Error: PeopleID is required for all operations")
            return "Error: PeopleID is required for all operations"
        
        if USE_MOCK_DATA:
            result = _mock_people_operations(action, people_id, data)
            print(f"[DEBUG] people_tool returning: {result}")
            return result
        else:
            result = _real_people_operations(action, people_id, data)
            print(f"[DEBUG] people_tool returning: {result}")
            return result
    
    except Exception as e:
        print(f"[DEBUG] people_tool returning: Database error: {str(e)}")
        return f"Database error: {str(e)}"

def _mock_people_operations(action: str, people_id: int, data: Optional[Dict[str, Any]] = None) -> str:
    """Mock database operations for testing"""
    if action == 'read':
        if people_id in MOCK_USER_DATA:
            return [MOCK_USER_DATA[people_id]]
        else:
            return []
    elif action == 'update':
        if people_id in MOCK_USER_DATA:
            if data:
                for field, value in data.items():
                    if field in PEOPLE_COLUMNS:
                        MOCK_USER_DATA[people_id][field] = value
            return f"Updated person with PeopleID {people_id}"
        else:
            return f"Error: Person with PeopleID {people_id} not found"
    elif action == 'create':
        if people_id in MOCK_USER_DATA:
            return f"Error: Person with PeopleID {people_id} already exists"
        else:
            new_doc = {
                'PeopleID': people_id,
                'PeopleFirstName': data.get('PeopleFirstName', ''),
                'PeopleMiddleInitial': data.get('PeopleMiddleInitial', ''),
                'PeopleLastName': data.get('PeopleLastName', ''),
                'PeoplePhone': data.get('PeoplePhone', ''),
                'PeopleCell': data.get('PeopleCell', ''),
                'PeopleFax': data.get('PeopleFax', ''),
                'PeopleEmail': data.get('PeopleEmail', ''),
                'UserName': data.get('UserName', ''),
                'PeopleBio': data.get('PeopleBio', '')
            }
            MOCK_USER_DATA[people_id] = new_doc
            return f"Created person with PeopleID {people_id}"
    elif action == 'delete':
        if people_id in MOCK_USER_DATA:
            del MOCK_USER_DATA[people_id]
            return f"Deleted person with PeopleID {people_id}"
        else:
            return f"Error: Person with PeopleID {people_id} not found"
    else:
        return f"Error: Unknown action '{action}'"

def _real_people_operations(action: str, people_id: int, data: Optional[Dict[str, Any]] = None) -> str:
    """Real Azure SQL database operations"""
    try:
        if action == 'read':
            return azure_sql_crud.read_person({'PeopleID': people_id})
        elif action == 'update':
            return azure_sql_crud.update_person({'PeopleID': people_id}, data or {})
        elif action == 'create':
            return azure_sql_crud.update_person({'PeopleID': people_id}, data or {})  # Use update for create
        elif action == 'delete':
            return azure_sql_crud.delete_person({'PeopleID': people_id})
        else:
            return f"Error: Unknown action '{action}'"
    except Exception as e:
        return f"Database error: {str(e)}" 