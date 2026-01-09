import os
import sys
import pyodbc
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# Environment / path setup
# -----------------------------------------------------------------------------

load_dotenv()

# Add parent directory to path for imports (kept from original file for compatibility)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# -----------------------------------------------------------------------------
# Connection
# -----------------------------------------------------------------------------

AZURE_CONNECTION_STRING = os.getenv("AZURE_SQL_CONNECTION_STRING")
if not AZURE_CONNECTION_STRING:
    raise ValueError("AZURE_SQL_CONNECTION_STRING environment variable is required")

def _connect():
    """Create a database connection using the global connection string."""
    return pyodbc.connect(AZURE_CONNECTION_STRING)

# -----------------------------------------------------------------------------
# PEOPLE: preserved from original database_tools.py (with fixes)
# -----------------------------------------------------------------------------

PEOPLE_COLUMNS = [
    'PeopleFirstName', 'PeopleMiddleInitial', 'PeopleLastName',
    'PeoplePhone', 'PeopleCell', 'PeopleFax', 'PeopleEmail',
    'UserName', 'PeopleBio'
]

USE_MOCK_DATA = False  # Set to True to use the mock path below for people_tool

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

class AzureSQLPeopleCRUD:
    """Handles CRUD operations for the people table in Azure SQL Database."""
    def __init__(self):
        self.connection_string = AZURE_CONNECTION_STRING

    def _connect(self):
        return _connect()

    def read_person(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        sql = f"SELECT PeopleID, {', '.join(PEOPLE_COLUMNS)} FROM people"
        params: List[Any] = []
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
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [dict(zip(['PeopleID'] + PEOPLE_COLUMNS, row)) for row in rows]

    def update_person(self, people_id: int, data: Dict[str, Any]) -> str:
        valid = {k: v for k, v in data.items() if k in PEOPLE_COLUMNS}
        if not valid:
            return "Error: No valid fields to update"
        set_sql = ", ".join([f"{k} = ?" for k in valid.keys()])
        sql = f"UPDATE people SET {set_sql} WHERE PeopleID = ?"
        params = list(valid.values()) + [people_id]
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
        return f"Updated {len(valid)} field(s) for PeopleID {people_id}"

    def upsert_person(self, people_id: int, data: Dict[str, Any]) -> str:
        """Create or update a person by PeopleID."""
        valid = {k: v for k, v in data.items() if k in PEOPLE_COLUMNS}
        if not valid:
            return "Error: No valid fields to upsert"

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(1) FROM people WHERE PeopleID = ?", [people_id])
            exists = cur.fetchone()[0] > 0

            if exists:
                set_sql = ", ".join([f"{k} = ?" for k in valid.keys()])
                sql = f"UPDATE people SET {set_sql} WHERE PeopleID = ?"
                params = list(valid.values()) + [people_id]
                cur.execute(sql, params)
                conn.commit()
                return f"Updated {len(valid)} field(s) for PeopleID {people_id}"
            else:
                cols = ['PeopleID'] + list(valid.keys())
                placeholders = ", ".join(["?"] * len(cols))
                sql = f"INSERT INTO people ({', '.join(cols)}) VALUES ({placeholders})"
                params = [people_id] + list(valid.values())
                cur.execute(sql, params)
                conn.commit()
                return f"Created PeopleID {people_id} with {len(valid)} field(s)"

    def delete_person(self, people_id: int) -> str:
        # Soft delete like the original: set all columns to NULL
        set_sql = ", ".join([f"{c} = NULL" for c in PEOPLE_COLUMNS])
        sql = f"UPDATE people SET {set_sql} WHERE PeopleID = ?"
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, [people_id])
            conn.commit()
        return f"Deleted all data for PeopleID {people_id}"

# Global instance
_people_crud = AzureSQLPeopleCRUD()

