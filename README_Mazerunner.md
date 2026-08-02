# 🌀 Mazerunner-DT-IsaacSim-Extension

**Digitaler Zwilling der Maze-Runner-Anlage der Hochschule Rhein-Main (HSRM)**
Steuerungs- und Diagnose-Panel für NVIDIA Omniverse Isaac Sim

---

📌 **Projektarbeit** von Tobias Küster (Matrikelnummer 1690767)
🎓 Hochschule Hannover — Fakultät II, Maschinenbau und Bioverfahrenstechnik
👥 Betreut von Prof. Diersen, Dr. Yübo Wang (Hochschule Rhein-Main), Herrn Ernst

> ℹ️ Diese Extension entstand im vorangegangenen IIM-Projekt und bildet die Erfahrungsgrundlage für die anschließende Bachelorarbeit, in der mit derselben Architektur eine zweite Extension für den Dobot Magician entwickelt wurde: [Dobot-Magician-DT-IsaacSim-Extension](../README_Dobot.md). Beide Projekte sind eigenständig und werden hier bewusst nicht vermischt.

<p align="center">
  <img src="docs/img/Mazerunner_Aktorik.png" width="46%" alt="Reale Maze-Runner-Anlage im LFP">
  <img src="docs/img/Mazerunner_in_Isaac_Sim.png" width="46%" alt="Maze Runner als Digitaler Zwilling in Isaac Sim">
</p>
<p align="center"><em>Links: reale Maze-Runner-Anlage im Labor für Produktentwicklung und Digitale Fabrik (LFP) der HsH. Rechts: derselbe Aufbau als Digitaler Zwilling in NVIDIA Isaac Sim.</em></p>

---

## Inhaltsverzeichnis

