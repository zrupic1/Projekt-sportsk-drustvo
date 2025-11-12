from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional, Dict
from datetime import date, time


# Kreiranje glavnog objekta FastAPI
app = FastAPI(
    title="Evidencija članarina sportskog društva Sparta",
    version="1.2.0"
)
ALLOWED_GROUPS = {"početni", "srednji", "napredni"}
ALLOWED_DAYS = {"ponedjeljak", "utorak", "srijeda", "četvrtak", "petak", "subota"}
ALLOWED_STATUS = {"aktivan", "neaktivan"}

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
            raise ValueError(f"grupa mora biti jedna od: {sorted(ALLOWED_DAYS)}")
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
@app.post("/members")
def add_member(member: Member):
    if any(m.id == member.id for m in members_db):
        raise HTTPException(status_code=409, detail=f"Član s ID={member.id} već postoji.")
    if any(m.email == member.email for m in members_db):
        raise HTTPException(status_code=409, detail=f"Član s emailom {member.email} već postoji.")

    members_db.append(member)
    return {"message": f"Član {member.ime} {member.prezime} uspješno dodan."}

# Ruta za dohvat svih članova
@app.get("/members")
def get_members():
    return members_db

# Promjena podataka o stanju članarine
@app.put("/members/{member_id}/membership")
def update_membership(member_id: int, membership: Membership):
    for member in members_db:
        if member.id == member_id:
            member.membership = membership
            return {"message": f"Članarina za {member.ime} {member.prezime} ažurirana."}
    return {"error": "Član nije pronađen."}

# Dodavanje člana u termin
@app.get("/members/{member_id}")
def get_member(member_id: int) -> Member:
    member = get_member_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Član nije pronađen.")
    return member

@app.patch("/members/{member_id}")
def update_member(member_id: int, patch: MemberUpdate):
    member = get_member_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Član nije pronađen.")

    # ako mijenjamo email, provjeri da nije zauzet
    if patch.email and any(m.email == patch.email and m.id != member_id for m in members_db):
        raise HTTPException(status_code=409, detail=f"Email {patch.email} već koristi drugi član.")

    # primijeni promjene samo na poslana polja
    data = patch.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(member, k, v)
    return {"message": f"Podaci člana {member.ime} {member.prezime} ažurirani."}

@app.delete("/members/{member_id}")
def delete_member(member_id: int):
    idx = next((i for i, m in enumerate(members_db) if m.id == member_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Član nije pronađen.")
    removed = members_db.pop(idx)
    return {"message": f"Član {removed.ime} {removed.prezime} obrisan."}

# Članarina (postavljanje/izmjena)
@app.put("/members/{member_id}/membership")
def update_membership(member_id: int, membership: Membership):
    member = get_member_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Član nije pronađen.")
    member.membership = membership
    return {"message": f"Članarina za {member.ime} {member.prezime} ažurirana."}

# Brisanje članarine
@app.delete("/members/{member_id}/membership")
def delete_membership(member_id: int):
    member = get_member_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Član nije pronađen.")
    member.membership = None
    return {"message": f"Članarina za {member.ime} {member.prezime} obrisana."}

# Termini
@app.put("/members/{member_id}/assign-session/{session_id}")
def assign_session(member_id: int, session_id: int):
    member = get_member_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Član nije pronađen.")
    session = get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Termin nije pronađen.")

    if member.grupa != session.grupa:
        raise HTTPException(status_code=400, detail=f"Član je u grupi '{member.grupa}', a termin je za grupu '{session.grupa}'.")

    if count_enrolled(session_id) >= session.max_clanova:
        raise HTTPException(status_code=409, detail="Termin je popunjen (dosegnut maksimalni broj članova).")

    member.termin = session_id
    return {"message": f"{member.ime} {member.prezime} upisan u termin {session.grupa} ({session.dan} u {session.vrijeme})."}

# Odjava iz termina
@app.put("/members/{member_id}/unassign-session")
def unassign_session(member_id: int):
    member = get_member_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Član nije pronađen.")
    member.termin = None
    return {"message": f"{member.ime} {member.prezime} odjavljen iz termina."}

# TERMINI
@app.post("/sessions")
def add_session(session: TrainingSession):
    if any(s.id == session.id for s in sessions_db):
        raise HTTPException(status_code=409, detail=f"Termin s ID={session.id} već postoji.")
    sessions_db.append(session)
    return {"message": f"Termin za grupu {session.grupa} ({session.dan} u {session.vrijeme}) dodan."}

@app.get("/sessions")
def get_sessions() -> List[TrainingSession]:
    return sessions_db

# IZVJEŠĆA
@app.get("/reports/occupancy")
def report_occupancy() -> List[Dict]:
    """Popunjenost po terminima (upisani / max / preostalo)."""
    out = []
    for s in sessions_db:
        upisani = count_enrolled(s.id)
        out.append({
            "session_id": s.id,
            "grupa": s.grupa,
            "dan": s.dan,
            "vrijeme": s.vrijeme.isoformat(),
            "upisani": upisani,
            "max": s.max_clanova,
            "preostalo": max(0, s.max_clanova - upisani),
        })
    return out

@app.get("/reports/active-per-group")
def report_active_per_group() -> Dict[str, int]:
    """Broj aktivnih članova po grupama."""
    result = {g: 0 for g in ALLOWED_GROUPS}
    for m in members_db:
        if m.status == "aktivan":
            result[m.grupa] += 1
    return result