def _mock_people_operations(action: str, people_id: int, data: Optional[Dict[str, Any]] = None) -> Any:
    if action == 'read':
        return [MOCK_USER_DATA[people_id]] if people_id in MOCK_USER_DATA else []
    elif action == 'update':
        if people_id in MOCK_USER_DATA:
            if data:
                for k, v in data.items():
                    if k in PEOPLE_COLUMNS:
                        MOCK_USER_DATA[people_id][k] = v
            return f"Updated person with PeopleID {people_id}"
        return f"Error: Person with PeopleID {people_id} not found"
    elif action == 'create':
        if people_id in MOCK_USER_DATA:
            return f"Error: Person with PeopleID {people_id} already exists"
        new_doc = {'PeopleID': people_id, **{c: data.get(c, '') for c in PEOPLE_COLUMNS}}
        MOCK_USER_DATA[people_id] = new_doc
        return f"Created person with PeopleID {people_id}"
    elif action == 'delete':
        if people_id in MOCK_USER_DATA:
            del MOCK_USER_DATA[people_id]
            return f"Deleted person with PeopleID {people_id}"
        return f"Error: Person with PeopleID {people_id} not found"
    else:
        return f"Error: Unknown action '{action}'"

def _real_people_operations(action: str, people_id: int, data: Optional[Dict[str, Any]] = None) -> Any:
    if action == 'read':
        return _people_crud.read_person({'PeopleID': people_id})
    elif action == 'update':
        return _people_crud.upsert_person(people_id, data or {})
    elif action == 'create':
        return _people_crud.upsert_person(people_id, data or {})
    elif action == 'delete':
        return _people_crud.delete_person(people_id)
    else:
        return f"Error: Unknown action '{action}'"

def people_tool(action: str, identifier: Dict[str, Any], data: Optional[Dict[str, Any]] = None) -> Any:
    """Thin wrapper around People CRUD with optional mock path (backward compatible)."""
    people_id = (identifier or {}).get('PeopleID')
    if not people_id:
        return "Error: PeopleID is required for all operations"
    if USE_MOCK_DATA:
        return _mock_people_operations(action, people_id, data)
    return _real_people_operations(action, people_id, data)

# -----------------------------------------------------------------------------
# Reusable CRUD base
# -----------------------------------------------------------------------------

