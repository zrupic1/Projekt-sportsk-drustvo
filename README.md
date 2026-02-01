# Evidencija članarina - Sportsko društvo "Sparta"

Distribuirani sustav za evidenciju članova, članarina i rasporeda treninga sportskog društva. Backend je razvijen u Pythonu korištenjem FastAPI frameworka, a podaci o članovima i terminima pohranjeni su u DynamoDB bazi podataka. Horizontalna skalabilnost postignuta je pomoću Nginx alata koji ravnomjerno raspoređuje promet između više instanci servisa.

# Funkcionalnosti

Sustav omogućuje:
- Unos, ažuriranje, brisanje i pregled članova s mogućnošću filtriranja po grupi i statusu
- Dodavanje termina vježbanja s provjerom kapaciteta (maksimalno 20 članova po grupi)
- Upis i odjavu članova u termine s provjerom usklađenosti grupe
- Praćenje članarina (datum uplate, datum isteka, iznos, status)
- Generiranje izvještaja o popunjenosti termina i broju aktivnih članova po grupama


Grupe članova podijeljene su na tri razine: početni, srednji i napredni. Sustav provjerava je li član može biti upisan u određeni termin na temelju njegove grupe.

# Arhitektura sustava

Sustav se sastoji od sljedećih komponenti:
```
                    Nginx Load Balancer (port 80)
                              |
            +-----------------+-----------------+
            |                 |                 |
      FastAPI (8081)    FastAPI (8082)    FastAPI (8083)
            |                 |                 |
            +-----------------+-----------------+
                              |
                         DynamoDB (8000)
```

Komponente:
- FastAPI - backend aplikacija razvijena u Pythonu
- DynamoDB Local - NoSQL baza podataka pokrenuta u Docker containeru
- Nginx - load balancer za raspodjelu prometa između API instanci
- Docker Compose - orkestracija svih servisa

# Pokretanje projekta

# Lokalni development

Za lokalno pokretanje aplikacije potrebno je pokrenuti DynamoDB i FastAPI aplikaciju:
```bash
docker run -d --name dynamodb-local -p 8000:8000 amazon/dynamodb-local -jar DynamoDBLocal.jar -sharedDb
start.bat
```

Aplikacija će biti dostupna na http://127.0.0.1:8000

# Distribuirani sustav

Za pokretanje kompletnog distribuiranog sustava s tri API instance i Nginx load balancerom:
```bash
docker-compose build
docker-compose up -d
docker-compose ps
```

Aplikacija će biti dostupna na http://localhost

Provjera statusa servisa:
```bash
docker-compose logs -f
```

Zaustavljanje servisa:
```bash
docker-compose down
```

## Testiranje

# Popunjavanje baze testnim podacima

Projekt uključuje skriptu za automatsko popunjavanje baze testnim podacima:
```bash
python seed_data.py
```

Skripta dodaje primjerne testne podatke.

# API endpointi

Sustav ima sljedeće endpointe:

Članovi:
- GET /members - dohvat svih članova
- GET /members?grupa=početni&status=aktivan - filtriranje članova
- GET /members/{id} - dohvat pojedinog člana
- POST /members - dodavanje novog člana (zahtijeva API Key)
- PATCH /members/{id} - ažuriranje člana (zahtijeva API Key)
- DELETE /members/{id} - brisanje člana (zahtijeva API Key)

Termini:
- GET /sessions - dohvat svih termina
- POST /sessions - dodavanje termina (zahtijeva API Key)
- PUT /members/{id}/assign-session/{sid} - upis člana u termin (zahtijeva API Key)
- PUT /members/{id}/unassign-session - odjava člana iz termina (zahtijeva API Key)

Članarine:
- PUT /members/{id}/membership - postavljanje/ažuriranje članarine (zahtijeva API Key)
- DELETE /members/{id}/membership - brisanje članarine (zahtijeva API Key)

Izvještaji:
- GET /reports/occupancy - izvještaj o popunjenosti termina
- GET /reports/active-per-group - broj aktivnih članova po grupama

# Autentifikacija

Mutirajuće operacije (POST, PUT, PATCH, DELETE) zaštićene su API ključem. Za pristup potrebno je u HTTP header dodati:
```
X-API-Key: sparta-secret-key-2024
```

U Swagger UI dokumentaciji potrebno je kliknuti na gumb "Authorize" i unijeti API ključ.

## Struktura projekta
```
Projekt-sportsk-drustvo/
├── app/
│   ├── __init__.py
│   ├── main.py          
│   └── dynamo.py        
├── docker-compose.yml   
├── Dockerfile           
├── nginx.conf           
├── seed_data.py         
├── requirements.txt     
├── start.bat            
└── README.md            
```

Opis datoteka:
- main.py - FastAPI rute, validatori i poslovna logika
- dynamo.py - funkcije za pristup DynamoDB bazi podataka
- docker-compose.yml - konfiguracija Docker servisa (DynamoDB, 3x FastAPI, Nginx)
- Dockerfile - definicija Docker slike za FastAPI aplikaciju
- nginx.conf - konfiguracija Nginx load balancera
- seed_data.py - skripta za popunjavanje baze testnim podacima
- requirements.txt - popis Python paketa
- start.bat - skripta za pokretanje aplikacije u lokalnom okruženju

## DynamoDB tablice

Sustav koristi tri DynamoDB tablice:

1. members - podaci o članovima (Primary Key: id)
2. sessions - termini treninga (Primary Key: id)
3. memberships - podaci o članarinama (Primary Key: member_id)

Tablice se automatski kreiraju pri prvom pokretanju aplikacije.

## Dokumentacija

FastAPI automatski generira interaktivnu dokumentaciju dostupnu na:
- /docs - Swagger UI dokumentacija
- /redoc - ReDoc dokumentacija

## Rješavanje problema

Ako DynamoDB ne radi:
```bash
docker restart dynamodb-local
```

Ako je port zauzet:
```bash
uvicorn app.main:app --reload --port 8081
```

Ako Docker Compose ne radi kako treba:
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## Autor

Željka Rupić
Sveučilište Jurja Dobrile u Puli
Kolegij: Raspodijeljeni sustavi

Projekt razvijen za potrebe polaganja kolegija.