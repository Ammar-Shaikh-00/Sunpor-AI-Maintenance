# SUNPOR × SCLERA – Projektanforderungsdokument
**Projekt:** KI-basiertes Prozessüberwachungs-, Frühwarn- und prädiktives Qualitätssystem für die EPS-Schaumextrusion
**Produktionslinie:** E10 (erste Linie; System zur späteren Erweiterung auf weitere Linien konzipiert)
**Erstellt von:** SCLERA Group – AI Solutions
**Kunde:** SUNPOR
**Dokumenttyp:** Dokument mit Lebensanforderungen und Entwicklungspfad (kundengesteuert)
**Version:** 2.0
**Status:** Basislinie für die Entwicklung

# 0. So lesen Sie dieses Dokument
Dieses Dokument ist die **einzige Quelle der Wahrheit** für das, was wir bauen und warum. Es wird **aus den angegebenen Bedürfnissen des Kunden** abgeleitet (Besprechungs-E-Mails und technischer Fragebogen).
Zwei wichtige Rahmenpunkte:
1. **Der Kunde ist ein Domänenexperte, kein Technik-/KI-Experte.** Er sagt uns, was das System tun soll; **Wir entwerfen, entscheiden und steuern die technische Umsetzung** selbst.
1. **Es ist kein historischer Datensatz vom Kunden verfügbar.** Alle Lerndaten – Signalverlauf, Bedienereingaben, Qualitätsergebnisse, Wartungsereignisse – werden von unserem System vom ersten Tag an **live** erfasst und im Laufe der Zeit aufgebaut.
Das System ist in **Erkennungsfunktionen** unterteilt (keine nummerierten Modelle). Jede Funktion wird auf die gleiche Weise beschrieben:
- **Kundenbedarf** – was SUNPOR in der Absicht will
- **Was es erkennt** – die konkrete Ausgabe, die das System erzeugt
- **Eingaben** – Signale + Bedienerformulare + Qualitäts-/Wartungsdaten
- **Wie wir es entwickeln** – die Methode/der Ansatz, ggf. in Etappen
- **Abhängigkeiten** – was zuerst vorhanden sein muss, entweder technisch oder in Bezug auf die gesammelten Daten
- **Offene Posten** – was wir noch vom Kunden benötigen, um es fertigzustellen oder zu verbessern
Alle Fähigkeiten werden als **gleich wichtige Säulen** behandelt. Die Build-Reihenfolge wird durch **technische Abhängigkeit** bestimmt, nicht durch die Rangfolge einer Fähigkeit über einer anderen.

# 1. Kundenvision
SUNPOR möchte **nicht** nur ein Dashboard oder eine Visualisierung von Sensorwerten. Der Kunde wünscht sich ein **intelligentes Assistenz- und Interpretationssystem** für die Produktion, das:
1. Analysiert das Prozessverhalten über alle Anlagenbereiche hinweg.
1. Erkennt Muster in den gesammelten Produktionsdaten und verknüpft sie mit Qualitätsergebnissen im Laufe der Zeit.
1. Erkennt **Frühindikatoren**, bevor ein Fehler, ein Stillstand oder ein Qualitätsverlust auftritt.
1. Prognostiziert den Wartungsbedarf (Werkzeugverschleiß: Messer, Sieb, Düse).
1. Priorisiert kritische Entwicklungen und unterstützt die Betreiber aktiv.
1. Generiert automatisch relevante Warnungen (einschließlich mobiler Warnungen).
Vom Kunden angegebenes Kernprinzip:
> „Nicht erst reagieren, wenn ein Fehler bereits aufgetreten ist, sondern Entwicklungen und Auffälligkeiten möglichst frühzeitig sichtbar machen.“

# 2. Zentrale Probleme, die das System lösen muss

## 2.1 Verzögerte Fehlererkennung (frühe Dosiererdrift)
Veränderungen treten **frühzeitig an den Dosiereinheiten** auf – längere Einlauf-/Förderzeiten, ungewöhnliche Vibrationen, Dosierabweichungen – **bevor** der Extruder oder die Produktion einen Fehler meldet. Heute werden diese frühen Anzeichen übersehen.
**Anforderung:** Erkennen Sie Verhaltensänderungen und Frühindikatoren **an der Quelle**, bevor der eigentliche Fehler auftritt. Dies ist eine Phase-1-Priorität.

## 2.2 Verzögerte Qualitätsbewertung
Die endgültige Qualität wird **Tage nach der Produktion** gemessen (das Produkt muss schäumen, aushärten und gelagert werden). Qualitätsprobleme werden daher erst mit großer Verzögerung sichtbar.
**Anforderung:** Sobald spätere Qualitätsergebnisse von der Qualitätsabteilung aufgezeichnet werden, **korrelieren** Sie diese wieder mit den erfassten Signal- und Bedienerdaten des Laufs, damit das System nach und nach lernt, **die Qualität während der Produktion vorherzusagen**.

## 2.3 Undokumentierte Wartungs- und Bedienerereignisse
Ereignisse wie Messerwechsel/-schärfen, Reinigung, Materialwechsel und manuelle Eingriffe werden oft **nicht erfasst** in SCADA-/Produktionsdaten, sind aber für die Analyse unerlässlich.
**Anforderung:** Erfassen Sie diese über Bedienereingabeformulare und verwenden Sie sie als Beschriftungen/Kontext.

# 3. Systemumfang

## 3.1 Im Geltungsbereich
- Aufnahme von Live-WinCC-Signalen (Linie E10, heute 104 Tags; weitere werden hinzugefügt).
- Datenbereinigung, Qualitätskennzeichnung und fortlaufender Verlauf.
- Feature-Engineering über mehrere Zeitfenster.
- Erkennungsfunktionen (Abschnitt 7) + Korrelations-/Lernschicht.
- Bedienereingabeformulare (Ereignisse, Materialverhalten, Qualität, Blockierung).
- Progressive Live-Datenerfassung zum Aufbau des internen Lerndatensatzes.
- Korrelation von Produktionsdaten mit verzögerten Qualitätsergebnissen (so wie sie eintreffen).
- Vorhersagen/Warnungen werden gespeichert und im Dashboard angezeigt; Handy-/Benachrichtigungsalarme.

## 3.2 Außerhalb des Geltungsbereichs (explizit)
- Rezepte und vertrauliche Produktionsparameter (vom Kunden bestätigt, nicht erforderlich).
- Direkte Maschinensteuerung / Regelung im geschlossenen Regelkreis – das System ist **beratend**.
- Ersetzt das Urteilsvermögen des Bedieners – das System **unterstützt** den Bediener bei der Entscheidung.
- Vertrauen auf einen bereits vorhandenen historischen Datensatz des Clients (kein verfügbar).

## 3.3 Nichtfunktionale Anforderungen
- **Nur Hinweis:** Kein Zurückschreiben zur Maschinensteuerung.
- **Jederzeit konfigurierbar:** Dropdown-Felder sind datengesteuert und ohne erneute Bereitstellung bearbeitbar; Erkennungsschwellenwerte sind in der Konfiguration enthalten und können mit zunehmender Erfahrung angepasst werden (dies beantwortet direkt die Frage des Kunden nach späteren Dropdown-/Schwellenwertänderungen).
- **Erweiterbar:** Durch das Hinzufügen eines Signals zu einer Maschinenbereichsgruppe wird es automatisch an die richtigen Funktionen weitergeleitet – keine fest codierten Tag-Namen.
- **Robust:** Aufnahme-/Funktions-/Vorhersageschleifen dürfen den Dienst niemals zum Absturz bringen.
- **Nachverfolgbar:** Jede Vorhersage speichert ihr Eingabezeitfenster und eine für Menschen lesbare Erklärung.
- **Mehrzeilenfähig:** Das Design muss von E10 auf andere Zeilen verallgemeinert werden.
- **Lernt mit der Zeit:** Die Funktionen funktionieren vom ersten Tag an in einer grundlegenden (Regel-/heuristischen) Form und verbessern sich automatisch, wenn Live-Daten anfallen.

# 4. Datenquellen

## 4.1 Automatisch (WinCC-Signale – 104 Tags auf E10 heute)
Gruppiert nach Maschinenbereich; Gruppen sind die Einheit des Feature-Engineerings.

| Signalgruppe | Zählen | Hauptverwendung |
|---|---|---|
| Heizzonen | 27 | Prozessstatus, Anomalie |
| Feeder | 31 | Prozesszustand, frühe Anomalie, Materialverhalten |
| extruder_meltpump | 4 | Prozessstatus, Anomalie |
| Schmelzdruck | 5 | Prozesszustand, Düse/Sieb, Vorhersagequalität |
| screen_changer | 14 | Düse/Sieb, Anomalie |
| Prozesswasser | 7 | Materialverhalten, Granulator, Anomalie |
| Granulator | 6 | Granulator/Messer, Anomalie |
| Pentan_Stickstoff | 3 | Materialverhalten, Anomalie |
| Offspec | 5 | Vorhersagequalität, Anomalie |
| Status | 1 | Prozessstatus |

