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


# Columns from the Animals table, excluding any *ID fields and watermark/date/day/month/year/timestamp fields
ANIMALS_COLUMNS: List[str] = [
    'PublishForSale', 'PublishStud', 'Quantity', 'FullName', 'ShortName', 'CoOwner', 'CoOwnerLink', 'Category', 'CLAA', 'Horns', 'Breed', 'ExternalLink', 'Description', 
    'WhyOnABH', 'StudDescription', 'Owner', 'ShowOnOurHerdPage', 'LotNumber', 'MicrochipNumber', 'AgeClass', 'RegVerified', 'Shearingmethod', 'Handler', 'CoOwnerName1',
    'CoOwnerLink1', 'CoOwnerBusiness1', 'CoOwnerName2', 'CoOwnerLink2', 'CoOwnerBusiness2', 'CoOwnerName3', 'CoOwnerLink3', 'CoOwnerBusiness3', 'Brokered', 'AGBrokered',
    'Weight', 'Height', 'Gaited', 'Temperment', 'Skills', 'Markings', 'Warmblooded', 'Trade', 'Tradefor', 'Lease', 'AssociationName', 'Donor', 'Polled', 'Clone', 'Frame', 
    'ShippingpointStreet', 'ShippingPointcity', 'ShippingPointState', 'ShippingPointzip', 'NumberofAnimals', 'Preferedspecies', 'Vaccinations', 'Financeterms','AncestryDescription',
]


# Columns from Ancestors table
ANCESTORS_COLUMNS: List[str] = [
    'Dam', 'DamColor', 'DamAri', 'DamCLAA', 'DamLink', 'Damdam', 'DamDamColor', 'DamDamARI', 'DamDamCLAA', 'DamDamLink', 'Damsire', 'DamsireARI', 'DamsireCLAA', 'DamsireColor',
    'DamsireLink', 'DamDamDam', 'DamDamDamColor', 'DamDamDamARI', 'DamDamDamCLAA', 'DamDamDamLink', 'DamDamSire', 'DamDamSireColor', 'DamDamSireARI', 'DamDamSireCLAA',
    'DamDamSireLink', 'DamSireDam', 'DamSireDamColor', 'DamSireDamARI', 'DamSireDamCLAA', 'DamSireDamLink', 'DamSireSire', 'DamSireSireColor', 'DamSireSireARI', 'DamSireSireCLAA',
    'DamSireSireLink', 'Sire', 'SireColor', 'SireARI', 'SireCLAA', 'SireLink', 'Siredam', 'SiredamColor', 'SiredamARI', 'SiredamCLAA', 'SiredamLink', 'SireSire', 'SireSireColor', 
    'SireSireARI', 'SireSireCLAA', 'SireSireLink', 'SireDamDam', 'SireDamDamColor', 'SireDamDamARI', 'SireDamDamCLAA', 'SireDamDamLink', 'SireDamSire', 'SireDamSireColor', 'SireDamSireARI',
    'SireDamSireCLAA', 'SireDamSireLink', 'SireSireDam', 'SireSireDamColor', 'SireSireDamARI', 'SireSireDamCLAA', 'SireSireDamLink', 'SireSireSire', 'SireSireSireColor', 'SireSireSireARI', 
    'SireSireSireCLAA', 'SireSireSireLink',
]

# Columns from Ancestrypercent table
ANCESTRYPERCENT_COLUMNS: List[str] = [
    'PercentPeruvian', 'PercentBolivian', 'PercentChilean', 'PercentAccoyo', 'PercentUnknownOther',
]

# Columns from AnimalRegistration table
ANIMALREGISTRATION_COLUMNS: List[str] = [
    'RegType', 'RegNumber'
]

# Columns from AnimalStats table
ANIMALSTATS_COLUMNS: List[str] = [
    'AnimalName',
    'Websitename',
]

# Columns from Awards table
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
    'ShowLevel',
]

