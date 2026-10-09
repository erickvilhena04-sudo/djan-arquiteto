"""Partitura da faixa (Psytrance, 142 BPM, Fá maior).

Tudo em batidas (1 compasso = 4 batidas). Cada evento: (inicio, duracao, nota_midi, velocidade[, vogal]).
A estrutura (quais faixas tocam em cada bloco de 8 compassos) segue o que foi medido na referencia.
"""

BPM = 142.0
NBARS = 259
BLOCK = 8

# nome, nota do baixo, notas do pad, notas do arpejo (6 notas)
CHORDS = [
    ("F",  29, [53, 57, 60, 65], [53, 57, 60, 65, 69, 72]),
    ("C",  36, [55, 60, 64, 67], [60, 64, 67, 72, 76, 79]),
    ("Dm", 38, [53, 57, 62, 65], [62, 65, 69, 74, 77, 81]),
    ("Bb", 34, [53, 58, 62, 65], [58, 62, 65, 70, 74, 77]),
]

# K kick, B baixo, H hats/shaker, O hat aberto, P perc/clap, D pad, A arpejo, L lead, V coro, C vocal picotado
BLOCK_TRACKS = {
    1: "KHD", 2: "KHODA", 3: "KBHOPDA", 4: "KBHOPDAL", 5: "KBHOPDALV", 6: "KBHOPDALV",
    7: "DALVC",
    8: "KBHOPDAL", 9: "KBHOPDALV", 10: "KBHOPDALC", 11: "KBHODLV", 12: "KBHOPDALC", 13: "KBHOPDALVC",
    14: "DALVC",
    15: "KBHOPDAL", 16: "KBHOPDLV", 17: "KBPDAL", 18: "KBHOPDLV",
    19: "DV",
    20: "KBHDAL", 21: "KBHODALV", 22: "KBHDAL",
    23: "KBHOPDAL", 24: "KBHOPDAL", 25: "KBHOPDALC", 26: "KBHOPDALVC", 27: "KBHODLV",
    28: "KBHOPDALC", 29: "KBHOPDALVC", 30: "KBHOPDAL", 31: "KBPDAL",
    32: "DV", 33: "D",
}

SECTIONS = [
    (0, "Intro"), (8, "Intro 2"), (16, "Build 1"), (32, "Build 1b"), (48, "Break 1"),
    (56, "Drop 1"), (80, "Drop 1 - dip"), (88, "Drop 1b"), (104, "Break 2"),
    (112, "Drop 2"), (144, "Break 3"), (152, "Build 2"), (176, "Drop 3"),
    (208, "Drop 3 - dip"), (216, "Drop 3b"), (248, "Outro"), (256, "Fim"),
]

# efeitos: (tipo, compasso_inicial, n_compassos)
FX = [
    ("atmos", 0, 16), ("atmos", 144, 8), ("atmos", 248, 11),
    ("riser", 48, 8), ("riser", 104, 8), ("riser", 144, 8), ("riser", 168, 8),
    ("roll", 54, 2), ("roll", 110, 2), ("roll", 174, 2),
    ("revcrash", 55, 1), ("revcrash", 111, 1), ("revcrash", 175, 1), ("revcrash", 151, 1),
    ("impact", 56, 1), ("impact", 112, 1), ("impact", 176, 1), ("impact", 152, 1),
    ("down", 56, 2), ("down", 112, 2), ("down", 176, 2), ("down", 80, 2), ("down", 208, 2),
]

BASS_ROOTS = [29, 29, 29, 29, 29, 29, 34, 36]

# frase do lead: (batida dentro de 8 compassos, duracao, nota)
LEAD_PHRASE = [
    (0, 1.5, 69), (1.5, 0.5, 67), (2, 2, 69), (4, 1.5, 72), (5.5, 0.5, 69), (6, 2, 67),
    (8, 1.5, 67), (9.5, 0.5, 64), (10, 2, 67), (12, 2, 72), (14, 1, 69), (15, 1, 67),
    (16, 1.5, 65), (17.5, 0.5, 69), (18, 2, 74), (20, 1.5, 72), (21.5, 0.5, 69), (22, 2, 65),
    (24, 1.5, 70), (25.5, 0.5, 74), (26, 2, 77), (28, 2, 74), (30, 1, 72), (31, 1, 69),
]