**Zu ergänzende Signale (vom Kunden genannt, noch nicht im Export):** Dosierer-Vibrationssensoren, Dosierer-Einspeise-/Förderzeiten, Dosierer gefüllt/aktiver Status, Granulator-Vibration, Dosierer 6/7 tatsächlicher Durchsatz. Diese sind wichtig für die Früherkennung von Dosiererfehlern (Abschnitt 7.2).

## 4.2 Operatorformulare (manueller Kontext und Beschriftungen)
Produktionsstart; Extruder-Events; Granulator-Ereignisse; Reinigung; Fehler; Materialverhalten; Materialblockierung; tägliche Qualität. (Siehe Abschnitt 9.)

## 4.3 Qualitätsabteilung
Spätere Qualitätsbewertungen, Anomalien, Genehmigungen/Ablehnungen – die **grundlegende Wahrheit** für die Vorhersagequalität.

## 4.4 Interner Lerndatensatz (von uns erstellt)
Da es keinen historischen Datensatz gibt, erstellen wir unseren eigenen, indem wir kontinuierlich Folgendes aufzeichnen:
- Alle aufgenommenen Signale und ihre berechneten Merkmale.
- Alle Vorhersagen (mit Eingabefenstern und Erklärungen).
- Alle Operator-Formulareinträge.
- Alle Ergebnisse der Qualitätsabteilung.
- Alle Wartungsereignisse.
Dieser Datensatz ermöglicht es, die Vorhersagequalität (7.4) und die Korrelations- und Lernschicht (Abschnitt 10) im Laufe der Zeit zu verbessern.

# 5. Systemarchitektur

```
WinCC / Backend  ──►  Ingestion (periodic poll)
                        │
                        ▼
                    Data Cleaner  (validate, deduplicate, quality tag:
                                   GOOD / STALE / OUT_OF_RANGE / BAD / MISSING)
                        │
                        ▼
                Rolling Window Buffer  (recent history per signal)
                        │
                        ▼
                  Feature Engine  (windows: 1m / 5m / 15m / 30m / full-run
                                   → mean, std, trend, rate-of-change)
                        │
                        ▼
   ┌────────────────────┼───────────────────────────────────────┐
   ▼                    ▼                                       ▼
Process State     Early Anomaly Detection             Specific Risk Detections
(+ low-prod       (state-aware baselines,             (Material Behavior,
 cause/severity)   doser drift)                        Granulator/Knife,
   │                    │                              Nozzle/Screen, Predictive Quality)
   └────────────────────┴───────────────────┬─────────────────┘
                                            ▼
                              Predictions + Prioritized Warnings (stored)
                                            ▼
                              Dashboard + Notifications (incl. mobile)

        Correlation & Learning Layer  ◄── joins each run's signals/predictions with
                                          later quality + maintenance events
                                          (data grows over time from live capture)
```

# 6. Was bereits umgesetzt ist
Das folgende Fundament ist aufgebaut und in Betrieb. Es ist die Grundlage für jede in Abschnitt 7 beschriebene Erkennungsfähigkeit. Durch die Markierung dieses Abschnitts wird ausdrücklich eine Verwechslung zwischen „geplant“ und „bereits geliefert“ vermieden.

## 6.1 Einnahme (FERTIG)
Ein periodischer Poller liest den neuesten Snapshot aller Line E10 WinCC-Werte aus dem Backend. Das Abfrageintervall ist konfigurierbar. Der aktuelle Standardwert ist alle 10 Sekunden. Der Poller ist asynchron, Timeout-geschützt und stürzt den Dienst nie ab, wenn das Backend vorübergehend nicht erreichbar ist – er überspringt einfach das Häkchen und versucht es erneut. Jede erfolgreiche Abfrage erhöht einen Zähler, der für Integritätsprüfungen verfügbar gemacht wird.

## 6.2 Datenbereinigung (FERTIG)
Jeder vom Backend empfangene Wert durchläuft den Cleaner, bevor er in den Puffer gelangt. Der Reiniger macht drei Dinge:
1. **Validierung:** prüft, ob der Wert einen numerischen Typ hat, nicht null ist und einen plausiblen Zeitstempel hat.
1. **Deduplizierung:** Wenn sich ein Wert mit demselben Zeitstempel für dasselbe Signal bereits im Puffer befindet, wird die neue Kopie verworfen.
1. **Qualitätskennzeichnung:** Jeder Wert ist mit einem von fünf Zuständen gekennzeichnet:
- GUT – Normalwert innerhalb der erwarteten Grenzen.
- STALE – Der Wert hat sich länger als der konfigurierte Schwellenwert für „festsitzender Sensor“ nicht geändert (derzeit 30 identische Abtastwerte hintereinander für nicht ausgenommene Signale).
- OUT_OF_RANGE – Wert liegt außerhalb der für seine (Gruppen-, Rollen-)Kombination definierten Grenzen (z. B. eine Temperatur außerhalb von 0–350 °C).
- SCHLECHT – wird von der Quelle als fehlerhaft gekennzeichnet oder besteht eine strenge Gültigkeitsprüfung nicht.
- FEHLT – in diesem Schnappschuss erwartet, aber nicht vorhanden.
Grenzen werden nach **Signalrolle und -gruppe** (Istwert, Sollwert, Steuerausgang, Fehlercode, Modus, Status) gesucht, was bedeutet, dass negative Steuerausgangswerte (ein normaler PID-Heizungsbefehl) nicht als fehlerhaft gekennzeichnet werden. Unbekannte Rollen-/Gruppenkombinationen werden als GUT durchgereicht und nicht fälschlicherweise abgelehnt. Dieses Design bedeutet, dass das Hinzufügen eines neuen Signals niemals zu Fehlalarmen führt.
Nachgeschaltete Funktionen unterscheiden zwischen „schlechter Qualität“ und „schwerem Fehler“ (nur OUT_OF_RANGE oder BAD), sodass ein festsitzender oder fehlender Sensor niemals eine falsche Fehlerphase auslöst.

## 6.3 Rollfensterpuffer (FERTIG)
Ein In-Memory-Puffer speichert den aktuellen Verlauf jedes Signals (bis zu ~8 Stunden). Neue Werte werden angehängt und die ältesten werden gelöscht, sobald der Puffer voll ist. Der Puffer ist die Quelle für alle Feature-Berechnungen. Da es sich im Speicher befindet, erfolgt die Feature-Berechnung sofort und berührt nie die Datenbank.

## 6.4 Feature Engine (FERTIG)
Bei jedem Tick berechnet die Feature-Engine einen **Feature-Vektor pro Fähigkeit** aus dem aktuellen Pufferinhalt. Für jedes Signal wird das Ende des Puffers in fünf parallele Fenster unterteilt:
- **1 Minute** – sehr kurz, empfindlich gegenüber Spitzen.
- **5 Minuten** – das primäre Fenster für den Prozessstatus; gleicht Reaktionsfähigkeit und Stabilität aus.
- **15 Minuten** – erfasst langsame Trends.
- **30 Minuten** – unterstützt die Erkennung langsamer Abnutzung (Siebverstopfung, Messerverschleiß).
- **Vollständiger Lauf** – alles, was der Puffer enthält, für Kontext auf Run-Ebene.
Für jedes Fenster werden Folgendes berechnet: **Mittelwert, Standardabweichung, linearer Trend (Regressionssteigung), Änderungsrate, Minimum, Maximum und letzter Wert**. Die Werte werden dann pro Gruppe aggregiert (Mittelwert der Mittelwerte, Mittelwert der letzten Werte, Mittelwert der Trends, Mittelwert der Standardabweichungen, Verhältnis schlechter Qualität pro Gruppe, Verhältnis schwerer Fehler pro Gruppe), sodass Regel-Engines auf der Ebene eines Maschinenbereichs und nicht auf der Ebene einzelner Tags schlussfolgern können.
Ein Fenster gilt nur dann als „bereit“ für ein Signal, wenn genügend Proben gesammelt wurden; Ein ganzer Vektor ist nur dann „bereit“, wenn das primäre Fenster für genügend Signale bereit ist. Dies verhindert, dass beim Start Vorhersagen über unvollständige Daten getroffen werden.

## 6.5 Unterstützende Mechanik bereits vorhanden
- **Signalkataloggesteuertes Routing.** Signale gehören zu einer Gruppe im Backend-Katalog; Durch das Hinzufügen eines Signals zu einer Gruppe wird es automatisch an alle Funktionen weitergeleitet, die diese Gruppe nutzen. Nirgendwo sind Tag-Namen fest codiert.
- **Vorhersagespeicherung mit Rückverfolgbarkeit im Eingabefenster.** Jede gespeicherte Vorhersage zeichnet das genaue Zeitfenster der Daten auf, auf denen sie basiert, sowie eine Klartexterklärung der Regel/Heuristik, die sie erstellt hat. Dies macht jede Warnung vertretbar, wenn sie von einem Bediener befragt wird.
- **In der SUNPOR AI-Anwendung gibt es erste Bedienereingabeformulare** – Produktionsstart, Extruder-Ereignisse, Granulator-Ereignisse, Reinigung, Störungen, Materialverhalten, Materialblockierung, tägliche Qualität. Die UI-Tests sind noch im Gange.
- **Die Prozesszustands-Erkennung läuft bereits in einer ersten Form.** Die Phase **Stabile Produktion** wird anhand realer Daten der Linie E10 kalibriert. Für die verbleibenden acht Phasen sind noch vom Kunden bereitgestellte Definitionen und live erfasste Beispiele erforderlich, bevor sie als kalibriert markiert werden können (Abschnitt 7.1).
Alles ab Abschnitt 7 baut **auf** diesem Fundament auf.