# Columns from Business table
BUSINESS_COLUMNS: List[str] = [
    'BusinessName',
    'BusinessEmail',
    'BusinessHours',
    'BusinessLogo',
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
    'Cell',
    'Fax',
    'Preferedspecies',
    'RanchHomeText',
    'RanchHomeHeading',
    'RanchHomeText2',
    'Logo',
    'Header',
    'BusinessAcronym',
]

# Columns from Colorlookup table
COLORLOOKUP_COLUMNS: List[str] = [
    'Color',
    'Abbreviation',
    'ColorGroup',
    'JudgingType',
    'Breed',
]

# Columns from Colors table
COLORS_COLUMNS: List[str] = [
    'Color1',
    'Color2',
    'Color3',
    'Color4',
    'Color5',
]

# Columns from Country table
COUNTRY_COLUMNS: List[str] = [
    'name',
    'iso_code',
    'Currency',
    'CurrencyCode',
    'Active',
    'Paycode',
    'region',
    'ProvinceTitle',
]

# Columns from Fiber table
FIBER_COLUMNS: List[str] = [
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
    'StapleLength',
]

# Columns from Maledata table
MALEDATA_COLUMNS: List[str] = [
    'StudFee', 'Herdsire', 'JrHerdsire', 'JuvenileMale', 'Comments'
]

# Columns from PeopleTitleLookup table
PEOPLETITLELOOKUP_COLUMNS: List[str] = [
    'PeopleTitle', 'PeopleTitleDescription'
]

# Columns from Sire table
SIRE_COLUMNS: List[str] = [
    'SiresName',
    'SiresRegistration',
    'SiresColor',
]

# Columns from SpeciesBreedLookUpTable table
SPECIESBREEDLOOKUPTABLE_COLUMNS: List[str] = [
    'breedavailable',
    'Breed',
    'Breeddescription',
    'BreedImage',
    'Breedvideo',
    'BreedImageCaption',
    'BreedImageOrientation',
    'MeatBreed',
    'MilkBreed',
    'WoolBreed',
    'EggBreed',
    'Working',
    'HoneyBreed',
]

# Columns from SpeciesCategory table
SPECIESCATEGORY_COLUMNS: List[str] = [
    'SpeciesCategory',
    'SpeciesCategoryOrder',
    'SpeciesCategoryPlural',
    'QuantityType',
]

# Columns from SpeciesColorLookUpTable table
SPECIESCOLORLOOKUPTABLE_COLUMNS: List[str] = [
    'SpeciesColor',
]

# Columns from SpeciesRegistrationLookup table
SPECIESREGISTRATIONTYPELOOKUPTABLE_COLUMNS: List[str] = [
    'SpeciesRegistrationType',
]

# Columns from State Province table
STATE_PROVINCE_COLUMNS: List[str] = [
    'name',
    'abbreviation',
]

# Columns from States table
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
    'Rep58',
]

# Columns from Associations table
ASSOCIATIONS_COLUMNS: List[str] = [
    'Position',
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
]

# Columns from Associationmember table
ASSOCIATIONMEMBERS_COLUMNS: List[str] = [
    'MemberPosition',
    'AccessLevel',
    'Favorite',
]




