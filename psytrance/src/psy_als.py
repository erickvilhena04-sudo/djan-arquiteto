"""Gera o projeto do Ableton Live 12 (.als) com os stems no Arrangement.

Parte de um set real salvo pelo Live 12 (modelo/live-12-default.als), troca as faixas pelas faixas de audio dos
stems (cada uma com um AudioClip ja posicionado em 1.1.1), ajusta BPM, marcadores e laco.
"""
import copy
import gzip
import os
import re
import xml.etree.ElementTree as ET

import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "modelo", "live-12-default.als")
POINTEE_TAGS = {"AutomationTarget", "Pointee"}


def sub(parent, tag, value=None, **attrs):
    e = ET.SubElement(parent, tag, {k: str(v) for k, v in attrs.items()})
    if value is not None:
        e.set("Value", str(value))
    return e


def _is_pointee(e):
    return e.tag in POINTEE_TAGS or e.tag.startswith("ControllerTargets.") or e.tag.endswith("ModulationTarget")


def audio_clip(name, color, rel_path, abs_path, frames, sr, file_size, mtime, beats, secs):
    c = ET.Element("AudioClip", {"Id": "0", "Time": "0"})
    sub(c, "LomId", 0)
    sub(c, "LomIdView", 0)
    sub(c, "CurrentStart", 0)
    sub(c, "CurrentEnd", beats)
    lp = sub(c, "Loop")
    for t, v in (("LoopStart", 0), ("LoopEnd", beats), ("StartRelative", 0), ("LoopOn", "false"),
                 ("OutMarker", beats), ("HiddenLoopStart", 0), ("HiddenLoopEnd", beats)):
        sub(lp, t, v)
    sub(c, "Name", name)
    sub(c, "Annotation", "")
    sub(c, "Color", color)
    sub(c, "LaunchMode", 0)
    sub(c, "LaunchQuantisation", 0)
    ts = sub(sub(c, "TimeSignature"), "TimeSignatures")
    rts = sub(ts, "RemoteableTimeSignature", Id=0)
    sub(rts, "Numerator", 4)
    sub(rts, "Denominator", 4)
    sub(rts, "Time", 0)
    env = sub(c, "Envelopes")
    sub(env, "Envelopes")
    stp = sub(c, "ScrollerTimePreserver")
    sub(stp, "LeftTime", 0)
    sub(stp, "RightTime", beats)
    tsel = sub(c, "TimeSelection")
    sub(tsel, "AnchorTime", 0)
    sub(tsel, "OtherTime", 0)
    sub(c, "Legato", "false")
    sub(c, "Ram", "false")
    sub(sub(c, "GrooveSettings"), "GrooveId", -1)
    sub(c, "Disabled", "false")
    sub(c, "VelocityAmount", 0)
    fa = sub(c, "FollowAction")
    for t, v in (("FollowTime", 4), ("IsLinked", "true"), ("LoopIterations", 1), ("FollowActionA", 4),
                 ("FollowActionB", 0), ("FollowChanceA", 100), ("FollowChanceB", 0), ("JumpIndexA", 1),
                 ("JumpIndexB", 1), ("FollowActionEnabled", "false")):
        sub(fa, t, v)
    g = sub(c, "Grid")
    for t, v in (("FixedNumerator", 1), ("FixedDenominator", 16), ("GridIntervalPixel", 20), ("Ntoles", 2),
                 ("SnapToGrid", "true"), ("Fixed", "false")):
        sub(g, t, v)
    sub(c, "FreezeStart", 0)
    sub(c, "FreezeEnd", 0)
    sub(c, "IsWarped", "true")
    sub(c, "TakeId", 0)
    sub(c, "IsInKey", "true")
    si = sub(c, "ScaleInformation")
    sub(si, "Root", 0)
    sub(si, "Name", 0)
    sr_el = sub(c, "SampleRef")
    fr = sub(sr_el, "FileRef")
    sub(fr, "RelativePathType", 3)
    sub(fr, "RelativePath", rel_path)
    sub(fr, "Path", abs_path)
    sub(fr, "Type", 1)
    sub(fr, "LivePackName", "")
    sub(fr, "LivePackId", "")
    sub(fr, "OriginalFileSize", file_size)
    sub(fr, "OriginalCrc", 0)
    sub(sr_el, "LastModDate", mtime)
    sub(sr_el, "SourceContext")
    sub(sr_el, "SampleUsageHint", 0)
    sub(sr_el, "DefaultDuration", frames)
    sub(sr_el, "DefaultSampleRate", sr)
    sub(sr_el, "SamplesToAutoWarp", 1)
    on = sub(c, "Onsets")
    sub(on, "UserOnsets")
    sub(on, "HasUserOnsets", "false")
    for t, v in (("WarpMode", 3), ("GranularityTones", 30), ("GranularityTexture", 65), ("FluctuationTexture", 25),
                 ("TransientResolution", 6), ("TransientLoopMode", 2), ("TransientEnvelope", 100),
                 ("ComplexProFormants", 100), ("ComplexProEnvelope", 128), ("Sync", "true"), ("HiQ", "true"),
                 ("Fade", "false")):
        sub(c, t, v)
    fd = sub(c, "Fades")
    for t, v in (("FadeInLength", 0), ("FadeOutLength", 0), ("ClipFadesAreInitialized", "true"),
                 ("CrossfadeInState", 0), ("FadeInCurveSkew", 0), ("FadeInCurveSlope", 0),
                 ("FadeOutCurveSkew", 0), ("FadeOutCurveSlope", 0), ("IsDefaultFadeIn", "false"),
                 ("IsDefaultFadeOut", "false")):
        sub(fd, t, v)
    sub(c, "PitchCoarse", 0)
    sub(c, "PitchFine", 0)
    sub(c, "SampleVolume", 1)
    wm = sub(c, "WarpMarkers")
    sub(wm, "WarpMarker", Id=0, SecTime=0, BeatTime=0)
    sub(wm, "WarpMarker", Id=1, SecTime=repr(float(secs)), BeatTime=beats)
    sub(c, "SavedWarpMarkersForStretched")
    sub(c, "MarkersGenerated", "true")
    sub(c, "IsSongTempoLeader", "false")
    return c


