"""Gera Psytrance_142.als a partir dos stems ja exportados."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psy_als  # noqa: E402
import psy_score as sc  # noqa: E402
import psy_synth as sy  # noqa: E402
import soundfile as sf  # noqa: E402

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJETO = os.path.join(RAIZ, "Psytrance 142 Project")
STEMS = [
    ("01_KICK.flac", "01 KICK", 69), ("02_BASS.flac", "02 BASS", 61), ("03_HATS.flac", "03 HATS", 17),
    ("04_PERC.flac", "04 PERC", 13), ("05_PAD.flac", "05 PAD", 27), ("06_ARP.flac", "06 ARP", 40),
    ("07_LEAD.flac", "07 LEAD", 9), ("08_VOCAL.flac", "08 VOCAL", 57), ("09_FX.flac", "09 FX", 1),
]


def main():
    total_beats = sc.NBARS * 4
    n = sf.info(os.path.join(PROJETO, "Samples", "Imported", STEMS[0][0])).frames
    secs = n / sy.SR
    secoes = [(bar * 4, nome) for bar, nome in sc.SECTIONS]
    out = os.path.join(PROJETO, "Psytrance_142.als")
    psy_als.build_als(out, PROJETO, STEMS, secoes, sc.BPM, total_beats, secs, sy.SR)
    print("gerado:", out, os.path.getsize(out), "bytes; duracao do stem:", round(secs, 3), "s =", total_beats, "batidas")


if __name__ == "__main__":
    main()