# 7. Erkennungsfähigkeiten (Entwicklungspfad)
Die Build-Reihenfolge richtet sich nach der technischen Abhängigkeit. **Der Prozessstatus wird zuerst erstellt**, da jede andere Funktion die Produktionsphase kennen muss – ein Signal, das in einer Phase normal ist (z. B. niedriger Schmelzedruck während eines Leerlaufs), ist in einer anderen Phase (während einer stabilen Produktion) ein ernstes Problem. Ohne Process State würde jede Risikofunktion beim Anfahren, Reinigen und Leerlauf ständig Fehlalarme erzeugen.
Jede der folgenden Funktionen wird in der gleichen Struktur beschrieben: Kundenbedarf, was sie erkennt, Eingaben, wie wir sie entwickeln, Abhängigkeiten, offene Punkte.

## 7.1 Prozesszustands-Erkennung (Grundlage)
**Kundenbedarf.** SUNPOR benötigt das System, um jederzeit zu wissen, **was die Linie tut**. Dies ist der wichtigste Kontext im gesamten System: Jede Warnung, jedes Qualitätsrisiko, jeder Wartungshinweis hängt davon ab. Ein Druckabfall während einer Leerfahrt ist zu erwarten und sollte geräuschlos sein; Der gleiche Druckabfall während einer stabilen Produktion ist ein alarmierendes Ereignis. Ohne den Phasenkontext würde jede Fähigkeit Fehlalarme erzeugen.
**Was es erkennt.** Die aktuelle Produktionsphase, ausgewählt aus:
- **Aufheizen** – die Leitung erreicht die Temperatur; Extruder läuft noch nicht oder ist sehr langsam; Heizzonen im Aufwärtstrend; Feeder stehen still; der Schmelzedruck ist niedrig; Das Produktionsstatusflag ist 0.
- **Startup** – Aufheizen ist abgeschlossen; die Extruderschnecke läuft hoch; Die Futterautomaten beginnen zu dosieren; Der Durchsatz steigt in Richtung des Sollwerts. Der Schmelzedruck baut sich auf.
- **Stabile Produktion** – der Referenzzustand für jede Qualitäts-/Risikofähigkeit. Der Durchsatz ist auf dem Sollwert, das Statusflag ist 1, die Drücke liegen innerhalb ihres normalen Bereichs, die Erwärmungsvarianz ist gering, der Granulator läuft.
- **Geringe Produktion** – Der Durchsatz liegt deutlich unter dem Sollwert, während sich die Linie noch im Produktionszustand befindet (kein Start, kein Leerlauf). Siehe Unteranalyse unten.
- **Reinigungslauf** – Reinigungszyklus läuft; Normalerweise ist das Wassersystem eingeschaltet, die Futterspender sind ausgeschaltet und der Status ist 0.
- **Leerlauf** – der Extruder läuft, aber es wird kein Material zugeführt; Druck ist niedrig, Feeder im Leerlauf, Status ist 0. Dies ist ein legitimer, geplanter Zustand, der keine Alarme auslösen darf.
- **Abkühlung** – die Temperaturen tendieren nach unten; Feeder und Extruder werden gestoppt.
- **Herunterfahren** – die Leitung ist in Ruhe; Die Temperaturen sind niedrig, alles ist nahe Null.
- **Fehler** – das Muster weist auf eine tatsächliche Störung hin: Das Signalverhältnis bei einem schweren Fehler ist hoch oder die Drücke weisen extreme Schwankungen auf, die nicht mit dem normalen Betrieb vereinbar sind.
Jede Erkennung gibt einen Phasennamen, einen Konfidenzwert (Bruchteil der Regelbedingungen der Phase, die erfüllt wurden), ob es sich um eine „kalibrierte“ Phase (heute nur stabile Produktion) oder eine „geschätzte“ Phase handelt, sowie eine für Menschen lesbare Erklärung zurück.
**Eingaben.** Ist- und Soll-Gesamtdurchsatz, Geschwindigkeit und Drehmoment der Extruderschnecke, Schmelzedruck und -temperatur, Mittelwerte und Abweichungen der Heizzone, Geschwindigkeit und Drehmoment der Schmelzepumpe, Betriebsmodi der Zuführung, Materialproduktionsstatusflag sowie (von der Feature-Engine) Trend- und Standardabweichungswerte, die beschreiben, wie sich diese über das primäre 5-Minuten-Fenster ändern.
**Wie wir es entwickeln.** Eine konfigurierbare Regel-Engine sitzt auf der Feature-Engine. Regeln für jede Phase befinden sich in einer YAML-Konfigurationsdatei (rules_config.yaml). Jede Regel gibt eine Reihe von Bedingungen für Features auf Gruppenebene an (z. B. Feeders.mean_of_lasts >= 300, Melt_Pressure.Mean_of_Lasts >= 80, Heating_zones.Mean_of_Stds < 5) mit einem Operator (>=, <, ==, ...) und einem Schwellenwert. Eine Phase stimmt überein, wenn ein konfigurierbarer Bruchteil ihrer Bedingungen erfüllt ist (z. B. 70 %). Phasen haben Prioritäten, so dass in unklaren Situationen die sicherere/spezifischere Phase gewinnt (Fehler haben immer Vorrang vor allem, stabile Produktion hat Vorrang vor Anlauf, sodass echte stabile Daten niemals als Anlauf missverstanden werden).
Der Arbeitsablauf zum Kalibrieren der verbleibenden Phasen ist:
1. Der Kunde beantwortet die Fragen zur Phasendefinition (Abschnitt 13).
1. Das System läuft live und zeichnet Kandidatenphasen auf.
1. Bediener bestätigen oder korrigieren die gekennzeichnete Phase im Dashboard.
1. Das Team passt die YAML-Schwellenwerte an, damit die Regeln dem beobachteten Verhalten entsprechen.
1. Die Phase wird im Kalibrierungsstatusblock als kalibriert markiert.
**Abhängigkeiten.** Live-Aufnahme und Feature-Engine (beide bereits in Abschnitt 6 implementiert).
**Offene Posten (Mandant).**
- Die Bediener-/Etage-Definition jeder Phase (welche Signale sagen einem Bediener „Dies ist Anlauf“ oder „Dies ist eine stabile Produktion“?).
- Die Bedeutung des Materialproduktionsstatus = 1 in jeder Phase. Steht das Flag nur bei stabiler Produktion auf 1, oder ist es auch beim Hochfahren, Leerlauf, Reinigen 1?
- Die Bedeutung der Feeder-Betriebsmodi (GD, VR, VS, LF, EF und alle anderen tatsächlich auf E10 verwendeten Codes). Diese Modi sind mit ziemlicher Sicherheit die schnellste Möglichkeit, Phasen auf Feeder-Ebene zu unterscheiden.
- Datums-/Uhrzeitbeispiele für jede instabile Phase, die während des Live-Betriebs erfasst wurden. Da es keinen historischen Datensatz gibt, werden diese Beispiele in Echtzeit erfasst. Der Bediener markiert „wir befinden uns jetzt in [Phase], weil [Grund]“ und das System speichert dies als gekennzeichnetes Beispiel.
### Unteranalyse – Ursache und Schweregrad der geringen Produktion
**Was es hinzufügt.** Wenn der Prozessstatus „geringe Produktion“ anzeigt, liefert diese Unteranalyse zusätzliche Details: wie weit unter dem Sollwert die Linie liegt (Schweregrad), wie lange sie schon niedrig war (Dauer) und die wahrscheinlichste Ursache unter:
- Übergang zum Starten oder Herunterfahren (die Phasen-Engine wurde noch nicht umgedreht).
- Feeder-Fehler (ein oder mehrere Feeder zeigen eine Warnung oder einen Ausschussalarm an).
- Materialproblem (ein Materialverhaltensereignis wurde kurz davor oder währenddessen protokolliert).
- Druck- oder Prozessinstabilität (Extruder-/Schmelzpumpendrehmoment oder Druckschwankung ist hoch).
- Sieb- oder Düsenverstopfung (Differenzdruck über dem Sieb steigt).
- Geplante Verlangsamung (ein Bediener hat ein Ereignis mit niedriger Produktion eingegeben, das als „geplant“ markiert ist).
- Rezept- oder Materialänderung (Produktionsstart oder Materialänderungsereignis wurde protokolliert).
**Eingaben.** Ist-Gesamtdurchsatz im Vergleich zum Sollwert, Ist-Wert pro Feeder im Vergleich zum Sollwert, Feeder-Betriebsmodi, Feeder-Fehlercodes und das neue Bedienerereignis „Geringe Produktion“ mit seinem Dropdown-Menü „Ursache“ und dem Flag „Geplant/ungeplant“.
**Wie wir es entwickeln.** Da Process State die Phase bereits erkennt, handelt es sich hierbei um eine einfache Regel/Heuristik zusätzlich zur Process State-Ausgabe – es handelt sich bewusst **kein** separates ML-Modell. Geplante Verlangsamungen (vom Bediener eingegeben) werden von tatsächlichen Problemen getrennt, sodass sie niemals eine „Problem“-Warnung auslösen. Der Schweregrad wird als 1 berechnet – Istwert/Sollwert auf [0, 1] begrenzt; Die Dauer ist ein einfacher laufender Zähler aufeinanderfolgender Ticks, wobei Phase = niedrige Produktion.
**Offene Posten (Mandant).**
- Wie viel Prozent unter dem Sollwert und wie lange gilt als „geringe Produktion“? Zählt ein 5-minütiger Rückgang oder nur ein anhaltender 15-minütiger Rückgang?
- Sollte der Vergleich mit dem **Gesamtdurchsatz-Sollwert** oder mit dem Istwert pro Zuführung gegenüber dem Sollwert (oder beiden) erfolgen?
- Wie erfassen Betreiber aktuell geplante Abschwächungen? Sollte das Formular mit geringer Produktion standardmäßig auf „geplant“ eingestellt sein, wenn der Schichtleiter es initiiert?
- Wie hängt ein **Dosierungsausschussalarm** (kritische EPS-/Pentan-/Stickstoffdosierung) mit einer geringen Produktion zusammen? Wird es als geringe Produktion, als Fehler oder als eigene Kategorie eingestuft?