def _renumber_pointees(track, next_id):
    mapping = {}
    for e in track.iter():
        if _is_pointee(e):
            old = int(e.attrib["Id"])
            if old in mapping:
                raise ValueError(f"Id de ponteiro duplicado em {e.tag}: {old}")
            mapping[old] = next_id
            e.attrib["Id"] = str(next_id)
            next_id += 1
    for e in track.iter("PointeeId"):
        old = int(e.attrib["Value"])
        if old not in mapping:
            raise ValueError(f"Referencia a ponteiro desconhecido: {old}")
        e.attrib["Value"] = str(mapping[old])
    return next_id


def build_als(out_path, project_dir, stems, sections, bpm, total_beats, secs, sr=44100):
    """stems: lista de (arquivo_na_pasta_Samples/Imported, nome_da_faixa, cor)."""
    with gzip.open(TEMPLATE, "rb") as f:
        root = ET.fromstring(f.read())
    ls = root.find("LiveSet")
    tracks = ls.find("Tracks")
    proto = copy.deepcopy(next(t for t in tracks if t.tag == "AudioTrack"))
    for t in [t for t in tracks if t.tag in ("AudioTrack", "MidiTrack")]:
        tracks.remove(t)
    first_return = next(i for i, t in enumerate(tracks) if t.tag == "ReturnTrack")

    next_pointee = int(ls.find("NextPointeeId").attrib["Value"])
    next_track = max([int(t.attrib["Id"]) for t in tracks] + [0]) + 1
    for i, (fname, title, color) in enumerate(stems):
        path = os.path.join(project_dir, "Samples", "Imported", fname)
        info = sf.info(path)
        t = copy.deepcopy(proto)
        t.attrib["Id"] = str(next_track)
        next_track += 1
        next_pointee = _renumber_pointees(t, next_pointee)
        nm = t.find("Name")
        nm.find("EffectiveName").set("Value", title)
        nm.find("UserName").set("Value", title)
        nm.find("MemorizedFirstClipName").set("Value", title)
        t.find("Color").set("Value", str(color))
        clip = audio_clip(
            title, color, f"Samples/Imported/{fname}", path.replace("\\", "/"), info.frames, int(info.samplerate),
            os.path.getsize(path), int(os.path.getmtime(path)), total_beats, secs)
        events = t.find("DeviceChain/MainSequencer/Sample/ArrangerAutomation/Events")
        events.append(clip)
        tracks.insert(first_return + i, t)

    ls.find("NextPointeeId").set("Value", str(next_pointee))
    tempo = ls.find("MainTrack/DeviceChain/Mixer/Tempo/Manual")
    tempo.set("Value", repr(float(bpm)))

    loc = ls.find("Locators/Locators")
    for i, (beat, name) in enumerate(sections):
        lc = sub(loc, "Locator", Id=i)
        sub(lc, "LomId", 0)
        sub(lc, "Time", beat)
        sub(lc, "Name", name)
        sub(lc, "Annotation", "")
        sub(lc, "IsSongStart", "false")

    tp = ls.find("Transport")
    tp.find("LoopStart").set("Value", "0")
    tp.find("LoopLength").set("Value", str(total_beats))
    tp.find("LoopOn").set("Value", "false")

    ET.indent(root, space="\t")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"
    with gzip.GzipFile(out_path, "wb", compresslevel=9, mtime=0) as f:
        f.write(xml.encode("utf-8"))
    return xml


def validate(als_path, schema_path):
    """Checagens estruturais: XML valido, IDs unicos, arquivos existem, tags/relacoes conhecidas pelo esquema do Live 12."""
    import json
    problems = []
    with gzip.open(als_path, "rb") as f:
        root = ET.fromstring(f.read())
    schema = json.load(open(schema_path))["element_catalog"]
    seen = {}
    for parent in root.iter():
        for child in parent:
            if child.tag not in schema:
                problems.append(f"tag desconhecida no esquema: {child.tag} (em {parent.tag})")
            elif parent.tag not in schema[child.tag]["parents"]:
                problems.append(f"relacao nao vista no esquema: {parent.tag} > {child.tag}")
        if _is_pointee(parent) and "Id" in parent.attrib:
            pid = parent.attrib["Id"]
            if pid in seen:
                problems.append(f"Id de ponteiro repetido: {pid} ({parent.tag} e {seen[pid]})")
            seen[pid] = parent.tag
    nxt = int(root.find("LiveSet/NextPointeeId").attrib["Value"])
    if seen and max(int(k) for k in seen) >= nxt:
        problems.append("NextPointeeId nao e maior que todos os Ids")
    ids = [t.attrib["Id"] for t in root.find("LiveSet/Tracks")]
    if len(ids) != len(set(ids)):
        problems.append(f"Ids de faixa repetidos: {ids}")
    return problems, len(seen)
