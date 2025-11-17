@echo off
echo Pokrećem aplikaciju...
call .venv\Scripts\activate
set DDB_ENDPOINT=http://localhost:8000
echo.
echo Aplikacija će biti dostupna na: http://127.0.0.1:8080
echo Pritisni Ctrl+C za zaustavljanje
echo.
uvicorn app.main:app --reload --port 8080