## 7.2 Frühe Anomalie-Erkennung (Phase-1-Priorität)
**Kundenbedürfnis.** Dies ist der einzige **am meisten hervorgehobene** Schmerzpunkt in jedem Gespräch mit dem Kunden. Die Dosiereinheiten beginnen sich ungewöhnlich zu verhalten, Minuten bevor der Extruder die Wirkung zeigt, und heute werden diese ersten Anzeichen übersehen. Das System muss abnormales Verhalten des Dosierers an der Quelle erkennen – auch wenn keine explizite Regel existiert – damit Bediener reagieren können, bevor es zu einem tatsächlichen Fehler oder Ausschuss kommt.
**Was es erkennt.** Anomaliebewertungen pro Gruppe plus spezifische Frühdrift-Flags wie:
- Dosierereinspeise-/Förderzeit steigt über eine Schicht hinweg schleichend an.
- Ungewöhnliches Vibrationsmuster an einem bestimmten Dosierer.
- Instabile Dosierung (Sollwert-Ist-Abweichung nimmt zu oder das Soll-Ist-Delta wird variabler als üblich).
- Das Drehmoment des Extruders steigt relativ zu seiner Grundlinie für die aktuelle Phase an.
- Die Standardabweichung des Schmelzedrucks steigt über die Phasennorm hinaus.
- Jede Signalgruppe, die erheblich von der Grundlinie abweicht, „wie sich diese Gruppe während einer stabilen Produktion auf dieser Linie verhält“.
Zu jeder Flagge gehört eine Bewertung, eine Gruppe, eine „Frühwarnung“-Kennzeichnung und eine Erklärung im Klartext, was sich geändert hat.
**Eingänge.** Alle Funktionen des Signalgruppenfensters. Die 15-Minuten- und 30-Minuten-Fenster sind die primären Eingaben (sie erkennen die langsame Abweichung; das 1-Minuten-Fenster erfasst plötzliche Spitzen). Vorrangige Signale sofern vorhanden: Dosierervibration, Einspeise-/Förderzeiten, Dosierabweichungen (alle in Abschnitt 4.1 als „zu ergänzen“ aufgeführt).
**Wie wir es entwickeln.** In zwei Phasen:
1. **Statistische Basislinien pro Phase.** Für jede Signalgruppe und jede Phase berechnen wir eine rollierende Basislinie (einen robusten Mittelwert und eine robuste Streuung) aus Live-Stallproduktionsdaten. Dann löst jede Gruppe, deren aktuelle Werte zu weit von dieser Basislinie abweichen (gemessen anhand eines robusten Z-Scores oder eines multivariaten Scores im Isolation-Forest-Stil für Gruppen mit vielen Signalen), eine Anomalie aus. Baselines sind **phasenspezifisch**: Was beim Start normal ist, ist während der stabilen Produktion nicht normal und umgekehrt. Aus diesem Grund ist Process State (7.1) eine harte Abhängigkeit.
1. **Signalspezifische Driftdetektoren** für die Prioritätssignale des Kunden (Einspeisezeit, Vibration). Diese verwenden Vergleiche zwischen kurzen und langen Fenstern, um schleichende Änderungen lange vor einem Schwellenwertalarm zu kennzeichnen.
Die Grundlinie verbessert sich, je länger das System läuft. Am ersten Tag, mit spärlichen Basisdaten, traten nur klare Anomalien auf; Je mehr stabile Produktionsstunden sich ansammeln, desto schärfer wird die Basislinie und subtilere Abweichungen werden erfasst.
**Abhängigkeiten.** Prozessstatus (für phasenbewusste Baselines); die zusätzlichen Dosierersignale für den vollen Wert (ohne sie können wir bereits Anomalien an den vorhandenen Signalen erkennen, aber die Qualität der „Frühwarnung“ ist bei Vibrations- und Zeitdaten viel stärker).
**Offene Posten (Mandant).**
- Verfügbarkeit und Integrationspfad für die Vibrations- und Einspeise-/Förderzeitsignale des Dosierers.
- Bei welchen Dosierern kommt es nach Erfahrung des Kunden am häufigsten zu diesen frühen Abweichungen? (Die Rangfolge hilft uns dabei, die Benachrichtigungspriorität zu optimieren.)

## 7.3 Wesentliches Verhaltensrisiko
**Kundenbedarf.** Prognostizieren Sie frühzeitig auftretende **Materialprobleme** – Probleme, die eher auf die Dosierung oder die Materialzusammensetzung als auf mechanischen Verschleiß zurückzuführen sind. Dies sind die Probleme, die der Bediener am Boden bemerkt, wenn „das Material sich heute seltsam verhält“: Klumpen, Doppelperlen, Schaumprobleme, Abweichung der Siebtoleranz.
**Was es erkennt.** Risiko pro Problemtyp:
- **Klumpenbildung** – sichtbare Klumpen im Produkt.
- **Zwillingsperlen** – paarweise zusammengeklebte Perlen.
- **Material außerhalb der Siebtoleranz** – Kornverteilung weicht außerhalb der Spezifikation.
- **Zu wenig Pentan** – unzureichendes Schaummittel.
- **Zu viel Pentan** – zu viel Pentan, beeinflusst die Dichte.
- **Schlechtes Schaumverhalten** – Perlen schäumen bei der späteren Verarbeitung nicht richtig auf.
Bei jedem Risiko handelt es sich um eine Bewertung mit einer zugehörigen Ursachenhypothese (welche Signale oder Feederabweichungen es ausgelöst haben) und einer Erklärung im Klartext.
**Eingaben.** Temperatur- und Druckprofile (Mittelwert, Standard, Trend über Heizzonen und Schmelzdrücke), Durchsatz, Zufuhranteile (EPS / Graphit / recycelt / außerhalb der Spezifikation), Pentan- und Stickstoffflüsse, Prozesswassertemperatur und -fluss (im Zusammenhang mit Klumpenbildung und Doppelperlen laut Fragebogen), Granulatorverhalten, aktueller Materialtyp ab Produktionsstart, aktuelle Phase ab Prozessstatus. Bedienereinträge aus dem Formular „Materialverhalten“ enthalten Bezeichnungen (welches Problem beobachtet wurde) und Schweregrad (1–5).
**Wie wir es entwickeln.** In Etappen:
1. **Day-One-Regel-/heuristische Prüfungen**, die direkt aus den Fragebogenantworten des Kunden abgeleitet werden. Zum Beispiel: tatsächliche Abweichung von Pentan im Verhältnis zum erwarteten Verhältnis → Schaumrisiko; Prozesswassertemperatur nähert sich der Gefahrenschwelle von 65 °C → Klumpen-/Doppelperlengefahr; Graphitanteil führt zu Drehmomentschwankungen → extruderbedingtes Materialrisiko. Diese Regeln nutzen das Wissen der Clientdomäne als Ausgangspunkt, sodass das System vom ersten Tag an nützliche Ergebnisse liefert, auch ohne erfasste Daten.
1. **Progressives Lernen aus Bedienerkennzeichnungen.** Während Bediener Materialverhaltensereignisse während einer stabilen Produktion protokollieren, verknüpft die Korrelationsschicht diese Ereignisse mit den Signalmustern der vorangegangenen Minuten. Mit der Zeit lernt das System die spezifischen Muster, die jedem Problemtyp in Zeile E10 (nicht in generischen EPS-Zeilen) vorausgehen, und verfeinert die Regeln oder wechselt zu einem ML-Klassifikator.
**Abhängigkeiten.** Prozessstatus (nur bei stabiler Produktion sinnvoll); Protokollierung des Bedienerverhaltens (Kennzeichnungen zum Lernen); die Ursachenkenntnis des Auftraggebers (§ 13).
**Offene Posten (Mandant).**
- Die Ursachen pro Problem – die Antworten auf den Fragebogen decken das meiste davon ab, wir benötigen jedoch eine Bestätigung der Rangfolge der „wahrscheinlichsten Ursachen“ pro Problem speziell für Zeile E10.
- Welche Dosierer sind kritisch (EPS / Pentan / Stickstoff → Schrott) im Vergleich zu nur mit Warnung (Graphit / 600 / außerhalb der Spezifikation / recycelt → Warnung).
- Historische Erfahrung: Materialmischungen, die in der Vergangenheit zu Kundenbeschwerden geführt haben (ungefähr, kein Rezept).

