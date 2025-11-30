from dotenv import load_dotenv
load_dotenv()
import os
import time
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date, time as time_type
import boto3
from botocore.exceptions import ClientError

# KONEKCIJA
DDB_ENDPOINT = os.getenv("DDB_ENDPOINT", "http://localhost:8000")  # Default za local
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")

_dynamodb = boto3.resource(
    "dynamodb",
    region_name=AWS_REGION,
    endpoint_url=DDB_ENDPOINT,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


MEMBERS_TBL = "members"
SESSIONS_TBL = "sessions"
MEMBERSHIPS_TBL = "memberships"

# POMOĆNE KONVERZIJE 
def _to_decimal(n: float) -> Decimal:
    return Decimal(str(n))

def _time_to_str(t: time) -> str:
    return t.strftime("%H:%M:%S")

def _date_to_str(d: date) -> str:
    return d.strftime("%Y-%m-%d")

# REIRANJE TABLICA (idempotentno)
def ensure_tables() -> None:
    """
    Idempotentno kreiranje tablica.
    Koristi client.list_tables() umjesto resource.tables.all() za robusnost.
    """
    print("Provjeravam DynamoDB tablice...")
    
    # Koristi client umjesto resource za robusnije listanje
    client = boto3.client(
        "dynamodb",
        region_name=AWS_REGION,
        endpoint_url=DDB_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    
    try:
        response = client.list_tables()
        existing = response.get("TableNames", [])
        print(f"Postojeće tablice: {existing}")
    except Exception as e:
        print(f"⚠️  Greška pri dohvatu tablica: {e}")
        existing = []
    
    # Definicije tablica
    tables_to_create = [
        {
            "name": MEMBERS_TBL,
            "key_schema": [{"AttributeName": "id", "KeyType": "HASH"}],
            "attribute_definitions": [{"AttributeName": "id", "AttributeType": "N"}],
        },
        {
            "name": SESSIONS_TBL,
            "key_schema": [{"AttributeName": "id", "KeyType": "HASH"}],
            "attribute_definitions": [{"AttributeName": "id", "AttributeType": "N"}],
        },
        {
            "name": MEMBERSHIPS_TBL,
            "key_schema": [{"AttributeName": "member_id", "KeyType": "HASH"}],
            "attribute_definitions": [{"AttributeName": "member_id", "AttributeType": "N"}],
        },
    ]
    
    # Kreiraj tablice koje ne postoje
    for table_def in tables_to_create:
        table_name = table_def["name"]
        
        if table_name not in existing:
            print(f"Kreiram tablicu: {table_name}...")
            try:
                client.create_table(
                    TableName=table_name,
                    KeySchema=table_def["key_schema"],
                    AttributeDefinitions=table_def["attribute_definitions"],
                    BillingMode="PAY_PER_REQUEST",
                )
                print(f"✅ Tablica {table_name} kreirana!")
                
                # Pričekaj da tablica bude aktivna (max 10s)
                for _ in range(10):
                    try:
                        table_status = client.describe_table(TableName=table_name)
                        if table_status["Table"]["TableStatus"] == "ACTIVE":
                            print(f"✅ Tablica {table_name} je aktivna!")
                            break
                    except:
                        pass
                    time.sleep(1)
                    
            except Exception as e:
                if "ResourceInUseException" in str(e):
                    print(f"ℹ️  Tablica {table_name} već postoji.")
                else:
                    print(f"❌ Greška pri kreiranju tablice {table_name}: {e}")
        else:
            print(f"ℹ️  Tablica {table_name} već postoji.")
    
    print("✅ Sve tablice provjerene/kreirane!")
# MEMBERS
def put_member(item: Dict[str, Any]) -> None:
    _dynamodb.Table(MEMBERS_TBL).put_item(Item=item)

def get_member(member_id: int) -> Optional[Dict[str, Any]]:
    resp = _dynamodb.Table(MEMBERS_TBL).get_item(Key={"id": member_id})
    return resp.get("Item")

def list_members() -> List[Dict[str, Any]]:
    resp = _dynamodb.Table(MEMBERS_TBL).scan()
    return resp.get("Items", [])

def delete_member(member_id: int) -> None:
    _dynamodb.Table(MEMBERS_TBL).delete_item(Key={"id": member_id})

def member_email_exists(email: str) -> bool:
    # Jednostavan scan
    tbl = _dynamodb.Table(MEMBERS_TBL)
    resp = tbl.scan(
        ProjectionExpression="#e",
        FilterExpression="#e = :v",
        ExpressionAttributeNames={"#e": "email"},
        ExpressionAttributeValues={":v": email},
    )
    return len(resp.get("Items", [])) > 0

def count_enrolled(session_id: int) -> int:
    resp = _dynamodb.Table(MEMBERS_TBL).scan(
        ProjectionExpression="termin",
        FilterExpression="termin = :sid",
        ExpressionAttributeValues={":sid": session_id},
    )
    return len(resp.get("Items", []))

def assign_session(member_id: int, session_id: int) -> None:
    _dynamodb.Table(MEMBERS_TBL).update_item(
        Key={"id": member_id},
        UpdateExpression="SET termin = :sid",
        ExpressionAttributeValues={":sid": session_id},
    )

def unassign_session(member_id: int) -> None:
    _dynamodb.Table(MEMBERS_TBL).update_item(
        Key={"id": member_id},
        UpdateExpression="REMOVE termin",
    )

# SESSIONS 
def put_session(item: Dict[str, Any]) -> None:
    _dynamodb.Table(SESSIONS_TBL).put_item(Item=item)

def get_session(session_id: int) -> Optional[Dict[str, Any]]:
    resp = _dynamodb.Table(SESSIONS_TBL).get_item(Key={"id": session_id})
    return resp.get("Item")

def list_sessions() -> List[Dict[str, Any]]:
    resp = _dynamodb.Table(SESSIONS_TBL).scan()
    return resp.get("Items", [])

# ---- MEMBERSHIP (1:1 po članu) ----
def put_membership(member_id: int, datum_uplate: date, datum_isteka: date, iznos: float, status: str) -> None:
    _dynamodb.Table(MEMBERSHIPS_TBL).put_item(
        Item={
            "member_id": member_id,
            "datum_uplate": _date_to_str(datum_uplate),
            "datum_isteka": _date_to_str(datum_isteka),
            "iznos": _to_decimal(iznos),
            "status": status,
        }
    )

def get_membership(member_id: int) -> Optional[Dict[str, Any]]:
    resp = _dynamodb.Table(MEMBERSHIPS_TBL).get_item(Key={"member_id": member_id})
    return resp.get("Item")

def delete_membership(member_id: int) -> None:
    _dynamodb.Table(MEMBERSHIPS_TBL).delete_item(Key={"member_id": member_id})

def update_member(member_id: int, set_parts: list[str], values: dict):
    ue = "SET " + ", ".join(set_parts)
    # Pretvori float u Decimal (DynamoDB ne voli 'float')
    clean_vals = {k: (Decimal(str(v)) if isinstance(v, float) else v) for k, v in values.items()}
    _dynamodb.Table(MEMBERS_TBL).update_item(
        Key={"id": member_id},
        UpdateExpression=ue,
        ExpressionAttributeValues=clean_vals,
    )

