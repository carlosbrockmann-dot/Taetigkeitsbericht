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
- Uhrzeit_Von: Time
- Uhrzeit_Bis: Time
- Unterbrechung_Beginn: Time
- Unterbrechung_Ende: Time
- Anmerkung: String(80) 


## Desktop-Frontend 

Diese Anwendung soll eine plattformübergreifendes Desktop-Frontend ergeben, das die Zeitaufschreibung in eine MySQL-Datenbank speichert. 
Zusätzlich soll ein Export der Stunden nach MS-Excel möglich sein. 

## Web-Frontend 

Über IndexedDB wird man sich die eigenen Einträge sichern, die man mit dem Backend synchronisieren kann. 

## Backend über GraphQL 

Die Kommunikation soll zu einer GraphQL-API geschehen, wenn man am Monatsende die Stunden "abgeben" will und die Abrechnung für den Monat geschehen soll. 
Dann spätestens muss man sich vorher einloggen und ein Token für die Abgabe erhalten. 

## Anbindung zur Datenbank 

Soll auf jeden Fall über ein ORM-Framework wie AIAlchemy oder SQLModel geschehen. Per DI und mit dem Reposity-Pattern kann man sich aussuchen, mit welcher Datenbank sich verbinden will. 