## 7.4 Vorhersagequalität
**Kundenbedarf.** Dies ist die ehrgeizigste Funktion: Vorhersage der späteren (Labor-)Qualität **während** der Produktion, Tage bevor das Laborergebnis eintrifft. Es löst Problem 2.2 (verzögerte Qualitätsbewertung) direkt. Wenn das System einen Lauf als „hohes Risiko für offene Löcher“ oder „hohes Risiko für Schaumbildung NOK“ markieren kann, während der Lauf noch läuft, können Bediener eingreifen, den Lauf anpassen oder stoppen – und so Material sparen, das sonst zu Ausschuss werden und erst nach dem Verpacken aufgefangen werden würde.
**Was es erkennt.** Qualitätsrisiko **pro Lauf** für:
- **Offene Löcher** – prozentuales Risiko, dass die tägliche Qualitätsmessung schlecht ausfällt.
- **Siebverteilung** – Risiko, dass die Siebanalyse außerhalb der Toleranz liegt.
- **Schaumbildung OK/NOK** – es besteht die Gefahr, dass Schaumbildung als „Nicht OK“ eingestuft wird.
- **Probleme mit der Zellstruktur** – Risiko einer schlechten Zellstruktur (Feuchtigkeit des Rohmaterials, Stickstoffdosierung, gemäß Fragebogen).
- **Erhebliches Blockierungsrisiko** – Wahrscheinlichkeit, dass der Lauf später rückwirkend blockiert wird.
Bei jedem Risiko handelt es sich um einen Prozentsatz mit einem Treiber (welche Signale/Ereignisse das Risiko erhöht haben) und einer Erklärung.
**Eingänge.** Der vollständige Satz stabiler Phasensignale – Schmelzedruck, Abweichungszähler, Granulatorverhalten, Pentan/Stickstoff, Zufuhrverhalten, Prozesswasser, Sieb-/Düsentemperaturen – sowie alle während des Laufs protokollierten Wartungsereignisse sowie alle Materialverhaltensereignisse. Die **Ziele** (was das System vorhersagen soll) stammen künftig aus der Live-Erfassung: **Tagesqualitätsformulare**, **Materialblockierungsformulare** und **Bewertungen der Qualitätsabteilung**, sobald sie nach dem Lauf eintreffen.
**Wie wir es entwickeln.** In zwei Phasen:
1. **Regelbasierte Risikobewertungen vom ersten Tag an.** Schon vor jedem ML-Training können wir durch Summieren von Beweisen eine nützliche Risikobewertung erstellen: Wenn Pentan von seinem normalen Verhältnis abweicht, steigt das Schaumrisiko; Wenn die Werte für grobe/feine Abweichungen außerhalb der Spezifikation bei stabiler Produktion schnell ansteigen, steigt das Siebrisiko. Wenn die Temperaturen der Düsenplatte instabil sind, steigt das Risiko offener Löcher. Wenn für den Lauf ein Materialverhaltensereignis protokolliert wurde, steigen alle mit diesem Ereignis verbundenen Risiken. Dadurch erhält der Betreiber vom ersten Tag an ein Live-Risikobild.
1. Die **ML-basierte Vorhersage** setzt ein, sobald die Korrelations- und Lernschicht (Abschnitt 10) genügend Durchläufe mit Ergebnissen gesammelt hat. Für jeden Lauf haben wir ein beschriftetes Beispiel: (Signalstatistik + Ereignisse während des Laufs) → (späteres Qualitätsergebnis). Überwachtes Standardlernen (gradientenverstärkte Bäume/logistische Regression als Basislinien; komplexere Modelle mit zunehmender Datenmenge) erzeugt dann eine Wahrscheinlichkeit pro Qualitätsergebnis. Das System vergleicht den aktuellen Lauf mit historischen **„guten“ Läufen** für denselben Materialtyp und markiert Abweichungen.
Da der Kunde über keinen historischen Datensatz verfügt, beginnen ML-Vorhersagen nur für die Qualitätsergebnisse, von denen wir zunächst viele gekennzeichnete Beispiele erhalten (wahrscheinlich tägliche Qualität – ein Eintrag pro Schicht). Langsamer eintretende Ergebnisse (Materialblockierung) brauchen länger, um sich anzusammeln, versorgen aber letztendlich dieselbe Schicht.
**Abhängigkeiten.** Prozessstatus (nur stabile Produktion wird für das Training verwendet), Materialverhalten (seine Vorhersagen und Bedienerbezeichnungen sind Eingaben), Düse/Sieb und Granulator (ihre Risiken tragen dazu bei), die Korrelations- und Lernschicht und genügend live erfasste Läufe mit Ergebnissen.
**Offene Posten (Mandant).**
- Wie, wann und von wem werden offene Löcher, Siebe und Schaum gemessen? Was sind die „OK“-Schwellenwerte – gibt es einen numerischen Grenzwert für offene Löcher in % oder handelt es sich um eine Beurteilung?
- Wie schnell nach der Produktion wird ein Lauf normalerweise blockiert, und wer leitet die Blockierung ein?
- Als Ursache für Zellstrukturprobleme wird im Fragebogen Rohstofffeuchtigkeit genannt. Wird es heute irgendwo aufgezeichnet, oder sollten wir es als Bedienerfeld beim Produktionsstart hinzufügen?

## 7.5 Granulator-/Messerverschleiß
**Kundenbedarf.** Sagen Sie voraus, wann ein Messer gewechselt oder geschärft werden muss, und erkennen Sie Probleme bei der Kornverteilung, bevor sie als Ausschuss auftauchen. Heute entscheidet der Kunde über die Messerpflege anhand des Schnittmusters (visuell) und der Doppelraupen in der Siebanalyse. Dem sollte das System zuvorkommen.
**Was es erkennt.**
- **Messerzustand** – normal oder kurz vor der Wartung, mit einem Hinweis auf die geschätzte „verbleibende Lebensdauer“.
- **Kornverteilungsrisiko** – Wahrscheinlichkeit, dass der aktuelle Lauf aus der Siebtoleranz abdriftet.
- **Wartungsempfehlung** – ein spezifischer Hinweis wie „Messerschärfen innerhalb der nächsten 4 Stunden planen“ oder „Messerwechsel vor dem nächsten Materialwechsel empfohlen“.
**Eingaben.** Soll-/Ist-Geschwindigkeit des Granulators, Drehmoment des Granulators, Messerposition, Soll-/Istwert der hydraulischen Kontaktkraft, Prozesswasser (Kühlung beeinflusst die Schnittqualität), grobe und feine Zähler außerhalb der Spezifikation. Sobald verfügbar: Vibration des Granulators. Aus Formen: Messerwechsel und Messerschleifveranstaltungen; Twin-Bead-Beobachtungen; Sieb % aus Tagesqualität.
**Wie wir es entwickeln.** Verfolgen Sie Drehmoment- und Kontaktkrafttrends zwischen protokollierten Messerereignissen. Wenn ein Messerwechsel stattfindet, wird die „Uhr“ zurückgesetzt – die Signalstatistik direkt vor dem Wechsel wird zu einem Trainingsbeispiel für „ein Messer, das gewartet werden muss“ und die Statistik direkt danach wird zu einem Beispiel für „ein frisches Messer“. Über viele Messerereignisse lernt das System das Driftmuster, das der Änderung vorausgeht. Abweichungen außerhalb der Spezifikation (steigende Sieb-Grob- oder Feinzähler) verstärken das Signal. Sieb % aus der Tagesqualitätsform gibt uns das Ergebnis, mit dem wir korrelieren können.
Da Messerereignisse (im Vergleich zu Signalen) relativ selten sind, dauert es länger, bis diese Funktion hochpräzise ist – sie liefert jedoch vom ersten Tag an nützliche trendbasierte Hinweise.
**Abhängigkeiten.** Prozessstatus (Messergesundheit nur bei stabiler Produktion beurteilen); Messerereignisprotokollierung in Zukunft.
**Offene Posten (Mandant).**
- Was ist nach Erfahrung des Bedieners der früheste konkrete Hinweis darauf, dass ein Messer gewechselt oder geschärft werden muss? (Im Fragebogen steht „keine typische Signaländerung“ – wir müssen dies jedoch anhand realer Daten überprüfen.)
- Typische Zeitspanne von „Schnittbild wird schlechter“ bis „Messerwechsel durchgeführt“?

