import os
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date, time

import boto3
from botocore.exceptions import ClientError

# KONEKCIJA
DDB_ENDPOINT = os.getenv("DDB_ENDPOINT")  # npr. http://localhost:4566 ili http://localhost:8000
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
    existing = [t.name for t in _dynamodb.tables.all()]
    # members: PK id (Number)
    if MEMBERS_TBL not in existing:
        _dynamodb.create_table(
            TableName=MEMBERS_TBL,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "N"}],
            BillingMode="PAY_PER_REQUEST",
        ).wait_until_exists()
    # sessions: PK id (Number)
    if SESSIONS_TBL not in existing:
        _dynamodb.create_table(
            TableName=SESSIONS_TBL,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "N"}],
            BillingMode="PAY_PER_REQUEST",
        ).wait_until_exists()
    # memberships: PK member_id (Number)
    if MEMBERSHIPS_TBL not in existing:
        _dynamodb.create_table(
            TableName=MEMBERSHIPS_TBL,
            KeySchema=[{"AttributeName": "member_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "member_id", "AttributeType": "N"}],
            BillingMode="PAY_PER_REQUEST",
        ).wait_until_exists()

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

