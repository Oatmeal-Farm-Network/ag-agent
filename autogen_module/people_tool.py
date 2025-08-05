import os
import pyodbc
from dotenv import load_dotenv
from typing import Optional, Dict, Any

# Load environment variables
load_dotenv()
AZURE_CONNECTION_STRING = os.getenv('AZURE_SQL_CONNECTION_STRING')

PEOPLE_COLUMNS = [
    'PeopleFirstName', 'PeopleMiddleInitial', 'PeopleLastName',
    'PeoplePhone', 'PeopleCell', 'PeopleFax', 'PeopleEmail',
    'UserName', 'PeopleBio'
]

class PeopleCRUD:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def _connect(self):
        return pyodbc.connect(self.connection_string)

    def create_person(self, data: Dict[str, Any]) -> str:
        columns = [col for col in PEOPLE_COLUMNS if col in data]
        if not columns:
            return "No valid columns provided."
        values = [data[col] for col in columns]
        placeholders = ', '.join(['?'] * len(columns))
        sql = f"INSERT INTO people ({', '.join(columns)}) VALUES ({placeholders})"
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
        return f"Person created with columns: {', '.join(columns)}"

    def read_person(self, filters: Optional[Dict[str, Any]] = None) -> list:
        sql = f"SELECT {', '.join(PEOPLE_COLUMNS)} FROM people"
        params = []
        if filters:
            where_clauses = [f"{col} = ?" for col in filters if col in PEOPLE_COLUMNS]
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
                params = [filters[col] for col in filters if col in PEOPLE_COLUMNS]
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(zip(PEOPLE_COLUMNS, row)) for row in rows]

    def update_person(self, identifier: Dict[str, Any], updates: Dict[str, Any]) -> str:
        set_clauses = [f"{col} = ?" for col in updates if col in PEOPLE_COLUMNS]
        if not set_clauses:
            return "No valid columns to update."
        where_clauses = [f"{col} = ?" for col in identifier if col in PEOPLE_COLUMNS]
        if not where_clauses:
            return "No valid identifier provided."
        sql = f"UPDATE people SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
        params = [updates[col] for col in updates if col in PEOPLE_COLUMNS] + [identifier[col] for col in identifier if col in PEOPLE_COLUMNS]
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
        return f"Updated person where {' AND '.join(where_clauses)}."

    def delete_person(self, identifier: Dict[str, Any]) -> str:
        where_clauses = [f"{col} = ?" for col in identifier if col in PEOPLE_COLUMNS]
        if not where_clauses:
            return "No valid identifier provided."
        sql = f"DELETE FROM people WHERE {' AND '.join(where_clauses)}"
        params = [identifier[col] for col in identifier if col in PEOPLE_COLUMNS]
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
        return f"Deleted person where {' AND '.join(where_clauses)}."

def people_tool(action: str, data: Optional[Dict[str, Any]] = None, identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the people table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = PeopleCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create_person(data or {})
    elif action == 'read':
        return crud.read_person(identifier)
    elif action == 'update':
        return crud.update_person(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete_person(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'." 