ARP_A = [0, 3, 2, 3, 1, 3, 2, 3, 0, 3, 2, 3, 1, 4, 2, 5]
ARP_B = [5, 3, 4, 2, 3, 1, 2, 0, 5, 3, 4, 2, 3, 1, 4, 3]

CHOIR = {  # notas do coro por acorde
    "F": [65, 69, 72], "C": [64, 67, 72], "Dm": [62, 65, 69], "Bb": [62, 65, 70],
}
CHOP_ONSETS = [0, 1.5, 3, 4.5, 6, 7]
VOWELS = ["a", "o", "u", "e"]


def block_of(bar):
    return bar // BLOCK + 1


def tracks_in_bar(bar):
    return BLOCK_TRACKS.get(block_of(bar), "")


def chord_of(bar):
    return CHORDS[(bar // 2) % 4]


def build_score():
    sc = {k: [] for k in ("KICK", "BASS", "HATS", "PERC", "PAD", "ARP", "LEAD", "VOCAL")}
    for bar in range(NBARS):
        tr = tracks_in_bar(bar)
        b0 = bar * 4
        name, root, pad, arp = chord_of(bar)

        if "K" in tr:
            for i in range(4):
                sc["KICK"].append((b0 + i, 0.25, 36, 110))

        if "B" in tr:
            r = BASS_ROOTS[bar % 8]
            for i in range(4):
                b = b0 + i
                up = 12 if (bar % 4 == 3 and i % 2 == 1) else 0
                sc["BASS"].append((b + 0.5, 0.19, r, 110))
                sc["BASS"].append((b + 0.75, 0.19, r + up, 105))

        if "H" in tr and not (bar < 4):
            for i in range(4):
                b = b0 + i
                sc["HATS"].append((b + 0.25, 0.1, 42, 70))
                sc["HATS"].append((b + 0.75, 0.1, 42, 85))
                for s in range(4):
                    sc["HATS"].append((b + s * 0.25, 0.1, 70, 35 + (10 if s % 2 else 0)))
        if "O" in tr:
            for i in range(4):
                sc["HATS"].append((b0 + i + 0.5, 0.2, 46, 100))

        if "P" in tr:
            sc["PERC"].append((b0 + 1, 0.25, 39, 100))
            sc["PERC"].append((b0 + 3, 0.25, 39, 100))
            if bar % 2 == 1:
                for pos, p in ((0.75, 50), (1.75, 47), (2.5, 50), (3.5, 47)):
                    sc["PERC"].append((b0 + pos, 0.2, p, 70))

        if "D" in tr and bar % 2 == 0:
            for p in pad:
                sc["PAD"].append((b0, 8.0, p, 85))

        if "A" in tr:
            pat = ARP_A if bar % 2 == 0 else ARP_B
            for s in range(16):
                acc = 100 if s % 4 == 0 else (85 if s % 2 == 0 else 70)
                sc["ARP"].append((b0 + s * 0.25, 0.2, arp[pat[s]], acc))

        if "L" in tr and bar % 8 == 0:
            for (o, d, p) in LEAD_PHRASE:
                sc["LEAD"].append((b0 + o, d, p, 100))

        if "V" in tr and bar % 2 == 0:
            vow = "a" if (bar // 2) % 2 == 0 else "o"
            for p in CHOIR[name]:
                sc["VOCAL"].append((b0, 8.0, p, 80, vow))
        if "C" in tr and bar % 2 == 0:
            notes = CHOIR[name]
            for k, o in enumerate(CHOP_ONSETS):
                sc["VOCAL"].append((b0 + o, 0.4, notes[k % 3] + 12, 95, VOWELS[k % 4]))
    return sc


def fx_midi_events():
    """Gatilhos de FX como notas (para o MIDI): impact C1, riser D1, roll E1, revcrash F1, down G1, atmos A1."""
    mp = {"impact": 36, "riser": 38, "roll": 40, "revcrash": 41, "down": 43, "atmos": 45}
    out = []
    for (kind, bar, n) in FX:
        out.append((bar * 4, n * 4 - 0.1, mp[kind], 100))
    return sorted(out)
