import sys
import json
import io
import logging

# Log-Datei für Diagnose - auch wenn Claude Code keine Antwort gibt
logging.basicConfig(
    filename=r'c:\Bachelorarbeit\hook_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Windows: stdin/stdout auf UTF-8 zwingen
if hasattr(sys.stdin, 'buffer'):
    sys.stdin  = io.TextIOWrapper(sys.stdin.buffer,  encoding='utf-8')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

logging.debug("Hook gestartet")

try:
    import anthropic
    logging.debug("anthropic importiert")
    client = anthropic.Anthropic()
    MODEL = "claude-sonnet-4-6"
except Exception as e:
    logging.error(f"Import/Init fehlgeschlagen: {e}")
    client = None

def call_claude(system: str, user: str) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": user}],
        system=system,
        timeout=30.0,
    )
    return response.content[0].text.strip()

def klingt_nach_diktat(text: str) -> bool:
    fuellwoerter = ["ähm", "äh", "irgendwie", "sozusagen", "quasi", "halt", "eigentlich", "nämlich"]
    text_lower = text.lower()
    treffer = sum(1 for w in fuellwoerter if w in text_lower)
    return treffer >= 2

def stage1_wissenschaftlichung(text: str) -> str:
    system = """Du bist ein wissenschaftlicher Lektor für deutschsprachige Ingenieurwissenschaften.
Wandle den folgenden, grob gesprochenen oder diktierten Rohtext in einen präzisen,
akademischen Fließtext um. Behalte den Inhalt vollständig, füge aber nichts hinzu.
Gib nur den überarbeiteten Text zurück, ohne Kommentare."""
    return call_claude(system, text)

def stage2_humanisierung(text: str) -> str:
    system = """Du bist ein stilistischer Lektor für wissenschaftliche Texte.
Überarbeite nach diesen Regeln:
- Keine Bindestriche als Gedankenstriche, keine Doppelpunkte mitten im Satz, keine Semikolons
- Keine KI-Floskeln: 'es ist wichtig zu betonen', 'hervorzuheben ist', 'spielt eine entscheidende Rolle'
- Maximal 1 Adjektiv pro Nominalgruppe
- Aktive, direkte Sätze
- Wissenschaftlicher Ton bleibt erhalten
Gib nur den überarbeiteten Text zurück, ohne Kommentare."""
    return call_claude(system, text)

def stage3_anschluss(text: str) -> str:
    system = """Du bist ein Lektor für wissenschaftliche Texte.
Prüfe ob der Text einen sauberen Einstieg hat und am Ende eine natürliche Überleitung enthält.
Passe minimal an wenn nötig. Gib nur den Text zurück."""
    return call_claude(system, text)

def main():
    raw = sys.stdin.read()
    logging.debug(f"stdin gelesen: {repr(raw[:100])}")

    try:
        data = json.loads(raw)
    except Exception as e:
        logging.error(f"JSON-Parse fehlgeschlagen: {e}")
        print(raw, end='')
        return

    rohtext = data.get("prompt", "")
    logging.debug(f"Prompt: {repr(rohtext[:80])}")

    if not klingt_nach_diktat(rohtext):
        logging.debug("Kein Diktat erkannt – durchlassen")
        print(json.dumps({"prompt": rohtext}, ensure_ascii=False))
        return

    logging.debug("Diktat erkannt – starte Pipeline")

    if client is None:
        logging.error("anthropic nicht verfügbar – Original durchlassen")
        print(json.dumps({"prompt": rohtext}, ensure_ascii=False))
        return

    try:
        text = stage1_wissenschaftlichung(rohtext)
        text = stage2_humanisierung(text)
        text = stage3_anschluss(text)
        logging.debug("Pipeline erfolgreich")
        print(json.dumps({"prompt": text}, ensure_ascii=False))
    except Exception as e:
        logging.error(f"Pipeline-Fehler: {e}")
        print(json.dumps({"prompt": rohtext}, ensure_ascii=False))

if __name__ == "__main__":
    main()