## 7.6 Düse / Sieb / Druck
**Kundenbedarf.** Erkennen Sie Düsenverstopfungen, Siebverstopfungen und Druckprobleme frühzeitig, bevor sie einen Eingriff erzwingen oder die Qualität beeinträchtigen. Der primäre Indikator ist heute der Differenzdruck über dem Siebwechsler; Die Kundenantworten im Fragebogen deuten auch auf die Trends des Einlass-/Auslassdrucks und die Gleichmäßigkeit der Düsenplattentemperatur hin.
**Was es erkennt.** Ein Druckproblemrisiko ja/nein plus eine wahrscheinliche Ursache:
- **Siebverstopfung** – Der Schmelzedruck am Einlass minus Auslass am Siebwechsler steigt.
- **Düse verstopft** – Der Druck des Startventils steigt, die Düsenplattentemperaturen werden ungleichmäßig.
- **Verstopfung an anderer Stelle** – Drehmoment der Schmelzepumpe hoch, Drehmoment des Extruders hoch, allgemeines Druckungleichgewicht.
**Eingaben.** Schmelzedrücke 1–4, Siebwechsler-Einlass- und -Auslass-Schmelzedrücke, Startventildruck, Düsenplattentemperaturen (unter Berücksichtigung der Gleichmäßigkeit aller Düsenzonen), Schmelzetemperatur, Extruderdrehmoment, Schmelzepumpendrehmoment. Aus Formularen: Siebwechselereignisse, Düsenwechsel-/Spülungs-/Mahlereignisse, Offene Löcher % (Tagesqualität), Düsenverstopfungsfehler.
**Wie wir es entwickeln.** Regelbasiert vom ersten Tag an anhand der Fragebogenantworten:
- Der Trend des Differenzdrucks (Einlass − Auslass) steigt → Siebverstopfungsgefahr (kalibriert anhand der ΔP-Schwellenwerte des Kunden, sobald diese bereitgestellt wurden).
- Standardabweichung der Düsenplattentemperatur über die Zonen hinweg steigt → Risiko von Düsenungleichmäßigkeiten, korreliert mit dem Prozentsatz offener Löcher von der Tagesqualität.
- Der Druck des Startventils steigt → Gefahr einer Düsenverstopfung.
Während sich Bildschirm-/Düsenereignisse in Bedienerformularen häufen, lernt das System die spezifischen ΔP-Werte und Trendraten auf Linie E10, die tatsächlich einer erforderlichen Änderung vorausgingen, und verfeinert seine Regeln.
**Abhängigkeiten.** Prozessstatus (Bildschirm ΔP verhält sich beim Start anders als im stabilen Betrieb); Protokollierung von Bildschirm-/Düsenereignissen in Zukunft.
**Offene Posten (Mandant).**
- Differenzdruckschwellenwerte für „bald ändern“ vs. „jetzt ändern“ in bar.
- Symptome, auf die Bediener vor dem Düsenwechsel/-schleifen achten (im Fragebogen werden „Schlauchboot“-Formen, Klumpen, Siebabweichungen und offene Löcher erwähnt – wir müssen wissen, welches als Signal am zuverlässigsten ist).
- Welche Qualitätsmerkmale verschlechtern sich zuerst, wenn die Düse auszufallen beginnt?

## 7.7 Wartungsvorhersage und -priorisierung
**Kundenbedarf.** Wandeln Sie die rohen Risikoausgaben von Granulator/Messer, Düse/Sieb und Frühanomalie in eine **priorisierte** Liste mit Hinweisen für Bediener und Schichtleiter um. In einer Schicht passieren viele kleine Probleme gleichzeitig; Der Kunde möchte eine einzelne Rangfolgeansicht, die antwortet: „Was sollte ich mir zuerst ansehen?“.
**Was es erkennt.** Wartungsrisiko (Messer/Düse/Sieb) mit Dringlichkeitsstufe sowie einer Rangliste der derzeit kritischsten Entwicklungen in der gesamten Linie. Zu jedem Element gehören die Fähigkeit, die es hervorgebracht hat, die betroffene Gruppe, die Dringlichkeit, eine vorgeschlagene Aktion und ggf. eine voraussichtliche Ankunftszeit.
**Eingaben.** Ausgaben von Granulator/Messer (7.5), Düse/Sieb (7.6) und frühe Anomalie (7.2) sowie der live erfasste Wartungsereignisverlauf (um zu vermeiden, dass eine Aktion, die gerade ausgeführt wurde, wiederholt empfohlen wird).
**Wie wir es entwickeln.** Fassen Sie einzelne Risiken zu priorisierten Empfehlungen zusammen. Die Priorität ist eine Funktion der Dringlichkeit, des Schweregrads und der Zeit seit der letzten Aktion für diesen bestimmten Wartungstyp. Zeigen Sie die priorisierte Liste im Dashboard an und führen Sie Benachrichtigungen (in-App; mobilfähig) für die wichtigsten Elemente durch.
**Abhängigkeiten.** Granulator/Messer, Düse/Sieb, frühe Anomalie.
**Offene Posten (Mandant).**
- Bevorzugte Benachrichtigungskanäle (E-Mail, Mobile Push, SMS, nur In-App?) und Eskalationsregeln (Wer wird bei welcher Dringlichkeit benachrichtigt).

# 8. Vorhersageausgaben (gespeichert und angezeigt)
Jede Funktion schreibt ihre Ausgabe als ml_prediction in das Backend, mit einer konsistenten Form, damit das Dashboard sie einheitlich anzeigen kann. Für jede Vorhersage gespeicherte Regeln:
- Zeitstempel der Vorhersage.
- Anfang und Ende des Eingabefensters (reales Datenfenster, keine Rechenzeit).
- Modellname (z. B. process_state_rule_v1).
- Vorhersagetyp (aus der Tabelle unten).
- Vorhersagewert (Zahl oder Index).
- Vertrauen.
- Für Menschen lesbare Erklärung.
- Link zum Produktionslauf, zu dem es gehört.

| Ausgabetyp | Quellenfähigkeit | Bedeutung |
|---|---|---|
| Prozessstatus | Prozessstatus | Aktueller Phasenindex + Vertrauen |
| Low_Production_Detail | Prozessstatus (Unteranalyse) | Schweregrad (Anteil unter dem Sollwert), Dauer (Ticks), Ursachenbezeichnung |
| anomaly_score | Frühe Anomalie | Punktzahl pro Gruppe, plus Early-Drift-Flags |
| material_behavior_risk | Materialverhalten | Risikobewertung pro Problemtyp, mit den Fahrersignalen |
| qualitätsrisiko | Vorhersagequalität | Prognostiziertes Qualitätsrisiko pro Lauf und Ergebnistyp |
| granulator_risk | Granulator/Messer | Messerzustand, Kornrisiko, Wartungshinweis |
| Druck_Problem_Risiko | Düse/Sieb | Sieb-/Düsen-/Verstopfungsrisiko mit wahrscheinlicher Ursache |
| Wartungsrisiko | Priorisierung der Wartung | Bewertete Wartungsempfehlungen |

**Regel:** Qualitäts- und Wartungswarnungen gelten **nur während einer stabilen Produktion** – sie werden durch den Prozessstatus begrenzt. Während des Anfahrens, Leerlaufs, Reinigens, Kühlens oder Herunterfahrens werden diese Ausgaben auf dem Dashboard unterdrückt (sie können zu Lernzwecken weiterhin intern berechnet werden).

# 9. Betreiberformulare – Anforderungen
Die Bedienerformulare sind die menschliche Eingabeseite des Systems. Sie sind die Hauptquelle für **Bezeichnungen** für jede Lernfähigkeit und stellen den **Kontext** bereit, der Signaldaten in Echtzeit interpretierbar macht. Da die Mitarbeiter sie während einer Schicht unter Zeitdruck ausfüllen, müssen die Formulare schnell sein, die Sprache verwenden, die die Mitarbeiter tatsächlich verwenden, und nach Möglichkeit Dropdown-Listen anstelle von Freitext enthalten.
Alle Dropdown-Werte werden im Backend gespeichert und können **jederzeit bearbeitet werden**, ohne die Anwendung erneut bereitzustellen – dadurch wird die Frage des Kunden direkt in der Antwort-E-Mail beantwortet.