1. [Über dieses Projekt](#über-dieses-projekt)
2. [Systemarchitektur](#systemarchitektur)
3. [Betriebsmodi](#betriebsmodi)
4. [Kommunikationsprotokolle](#kommunikationsprotokolle)
5. [Kamera-Livestream](#kamera-livestream)
6. [Voraussetzungen](#voraussetzungen)
7. [Installation in Isaac Sim](#installation-in-isaac-sim)
8. [Bedienung](#bedienung)
9. [Node-Konfiguration (`nodes_db.json`)](#node-konfiguration-nodes_dbjson)
10. [Projektstruktur](#projektstruktur)
11. [Inbetriebnahme der Anlage](#inbetriebnahme-der-anlage)
12. [Bekannte Einschränkungen](#bekannte-einschränkungen)
13. [Gemeinsamer Laboraufbau](#gemeinsamer-laboraufbau)
14. [Weiterführende Dokumentation](#weiterführende-dokumentation)
15. [Kontakt](#kontakt)

---

## Über dieses Projekt

Die Maze-Runner-Anlage ist ein physischer Rundtakttisch im Labor für Produktentwicklung und Digitale Fabrik (LFP) der Hochschule Hannover, der ursprünglich von der Hochschule Rhein-Main (HSRM) für die industrielle Lehre entwickelt wurde. In einer hochschulübergreifenden Online-Vorlesung greifen internationale Partnerhochschulen wechselseitig auf die Digitalen Zwillinge der beteiligten Standorte zu. Damit die Anlage dabei ortsunabhängig gesteuert und beobachtet werden kann, ist sie an die **Digital Twin App** der HSRM (`digitaltwinapp.de`) angebunden, deren Backend der **DigitalTwinService** (`digitaltwinservice.de`) bildet.

<p align="center"><img src="docs/img/DigitalTwinAppDashboard.png" width="85%" alt="Digital Twin App Dashboard"></p>
<p align="center"><em>Digital Twin App Dashboard: Kamera-Livestream, Live-Übertragung der Isaac-Sim-Simulation, Fernsteuerungspanel und die visuelle Programmiersprache Blockly für einfache eigene Anwendungen.</em></p>

Diese Extension schließt die Lücke zwischen der Simulation in **NVIDIA Isaac Sim** und der realen Anlage. Sie stellt ein in Isaac Sim angedocktes Human-Machine-Interface (HMI) bereit, über das sich alle steuerbaren Aktoren der Anlage sowohl virtuell testen als auch live an der realen Hardware auslösen lassen, ohne dass in den Quellcode eingegriffen werden muss.

<p align="center"><img src="docs/img/MazerunnerExtension.png" width="90%" alt="Isaac-Sim-Oberfläche mit HMI"></p>
<p align="center"><em>Isaac-Sim-Oberfläche mit dem angedockten Maze-Runner-HMI.</em></p>

<p align="center"><img src="docs/img/MazerunnerHMI.png" width="55%" alt="Maze-Runner-HMI im Detail"></p>
<p align="center"><em>Maze-Runner-HMI im Detail: Moduswahl LIVE/SIM oben, Knotenliste mit Status und Fernsteuerungs-Buttons, farbkodierter Log-Bereich unten.</em></p>

---

## Systemarchitektur

Die Extension kommuniziert nicht direkt mit der Anlagensteuerung (SPS), sondern ausschließlich über den DigitalTwinService der HSRM, der als vermittelnde Instanz zwischen Isaac Sim, dem Internet und dem Labornetzwerk der Maze-Runner-Anlage fungiert. Die Gesamtarchitektur umfasst drei Netzwerkzonen, das Netzwerk der Digitalen Fabrik im Labor, das Netzwerk der HSRM sowie das freie Internet, in dem sich auch der Simulationsrechner mit NVIDIA Isaac Sim befindet.

<p align="center"><img src="docs/img/MazeRunnerIBD.png" width="100%" alt="Netzwerkarchitektur"></p>
<p align="center"><em>Netzwerkarchitektur zur Anbindung Digitaler Zwillinge in NVIDIA Omniverse an die Digital Twin App der HSRM.</em></p>

**Steuerpfad:** Isaac-Sim-Extension → REST-HTTP → DigitalTwinService → OPC-UA-WriteValue → SPS
**Typische Latenz:** 100–500 ms pro Steuerbefehl

Ein Steuersignal wird von der Extension per REST-API an den DigitalTwinService übermittelt, der es als SPS-Datenstrom an den OPC-UA-Client der HSRM weiterleitet. Von dort gelangt das Signal über VPN-Gateway und VPN-Tunnel zum VPN-Router im Netzwerk der Maze-Runner-Anlage, der es über die SPS an die Aktorik weiterleitet. Da die REST-API keine Publish-Subscribe-Architektur bietet und wiederholtes Abfragen (Polling) unnötig ressourcenintensiv wäre, läuft der Rückkanal für Statusänderungen ausschließlich über die **MQTT-WebSocket-Schnittstelle** des DigitalTwinService, wodurch die Extension ressourcenschonend auf Wertänderungen der Anlage lauschen kann.

Das in NVIDIA Isaac Sim dargestellte OpenUSD-Modell der Anlage ist in Abbildung unten mit Viewport, Stage-Baum und Property-Panel zu sehen. Die hierarchische Ordnerstruktur der Stationen ist dabei in `_fix`- und `_move`-Unterordner gegliedert, jeweils mit dem zugehörigen Gelenk im selben Ordner.

<p align="center"><img src="docs/img/Mazerunner_in_Isaac_Sim.png" width="90%" alt="OpenUSD-Modell in Isaac Sim"></p>
<p align="center"><em>OpenUSD-Modell des Maze-Runners in NVIDIA Isaac Sim.</em></p>

---

## Betriebsmodi

| Modus | Beschreibung |
|-------|-------------|
| 🖥️ **SIM** | Reine lokale Simulation in Isaac Sim, keine Netzwerkverbindung, alle Knotenzustände werden lokal verwaltet. Ideal für Entwicklung und Test ohne physische Hardware. |
| 🔴 **LIVE** | Steuerbefehle werden per REST-API an die reale Anlage übertragen, Statusänderungen kommen live per MQTT zurück. |

Umgeschaltet wird über den **→ LIVE / → SIM**-Button oben rechts im HMI.

> ⚠️ Der Button **▶ Gesamtprozess** steht ausschließlich im SIM-Modus zur Verfügung. Der automatische Produktionsbetrieb wird von der SPS verwaltet und darf aus Sicherheitsgründen nicht ferngesteuert ausgelöst werden.

---

## Kommunikationsprotokolle

| Richtung | Protokoll | Zweck |
|----------|-----------|-------|
| Extension → DigitalTwinService | REST-API (HTTP POST, authentifiziert) | Steuerbefehle senden (Aktor schalten, Zielposition setzen, Routine starten) |
| DigitalTwinService → Extension | MQTT über WebSocket | Live-Statusänderungen der Anlage empfangen |
| DigitalTwinService → SPS | OPC-UA (WriteValue/ReadValue) | Ansteuerung der Siemens-SPS über verschlüsselten VPN-Tunnel |

Der MQTT-Client ist in `websocket_mqtt.py` als schlanke Eigenimplementierung von **MQTT v3.1.1 über WebSocket-Transport** realisiert und wird von `mqtt_handler.py` zum Abonnieren von Topics sowie zum Empfangen von PUBLISH-Paketen genutzt.

---

## Kamera-Livestream

Zusätzlich zur Datenkopplung über REST-API und MQTT überträgt eine Tapo-Überwachungskamera ein Livebild der realen Anlage. Dieses nimmt einen eigenen Weg unabhängig vom Steuerpfad: Die Kamera sendet per RTSP an einen OBS-Livestream-Rechner (denselben Laptop, auf dem auch NVIDIA Isaac Sim läuft), der das Bild per RTMP an einen Twitch-Ingest-Server weiterleitet, von wo aus die Digital Twin App den Stream als HLS-Videostream einbindet. Eine Fernsteuerung der Gier- und Nickmotorik der Kamera wird dabei nicht unterstützt, es wird ausschließlich das Bild übertragen.

---

## Voraussetzungen

### API-Key setzen

In [`constants.py`](constants.py) muss der gültige API-Key der HSRM eingetragen sein:

```python
API_KEY = "dein-api-key-hier"
```

Ohne gültigen Key schlagen sämtliche REST-API-Aufrufe im LIVE-Modus fehl.

### Python-Abhängigkeiten

Folgende Pakete werden zusätzlich zur Isaac-Sim-eigenen Python-Umgebung benötigt und lassen sich über `pip install` im eingebetteten Python der Omniverse-Installation nachinstallieren:

```
aiohttp
websockets
```

Die MQTT-Bibliothek `paho-mqtt` liegt bereits gebündelt im Ordner `paho/` bei und muss nicht separat installiert werden.

### Kompatibilität

| Komponente | Version |
|------------|---------|
| NVIDIA Isaac Sim | Omniverse Kit Extension Framework |
| Python | eingebettete Isaac-Sim-Python-Umgebung |
| USD-Stage | `MazeRunnerDigiTwin.usd` |

---

## Installation in Isaac Sim

1. 📁 Den Ordner `Mazerunner_DT_IsaacSim_Extension` in ein lokales Extension-Verzeichnis kopieren, das Isaac Sim kennt (z. B. `~/Documents/Kit/apps/Isaac-Sim/exts/`).
2. 🧩 Isaac Sim öffnen → **Window → Extensions** → nach der Extension suchen → **Enable**.
3. 🖱️ Das Fenster **Maze Runner** dockt sich automatisch in den Property-Bereich der Isaac-Sim-Oberfläche ein.
4. 🔑 API-Key in `constants.py` eintragen (siehe [Voraussetzungen](#voraussetzungen)).

---

## Bedienung

### Steuerfeld

| Element | Funktion |
|---------|----------|
| 🔄 **Refresh JSON** | Lädt `nodes_db.json` neu, z. B. nach Konfigurationsänderungen, ohne die Extension neu starten zu müssen. |
| ♻️ **Restart Extension** | Startet die Extension vollständig neu, ohne Isaac Sim zu beenden. |
| 🔀 **→ LIVE / → SIM** | Wechsel zwischen Simulationsmodus und Live-Anbindung an die reale Anlage. |
| ▶️ **Gesamtprozess** | Demonstriert einmalig den vollautomatischen Produktionsablauf (nur im SIM-Modus verfügbar). |

### Node-Liste

Jede Zeile im HMI entspricht einem Maschinenelement aus `nodes_db.json` und besitzt einen eigenen Steuerungsmodus:

- 🔘 **toggle** — schaltet einen Aktor zwischen zwei Endlagen um, z. B. das Ausfahren eines Schiebers.
- 📈 **impulse** — erhöht die hinterlegte Zielposition (`target_value`) um einen festen Winkelschritt (`step_degrees`). Bei der Drehscheibe entspricht dieser Schritt sechzig Grad, passend zur Anordnung der sechs vom induktiven Sensor erfassten Metallpins, wodurch trotz zielpositionsbasierter Gelenksteuerung eine fortlaufende Drehung nachgebildet wird.
- 🔁 **routine** — führt eine vordefinierte Abfolge mehrerer Einzelaktionen als Schrittkette aus, z. B. `BA_Start`.

Die Knoten `Sauggreifer`, `Schwenkarm_Deckel_trans` und `Schwenkarm_Deckel_rot` gehören sämtlich zur Routine `BA_Start`, die das Ansaugen und Ablegen des Deckels sowie die Steuerung von Schrittmotor, Zylinder und Schwenkarm verwaltet. Sie werden im HMI dennoch einzeln aufgeführt, um die Funktion jedes Aktors isoliert prüfen zu können, bevor sie gemeinsam über die Routine ausgeführt werden. Die Ausgabestation der zweiten SPS ist vorerst nicht in die Extension integriert, da eine äquivalente Routine hierfür zunächst nur ein Duplikat wäre.

### Simulation starten

1. USD-Szene `MazeRunnerDigiTwin.usd` öffnen.
2. Im **SIM**-Modus auf **▶ Play** drücken.
3. Einzelne Aktoren über die Node-Liste ansteuern oder den gesamten Ablauf über **▶ Gesamtprozess** demonstrieren.

---

## Node-Konfiguration (`nodes_db.json`)

Jeder Eintrag in `nodes_db.json` verknüpft einen SPS-Knoten mit dem Digitalen Zwilling.

<p align="center"><img src="docs/img/nodes_db.png" width="80%" alt="Ausschnitt nodes_db.json"></p>
<p align="center"><em>Ausschnitt der Konfigurationsdatei nodes_db.json.</em></p>

| Feld | Bedeutung |
|------|-----------|
| OPC-UA-Node-ID | Adresse des Knotens im OPC-UA-Adressraum der SPS, ausgelesen über UaExpert |
| USD-Pfad | Zielgelenk in der USD-Stage, das bei einer Zustandsänderung angesteuert wird |
| Gelenktyp | z. B. Revolute Joint oder Prismatic Joint |
| `target_value` | Zielwert des Gelenks |
| `step_degrees` | Schrittweite je Impuls, ausschließlich für den Modus `impulse` |
| `mode` | Steuerungsmodus des Knotens (`toggle`, `impulse`, `routine`) |

Änderungen an dieser Datei werden über den Button **Refresh JSON** im HMI übernommen, ohne dass die Extension neu gestartet werden muss.

---

## Projektstruktur

Der eigentliche Quellcode der Extension gliedert sich in zwölf Module.

<p align="center"><img src="docs/img/MazerunnerGithubRepo.png" width="55%" alt="Dateien des Extensionordners"></p>
<p align="center"><em>Dateien des Extensionordners, vollständig über dieses Repository bereitgestellt.</em></p>

| Datei | Zuständigkeit |
|-------|--------------|
| 🚀 `extension.py` | Einstiegspunkt der Extension. Implementiert die Klasse `MyExtension` (erbt von `omni.ext.IExt`) und ist damit vollständig in den Isaac-Sim-Lebenszyklus integriert. `on_startup()` und `on_shutdown()` initialisieren bzw. beenden sämtliche asynchronen Tasks und Komponenten. |
| 🗂️ `nodes_db.json` | JSON-Konfigurationsdatei mit der Verknüpfung jedes SPS-Knotens zum Digitalen Zwilling (siehe [Node-Konfiguration](#node-konfiguration-nodes_dbjson)). |
| 🧠 `node_manager.py` | Lädt die Knoten aus `nodes_db.json`, baut die Knotenliste im UI auf und fährt bei Zustandsänderungen die zugehörigen Gelenke über `target_value` in ihre Zielposition. |
| 🎛️ `ui_builder.py` | Baut das in Isaac Sim angedockte Maze-Runner-HMI einmalig auf und liefert Referenzen auf alle UI-Widgets an `extension.py` zurück. |
| 🌐 `api_client.py` | Sendet asynchrone HTTP-Requests an den DigitalTwinService der HSRM und aktualisiert über `node_manager.py` die Anzeige nach Erhalt der Antwort. |
| 📡 `mqtt_handler.py` | Startet und stoppt den MQTT-WebSocket-Client und leitet eingehende Nachrichten thread-sicher in den asyncio-Loop weiter, wo `node_manager.py` den Zustand aktualisiert. |
| 🔌 `websocket_mqtt.py` | Eigenimplementierung von MQTT v3.1.1 über WebSocket-Transport, genutzt von `mqtt_handler.py` zum Abonnieren von Topics und Empfangen von PUBLISH-Paketen. |
| 🔩 `deckel_joint_handler.py` | Verwaltet die Startposition des Deckels, bildet den `FixedJoint` zwischen Sauggreifer und Deckel beim Aufnehmen und löst ihn beim Loslassen, erstellt anschließend den `FixedJoint` zwischen Deckel und Boden, aktualisiert die Deckelposition während der Weiterbewegung auf der Drehscheibe und senkt den Deckel beim Ausfahren der Presse ab. |
| 🔁 `routines.py` | Enthält automatisierte Abläufe wie den Gesamtprozess und `BA_Start`, die `node_manager.py`, `deckel_joint_handler.py` und `extension.py` ansprechen. |
| ⏯️ `timeline_handler.py` | Reagiert auf Play und Stop der Omniverse-Timeline. Startet bei Play den SIM-Loop zum Halten und Verpressen des Deckels und setzt bei Stop alle Werte zurück. |
| 📝 `logger.py` | Schreibt Log-Zeilen farbkodiert nach Modul in den Fehlerausgabebereich des HMI und wird von allen übrigen Modulen genutzt. |
| ⚙️ `constants.py` | Bündelt zentrale Konfigurationswerte wie API-Key, URLs, Farbwerte für Panelflächen und Geometrie-Offsets für die gesamte Extension. |

Der Ordner wurde bewusst um alle für den Betrieb notwendigen Dateien ergänzt, darunter eine Schritt-für-Schritt-Anleitung im PowerPoint-Foliensatz, die USD-Stage der Anlage sowie diese README-Datei, sodass er sich unverändert als eigenständiges Repository bereitstellen lässt.

Weitere, nicht extensionspezifische Ordner:

| Ordner | Inhalt |
|--------|--------|
| `__pycache__` | Von Python automatisch erzeugter Bytecode |
| `.venv` | Virtuelle Python-Umgebung mit allen Abhängigkeiten |
| `paho` | Externe MQTT-Bibliothek `paho-mqtt` |

---

## Inbetriebnahme der Anlage

Bei der Übergabe der Anlage von Herrn Wang an das LFP befand sich diese noch im Rohzustand ohne die für den Laborbetrieb notwendige Peripherie.

<p align="center"><img src="docs/img/Ist-Zustand_Mazerunner.png" width="70%" alt="Ist-Zustand der Anlage bei Übergabe"></p>
<p align="center"><em>Ist-Zustand der Maze-Runner-Anlage im Hochschullabor bei Übergabe (Aufnahme von oben).</em></p>

Bis zum in Abbildung unten gezeigten finalen Tischaufbau waren zahlreiche, gemeinsam mit Herrn Wang festgelegte Anpassungen an Halterungen, Elektrik, SPS und Druckluftversorgung notwendig, unter anderem der Einbau eines Druckluftminderers mit passenden Anschlüssen für den Arbeitsdruck von vier Bar.

<p align="center"><img src="docs/img/Mazerunner_Aktorik.png" width="55%" alt="Aktorik der Anlage"></p>
<p align="center"><em>Aktorik der Maze-Runner-Anlage nach Inbetriebnahme.</em></p>

---

## Bekannte Einschränkungen

- 🚧 Die Ausgabestation der zweiten SPS ist aktuell **nicht** in die Extension integriert. Die Schwenkarm-Deckelstation stellt über `BA_Start` bereits die Infrastruktur einer Routine bereit, eine äquivalente Routine für die Ausgabestation wäre vorerst nur ein Duplikat.
- 🔒 Der Button **Gesamtprozess** ist bewusst auf den SIM-Modus beschränkt, da der Automatikbetrieb sicherheitshalber ausschließlich von der SPS verwaltet wird.
- 📏 Die pneumatischen Zylinder sind bauartbedingt etwas länger als für den vollen Rutschenweg vorgesehen, wodurch der Schieber im ausgefahrenen Zustand mit dem Gewinde der Zylinderfassung leicht in das Magazin hineinfährt.

---

## Gemeinsamer Laboraufbau

Im LFP teilen sich Maze-Runner-Anlage und Dobot Magician denselben Labortisch, der Dobot Magician übernimmt dabei perspektivisch Pick-and-Place-Aufgaben an der Ausgabestation des Maze Runners.

<p align="center"><img src="docs/img/tischaufbau.png" width="90%" alt="Gemeinsamer Tischaufbau"></p>
<p align="center"><em>Finaler Tischaufbau aus Dobot Magician (links) und Maze-Runner-Anlage (rechts) im LFP der Hochschule Hannover.</em></p>

---

## Weiterführende Dokumentation

- 📖 Vollständige technische Dokumentation, Netzwerkarchitektur und Reproduzierbarkeitsdokumentation: siehe Bachelorarbeit „Entwicklung Digitaler Zwillinge für Lehrzwecke am Beispiel Maze Runner und Dobot Magician" (Tobias Küster, Hochschule Hannover)
- 🎞️ `Kuester_Omniverse_Tutorial` — PowerPoint-Foliensatz mit 32 Folien als didaktische Schritt-für-Schritt-Anleitung zum Nachbau des Digitalen Zwillings
- 🕶️ VR-Demonstration auf Meta Quest 3 zur immersiven Inspektion des Digitalen Zwillings

---

## Kontakt

**Tobias Küster**
Hochschule Hannover, Fakultät II
Matrikelnummer 1690767

Betreuung: Prof. Diersen (Hochschule Hannover) · Dr. Yübo Wang (Hochschule Rhein-Main) · Herr Ernst
