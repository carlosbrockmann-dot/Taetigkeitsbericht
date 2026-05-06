# Tätigkeitsbericht

Die Zeitaufschreibung soll nach den Kriterien der Clean-Architektur passieren, sodass die Programmbestandteile 
wiederverwendet werden können. 

Das Programm soll sich die Feiertage aus einer bekannten JSON-Adresse von Google herunter laden können, 
und die entsprechende Tage damit markieren. 

## Model 

Tabelle Zeiteinträge (name=tblZeiteintraege) 
- Datum: Date
- Uhrzeit_Von: Time
- Uhrzeit_Bis: Time
- Unterbrechung_Beginn: Time
- Unterbrechung_Ende: Time
- Anmerkung: String(80) 

Tabelle Stundenplan (name=tblStundenplan)
- Wochentag: int (1 = Montag, 7 = Sonntag) 
- Uhrzeit_Von: Time
- Uhrzeit_Bis: Time
- Unterbrechung_Beginn: Time
- Unterbrechung_Ende: Time
- Anmerkung: String(80) 

Tabelle "Feiertage" (name=tblFeiertage)
- Datum: Date
- Feiertagname: String


## Desktop-Frontend 

Diese Anwendung soll eine plattformübergreifendes Desktop-Frontend ergeben, das die Zeitaufschreibung in eine SQLite-Datenbank speichert. 
Zusätzlich soll ein Export der Stunden nach MS-Excel möglich sein. 

## Web-Frontend 

Über IndexedDB wird man sich die eigenen Einträge sichern, die man mit dem Backend synchronisieren kann. 

## Backend über GraphQL 

Die Kommunikation soll zu einer GraphQL-API geschehen, wenn man am Monatsende die Stunden "abgeben" will und die Abrechnung für den Monat geschehen soll. 
Dann spätestens muss man sich vorher einloggen und ein Token für die Abgabe erhalten. 

## Anbindung zur Datenbank 

Die Persistenz erfolgt über SQLite. Die Anbindung geschieht über ein ORM (SQLModel auf Basis von SQLAlchemy); per Dependency Injection und Repository-Pattern bleiben die Aufrufer von der konkreten Speicherung entkoppelt. 


## Python Setup

Empfohlen ist eine lokale virtuelle Umgebung (`venv`), damit Abhaengigkeiten isoliert sind.

### Linux (Bash)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Zum Verlassen der Umgebung:

```bash
deactivate
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Zum Verlassen der Umgebung:

```powershell
deactivate
```

### Pydantic installieren

Mit aktivierter virtueller Umgebung (siehe oben) ist Pydantic bereits enthalten, wenn Sie alle Abhaengigkeiten aus `requirements.txt` installiert haben. Alternativ nur Pydantic nach gleicher Versionsvorgabe wie in der Datei:

**Linux (Bash)**

```bash
pip install "pydantic>=2.7,<3.0"
```

**Windows (PowerShell)**

```powershell
pip install "pydantic>=2.7,<3.0"
```

Die Befehle sind auf beiden Systemen identisch, sobald `pip` aus der aktiven `.venv` verwendet wird.

### SQLModel installieren

SQLModel baut auf SQLAlchemy und Pydantic auf; mit `pip install -r requirements.txt` ist es ebenfalls dabei. Nur SQLModel installieren (Version wie in `requirements.txt`):

**Linux (Bash)**

```bash
pip install "sqlmodel>=0.0.22"
```

**Windows (PowerShell)**

```powershell
pip install "sqlmodel>=0.0.22"
```

Wiederum gleicher `pip`-Aufruf unter Linux und Windows bei aktivierter virtueller Umgebung.

