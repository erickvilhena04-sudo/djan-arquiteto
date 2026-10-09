"""Exporta a partitura como arquivos MIDI (um por faixa + um com todas as faixas e marcadores)."""
import mido

from psy_score import BPM, SECTIONS, build_score, fx_midi_events

PPQ = 480
TRACK_FILES = [
    ("01_KICK", "KICK"), ("02_BASS", "BASS"), ("03_HATS", "HATS"), ("04_PERC", "PERC"),
    ("05_PAD", "PAD"), ("06_ARP", "ARP"), ("07_LEAD", "LEAD"), ("08_VOCAL", "VOCAL"),
]


def _track_from_events(name, events):
    tr = mido.MidiTrack()
    tr.append(mido.MetaMessage("track_name", name=name, time=0))
    msgs = []
    for e in events:
        on = int(round(e[0] * PPQ))
        off = max(on + 1, int(round((e[0] + e[1]) * PPQ)))
        msgs.append((on, 1, mido.Message("note_on", note=int(e[2]), velocity=int(e[3]), channel=0)))
        msgs.append((off, 0, mido.Message("note_off", note=int(e[2]), velocity=0, channel=0)))
    msgs.sort(key=lambda m: (m[0], m[1]))  # note_off antes de note_on no mesmo tick
    last = 0
    for tick, _, m in msgs:
        m.time = tick - last
        last = tick
        tr.append(m)
    tr.append(mido.MetaMessage("end_of_track", time=0))
    return tr


def _tempo_track(with_markers):
    tr = mido.MidiTrack()
    tr.append(mido.MetaMessage("track_name", name="Tempo", time=0))
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
    tr.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    if with_markers:
        last = 0
        for bar, name in SECTIONS:
            tick = bar * 4 * PPQ
            tr.append(mido.MetaMessage("marker", text=name, time=tick - last))
            last = tick
    tr.append(mido.MetaMessage("end_of_track", time=0))
    return tr


def export_all(outdir):
    sc = build_score()
    sc["FX"] = fx_midi_events()
    names = TRACK_FILES + [("09_FX", "FX")]
    allf = mido.MidiFile(type=1, ticks_per_beat=PPQ)
    allf.tracks.append(_tempo_track(True))
    for fname, key in names:
        ev = sorted(sc[key])
        f = mido.MidiFile(type=1, ticks_per_beat=PPQ)
        f.tracks.append(_tempo_track(False))
        f.tracks.append(_track_from_events(fname, ev))
        f.save(f"{outdir}/{fname}.mid")
        allf.tracks.append(_track_from_events(fname, ev))
    allf.save(f"{outdir}/00_TODAS_AS_FAIXAS.mid")
    return {k: len(v) for k, v in sc.items()}
