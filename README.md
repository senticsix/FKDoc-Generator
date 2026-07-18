# FKDoc-Generator – Fahrtkostenerstattung Familienheimfahrt

Eine kleine Desktop-App (Python + PyQt6), die das Formular **„Kostenerstattung für Familienheimfahrten"** automatisch ausfüllt: Sie trägt Name, Fahrtdaten, Kilometer, Ausbildungsdauer, Krankmeldung und eine generierte Unterschrift in die Word-Vorlage ein, speichert das Ergebnis als `.docx` und wandelt es über Microsoft Word direkt in ein PDF um.
---

## Funktionen

- **1 oder 2 Fahrten** pro Antrag, Datumsauswahl über einen Kalender, in dem An- und Rückreise mit zwei Klicks in einem Rutsch gewählt werden (Zeitraum wird farbig markiert)
- **Krankmeldung** per Häkchen zuschaltbar – im Formular werden die echten Ja/Nein-Kontrollkästchen umgeschaltet und der Krankmeldungszeitraum eingetragen
- **Ausbildungsdauer** („vom … bis …") wird direkt in die Word-Datumssteuerelemente der Vorlage geschrieben
- **Unterschrift** wird aus dem Namen generiert und in Schreibschrift (Brush Script MT) eingefügt – keine Bilddatei nötig
- **PDF-Export** automatisch nach dem Erstellen (über Microsoft Word)
- **Mail-Versand**: Nach dem Erstellen kann die PDF direkt verschickt werden – es öffnet sich ein fertiger Mail-Entwurf (Betreff „Fahrtkostenabrechnung") mit Anhang, der vor dem Senden noch geprüft werden kann. Beim ersten Versand fragt die App, welches Mail-Programm verwendet werden soll (macOS: Apple Mail, Outlook oder Thunderbird; Windows: Outlook oder Thunderbird) und merkt sich die Wahl
- **PDF-Ablage**: Optional werden alle erzeugten PDFs zusätzlich in einem frei wählbaren Root-Ordner nach Datum sortiert abgelegt (`<Ordner>/<Jahr>/<Monat>/Fahrtkostenerstattung_<von>_bis_<bis>.pdf`)
- **Plausibilitätsprüfungen**: Rückreise vor Abreise, überlappende Fahrten und Ausbildungsende vor -beginn werden abgefangen
- **Update-Check**: Die App prüft beim Start still im Hintergrund, ob auf GitHub ein neues stabiles Release verfügbar ist, und bietet den Download an; manuell über „Nach Updates suchen" in den Optionen

## Voraussetzungen

- **Microsoft Word** muss installiert sein (wird für die PDF-Umwandlung genutzt – auf dem Mac per AppleScript, unter Windows per COM)
- Beim Start aus dem Quellcode: **Python 3.10+** mit den Paketen aus `requirements.txt`
- Die Word-Vorlage `Fahrtkostenerstattung_Familienheimfahrt.docx` muss im Programmordner liegen (in der gebauten App ist sie bereits eingebettet)

## Start aus dem Quellcode

```bash
cd FKscript
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Bedienung

1. **Erster Start:** Es öffnet sich automatisch der Optionen-Dialog. Dort einmalig ausfüllen:
   - *Name* – voller Vor- und Nachname (daraus wird auch die Unterschrift generiert)
   - *Erstanreise*, *Ausbildungsbeginn*, *Ausbildungsende* – per Kalender wählbar
   - *Kilometer* – einfache Wegstrecke laut Routenplaner
   - *E-Mail-Empfänger* – vorausgefüllt mit `XXXXXXXXXXXXXX`, kann geändert werden
   - *Mail-Programm* – wird normalerweise beim ersten Versand abgefragt, kann hier geändert werden
   - *PDF-Ordner* – optional; Root-Ordner, in dem die PDFs nach Jahr/Monat sortiert abgelegt werden
   - *Speicherpfad* – wohin das fertige Dokument gespeichert wird
2. **Fahrt eintragen:** „1 Fahrt" oder „2 Fahrten" wählen, dann je Fahrt auf **Auswählen…** klicken. Im Kalender zuerst die Abreise, dann die Rückreise anklicken – fertig.
3. **Krankmeldung:** Falls vorhanden, Häkchen bei **„Krankmeldung liegt vor"** setzen und den Zeitraum genauso per Kalender wählen.
4. **Dokument erstellen** klicken. Die App speichert die `.docx` am eingestellten Ort und erzeugt daneben die PDF-Datei.
5. Auf Wunsch direkt im Anschluss: **„PDF jetzt per E-Mail verschicken?"** bestätigen – es öffnet sich ein Mail-Entwurf mit Betreff, Anschreiben und der PDF im Anhang. Prüfen und absenden.

Die Optionen lassen sich jederzeit über den Button **Optionen** ändern.

## Wo liegen meine Einstellungen?

| Situation | Speicherort der `config.json` |
|---|---|
| Start aus dem Quellcode | im Projektordner |
| Gebaute App, macOS | `~/Library/Application Support/FKscript/` |
| Gebaute App, Windows | `%APPDATA%\FKscript\` |

## Ausführbare App bauen

> PyInstaller kann nicht cross-kompilieren: Die macOS-App muss auf einem Mac
> gebaut werden, die Windows-`.exe` auf einem Windows-Rechner.

**macOS** – im Projektordner:

```bash
./build_mac.sh
```

Ergebnis: `dist/FKscript.app` – kann in den Programme-Ordner gezogen werden.
Beim ersten Öffnen ggf. Rechtsklick → „Öffnen", da die App nicht signiert ist.
Für die PDF-Umwandlung fragt macOS einmalig nach der Berechtigung, Word zu steuern.

**Windows** – im Projektordner (Doppelklick genügt):

```bat
build_win.bat
```

Ergebnis: `dist\FKscript.exe`. Beim ersten Start blockiert der SmartScreen-Filter
eventuell die unsignierte Datei („Weitere Informationen" → „Trotzdem ausführen").

## Updates & Versionierung

Der Code liegt auf GitHub (`senticsix/FKscript`) mit zwei Branches:

- **`main`** – stabiler Stand; von hier werden Releases veröffentlicht
- **`experimental`** – Entwicklung und neue Features; wird nach dem Testen in `main` gemergt

Die App vergleicht ihre Version (`version.py`) mit dem neuesten **stabilen** GitHub-Release
(Pre-Releases aus `experimental` werden ignoriert). Wird eine neuere Version gefunden,
zeigt die App die Release-Notes und öffnet auf Wunsch die Download-Seite im Browser –
es wird nichts automatisch installiert.

**Neues Release veröffentlichen:**

1. Version in `version.py` erhöhen (z. B. `1.1.0`) und committen
2. Tag setzen und pushen: `git tag v1.1.0 && git push origin main v1.1.0`
3. Auf GitHub unter *Releases → Draft a new release* den Tag auswählen, Release-Notes
   schreiben und die gebauten Apps (`dist/FKscript.app` als ZIP, `dist\FKscript.exe`)
   als Assets anhängen. Für Vorabversionen aus `experimental` zusätzlich
   *„Set as a pre-release"* ankreuzen – diese werden vom Update-Check übersprungen.

## Anpassung der Word-Vorlage

Die App füllt die Vorlage über drei Mechanismen:

- **Text-Platzhalter** in geschweiften Klammern, z. B. `{NAME}`, `{DATUM}`, `{DATUM_HIN}`, `{DATUM_BACK}`, `{DATUM_HIN1}`, `{DATUM_BACK1}`, `{KM}`, `{DATUM_ERSTANR}`, `{SIG_DATE}`, `{SIGNATURE}` – können frei im Text oder in Tabellen stehen
- **Word-Datumssteuerelemente** hinter den Wörtern „vom" und „bis" (Ausbildungsdauer)
- **Word-Kontrollkästchen** hinter „Ja:" und „Nein:" (Krankmeldung)

Wichtig: Die Steuerelemente werden über den davorstehenden Text gefunden. Die Beschriftungen „vom", „bis", „Ja:" und „Nein:" dürfen also umformuliert werden, dann muss aber auch der entsprechende Anker in `main.py` (`set_date_control` / `set_checkbox`-Aufrufe) angepasst werden.

## Projektstruktur

| Datei | Zweck |
|---|---|
| `main.py` | Einstiegspunkt, Dokument-Erzeugung, PDF-Umwandlung, PDF-Ablage |
| `WindowClass.py` | Hauptfenster, Optionen-Dialog, Kalender-Bereichsauswahl |
| `mailer.py` | Mail-Entwurf mit Anhang (Apple Mail, Outlook, Thunderbird) |
| `updater.py` / `version.py` | Update-Check gegen GitHub-Releases, App-Version |
| `ConfigManager.py` | Laden/Speichern der Einstellungen, Pfadlogik (auch für gebaute App) |
| `Fahrtkostenerstattung_Familienheimfahrt.docx` | Word-Vorlage |
| `build_mac.sh` / `build_win.bat` | Build-Skripte für die ausführbare App |

## Fehlerbehebung

**„PDF-Konvertierung fehlgeschlagen"** – Microsoft Word ist nicht installiert oder darf nicht gesteuert werden. Die `.docx` wird trotzdem erstellt und kann manuell in Word als PDF exportiert werden. Auf dem Mac: Systemeinstellungen → Datenschutz & Sicherheit → Automation → der App den Zugriff auf Word erlauben.

**Die Unterschrift sieht nach Standardschrift aus** – Die Schriftart „Brush Script MT" gehört zu Microsoft Office. Ist sie nicht vorhanden, ersetzt Word sie automatisch; ggf. in `main.py` (`replace_text_with_signature`) eine andere Schreibschrift eintragen.

**App startet auf dem Mac nicht („beschädigt")** – Die App ist nicht signiert. Rechtsklick → „Öffnen" oder im Terminal: `xattr -cr /Applications/FKscript.app`.

**Einstellungen zurücksetzen** – Die `config.json` am oben genannten Speicherort löschen; beim nächsten Start fragt die App alle Angaben neu ab.
