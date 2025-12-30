"""
Skripta za popunjavanje baze testnim podacima
"""
import os
import requests
from datetime import date, timedelta

# Postavi environment varijable
os.environ["DDB_ENDPOINT"] = "http://localhost:8000"

BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8080")  # Promijeni u http://localhost za Nginx
API_KEY = os.getenv("API_KEY", "sparta-secret-key-2024")

# Headers s API Key-em
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def check_api():
    """Provjeri je li API dostupan"""
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            print("API je dostupan")
            return True
    except Exception as e:
        print(f"API nije dostupan: {e}")
        print("Pokreni aplikaciju prvo: start.bat")
        return False

def add_sessions():
    """Dodaj termine treninga"""
    print("\n Dodajem termine...")
    
    sessions = [
        {"id": 1, "grupa": "početni", "dan": "ponedjeljak", "vrijeme": "18:00:00", "max_clanova": 15},
        {"id": 2, "grupa": "početni", "dan": "srijeda", "vrijeme": "18:00:00", "max_clanova": 15},
        {"id": 3, "grupa": "srednji", "dan": "utorak", "vrijeme": "19:00:00", "max_clanova": 12},
        {"id": 4, "grupa": "srednji", "dan": "četvrtak", "vrijeme": "19:00:00", "max_clanova": 12},
        {"id": 5, "grupa": "napredni", "dan": "ponedjeljak", "vrijeme": "20:00:00", "max_clanova": 10},
        {"id": 6, "grupa": "napredni", "dan": "petak", "vrijeme": "20:00:00", "max_clanova": 10},
    ]
    
    for session in sessions:
        try:
            response = requests.post(f"{BASE_URL}/sessions", json=session, headers=HEADERS)
            if response.status_code == 200:
                print(f"  Termin {session['id']}: {session['grupa']} - {session['dan']} {session['vrijeme']}")
            else:
                print(f"  Termin {session['id']} već postoji ili greška")
        except Exception as e:
            print(f" Greška pri dodavanju termina {session['id']}: {e}")

def add_members():
    """Dodaj članove"""
    print("\n Dodajem članove...")
    
    members = [
        {"id": 1, "ime": "Ana", "prezime": "Marić", "email": "ana.maric@test.com", "mobitel": "0912345678", "grupa": "početni", "status": "aktivan"},
        {"id": 2, "ime": "Marko", "prezime": "Horvat", "email": "marko.horvat@test.com", "mobitel": "0923456789", "grupa": "početni", "status": "aktivan"},
        {"id": 3, "ime": "Ivana", "prezime": "Kovač", "email": "ivana.kovac@test.com", "mobitel": "0934567890", "grupa": "srednji", "status": "aktivan"},
        {"id": 4, "ime": "Petar", "prezime": "Novak", "email": "petar.novak@test.com", "mobitel": "0945678901", "grupa": "srednji", "status": "aktivan"},
        {"id": 5, "ime": "Lucija", "prezime": "Babić", "email": "lucija.babic@test.com", "mobitel": "0956789012", "grupa": "napredni", "status": "aktivan"},
        {"id": 6, "ime": "Tomislav", "prezime": "Jurić", "email": "tomislav.juric@test.com", "mobitel": "0967890123", "grupa": "napredni", "status": "aktivan"},
        {"id": 7, "ime": "Maja", "prezime": "Božić", "email": "maja.bozic@test.com", "mobitel": "0978901234", "grupa": "početni", "status": "neaktivan"},
        {"id": 8, "ime": "Filip", "prezime": "Knežević", "email": "filip.knezevic@test.com", "mobitel": "0989012345", "grupa": "srednji", "status": "aktivan"},
    ]
    
    for member in members:
        try:
            response = requests.post(f"{BASE_URL}/members", json=member, headers=HEADERS)
            if response.status_code == 200:
                print(f"  ✓ Član {member['id']}: {member['ime']} {member['prezime']} ({member['grupa']})")
            else:
                print(f"  ⚠ Član {member['id']} već postoji ili greška")
        except Exception as e:
            print(f" Greška pri dodavanju člana {member['id']}: {e}")

def add_memberships():
    """Dodaj članarine aktivnim članovima"""
    print("\n💳 Dodajem članarine...")
    
    today = date.today()
    expiry = today + timedelta(days=365)
    
    active_members = [1, 2, 3, 4, 5, 6, 8]
    
    for member_id in active_members:
        membership = {
            "datum_uplate": today.isoformat(),
            "datum_isteka": expiry.isoformat(),
            "iznos": 500.00,
            "status": "aktivan"
        }
        try:
            response = requests.put(f"{BASE_URL}/members/{member_id}/membership", json=membership, headers=HEADERS)
            if response.status_code == 200:
                print(f" Članarina za člana {member_id}")
            else:
                print(f" Greška pri dodavanju članarine za člana {member_id}")
        except Exception as e:
            print(f" Greška: {e}")

def assign_to_sessions():
    """Upiši članove u termine"""
    print("\n Upisujem članove u termine...")
    
    assignments = [
        (1, 1),  
        (2, 2),  
        (3, 3),  
        (4, 4),  
        (5, 5), 
        (6, 6),  
        (8, 3), 
    ]
    
    for member_id, session_id in assignments:
        try:
            response = requests.put(f"{BASE_URL}/members/{member_id}/assign-session/{session_id}", headers=HEADERS)
            if response.status_code == 200:
                print(f"  ✓ Član {member_id} upisan u termin {session_id}")
            else:
                print(f"  ⚠ Greška pri upisu člana {member_id} u termin {session_id}")
        except Exception as e:
            print(f"Greška: {e}")

def show_reports():
    """Prikaži izvještaje"""
    print("\n IZVJEŠTAJI:")
    print("="*50)
    
    # Popunjenost termina
    print("\n1. Popunjenost termina:")
    try:
        response = requests.get(f"{BASE_URL}/reports/occupancy")
        if response.status_code == 200:
            occupancy = response.json()
            for session in occupancy:
                print(f"  Termin {session['session_id']}: {session['grupa']} - {session['dan']} {session['vrijeme']}")
                print(f"    Upisani: {session['upisani']}/{session['max']} (preostalo: {session['preostalo']})")
    except Exception as e:
        print(f"   Greška: {e}")
    
    # Aktivni po grupama
    print("\n2. Broj aktivnih članova po grupama:")
    try:
        response = requests.get(f"{BASE_URL}/reports/active-per-group")
        if response.status_code == 200:
            active = response.json()
            for grupa, count in active.items():
                print(f"  {grupa}: {count} članova")
    except Exception as e:
        print(f"   Greška: {e}")
    
    print("="*50)

def main():
    print("="*50)
    print("  POPUNJAVANJE BAZE TESTNIM PODACIMA")
    print("  Sportsko društvo 'Sparta'")
    print("="*50)
    
    if not check_api():
        return
    
    add_sessions()
    add_members()
    add_memberships()
    assign_to_sessions()
    show_reports()
    
    print("\n Svi testni podaci dodani!")
    print(f"\n Otvori u browseru: {BASE_URL}/docs")

if __name__ == "__main__":
    main()