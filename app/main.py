from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional, Dict, Annotated
from datetime import date, time
import os
from . import dynamo
from .dynamo import (
    ensure_tables, put_member, get_member as ddb_get_member, 
    list_members as ddb_list_members, delete_member as ddb_delete_member, 
    member_email_exists, put_session as ddb_put_session,
    get_session as ddb_get_session, list_sessions as ddb_list_sessions,
    count_enrolled as ddb_count_enrolled, assign_session as ddb_assign_session,
    unassign_session as ddb_unassign_session, put_membership as ddb_put_membership,
    get_membership as ddb_get_membership, delete_membership as ddb_delete_membership
)


# Kreiranje glavnog objekta FastAPI
app = FastAPI(
    title="Evidencija članarina sportskog društva Sparta",
    version="1.4.2"
)
API_KEY = os.getenv("API_KEY", "sparta-secret-key-2024")

async def verify_api_key(x_api_key: Annotated[str, Header()] = None):
    """Provjeri API ključ za mutirajuće operacije"""
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=403, 
            detail="Invalid or missing API Key. Provide X-API-Key header."
        )
    return x_api_key

ALLOWED_GROUPS = {"početni", "srednji", "napredni"}
ALLOWED_DAYS = {"ponedjeljak", "utorak", "srijeda", "četvrtak", "petak", "subota"}
ALLOWED_STATUS = {"aktivan", "neaktivan"}

@app.on_event("startup")
def _ensure_ddb():
    ensure_tables() 


# Model podataka za članarinu
class Membership(BaseModel):
    datum_uplate: date
    datum_isteka: date
    iznos: float
    status: str

# Model podataka za termine vježbanja
class TrainingSession(BaseModel):
    id: int
    grupa: str        
    dan: str          
    vrijeme: time     
    max_clanova: int   
    
    @field_validator("grupa")
    @classmethod
    def _val_grupa(clas, v: str) -> str:
        if v not in ALLOWED_GROUPS:
            raise ValueError(f"grupa mora biti jedna od: {sorted(ALLOWED_GROUPS)}")
        return v
    
    @field_validator("dan")
    @classmethod
    def _val_dan(clas, v: str) -> str:
        v = v.lower()
        if v not in ALLOWED_DAYS:
            raise ValueError(f"dan mora biti jedan od: {sorted(ALLOWED_DAYS)}")
        return v
    
    @field_validator("max_clanova")
    @classmethod
    def _val_kapacitet(clas, v: int) -> int:
        if not (1 <= v <= 20):
            raise ValueError("Broj članova u grupi može biti između 1 i 20")
        return v

# Model podataka za jednog člana
class Member(BaseModel):
    id: int
    ime: str
    prezime: str
    email: str
    mobitel: str
    grupa: str       # početni, srednji, napredni
    status: str      # aktivan / neaktivan
    membership: Optional[Membership] = None  # članarina
    termin: Optional[int] = None

    @field_validator("grupa")
    @classmethod
    def _val_member_grupa(cls, v: str) -> str:
        if v not in ALLOWED_GROUPS:
            raise ValueError(f"grupa mora biti jedna od: {sorted(ALLOWED_GROUPS)}")
        return v

    @field_validator("status")
    @classmethod
    def _val_status(cls, v: str) -> str:
        if v not in ALLOWED_STATUS:
            raise ValueError(f"status mora biti jedan od: {sorted(ALLOWED_STATUS)}")
        return v

    @field_validator("mobitel")
    @classmethod
    def _val_mobitel(cls, v: str) -> str:
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) < 8 or len(digits) > 15:
            raise ValueError("mobitel treba imati 8–15 znamenki (bez razmaka/točkica)")
        return digits
    