class _BaseCRUD:    
    TABLE_NAME: str = ""
    COLUMNS: List[str] = []

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def _connect(self):
        return pyodbc.connect(self.connection_string)

    def create(self, data: Dict[str, Any]) -> str:
        """
        Insert a new row into animals using only allowed columns.
        """
        columns = [c for c in ANIMALS_COLUMNS if c in data]
        if not columns:
            return "No valid columns provided."
        values = [data[c] for c in columns]
        placeholders = ", ".join(["?"] * len(columns))
        sql = f"INSERT INTO {self.TABLE_NAME} ({', '.join(columns)}) VALUES ({placeholders})"
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, values)
            conn.commit()
        return f"Row created with columns: {', '.join(columns)}"

    def read(self, filters: Optional[Dict[str, Any]] = None) -> list:
        """
        Read rows from animals; optional equality filters on allowed columns.
        """
        sql = f"SELECT {', '.join(ANIMALS_COLUMNS)} FROM {self.TABLE_NAME}"
        params: List[Any] = []
        if filters:
            where_clauses = [f"{c} = ?" for c in filters if c in ANIMALS_COLUMNS]
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
                params = [filters[c] for c in filters if c in ANIMALS_COLUMNS]
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [dict(zip(ANIMALS_COLUMNS, row)) for row in rows]

    def update(self, identifier: Dict[str, Any], updates: Dict[str, Any]) -> str:
        """
        Update rows in animals; identifier + updates restricted to allowed columns.
        """
        set_clauses = [f"{c} = ?" for c in updates if c in ANIMALS_COLUMNS]
        if not set_clauses:
            return "No valid columns to update."
        where_clauses = [f"{c} = ?" for c in identifier if c in ANIMALS_COLUMNS]
        if not where_clauses:
            return "No valid identifier provided."
        sql = f"UPDATE {self.TABLE_NAME} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
        params = [updates[c] for c in updates if c in ANIMALS_COLUMNS] + \
                 [identifier[c] for c in identifier if c in ANIMALS_COLUMNS]
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
        return f"Updated rows where {' AND '.join(where_clauses)}."

    def delete(self, identifier: Dict[str, Any]) -> str:
        """
        Delete rows in animals; identifier restricted to allowed columns.
        """
        where_clauses = [f"{c} = ?" for c in identifier if c in ANIMALS_COLUMNS]
        if not where_clauses:
            return "No valid identifier provided."
        sql = f"DELETE FROM {self.TABLE_NAME} WHERE {' AND '.join(where_clauses)}"
        params = [identifier[c] for c in identifier if c in ANIMALS_COLUMNS]
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
        return f"Deleted rows where {' AND '.join(where_clauses)}."
    
    
## Animals Table

class AnimalsCRUD(_BaseCRUD):
    TABLE_NAME = "animals"
    COLUMNS = ANIMALS_COLUMNS