class _BaseCRUD:
    """Reusable CRUD base with strict column allow-listing."""
    TABLE_NAME: str = ""
    COLUMNS: List[str] = []  # allowed set (excludes ID & timestamp columns)

    def _connect(self):
        return _connect()

    # --- helpers
    def _filter_valid_cols(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in (data or {}).items() if k in self.COLUMNS}

    # --- operations
    def create(self, data: Dict[str, Any]) -> str:
        valid = self._filter_valid_cols(data)
        if not valid:
            return "No valid columns provided."
        cols = list(valid.keys())
        vals = list(valid.values())
        placeholders = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO {self.TABLE_NAME} ({', '.join(cols)}) VALUES ({placeholders})"
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, vals)
            conn.commit()
        return f"Row created in {self.TABLE_NAME} with columns: {', '.join(cols)}"

    def read(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        sql = f"SELECT * FROM {self.TABLE_NAME}"
        params: List[Any] = []
        if filters:
            where, params = self._build_where(filters)
            if where:
                sql += " WHERE " + where
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def update(self, identifier: Dict[str, Any], updates: Dict[str, Any]) -> str:
        valid_updates = self._filter_valid_cols(updates)
        if not valid_updates:
            return "No valid columns to update."
        set_sql = ", ".join([f"{k} = ?" for k in valid_updates.keys()])
        where_sql, where_params = self._build_where(identifier or {})
        if not where_sql:
            return "No valid identifier provided."
        sql = f"UPDATE {self.TABLE_NAME} SET {set_sql} WHERE {where_sql}"
        params = list(valid_updates.values()) + where_params
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
        return f"Updated rows in {self.TABLE_NAME} where {where_sql}."

    def delete(self, identifier: Dict[str, Any]) -> str:
        where_sql, where_params = self._build_where(identifier or {})
        if not where_sql:
            return "No valid identifier provided."
        sql = f"DELETE FROM {self.TABLE_NAME} WHERE {where_sql}"
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, where_params)
            conn.commit()
        return f"Deleted rows in {self.TABLE_NAME} where {where_sql}."

    # --- internal
    def _build_where(self, ident: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """Build a WHERE clause. Allow primary key plus whitelisted columns."""
        if not ident:
            return "", []
        clauses: List[str] = []
        params: List[Any] = []
        # Union of PK names from both source files
        pk_names = {
            'PeopleID', 'AnimalID', 'AncestorID', 'AwardsID',
            'ColorID', 'AssociationMemberID', 'AssociationID', 'StateID',
            'BusinessID', 'BusinessAccessID', 'ID'
        }
        for k, v in ident.items():
            if k in pk_names or k in self.COLUMNS:
                clauses.append(f"{k} = ?")
                params.append(v)
        return (" AND ".join(clauses), params)

# -----------------------------------------------------------------------------
# ANIMALS
# -----------------------------------------------------------------------------

ANIMALS_COLUMNS: List[str] = [
    'PublishForSale', 'PublishStud', 'Quantity', 'FullName', 'ShortName', 'CoOwner', 'CoOwnerLink',
    'Category', 'CLAA', 'Horns', 'Breed', 'ExternalLink', 'Description', 'WhyOnABH',
    'StudDescription', 'Owner', 'ShowOnOurHerdPage', 'LotNumber', 'MicrochipNumber', 'AgeClass',
    'RegVerified', 'Shearingmethod', 'Handler', 'CoOwnerName1', 'CoOwnerLink1', 'CoOwnerBusiness1',
    'CoOwnerName2', 'CoOwnerLink2', 'CoOwnerBusiness2', 'CoOwnerName3', 'CoOwnerLink3',
    'CoOwnerBusiness3', 'Brokered', 'AGBrokered', 'Weight', 'Height', 'Gaited', 'Temperment',
    'Skills', 'Markings', 'Warmblooded', 'Trade', 'Tradefor', 'Lease', 'AssociationName', 'Donor',
    'Polled', 'Clone', 'Frame', 'ShippingpointStreet', 'ShippingPointcity', 'ShippingPointState',
    'ShippingPointzip', 'NumberofAnimals', 'Preferedspecies', 'Vaccinations', 'Financeterms',
    'AncestryDescription'
]

class AnimalsCRUD(_BaseCRUD):
    TABLE_NAME = "animals"
    COLUMNS = ANIMALS_COLUMNS

def animals_tool(action: str,
                 data: Optional[Dict[str, Any]] = None,
                 identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the animals table (create/read/update/delete)."""
    crud = AnimalsCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# ANCESTORS
# -----------------------------------------------------------------------------

ANCESTORS_COLUMNS: List[str] = [
    'AddressID',
    'Dam', 'DamColor', 'DamAri', 'DamCLAA', 'DamLink',
    'Damdam', 'DamDamColor', 'DamDamARI', 'DamDamCLAA', 'DamDamLink',
    'Damsire', 'DamsireARI', 'DamsireCLAA', 'DamsireColor', 'DamsireLink',
    'DamDamDam', 'DamDamDamARI', 'DamDamDamCLAA', 'DamDamDamColor', 'DamDamDamLink',
    'DamDamSire', 'DamDamSireARI', 'DamDamSireCLAA', 'DamDamSireColor', 'DamDamSireLink',
    'DamSireDam', 'DamSireDamARI', 'DamSireDamCLAA', 'DamSireDamColor', 'DamSireDamLink',
    'DamSireSire', 'DamSireSireARI', 'DamSireSireCLAA', 'DamSireSireColor', 'DamSireSireLink',
    'Sire', 'SireColor', 'SireARI', 'SireCLAA', 'SireLink',
    'Siredam', 'SiredamColor', 'SiredamARI', 'SiredamCLAA', 'SiredamLink',
    'SireSire', 'SireSireColor', 'SireSireARI', 'SireSireCLAA', 'SireSireLink',
    'SireDamDam', 'SireDamDamColor', 'SireDamDamARI', 'SireDamDamCLAA', 'SireDamDamLink',
    'SireDamSire', 'SireDamSireColor', 'SireDamSireARI', 'SireDamSireCLAA', 'SireDamSireLink',
    'SireSireDam', 'SireSireDamColor', 'SireSireDamARI', 'SireSireDamCLAA', 'SireSireDamLink',
    'SireSireSire', 'SireSireSireColor', 'SireSireSireARI', 'SireSireSireCLAA', 'SireSireSireLink'
]

class AncestorsCRUD(_BaseCRUD):
    TABLE_NAME = "ancestors"
    COLUMNS = ANCESTORS_COLUMNS

def ancestors_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the ancestors table (create/read/update/delete)."""
    crud = AncestorsCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# AWARDS
# -----------------------------------------------------------------------------

AWARDS_COLUMNS: List[str] = [
    'ShowName',
    'AwardYear',
    'Type',
    'PlacingNumber',
    'Placing',
    'Class',
    'Judge',
    'ShowYear',
    'Awardcomments',
    'ShowLevel'
]

class AwardsCRUD(_BaseCRUD):
    TABLE_NAME = "awards"
    COLUMNS = AWARDS_COLUMNS

def awards_tool(action: str,
                data: Optional[Dict[str, Any]] = None,
                identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the awards table (create/read/update/delete)."""
    crud = AwardsCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# BUSINESS
# -----------------------------------------------------------------------------

BUSINESS_COLUMNS: List[str] = [
    'BusinessTypeID',
    'BusinessName',
    'BusinessWebsiteID',
    'BusinessEmail',
    'BusinessHours',
    'PhoneID',
    'AddressID',
    'EventID',
    'BusinessLogo',
    'Contact1PeopleID',
    'GGWebsite',
    'BusinessLinkedIn',
    'BusinessFacebook',
    'BusinessX',
    'BusinessInstagram',
    'BusinessPinterest',
    'BusinessTruthSocial',
    'BusinessBlog',
    'BusinessYouTube',
    'BusinessOtherSocial1',
    'BusinessOtherSocial2',
    'AccessLevel',
    'PreferedBreed',
    'SubscriptionLevel',
    'BusinessPhone',
    'WebsitesID',
    'Cell',
    'Fax',
    'Preferedspecies',
    'RanchHomeText',
    'RanchHomeHeading',
    'RanchHomeText2',
    'Logo',
    'Header',
    'FavoriteAssocitaionID',
    'BusinessAcronym'
]

class BusinessCRUD(_BaseCRUD):
    TABLE_NAME = "business"
    COLUMNS = BUSINESS_COLUMNS

def business_tool(action: str,
                  data: Optional[Dict[str, Any]] = None,
                  identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the business table (create/read/update/delete)."""
    crud = BusinessCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# ----------------------------------------------------------------------------
# COLORLOOKUP
# -----------------------------------------------------------------------------

COLORLOOKUP_COLUMNS: List[str] = [
    'ColorName',
    'ColorCode',
    'ColorGroup',
    'ColorType',
    'ColorHex',
    'ColorDescription',
    'ActiveStatus'
]

class ColorLookupCRUD(_BaseCRUD):
    TABLE_NAME = "colorlookup"
    COLUMNS = COLORLOOKUP_COLUMNS

def colorlookup_tool(action: str,
                     data: Optional[Dict[str, Any]] = None,
                     identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the colorlookup table (create/read/update/delete)."""
    crud = ColorLookupCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# ANIMALSTATS
# -----------------------------------------------------------------------------

ANIMALSTATS_COLUMNS: List[str] = [
    'AnimalID',
    'StatType',
    'StatValue',
    'MeasurementUnit',
    'RecordedDate',
    'RecordedBy',
    'Notes'
]

class AnimalStatsCRUD(_BaseCRUD):
    TABLE_NAME = "animalstats"
    COLUMNS = ANIMALSTATS_COLUMNS

def animalstats_tool(action: str,
                     data: Optional[Dict[str, Any]] = None,
                     identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the animalstats table (create/read/update/delete)."""
    crud = AnimalStatsCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# ASSOCIATIONMEMBERS
# -----------------------------------------------------------------------------

ASSOCIATIONMEMBERS_COLUMNS: List[str] = [
    'PeopleID',
    'AssociationID',
    'MemberPosition',
    'AccessLevel',
    'Favorite',
    'BusinessID'
]

class AssociationMembersCRUD(_BaseCRUD):
    TABLE_NAME = "associationmembers"
    COLUMNS = ASSOCIATIONMEMBERS_COLUMNS

def associationmembers_tool(action: str,
                           data: Optional[Dict[str, Any]] = None,
                           identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the associationmembers table (create/read/update/delete)."""
    crud = AssociationMembersCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# ASSOCIATIONS
# -----------------------------------------------------------------------------

ASSOCIATIONS_COLUMNS: List[str] = [
    'PeopleId',
    'SpeciesID',
    'Position',
    'AddressID',
    'Registry',
    'AssociationName',
    'AssociationAcronym',
    'Associationwebsite',
    'AssociationEmailaddress',
    'AssociationStreet1',
    'AssociationStreet2',
    'AssociationCity',
    'AssociationState',
    'AssociationCountry',
    'AssociationZip',
    'AssociationPhone',
    'SentWelcomeEmail',
    'OfferedFreeMembership',
    'AcceptedFreeMemeberhip',
    'OfferFreeAssciationwebsite',
    'AcceptedFreeMembershipWebsite',
    'AssociationLogo',
    'AssociationDescription',
    'AssociationPassword',
    'AssociationContactName',
    'AssociationContactPosition',
    'AssociationContactEmail',
    'AssociationActivationCode',
    'AssociationShowaddress',
    'country_id',
    'AssociationType',
    'FarmersMarket',
    'FoodHub',
    'CSA',
    'Livestock',
    'FarmAg',
    'AssociationFacebook',
    'AssociationX',
    'AssociationInstagram',
    'AssociationTruthSocial',
    'AssociationBlog',
    'AssociationYouTube',
    'AssociationOtherSocial1',
    'AssociationOtherSocial2',
    'AssociationPinterest',
    'AssociationLinkedIn',
    'AssociationTollFreePhone',
    'AssociationFax',
    'AssociationTypeID'
]

class AssociationsCRUD(_BaseCRUD):
    TABLE_NAME = "associations"
    COLUMNS = ASSOCIATIONS_COLUMNS

def associations_tool(action: str,
                      data: Optional[Dict[str, Any]] = None,
                      identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the associations table (create/read/update/delete)."""
    crud = AssociationsCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# STATES
# -----------------------------------------------------------------------------

STATES_COLUMNS: List[str] = [
    'StateName',
    'StateAbbreviation',
    'StateHeaderImage',
    'StateDescription',
    'StateFlag',
    'Statebird',
    'StateSeal',
    'Moto',
    'Nicknames',
    'Weatherlink',
    'Governor',
    'Senator1',
    'Senator2',
    'Rep1',
    'Rep2',
    'Rep3',
    'Rep4',
    'Rep5',
    'Rep6',
    'Rep7',
    'Rep8',
    'Rep9',
    'Rep10',
    'Rep11',
    'Rep12',
    'Rep13',
    'Rep14',
    'Rep15',
    'Rep16',
    'Rep17',
    'Rep18',
    'Rep19',
    'Rep20',
    'Rep21',
    'Rep22',
    'Rep23',
    'Rep24',
    'Rep25',
    'Rep26',
    'Rep27',
    'Rep28',
    'Rep29',
    'Rep30',
    'Rep31',
    'Rep32',
    'Rep33',
    'Rep34',
    'Rep35',
    'Rep36',
    'Rep37',
    'Rep38',
    'Rep39',
    'Rep40',
    'Rep41',
    'Rep42',
    'Rep43',
    'Rep44',
    'Rep45',
    'Rep46',
    'Rep47',
    'Rep48',
    'Rep49',
    'Rep50',
    'Rep51',
    'Rep52',
    'Rep53',
    'Rep54',
    'Rep55',
    'Rep56',
    'Rep57',
    'Rep58'
]

class StatesCRUD(_BaseCRUD):
    TABLE_NAME = "states"
    COLUMNS = STATES_COLUMNS

def states_tool(action: str,
                data: Optional[Dict[str, Any]] = None,
                identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the states table (create/read/update/delete)."""
    crud = StatesCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# SPECIESREGISTRATIONTYPELOOKUPTABLE
# -----------------------------------------------------------------------------

SPECIESREGISTRATIONTYPELOOKUPTABLE_COLUMNS: List[str] = [
    'SpeciesID',
    'RegistrationTypeName',
    'RegistrationTypeDescription',
    'IsActive',
    'CreatedDate',
    'ModifiedDate'
]

class SpeciesRegistrationTypeLookupTableCRUD(_BaseCRUD):
    TABLE_NAME = "speciesregistrationtypelookuptable"
    COLUMNS = SPECIESREGISTRATIONTYPELOOKUPTABLE_COLUMNS

def speciesregistrationtypelookuptable_tool(action: str,
                                            data: Optional[Dict[str, Any]] = None,
                                            identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the speciesregistrationtypelookuptable (create/read/update/delete)."""
    crud = SpeciesRegistrationTypeLookupTableCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# SPECIESCATEGORY
# -----------------------------------------------------------------------------

SPECIESCATEGORY_COLUMNS: List[str] = [
    'SpeciesID',
    'SpeciesCategory',
    'SpeciesCategoryOrder',
    'SpeciesCategoryPlural',
    'QuantityType'
]

class SpeciesCategoryCRUD(_BaseCRUD):
    TABLE_NAME = "speciescategory"
    COLUMNS = SPECIESCATEGORY_COLUMNS

def speciescategory_tool(action: str,
                         data: Optional[Dict[str, Any]] = None,
                         identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the speciescategory table (create/read/update/delete)."""
    crud = SpeciesCategoryCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# SPECIESCOLORLOOKUPTABLE
# -----------------------------------------------------------------------------

SPECIESCOLORLOOKUPTABLE_COLUMNS: List[str] = [
    'SpeciesID',
    'ColorName',
    'ColorDescription',
    'ColorGroup',
    'ColorHex',
    'IsActive'
]

class SpeciesColorLookupTableCRUD(_BaseCRUD):
    TABLE_NAME = "speciescolorlookuptable"
    COLUMNS = SPECIESCOLORLOOKUPTABLE_COLUMNS

def speciescolorlookuptable_tool(action: str,
                                 data: Optional[Dict[str, Any]] = None,
                                 identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the speciescolorlookuptable (create/read/update/delete)."""
    crud = SpeciesColorLookupTableCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# SIRE
# -----------------------------------------------------------------------------

SIRE_COLUMNS: List[str] = [
    'SiresName',
    'SiresRegistration',
    'SiresColor'
]

class SireCRUD(_BaseCRUD):
    TABLE_NAME = "sire"  # change to "sires" if your actual table name is plural
    COLUMNS = SIRE_COLUMNS

def sire_tool(action: str,
              data: Optional[Dict[str, Any]] = None,
              identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the sire table (create/read/update/delete)."""
    crud = SireCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# ANIMALREGISTRATION
# -----------------------------------------------------------------------------

ANIMALREGISTRATION_COLUMNS: List[str] = [
    'AnimalID',
    'RegType',
    'RegNumber'
]

class AnimalRegistrationCRUD(_BaseCRUD):
    TABLE_NAME = "animalregistration"
    COLUMNS = ANIMALREGISTRATION_COLUMNS

def animalregistration_tool(action: str,
                            data: Optional[Dict[str, Any]] = None,
                            identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the animalregistration table (create/read/update/delete)."""
    crud = AnimalRegistrationCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# COLORS
# -----------------------------------------------------------------------------

COLORS_COLUMNS: List[str] = [
    'ID',
    'Color1',
    'Color2',
    'Color3',
    'Color4',
    'Color5'
]

class ColorsCRUD(_BaseCRUD):
    TABLE_NAME = "colors"
    COLUMNS = COLORS_COLUMNS

def colors_tool(action: str,
                data: Optional[Dict[str, Any]] = None,
                identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the colors table (create/read/update/delete)."""
    crud = ColorsCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# SPECIESBREEDLOOKUPTABLE
# -----------------------------------------------------------------------------

SPECIESBREEDLOOKUPTABLE_COLUMNS: List[str] = [
    'breedavailable',
    'SpeciesID',
    'Breed',
    'Breeddescription',
    'BreedImage',
    'Breedvideo',
    'BreedAnimalID',
    'BreedImageCaption',
    'BreedImageOrientation',
    'SpeciesRegistrationTypeID',
    'MeatBreed',
    'MilkBreed',
    'WoolBreed',
    'EggBreed',
    'Working',
    'HoneyBreed'
]

class SpeciesBreedLookupTableCRUD(_BaseCRUD):
    TABLE_NAME = "speciesbreedlookuptable"
    COLUMNS = SPECIESBREEDLOOKUPTABLE_COLUMNS

def speciesbreedlookuptable_tool(action: str,
                                 data: Optional[Dict[str, Any]] = None,
                                 identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the speciesbreedlookuptable (create/read/update/delete)."""
    crud = SpeciesBreedLookupTableCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# ANCESTRYPERCENTS
# -----------------------------------------------------------------------------

ANCESTRYPERCENTS_COLUMNS: List[str] = [
    'OwnerID',
    'PercentPeruvian',
    'PercentBolivian',
    'PercentChilean',
    'PercentAccoyo',
    'PercentUnknownOther'
]

class AncestryPercentsCRUD(_BaseCRUD):
    TABLE_NAME = "ancestrypercents"
    COLUMNS = ANCESTRYPERCENTS_COLUMNS

def ancestrypercents_tool(action: str,
                          data: Optional[Dict[str, Any]] = None,
                          identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the ancestrypercents table (create/read/update/delete)."""
    crud = AncestryPercentsCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# MALEDATA
# -----------------------------------------------------------------------------

MALEDATA_COLUMNS: List[str] = [
    'StudFee',
    'Herdsire',
    'JrHerdsire',
    'JuvenileMale',
    'Comments'
]

class MaleDataCRUD(_BaseCRUD):
    TABLE_NAME = "maledata"
    COLUMNS = MALEDATA_COLUMNS

def maledata_tool(action: str,
                  data: Optional[Dict[str, Any]] = None,
                  identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the maledata table (create/read/update/delete)."""
    crud = MaleDataCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# FIBER
# -----------------------------------------------------------------------------

FIBER_COLUMNS: List[str] = [
    'ID',
    'SampleDate',
    'SampleDateMonth',
    'SampleDateDay',
    'SampleDateYear',
    'SampleAge',
    'Average',
    'StandardDev',
    'COV',
    'GreaterThan30',
    'CF',
    'Curve',
    'Shearweight',
    'BlanketWeight',
    'Length',
    'CrimpPerInch',
    'LargeHistogram',
    'SmallHistogram',
    'StapleLength'
]

class FiberCRUD(_BaseCRUD):
    TABLE_NAME = "fiber"
    COLUMNS = FIBER_COLUMNS

def fiber_tool(action: str,
               data: Optional[Dict[str, Any]] = None,
               identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the fiber table (create/read/update/delete)."""
    crud = FiberCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."
    
# -----------------------------------------------------------------------------
# COUNTRY
# -----------------------------------------------------------------------------

COUNTRY_COLUMNS: List[str] = [
    'name',
    'iso_code',
    'Currency',
    'CurrencyCode',
    'Active',
    'Paycode',
    'region',
    'ProvinceTitle'
]

class CountryCRUD(_BaseCRUD):
    TABLE_NAME = "country"
    COLUMNS = COUNTRY_COLUMNS

def country_tool(action: str,
                 data: Optional[Dict[str, Any]] = None,
                 identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the country table (create/read/update/delete)."""
    crud = CountryCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# -----------------------------------------------------------------------------
# STATE_PROVINCE
# -----------------------------------------------------------------------------

STATE_PROVINCE_COLUMNS: List[str] = [
    'name',
    'abbreviation',
    'country_id'
]

class StateProvinceCRUD(_BaseCRUD):
    TABLE_NAME = "state_province"
    COLUMNS = STATE_PROVINCE_COLUMNS

def state_province_tool(action: str,
                        data: Optional[Dict[str, Any]] = None,
                        identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the state_province table (create/read/update/delete)."""
    crud = StateProvinceCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."


# -----------------------------------------------------------------------------
# PEOPLETITLELOOKUP
# -----------------------------------------------------------------------------

PEOPLETITLELOOKUP_COLUMNS: List[str] = [
    'PeopleTitle',
    'PeopleTitleDescription'
]

class PeopleTitleLookupCRUD(_BaseCRUD):
    TABLE_NAME = "peopletitlelookup"
    COLUMNS = PEOPLETITLELOOKUP_COLUMNS

def peopletitlelookup_tool(action: str,
                           data: Optional[Dict[str, Any]] = None,
                           identifier: Optional[Dict[str, Any]] = None) -> Any:
    """CRUD tool for the peopletitlelookup table (create/read/update/delete)."""
    crud = PeopleTitleLookupCRUD()
    action = (action or "").lower()
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier or {})
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."