class MemberUpdate(BaseModel):
    ime: Optional[str] = None
    prezime: Optional[str] = None
    email: Optional[EmailStr] = None
    mobitel: Optional[str] = None
    grupa: Optional[str] = None
    status: Optional[str] = None

    @field_validator("grupa")
    @classmethod
    def _val_member_grupa(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_GROUPS:
            raise ValueError(f"grupa mora biti jedna od: {sorted(ALLOWED_GROUPS)}")
        return v


    @field_validator("status")
    @classmethod
    def _val_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_STATUS:
            raise ValueError(f"status mora biti jedan od: {sorted(ALLOWED_STATUS)}")
        return v

    @field_validator("mobitel")
    @classmethod
    def _val_mobitel(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) < 8 or len(digits) > 15:
            raise ValueError("mobitel treba imati 8–15 znamenki")
        return digits
       
# Privremena "baza" u memoriji - kasnije će se povezati na DynamoDB
members_db: List[Member] = []
sessions_db: List[TrainingSession] = []

# Pomoćne funkcije
def get_member_by_id(member_id: int) -> Optional[Member]:
    return next((m for m in members_db if m.id == member_id), None)

def get_session_by_id(session_id: int) -> Optional[TrainingSession]:
    return next((s for s in sessions_db if s.id == session_id), None)

def count_enrolled(session_id: int) -> int:
    return sum(1 for m in members_db if m.termin == session_id)

# RUTE

# Početna testna ruta
@app.get("/")
def home():
    return {"message": "Dobrodošli u prostor za evidenciju članarina!"}

# Ruta za dodavanje novog člana
@app.post("/members", dependencies=[Depends(verify_api_key)])
def add_member(member: Member):
    if ddb_get_member(member.id):
        raise HTTPException(status_code=409, detail=f"Član s ID={member.id} već postoji.")
    if member_email_exists(member.email):
        raise HTTPException(status_code=409, detail=f"Član s emailom {member.email} već postoji.")
    item = {
        "id": member.id,
        "ime": member.ime,
        "prezime": member.prezime,
        "email": member.email,
        "mobitel": "".join(ch for ch in member.mobitel if ch.isdigit()),
        "grupa": member.grupa,
        "status": member.status,
    }
    if member.termin is not None:
        item["termin"] = member.termin
    put_member(item)
    return {"message": f"Član {member.ime} {member.prezime} uspješno dodan."}

# Ruta za dohvat svih članova
@app.get("/members")
def get_members(grupa: Optional[str] = None, status: Optional[str] = None):
    items = ddb_list_members()
    out: List[Member] = []
    for r in items:
        # Filtriranje po grupi
        if grupa and r.get("grupa") != grupa:
            continue
        # Filtriranje po statusu
        if status and r.get("status") != status:
            continue
        
        out.append(
            Member(
                id=int(r["id"]),
                ime=r["ime"],
                prezime=r["prezime"],
                email=r["email"],
                mobitel=r["mobitel"],
                grupa=r["grupa"],
                status=r["status"],
                membership=None,
                termin=int(r["termin"]) if "termin" in r else None
            )
        )
    return out

# Promjena podataka o stanju članarine


# Dodavanje člana u termin
@app.get("/members/{member_id}")
def get_member(member_id: int) -> Member:
    r = ddb_get_member(member_id)
    if not r:
        raise HTTPException(status_code=404, detail="Član nije pronađen.")
    mem = ddb_get_membership(member_id)
    membership = None
    if mem:
        membership = Membership(
            datum_uplate=date.fromisoformat(mem["datum_uplate"]),
            datum_isteka=date.fromisoformat(mem["datum_isteka"]),
            iznos=float(mem["iznos"]),
            status=mem["status"]
        )
    return Member(
        id=int(r["id"]),
        ime=r["ime"],
        prezime=r["prezime"],
        email=r["email"],
        mobitel=r["mobitel"],
        grupa=r["grupa"],
        status=r["status"],
        membership=membership,
        termin=int(r["termin"]) if "termin" in r else None
    )


@app.patch("/members/{member_id}", dependencies=[Depends(verify_api_key)])
def update_member(member_id: int, patch: MemberUpdate):
    existing = ddb_get_member(member_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Član nije pronađen.")

    data = patch.model_dump(exclude_unset=True)

    # provjera emaila: ako mijenjamo na drugi, a već postoji kod nekog drugog → 409
    if "email" in data and data["email"] != existing["email"] and member_email_exists(data["email"]):
        raise HTTPException(status_code=409, detail=f"Email {data['email']} već koristi drugi član.")

    # priprema update-a
    update_expr_parts = []
    expr_vals = {}
    for k, v in data.items():
        if k == "mobitel":
            v = "".join(ch for ch in v if ch.isdigit())
        update_expr_parts.append(f"{k} = :{k}")
        expr_vals[f":{k}"] = v

    if not update_expr_parts:
        return {"message": "Nema promjena."}

    from .dynamo import update_member as ddb_update_member
    try:
        ddb_update_member(member_id, update_expr_parts, expr_vals)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Greška pri ažuriranju.")

    return {"message": "Podaci člana ažurirani."}


@app.delete("/members/{member_id}", dependencies=[Depends(verify_api_key)])
def delete_member(member_id: int):
    if not ddb_get_member(member_id):
        raise HTTPException(status_code=404, detail="Član nije pronađen.")
    ddb_delete_member(member_id)
    # ako postoji membership – obriši
    ddb_delete_membership(member_id)
    return {"message": "Član obrisan."}

# Članarina (postavljanje/izmjena)
@app.put("/members/{member_id}/membership", dependencies=[Depends(verify_api_key)])
def update_membership(member_id: int, membership: Membership):
    if not ddb_get_member(member_id):
        raise HTTPException(status_code=404, detail="Član nije pronađen.")
    ddb_put_membership(
        member_id=member_id,
        datum_uplate=membership.datum_uplate,
        datum_isteka=membership.datum_isteka,
        iznos=membership.iznos,
        status=membership.status
    )
    return {"message": "Članarina ažurirana."}

# Brisanje članarine
@app.delete("/members/{member_id}/membership", dependencies=[Depends(verify_api_key)])
def delete_membership(member_id: int):
    if not ddb_get_member(member_id):
        raise HTTPException(status_code=404, detail="Član nije pronađen.")
    ddb_delete_membership(member_id)
    return {"message": "Članarina obrisana."}

# Termini
@app.put("/members/{member_id}/assign-session/{session_id}", dependencies=[Depends(verify_api_key)])
def assign_session(member_id: int, session_id: int):
    m = ddb_get_member(member_id)
    if not m:
        raise HTTPException(status_code=404, detail="Član nije pronađen.")
    s = ddb_get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Termin nije pronađen.")
    if m["grupa"] != s["grupa"]:
        raise HTTPException(status_code=400, detail=f"Član je u grupi '{m['grupa']}', a termin je za grupu '{s['grupa']}'.")
    if ddb_count_enrolled(session_id) >= int(s["max_clanova"]):
        raise HTTPException(status_code=409, detail="Termin je popunjen (dosegnut maksimalni broj članova).")
    ddb_assign_session(member_id, session_id)
    return {"message": "Član upisan u termin."}

@app.put("/members/{member_id}/unassign-session", dependencies=[Depends(verify_api_key)])
def unassign_session(member_id: int):
    if not ddb_get_member(member_id):
        raise HTTPException(status_code=404, detail="Član nije pronađen.")
    ddb_unassign_session(member_id)
    return {"message": "Član odjavljen iz termina."}

# Odjava iz termina


# TERMINI

@app.post("/sessions", dependencies=[Depends(verify_api_key)])
def add_session(session: TrainingSession):
    if ddb_get_session(session.id):
        raise HTTPException(status_code=409, detail=f"Termin s ID={session.id} već postoji.")
    ddb_put_session({
        "id": session.id,
        "grupa": session.grupa,
        "dan": session.dan.lower(),
        "vrijeme": session.vrijeme.strftime("%H:%M:%S"),
        "max_clanova": session.max_clanova
    })
    return {"message": f"Termin za grupu {session.grupa} ({session.dan} u {session.vrijeme}) dodan."}


# IZVJEŠĆA
@app.get("/reports/occupancy")
def report_occupancy() -> List[Dict]:
    out = []
    sessions = ddb_list_sessions()
    for s in sessions:
        sid = int(s["id"])
        upisani = ddb_count_enrolled(sid)
        out.append({
            "session_id": sid,
            "grupa": s["grupa"],
            "dan": s["dan"],
            "vrijeme": s["vrijeme"],
            "upisani": upisani,
            "max": int(s["max_clanova"]),
            "preostalo": max(0, int(s["max_clanova"]) - upisani),
        })
    return out

@app.get("/reports/active-per-group")
def report_active_per_group() -> Dict[str, int]:
    result = {g: 0 for g in ALLOWED_GROUPS}
    members = ddb_list_members()
    for m in members:
        if m.get("status") == "aktivan":
            result[m["grupa"]] += 1
    return result
@app.get("/sessions")
def get_sessions() -> List[TrainingSession]:
    items = ddb_list_sessions()
    out: List[TrainingSession] = []
    for r in items:
        out.append(
            TrainingSession(
                id=int(r["id"]),
                grupa=r["grupa"],
                dan=r["dan"],
                vrijeme=time.fromisoformat(r["vrijeme"]),
                max_clanova=int(r["max_clanova"]),
            )
        )
    return out