| Bilden | Schlüsselfelder | Füttert welche Fähigkeit |
|---|---|---|
| Produktionsstart | Materialtyp, Versuch (ja/nein), Schicht, Startzeit, Kommentar | Kontext für jede Fähigkeit (alle Ausgaben sind damit versehen) |
| Extruder-Events | Ebene 2 (Phase oder Wartungskategorie), Ebene 3 (spezifisches Ereignis), Grund, Zeit, Kommentar | Prozessstatus (Phasenbezeichnungen), Düse/Bildschirm (Bildschirm- und Düsenereignisse) |
| Granulator-Events | Level 2 = Messer, Level 3 = Messerwechsel / Messerschärfen, Grund, Zeit | Granulator/Messer |
| Reinigung | Stufe 2 (Wasserbad / Zentrifuge / allgemeine Reinigungsarbeiten), Grund, Zeit | Prozessstatus (Reinigungsphasenbezeichnung) |
| Fehler | Ebene 2 (mechanisch/elektrisch), Ebene 3 (spezifischer Untertyp), Textfeld, Zeit | Prozessstatus (Fehlerphase), Düse/Sieb (Düsenverstopfungsfehler) |
| Materialverhalten | Dropdown-Liste „Verhaltenstyp“ (6 Optionen aus Abschnitt 4.2), Schweregrad 1–5, Zeit, Kommentar | Materialverhalten (Bezeichnungen + Schweregrad) |
| Materialblockierung | Grund-Dropdown (aus Abschnitt 4.2), von Zeit zu Zeit, betroffenes Material, Kommentar | Vorhersagequalität (grundlegende Wahrheit für eine schlechte Charge) |
| Tägliche Qualität | Verschiebung, Eingabezeit, offene Löcher %, Siebverteilung %, Schaumverhalten (OK / Nicht OK), Kommentar | Vorhersagequalität (Etiketten), Granulator (Sieb %), Düse/Sieb (offene Löcher %) |
| Geringe Produktion (neu) | Ursachen-Dropdown, geplante/ungeplante Markierung, Start-/Endzeit, Kommentar | Prozessstatus (Unteranalyse) |

**Zu implementierende Formularanforderungen:**
1. **Fehlerformular:** Ebene 3 muss dynamisch basierend auf Ebene 2 umschalten. Derzeit zeigt das Formular nur mechanische Optionen der Ebene 3 an – die elektrische Option (Stromausfall) ist nicht auswählbar, wenn Ebene 2 = Elektrisch. Dies muss behoben werden.
1. **Formular für Extruderereignisse:** Ebene 2 → Ebene 3 muss kaskadiert werden, um ungültige Kombinationen zu verhindern (derzeit werden alle Optionen der Ebene 3 unabhängig von Ebene 2 angezeigt, sodass ein Bediener eine Düsenunteraktion unter einer Heizebene 2 auswählen kann, was bedeutungslos ist).
1. **Eintrag „Geringe Produktion“:** Fügen Sie im Extruder-Ereignisformular eine neue Ebene 2 = „Geringe Produktion“ mit einem Ursachen-Dropdown (siehe Liste in 7.1-Unteranalyse) und einer Markierung „Geplant/ungeplant“ hinzu.
1. **Tägliche Qualität:** Bestätigen Sie mit dem Kunden, ob die Eintrittshäufigkeit pro Schicht gilt (durch das Schichtfeld impliziert) und ob eine Schicht mehrere Einträge oder einen zusammenfassenden Eintrag haben kann.
Operatoren sind die **primäre Quelle von Beschriftungen** für jede Lernfähigkeit, daher sind diese Formulare nicht optional – sie sind eine harte Abhängigkeit, damit Materialverhalten, Granulator/Messer, Düse/Sieb und Vorhersagequalität nützlich werden.

# 10. Korrelations- und Lernebene
Da das Projekt mit **keinen historischen Datensatz** beginnt, ist diese Ebene unerlässlich. Es sammelt einen gekennzeichneten Datensatz vollständig aus dem Live-Betrieb und ermöglicht es, die Vorhersagequalität und alle „Risiko“-Fähigkeiten im Laufe der Zeit von regelbasiert zu ML-basiert zu verbessern.
Die Schicht arbeitet laufweise. Ein **Produktionslauf** wird erstellt, wenn der Bediener den Produktionsstart übermittelt; Es ist der Kontextcontainer für alles, was passiert, bis die Ausführung gestoppt wird. Während des Laufs:
1. Das System speichert **alle aufgenommenen Signale** und ihre berechneten Merkmalsvektoren, markiert mit der Lauf-ID.
1. Das System speichert **jede Vorhersage** von jeder Funktion, markiert mit der Lauf-ID und dem Eingabefenster.
1. Bediener protokollieren **Ereignisse (Extruder, Granulator, Reinigung, Störungen), Beobachtungen des Materialverhaltens und tägliche Qualitätseinträge** über die Formulare; Jedes ist an die Lauf-ID angehängt.
Nach Ende des Laufs (kann Stunden oder eine ganze Schicht dauern):
1. **Materialsperreinträge** erscheinen (normalerweise Tage später, wenn die Qualitätsabteilung ein Problem bestätigt). Jeder Blockeintrag wird nach Material und Zeitbereich wieder mit den Läufen verknüpft, auf die er sich auswirkt.
1. **Bewertungen der Qualitätsabteilung** (Genehmigungen, Ablehnungen, Anomalien) werden wieder dem entsprechenden Lauf hinzugefügt.
Jetzt verfügt der Lauf über eine vollständig beschriftete Aufzeichnung: seinen Signalverlauf, berechnete Funktionen, Live-Vorhersagen, Bedienerereignisse und spätere Ergebnisse. Über viele Läufe hinweg wird daraus der **Trainingsdatensatz**:
1. Das System lernt, welche Signalmuster während der Produktion stets bestimmten Qualitätsergebnissen vorausgingen. Dies ist die Eingabe für das Training des Predictive Quality ML-Modells.
1. Aktuelle Läufe werden kontinuierlich mit akkumulierten „guten Läufen“ für denselben Materialtyp verglichen. Überall dort, wo der aktuelle Lauf erheblich von historischen guten Läufen abweicht, wird eine Warnung ausgegeben – auch ohne explizite Regel.
Je länger das System läuft, desto stärker wird jede Fähigkeit. Dies ist beabsichtigt: Der Client verfügt über keine historischen Daten, daher ist die Fähigkeit des Systems, aus seinem eigenen Live-Betrieb zu lernen, der einzige Weg zu immer besseren Vorhersagen.

# 11. Rollen und Verantwortlichkeiten
Das System ist eine Partnerschaft zwischen drei menschlichen Rollen und zwei automatisierten Rollen. Alle Rollen sind erforderlich – eine Lücke in einer von ihnen schwächt die Ergebnisse.

| Rolle | Verantwortung |
|---|---|
| Bediener / Produktionspersonal | Protokollieren Sie Wartungsmaßnahmen (Messerwechsel/Schärfen, Siebwechsel, Düsenarbeiten), Werkzeugwechsel, Reinigung, Materialwechsel, manuelle Eingriffe, Materialverhaltensbeobachtungen am Boden, Ursachen für geringe Produktion und tägliche Qualität (offene Löcher %, Sieb %, Schaumbildung OK/NOK). Diese Protokolle sind die primären Bezeichnungen für jede Lernfähigkeit. |
| Qualitätsabteilung / Verantwortliche Mitarbeiter | Erfassen Sie Qualitätsbeurteilungen, Auffälligkeiten, Freigaben, Ablehnungen und Materialsperren. Dies ist die Grundwahrheit für Predictive Quality. |
| System (automatische Erfassung) | Erfassen und bereinigen Sie alle WinCC-Signalwerte, kennzeichnen Sie ihre Qualität, puffern Sie den aktuellen Verlauf, berechnen Sie Funktionen über Zeitfenster hinweg, führen Sie alle Erkennungsfunktionen aus, speichern Sie Vorhersagen mit Eingabefenstern und Erklärungen und generieren Sie Warnungen. |
| System (Dashboard & Benachrichtigungen) | Vorhersagen und Warnungen mit Priorisierung anzeigen; Liefern Sie In-App- und Mobilbenachrichtigungen für kritische Ereignisse. |
| SCLERA (uns) | Entwerfen Sie die Pipeline und die Funktionen. jede technische Entscheidung treffen (Algorithmen, Schwellenwerte, Architektur); Regeln mithilfe von Kundenantworten und live erfassten Daten kalibrieren; Betreiberformulare integrieren; das Dashboard liefern; Führen Sie die Korrelations- und Lernebene aus. Weiterentwicklung regelbasierter Fähigkeiten zu ML, wenn sich Daten ansammeln; pflegen und auf weitere Linien ausweiten. |

