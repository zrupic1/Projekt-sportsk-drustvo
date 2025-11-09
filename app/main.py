from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

# Kreiranje glavnog objekta FastAPI
app = FastAPI(
    title="Evidencija članarina sportskog društva Sparta",
    version="1.0.0"
)

# Model podataka za jednog člana
class Member(BaseModel):
    id: int
    ime: str
    prezime: str
    email: str
    mobitel: str
    grupa: str       # početni, srednji, napredni
    status: str      # aktivan / neaktivan

# Privremena "baza" u memoriji
members_db: List[Member] = []

# Početna testna ruta
@app.get("/")
def home():
    return {"message": "Dobrodošli u API za evidenciju članarina!"}

# Ruta za dodavanje novog člana
@app.post("/members")
def add_member(member: Member):
    members_db.append(member)
    return {"message": f"Član {member.ime} {member.prezime} uspješno dodan!"}

# Ruta za dohvat svih članova
@app.get("/members")
def get_members():
    return members_db
