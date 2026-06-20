import sys
import json
import os
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"

def call_claude(system: str, user: str) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": user}],
        system=system,
    )
    return response.content[0].text.strip()

def klingt_nach_diktat(text: str) -> bool:
    """Erkennt ob der Text nach gesprochenem Diktat klingt."""
    fuellwoerter = ["also", "ähm", "äh", "irgendwie", "sozusagen", "quasi",
                    "halt", "mal", "eigentlich", "nämlich", "sozusagen"]
    text_lower = text.lower()
    treffer = sum(1 for w in fuellwoerter if w in text_lower)
    # Feuert wenn: mindestens 2 Füllwörter ODER kein Satzzeichen am Ende
    return treffer >= 2 or (len(text) > 50 and not text.rstrip().endswith((".", "?", "!")))

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
    data = json.load(sys.stdin)
    rohtext = data.get("prompt", "")

    if not klingt_nach_diktat(rohtext):
        # Kein Diktat erkannt – Text unverändert durchlassen
        print(json.dumps({"prompt": rohtext}))
        return

    try:
        text = stage1_wissenschaftlichung(rohtext)
        text = stage2_humanisierung(text)
        text = stage3_anschluss(text)
        print(json.dumps({"prompt": text}))
    except Exception as e:
        # Bei Fehler: Original durchlassen, nicht blockieren
        sys.stderr.write(f"Pipeline-Fehler: {e}\n")
        print(json.dumps({"prompt": rohtext}))

if __name__ == "__main__":
    main()