# 12. Entwicklungs-Roadmap (Projektabschlusspfad)
Sortiert nach Abhängigkeit. Fähigkeiten bleiben im endgültigen System gleichermaßen wichtig; Die Reihenfolge hier spiegelt nur wider, was zuerst gebaut werden muss, damit das nächste Ding funktioniert.
**Phase 0 – Gründung – FERTIG**
- Aufnahme (regelmäßige Abfrage vom Backend).
- Datenbereinigung mit Tagging in voller Qualität (GOOD / STALE / OUT_OF_RANGE / BAD / MISSING).
- Rollfensterpuffer im Speicher.
- Multi-Window-Feature-Engine (1 m / 5 m / 15 m / 30 m / Volldurchlauf).
- Signalkataloggesteuertes Routing (Hinzufügen eines Signals zu einer Gruppe leitet automatisch zur richtigen Funktion weiter).
- Vorhersagespeicherung mit Rückverfolgbarkeit im Eingabefenster und für Menschen lesbaren Erklärungen.
- Erste Bedienerformulare in der SUNPOR AI-Anwendung (UI-Tests laufen).
- Anfängliche Prozessstatus-Pipeline läuft; **Stabile Produktion** Phase kalibriert auf Live-E10-Daten.
**Phase 1 – Prozessstatus + frühe Dosieranomalie (Kundenprioritäten)**
- Vervollständigen und kalibrieren Sie alle 9 Phasen (erfordert Kundendefinitionen aus Abschnitt 13 und live erfasste Phasenbeispiele, die von den Bedienern markiert wurden).
- Fügen Sie die Unteranalyse „Ursache und Schweregrad geringer Produktion“ hinzu.
- Sorgen Sie für eine frühzeitige Erkennung von Anomalien mit phasenbezogenen Basislinien. Priorisieren Sie die Dosiererabweichung – fügen Sie Dosierervibrationen und Einspeise-/Förderzeitsignale hinzu, sobald diese verfügbar sind.
- Zeigen Sie die aktuelle Phase und Frühwarnungen auf dem Dashboard an, mit eingeblendetem Erklärungs- und Eingabefenster.
**Phase 2 – Datengrundlage für Qualität**
- Beheben Sie die Lücken im Bedienerformular (Fehlerstufe 3 dynamisch, Extruderstufe 2→3 Kaskade, Eintrag „Geringe Produktion“ hinzufügen, tägliche Qualitätshäufigkeit bestätigen).
- Stellen Sie bei jedem Lauf eine konsistente Erfassung durch Bediener und Qualitätsabteilung sicher.
- Bauen Sie die Korrelations- und Lernschicht auf – die Leitung, die Laufsignale mit späteren Qualitäts- und Wartungsereignissen verknüpft und pro Lauf gekennzeichnete Datensätze erstellt.
**Phase 3 – Spezifische Risikofähigkeiten**
- Materialverhalten – regelbasiert auf der Grundlage des Kundenwissens über Ursachen; verbessert sich, da Bediener Verhaltensereignisse protokollieren.
- Granulator/Messer – trendbasiert vom ersten Tag an; verbessert sich, wenn sich Messerereignisse häufen.
- Düse/Sieb – regelbasiert auf ΔP und der Ebenheit der Düsenplatte; verfeinert sich, wenn sich Bildschirm-/Düsenereignisse häufen.
**Phase 4 – Vorhersagequalität**
- Regelbasierte Risikobewertungen vom ersten Tag an (Pentanabweichung, Off-Spec-Drift, Düsenplattenvarianz, Materialverhaltensereignisse).
- Sobald genügend Durchläufe mit Ergebnissen live erfasst wurden, trainieren Sie das ML-Modell, um Qualitätsrisiken während der Produktion vorherzusagen. Vergleichen Sie aktuelle Läufe mit akkumulierten guten Läufen für denselben Materialtyp.
**Phase 5 – Wartungspriorisierung + Benachrichtigungen**
- Fassen Sie einzelne Risiken in einer geordneten Empfehlungsliste auf dem Dashboard zusammen.
- Stellen Sie In-App- und Mobilbenachrichtigungen für Elemente mit der höchsten Priorität bereit, mit Eskalationsregeln je nach Kundenwunsch.
**Phase 6 – Härtung & Mehrleitung**
- Laufende Regel-/Schwellenwert-Neukalibrierung, wenn mehr Live-Daten anfallen.
- Erweitern Sie die Linie E10 auf weitere Linien (nur Konfiguration, keine Codeänderungen für die Signalweiterleitung).

# 13. Offene Posten / Mandantenabhängigkeiten (konsolidiert)
Nach Kategorie gruppiert. Dies ist es, was die oben genannten Roadmap-Phasen entsperrt oder verbessert.
**Signale / Daten**
- Fügen Sie Dosierschwingungssensoren zum WinCC-Export hinzu.
- Zufuhr-/Förderzeiten des Dosierers hinzufügen.
- Fügen Sie den Status „Dosierer gefüllt/aktiv“ hinzu.
- Fügen Sie die Vibration des Granulators hinzu.
- Addieren Sie den tatsächlichen Durchsatz von Zufuhr 6 (Pentan) und Zufuhr 7 (Stickstoff) (derzeit ist nur der Sollwert vorhanden).
**Definitionen und Schwellenwerte (erforderlich für Prozessstatus + niedrige Produktion)**
- Bedeutung des Materialproduktionsstatus = 1 in jeder Produktionsphase.
- Bedeutung der Feeder-Betriebsarten (GD, VR, VS, LF, EF und alle anderen).
- Bediener-/Etage-Definition jeder Phase (was sagt Ihnen, dass es sich um Anlauf vs. Stall vs. Leerlauf vs. Reinigung vs. Abkühlung vs. Abschaltung vs. Fehler handelt).
- Phasenbeispiele während des Live-Betriebs – Bediener markieren „wir sind jetzt in [Phase]“, damit das System echte Daten kennzeichnen kann.
- Schwellenwert für niedrige Produktion (% unter dem Sollwert + Dauer) und wie die geplante Verlangsamung aufgezeichnet wird.
- Differenzdruckschwellenwerte für Sieb („bald ändern“ vs. „jetzt ändern“).
- Normalbereiche der Wasserbox – größtenteils im Fragebogen angegeben (58–61 °C Wassertemperatur, Alarm bei 64 °C, Schaum bei 65 °C, ~10,1 bar), live zu bestätigen.
- Kritische (Schrott-) vs. Warndosierer und ihre Schwellenwerte – teilweise bereitgestellt.
**Qualität**
- Messmethode, Häufigkeit und Schwellenwerte für offene Löcher %, Sieb % und Schaumbildung OK/NOK.
- Typischer Zeitpunkt zwischen Laufabschluss und Materialblockierung (wenn ein Lauf blockiert ist).
- Ob die Rohstofffeuchtigkeit als Bedienerfeld beim Produktionsstart hinzugefügt werden sollte (diese wird im Fragebogen als Ursache für Zellstrukturprobleme genannt).
**Prozessverständnis (aus dem Fragebogen – weitgehend beantwortet, Bestätigung für E10-Spezifika erforderlich)**
- Ursache-Wirkungs-Beziehungen pro Station (meist beantwortet).
- Typische Fehler pro Station (meist beantwortet).
- Bedienereingriffe im laufenden Betrieb (meist beantwortet).
- Tägliche Entscheidungen von Schichtleitern und Maschinenführern (meist beantwortet).
**Operationen**
- Bevorzugte Benachrichtigungskanäle (In-App, E-Mail, SMS, Mobile Push).
- Eskalationsregeln – wer wird bei welcher Dringlichkeitsstufe alarmiert?

# 14. Erfolgskriterien
Das Projekt gilt als erfolgreich, wenn:
- **Prozessstatus** beschriftet alle 9 Phasen auf der stromführenden Linie E10 korrekt und wird von den Bedienern vor Ort validiert. Wenn der Bediener sagt: „Wir sind im Startup“, stimmt das System zu.
- **Ereignisse mit geringer Produktion** werden mit der richtigen Ursache und dem richtigen Schweregrad gemeldet, und das System erzeugt **keine** Fehlalarme während des normalen Hochfahrens, Herunterfahrens, Leerlaufs oder geplanter Verlangsamungen.
- **Frühe Dosieranomalien** werden vom System gekennzeichnet, **bevor** sie heute von den vorhandenen Schwellenalarmen gemeldet werden. Jede frühe Anomalie, die der Bediener als echtes Problem bestätigen kann, wird gemessen; Das Verhältnis von echten Frühwarnungen zu Fehlalarmen wird verfolgt und verbessert sich im Laufe der Zeit.
- **Frühwarnungen** werden **vor** dem tatsächlichen Fehler oder Qualitätsverlust für die Hauptproblemtypen (Siebverstopfung, Düsenverstopfung, Dosierdrift, Materialverhaltenssymptome) ausgegeben.
- **Predictive Quality** kennzeichnet riskante Läufe **während** der Produktion, und diese Risiken werden später durch Ergebnisse des Labors/der Qualitätsabteilung mit einer messbaren, über dem Zufall liegenden Rate bestätigt. Dies beginnt klein (regelbasiert) und verbessert sich, wenn der interne Datensatz wächst.
- **Wartungshinweise** gehen in den meisten Fällen dem eigentlichen Messer-/Düsen-/Sieb-Eingriff voraus und geben dem Bediener Zeit.
- Der **interne Lerndatensatz** wächst kontinuierlich aus dem Live-Betrieb; Die Fähigkeitsgenauigkeit verbessert sich messbar, je mehr markierte Läufe sich ansammeln. Dies ist die konkrete Art und Weise, wie wir zeigen, dass das System „lernt“.
- Das System bleibt **beratend, konfigurierbar, erweiterbar und für mehrere Leitungen bereit** – keine Maschinensteuerung, Dropdowns jederzeit editierbar, Schwellenwerte in der Konfiguration editierbar und neue Signale oder neue Leitungen erfordern eher eine Konfiguration als Codeänderungen.

*Dies ist ein lebendes Dokument. Aktualisieren Sie Definitionen, Schwellenwerte, den Status jeder Funktion und offene Punkte, sobald Kundenantworten eingehen und Live-Daten anfallen.*
