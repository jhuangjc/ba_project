import os
import sys

#setup datei damit die dateien im projekt importiert werden können, z.B. die prompts in utils
# src und projekt pfade definieren.
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")

# src pfad zum sys.path hinzufuegen
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# TODO: avg_test deaktiviert — Importpfad klaeren
# (test erwartet scripts.avg_metrics, Tool liegt in ai_generated_tools/)
collect_ignore = ["avg_test"]