def animals_tool(action: str,
                 data: Optional[Dict[str, Any]] = None,
                 identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the animals table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = AnimalsCRUD(AZURE_CONNECTION_STRING)
    if action == "create":
        return crud.create(data or {})
    elif action == "read":
        return crud.read(identifier)
    elif action == "update":
        return crud.update(identifier or {}, data or {})
    elif action == "delete":
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."
    

## Ancestors Table

class AncestorsCRUD(_BaseCRUD):
    TABLE_NAME = "ancestors"
    COLUMNS = ANCESTORS_COLUMNS


def ancestors_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = AncestorsCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."
    
    
## Ancestrypercent Table

class AncestrypercentCRUD(_BaseCRUD):
    TABLE_NAME = "ancestrypercent"
    COLUMNS = ANCESTRYPERCENT_COLUMNS


def Ancestrypercent_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = AncestrypercentCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."


# AnimalRegistration Table

class AnimalregistrationCRUD(_BaseCRUD):
    TABLE_NAME = "Animalregistration"
    COLUMNS = ANCESTORS_COLUMNS


def Animalregistration_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = AnimalregistrationCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."


# AnimalStats Table

class AnimalstatsCRUD(_BaseCRUD):
    TABLE_NAME = "Animalstats"
    COLUMNS = ANCESTORS_COLUMNS


def Animalstats_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = AnimalstatsCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# Awards Table

class AwardsCRUD(_BaseCRUD):
    TABLE_NAME = "Awards"
    COLUMNS = AWARDS_COLUMNS


def Awards_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = AwardsCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# Business Table

class BusinessCRUD(_BaseCRUD):
    TABLE_NAME = "Business"
    COLUMNS = BUSINESS_COLUMNS


def Business_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = BusinessCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."


# ColorLookup Table

class ColorlookupCRUD(_BaseCRUD):
    TABLE_NAME = "Colorlookup"
    COLUMNS = COLORLOOKUP_COLUMNS


def Colorlookup_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = ColorlookupCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# Colors Table

class ColorsCRUD(_BaseCRUD):
    TABLE_NAME = "Colors"
    COLUMNS = COLORS_COLUMNS


def Colors_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = ColorsCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# Fiber Table

class FiberCRUD(_BaseCRUD):
    TABLE_NAME = "Fiber"
    COLUMNS = FIBER_COLUMNS


def Fiber_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = FiberCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."
    

# MaleData Table

class MaledataCRUD(_BaseCRUD):
    TABLE_NAME = "Maledata"
    COLUMNS = MALEDATA_COLUMNS


def Maledata_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = MaledataCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."


# PeopleTitleLookup Table

class PeopletitlelookupCRUD(_BaseCRUD):
    TABLE_NAME = "Peopletitlelookup"
    COLUMNS = PEOPLETITLELOOKUP_COLUMNS


def Peopletitlelookup_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = PeopletitlelookupCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."
    

# Sire Table

class SireCRUD(_BaseCRUD):
    TABLE_NAME = "Sire"
    COLUMNS = SIRE_COLUMNS


def Sire_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = SireCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."
    

# SpeciesBreedLookup Table
class SpeciesbreedlookuptableCRUD(_BaseCRUD):
    TABLE_NAME = "Speciesbreedlookuptable"
    COLUMNS = SPECIESBREEDLOOKUPTABLE_COLUMNS


def Speciesbreedlookuptable_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = SpeciesbreedlookuptableCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."
    

# SpeciesCategory

class SpeciescategoryCRUD(_BaseCRUD):
    TABLE_NAME = "Speciescategory"
    COLUMNS = SPECIESCATEGORY_COLUMNS


def Speciescategory_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = SpeciescategoryCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."
    

# SpeciesColorLookup Table

class SpeciescolorlookuptableCRUD(_BaseCRUD):
    TABLE_NAME = "Speciescolorlookuptable"
    COLUMNS = SPECIESCOLORLOOKUPTABLE_COLUMNS


def Speciescolorlookuptable_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = SpeciescolorlookuptableCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."
    

# SpeciesRegistrationLookup Table

class SpeciesregistrationtypelookuptableCRUD(_BaseCRUD):
    TABLE_NAME = "Speciesregistrationtypelookuptable"
    COLUMNS = SPECIESREGISTRATIONTYPELOOKUPTABLE_COLUMNS


def Speciesregistrationtypelookuptable_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = SpeciesregistrationtypelookuptableCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."
    

# State Province Table

class State_provinceCRUD(_BaseCRUD):
    TABLE_NAME = "State_province"
    COLUMNS = STATE_PROVINCE_COLUMNS


def State_province_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = State_provinceCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."
    

# States Table

class StatesCRUD(_BaseCRUD):
    TABLE_NAME = "States"
    COLUMNS = STATES_COLUMNS


def States_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = StatesCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."
    

# Associations

class AssociationsCRUD(_BaseCRUD):
    TABLE_NAME = "Associations"
    COLUMNS = ASSOCIATIONS_COLUMNS


def Associations_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = AssociationsCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."
    

# Associationmembers

class AssociationmembersCRUD(_BaseCRUD):
    TABLE_NAME = "Associationmembers"
    COLUMNS = ASSOCIATIONMEMBERS_COLUMNS


def Associationmembers_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = AssociationmembersCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."

# Country Table

class CountryCRUD(_BaseCRUD):
    TABLE_NAME = "Associationmembers"
    COLUMNS = ASSOCIATIONMEMBERS_COLUMNS


def Country_tool(action: str,
                   data: Optional[Dict[str, Any]] = None,
                   identifier: Optional[Dict[str, Any]] = None) -> Any:
    """
    Tool for performing CRUD operations on the ancestors table.
    action: 'create', 'read', 'update', 'delete'
    data: dict of columns/values for create or update
    identifier: dict of columns/values to identify the row(s) for update/delete/read
    """
    crud = CountryCRUD(AZURE_CONNECTION_STRING)
    if action == 'create':
        return crud.create(data or {})
    elif action == 'read':
        return crud.read(identifier)
    elif action == 'update':
        return crud.update(identifier or {}, data or {})
    elif action == 'delete':
        return crud.delete(identifier or {})
    else:
        return "Invalid action. Use 'create', 'read', 'update', or 'delete'."
        
