# 🦾 Dobot-Magician-DT-IsaacSim-Extension

**Digital Twin Extension für NVIDIA Omniverse für die Pick-and-Place-Anwendung des Dobot Magician**

---

📌 **Bachelorarbeit** von Tobias Küster (Matrikelnummer 1690767)
🎓 Hochschule Hannover — Fakultät II, Maschinenbau und Bioverfahrenstechnik
👥 Betreut von Prof. Diersen, Prof. Vendl, Dr. Yübo Wang (Hochschule Rhein-Main), Herrn Ernst

> ℹ️ Diese Extension ist das zweite von zwei im Rahmen der Bachelorarbeit „Entwicklung Digitaler Zwillinge für Lehrzwecke am Beispiel Maze Runner und Dobot Magician mit NVIDIA Omniverse" entstandenen Projekten. Das erste, für die Maze-Runner-Anlage der Hochschule Rhein-Main, ist im separaten Repository [Mazerunner-DT-IsaacSim-Extension](../README_Mazerunner.md) dokumentiert. Beide Extensions sind eigenständig, ihre Konzepte werden hier bewusst nicht vermischt.

---

## Inhaltsverzeichnis

1. [Übersicht und Zielsetzung](#übersicht-und-zielsetzung)
2. [Von ROS 2 zu pydobot](#von-ros-2-zu-pydobot)
3. [Robotermodell](#robotermodell)
4. [Sauggreifer](#sauggreifer)
5. [Pick-and-Place-Szenario](#pick-and-place-szenario)
6. [Datenflussstruktur der Extension](#datenflussstruktur-der-extension)
7. [Voraussetzungen](#voraussetzungen)
8. [Installation in Isaac Sim](#installation-in-isaac-sim)
9. [Inbetriebnahme](#inbetriebnahme)
10. [Projektstruktur](#projektstruktur)
11. [Bekannte Einschränkungen](#bekannte-einschränkungen)
12. [Gemeinsamer Laboraufbau](#gemeinsamer-laboraufbau)
13. [Weiterführende Dokumentation](#weiterführende-dokumentation)
14. [Kontakt](#kontakt)

---

## Übersicht und Zielsetzung

Der Dobot Magician kommuniziert ausschließlich über ein serielles UART-Protokoll am USB-Port und ist nicht nativ in NVIDIA Isaac Sim integriert. Ohne eine vermittelnde Softwareschicht bleibt der reale Roboterarm von seinem virtuellen Abbild getrennt.

Die Extension `Dobot_DT_IsaacSim_Extension` schließt diese Lücke. Sie liest zyklisch die Pose des realen Dobot Magician über die Bibliothek [`pydobot`](https://github.com/luismesas/pydobot) aus, berechnet daraus die Gelenkwinkel und überträgt sie über die in NVIDIA Isaac Sim integrierte Dynamic-Control-API auf die Articulation des importierten Robotermodells. Umgekehrt lassen sich über ein in Isaac Sim angedocktes HMI Steuerbefehle, Jog-Bewegungen, die Vakuumgreifer-Schaltung sowie ein Pick-and-Place-Szenario per Teach-In an die reale Hardware senden.

Damit wird zunächst ein **Digitaler Schatten** nach Kritzinger et al. realisiert, der die Gelenkzustände des physischen Dobot Magician kontinuierlich im virtuellen Modell abbildet, ergänzt um eine manuell auslösbare Fernsteuerung in Gegenrichtung.

Als Anwendungsfall dient ein Pick-and-Place-Szenario, bei dem eine zylinderförmige Schutzkappe angesaugt und auf das Heck eines Modellfahrzeugs (DeLorean, „Zurück in die Zukunft") montiert wird. Ein weißer Würfel abstrahiert dabei das anliefernde fahrerlose Transportsystem (FTS).

<p align="center">
  <img src="docs/img/Dobot_PP_Scenario_mitte.png" width="46%" alt="PnP-Szenario in Isaac Sim">
  <img src="docs/img/DobotPnPLfp.png" width="46%" alt="PnP-Szenario im Labor">
</p>
<p align="center"><em>Links: Aufbau des Szenarios in NVIDIA Isaac Sim. Rechts: identischer Aufbau im Labor für Produktentwicklung und Digitale Fabrik (LFP) der HsH.</em></p>

---

## Von ROS 2 zu pydobot

Die Kopplung an Isaac Sim wurde nicht von Anfang an über `pydobot` realisiert. Ein früherer Ansatz publizierte die Gelenkzustände des Dobot Magician über ROS 2 als `JointState`-Nachrichten und band sie über einen Action-Graph mit Articulation-Controller-Knoten in die Isaac-Sim-Szene ein. Da Isaac Sim unter Windows läuft, ROS 2 zu diesem Zeitpunkt jedoch nur unter Linux verfügbar war, musste dafür zusätzlich WSL 2 sowie das Werkzeug `usbipd-win` eingesetzt werden, um den USB-Anschluss des Dobot für WSL sichtbar zu machen. Dieser Aufbau funktionierte grundsätzlich, verursachte aber durch die Prozessgrenze zwischen WSL 2 und Isaac Sim zusätzlichen Overhead und erforderte vor jedem Start ein separates WSL-Skript.

Der spätere Umstieg auf `pydobot` vereinfachte die Inbetriebnahme erheblich, da diese Zwischenschritte vollständig entfielen. Die vorliegende, aktuelle Version der Extension verwendet **ausschließlich `pydobot`** über eine direkte USB-Verbindung, **kein ROS 2** mehr.

---

## Robotermodell

Der Dobot Magician ist ein vierachsiger Desktop-Roboterarm mit den Gelenken J1 (Basisrotation), J2 (Schulter), J3 (Ellbogen) und J4 (Drehung des Werkzeugkopfs, servomotorisch am Sauggreifer realisiert), einer maximalen Reichweite von 320 mm und einer Nutzlast von bis zu 500 g.

<p align="center"><img src="docs/img/Dobot_Gelenkwinkel.png" width="60%" alt="Gelenkwinkelkonvention"></p>
<p align="center"><em>Gelenkwinkelkonvention des Dobot Magician mit den Nullstellungen der Gelenke J1–J4.</em></p>

Im Unterarm ist zur horizontalen Ausrichtung der Werkzeugaufnahme ein **Parallelogrammgetriebe** verbaut, das unabhängig von Schulter- und Ellbogengelenk dafür sorgt, dass der Sauggreifer stets senkrecht nach unten zeigt. Dieses Getriebe bildet eine geschlossene kinematische Kette, die von Physik-Engines wie NVIDIA PhysX, die ausschließlich offene kinematische Bäume unterstützen, nicht direkt abgebildet werden kann. Es wird deshalb im URDF **nicht** modelliert:

- Die Gelenke `j1` bis `j3` werden direkt aus den empfangenen Gelenkwinkeln des realen Dobot Magician gesetzt.
- Das aktive Gelenk `j6` repräsentiert die Werkzeugaufnahme und wird rechnerisch aus `j1` bis `j3` bestimmt, um sie unabhängig von der Armkonfiguration korrekt auszurichten.
- Der Saugkopf ist als eigener Link `link_suction` modelliert, der über das Fixed Joint `joint_suction` starr mit `link_6` verbunden ist. Seine CAD-Geometrie wurde mit dem Text-to-CAD-Werkzeug Zoo Studio erstellt.
- Das physische Gelenk J4 (Werkzeugkopfdrehung) wird in der Simulation **nicht** verwendet, da für den angestrebten Digitalen Schatten die Endeffektorpose im Vordergrund steht, nicht die exakte Simulation der internen Mechanik.

<p align="center"><img src="docs/img/Dobot_after_urdf.png" width="80%" alt="Stage-Hierarchie nach URDF-Import"></p>
<p align="center"><em>Dobot Magician und resultierende Stage-Hierarchie nach dem URDF-Import in NVIDIA Isaac Sim.</em></p>

<p align="center"><img src="docs/img/aufbau_digitaler_zwilling_urdf_usd_horizontal.png" width="90%" alt="Von der URDF-Beschreibung zur USD-Szene"></p>
<p align="center"><em>Aufbau des Digitalen Zwillings von der URDF-Beschreibung zur NVIDIA-Isaac-Sim-Szene.</em></p>

---

## Sauggreifer

Als Endeffektor ist ein pneumatischer Sauggreifer montiert, bestehend aus einem Saugkopf mit Luftschlauchanschluss und einer separaten Pumpeneinheit.

<p align="center"><img src="docs/img/Sauggreifer.png" width="70%" alt="Komponenten des Sauggreifers"></p>
<p align="center"><em>Saugkopf mit Luftschlauchanschluss (links) und Pumpeneinheit mit den Anschlüssen GP1 und SW1 (rechts).</em></p>

Die Pumpe wird über die digitalen Anschlüsse **GP1** und **Switch 1 (SW1)** angesteuert. Der Servomotor (J4) sitzt oben am Unterarm und ist über **GP3** angeschlossen, dreht den unteren Teil des Endeffektors jedoch um die Z-Achse und wird in dieser Anwendung nicht über reguläre Bewegungsbefehle genutzt, sondern ausschließlich über die Low-Level-Kommandos `SetIOMultiplexing` und `SetIOPWM`, für die `pydobot` lediglich eine `set_io()`-Methode bereitstellt, die IO-Register direkt setzt, ohne die Werte in einen Servowinkel umzurechnen.

<p align="center"><img src="docs/img/Sauggreifer_Anschließen.png" width="60%" alt="Anschluss des Sauggreifers"></p>
<p align="center"><em>Verkabelung der Pumpe über GP1 und SW1 (links) sowie Anbindung des Saugkopfs über GP3 an den Servomotor J4 (rechts).</em></p>

---

## Pick-and-Place-Szenario

Die anzufahrenden Punkte werden per **Teach-In-Methode** an den Dobot übergeben und anschließend automatisiert abgefahren: Die Schutzkappe wird angesaugt, verfahren und auf dem Modellfahrzeug abgelegt. Aufgezeichnete Sequenzen laufen über einen eigenen Thread, der mittels `wait_for_cmd()` blockierend auf den Bewegungsabschluss der jeweiligen `pydobot`-Bewegung wartet, während direkte UI-Befehle wie Jog- oder Vakuumgreifer-Schaltungen ohne Rückmeldung ausgeführt werden.

---

## Datenflussstruktur der Extension

Die Datenkopplung zwischen realem Dobot Magician und NVIDIA Isaac Sim läuft vollständig über USB. Die Methodennamen der Extension folgen einer festen Namenskonvention: Mit `sim_` beginnende Methoden wirken auf die Simulation, mit `real_` beginnende Methoden auf den realen Dobot Magician.

<p align="center"><img src="docs/img/dobot_wege.png" width="100%" alt="Datenflussstruktur der Extension"></p>
<p align="center"><em>Datenflussstruktur zwischen realem Dobot Magician und NVIDIA Isaac Sim. Grün: NVIDIA Isaac Sim. Blau: Extension.</em></p>

**Pfad 1, Real → Sim (Digitaler Schatten):**

1. `_sim_updater()` wird durch das Isaac-Sim-Update-Event ausgelöst, ein Callback, das bei jedem gerenderten Simulationsframe mit rund 60 Hz aufgerufen wird, den eigentlichen Auslesepfad jedoch intern über ein Zeit-Gate auf 2 Hz drosselt.
2. `_sim_updater()` ruft `real_read_joints()` auf, welche über `pydobot` den Befehl `device.pose()` absetzt. `pydobot` überträgt diesen als `GetPose`-Kommando in hexadezimaler Darstellung über UART.
3. Der Dobot Magician antwortet mit allen Gelenkwinkeln in Grad sowie der XYZ-Koordinate des Endeffektors in Millimetern; `pydobot` bildet daraus ein Python-Tupel mit den Gelenkstellungen J1–J4.
4. `real_read_joints()` berechnet daraus die Rohwinkel für die USD-Stage und gibt sie an `_sim_updater()` zurück, die sie an `SimBridge.apply_joints()` übergibt.
5. `SimBridge.apply_joints()` rechnet die Winkel von Grad in Radiant um und schreibt sie über die Dynamic-Control-API auf die Gelenke des Dobot-Modells.

**Pfad 2, Sim/UI → Real (Steuerung):**

1. Ein Klick-Event im Dobot-HMI löst eine der `real_*`-Methoden aus, etwa für Jog-Befehle, die Vakuumgreifer-Schaltung oder das Anfahren der Home-Position.
2. Die Methode übersetzt den Aufruf über `pydobot` in einen seriellen Steuerbefehl. Der Dobot Magician fährt die Zielposition intern über inverse Kinematik an, ohne eine Rückmeldung an den Code zu senden.

Da beide Pfade parallel und unabhängig voneinander laufen, liest `real_read_joints()` im nächsten Takt stets die aktuelle Ist-Position aus, unabhängig davon, ob über Pfad 2 noch eine Bewegung läuft.

---

## Voraussetzungen

### Hardware

| Komponente | Spezifikation |
|------------|----------------|
| GPU | NVIDIA RTX-fähige GPU, für flüssige Darstellung empfohlen |
| Roboter | Dobot Magician, USB-Verbindung über bekannten COM-Port |

### Software

| Komponente | Anforderung |
|------------|----------------|
| NVIDIA Isaac Sim | Aktuelle Version mit eingebetteter Python-3.11-Laufzeitumgebung |
| Betriebssystem | Windows |
| Python-Paket | `pydobot`, installierbar in der Isaac-Sim-eigenen Python-Umgebung |

Isaac Sim bringt eine eigene, isolierte Python-Laufzeitumgebung mit, die vollständig von einer etwaigen System-Python-Installation getrennt ist. Alle Extension-Skripte laufen in dieser gebündelten Umgebung, eine separate ROS-Installation ist nicht erforderlich.

---

## Installation in Isaac Sim

1. 📁 **Extension-Pfad eintragen**: Im Extension-Manager unter *Fenster → Extensions → Zahnrad → Paths* den Ordner der Extension als Suchpfad hinzufügen, alternativ das Hilfsskript `install_extension.py` ausführen.
2. 🧩 **Extension aktivieren**: Im Extension-Manager nach `Dobot_DT_IsaacSim_Extension` suchen und aktivieren.
3. 🦾 **URDF importieren**: Beim Import des Robotermodells `Merge Fixed Joints` und `Fix Base Link` aktivieren, `Instanceable` deaktivieren.
4. 🎯 **J1-Offset kalibrieren**: `calibrate_j1_offset.py` ausführen, um die Nullstellung von Gelenk J1 an die reale Montage anzupassen.

---

## Inbetriebnahme

1. Dobot Magician über das mitgelieferte Netzteil mit Spannung versorgen und per USB an den bekannten COM-Port anschließen, anschließend einschalten.
2. Sauggreifer in die Werkzeugführung einführen und mit der mitgelieferten Schraube fixieren.
3. Servomotor an GP3, Versorgungsstecker der Vakuumpumpe an GP1 sowie an SW1 zum Schalten der Pumpe anschließen.
4. Extension starten, COM-Port auswählen und Verbindung herstellen.

---

## Projektstruktur

| Datei / Ordner | Beschreibung |
|------------------|--------------|
| 🦾 `load_dobot/` | Quellcode der Extension |
| 📐 `meshes/` | STL-Geometrien für den URDF-Import |
| 🌐 `Dobot Digital Twin.usd` | Isaac-Sim-Szene mit Dobot, DeLorean und Labortisch |
| ⚙️ `constants.py` | Zentrale Konfigurationswerte der Extension |
| 🎯 `calibrate_j1_offset.py` | Kalibrierskript für den Nullpunkt-Offset von Gelenk J1 |
| 📥 `install_extension.py` | Kopiert die Extension automatisch in das Omniverse-Erweiterungsverzeichnis |
| 📖 `documentation.tex` / `.pdf` | Technische Dokumentation, mit `build_docs.py` / `.bat` aus `documentation.tex` erzeugt |

---

## Bekannte Einschränkungen

- 🔗 **Parallelogrammgetriebe nicht modelliert**: Die geschlossene kinematische Kette des Unterarms wird nicht simuliert, `j6` wird stattdessen rechnerisch aus `j1`–`j3` bestimmt.
- 🚫 **Keine Greifer-Rückmeldung**: Saugbefehle werden über `set_io()` als Fire-and-Forget gesendet. Ob ein Objekt tatsächlich gegriffen ist, kann ohne Drucksensor nicht verifiziert werden.
- 🎚️ **J4 in der Simulation ungenutzt**: Die reale Werkzeugkopfdrehung wird für den angestrebten Digitalen Schatten nicht benötigt und deshalb nicht auf die Simulation übertragen.

---

## Gemeinsamer Laboraufbau

Im LFP teilen sich Dobot Magician und Maze-Runner-Anlage denselben Labortisch, der Dobot Magician übernimmt dabei perspektivisch Pick-and-Place-Aufgaben an der Ausgabestation des Maze Runners.

<p align="center"><img src="docs/img/tischaufbau.png" width="90%" alt="Gemeinsamer Tischaufbau"></p>
<p align="center"><em>Finaler Tischaufbau aus Dobot Magician (links) und Maze-Runner-Anlage (rechts) im LFP der Hochschule Hannover.</em></p>

---

## Weiterführende Dokumentation

- 🎞️ `Kuester_Dobot_Tutorial` — PowerPoint-Foliensatz mit 21 Folien als didaktische Schritt-für-Schritt-Anleitung zum Nachbau des Digitalen Zwillings
- 📖 Vollständige technische Dokumentation der Extension: `documentation.pdf`
- 📚 Wissenschaftlicher Kontext zu Anlage, Kinematik und Konzept: Bachelorarbeit „Entwicklung Digitaler Zwillinge für Lehrzwecke am Beispiel Maze Runner und Dobot Magician mit NVIDIA Omniverse" (Tobias Küster, Hochschule Hannover)

---

## Kontakt

**Tobias Küster**
Hochschule Hannover, Fakultät II
Matrikelnummer 1690767

Betreuung: Prof. Diersen · Prof. Vendl (Hochschule Hannover) · Dr. Yübo Wang (Hochschule Rhein-Main) · Herr Ernst
