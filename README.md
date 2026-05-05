# Tätigkeitsbericht

Die Zeitaufschreibung soll nach den Kriterien der Clean-Architektur passieren, sodass die Programmbestandteile 
wiederverwendet werden können. 

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
