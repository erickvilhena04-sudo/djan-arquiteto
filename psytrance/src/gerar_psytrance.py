"""Gera a faixa completa: MIDI, stems (FLAC), mix de previa (MP3).

Uso:
    python3 gerar_psytrance.py midi   <pasta_saida>
    python3 gerar_psytrance.py render <pasta_cache>
    python3 gerar_psytrance.py master <pasta_cache> <pasta_saida> [--nivel 0.75]
"""
import argparse
import os
import subprocess
import sys
import time

import numpy as np
import soundfile as sf
from scipy import signal
from scipy.ndimage import uniform_filter1d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psy_score as sc  # noqa: E402
import psy_synth as sy  # noqa: E402
import psy_midi  # noqa: E402

PROJECT = "Psytrance 142 Project"
MONO_STEMS = {"01_KICK", "02_BASS"}
STEMS = ["01_KICK", "02_BASS", "03_HATS", "04_PERC", "05_PAD", "06_ARP", "07_LEAD", "08_VOCAL", "09_FX"]
GROUP = {"01_KICK": "low", "02_BASS": "low", "03_HATS": "hi", "04_PERC": "hi", "05_PAD": "mid",
         "06_ARP": "mid", "07_LEAD": "mid", "08_VOCAL": "mid", "09_FX": "fx"}
TRIM = {"01_KICK": 1.0, "02_BASS": 0.9, "03_HATS": 1.5, "04_PERC": 0.9, "05_PAD": 0.8, "06_ARP": 0.4,
        "07_LEAD": 1.2, "08_VOCAL": 2.0, "09_FX": 0.5}
BOUNDS = {"low": (0.03, 3.0), "mid": (0.3, 3.0), "hi": (0.3, 3.0)}

# medido na referencia: media por bloco de 8 compassos (grave 30-150 Hz, medio 150-2500 Hz, agudo 2500-10000 Hz) e RMS
REF = [
    (145.4, 638.0, 152.0, 0.127), (122.5, 1242.7, 865.5, 0.196), (409.8, 1382.1, 419.5, 0.287),
    (409.9, 1587.8, 899.9, 0.310), (425.8, 1761.7, 1289.3, 0.332), (305.9, 2259.3, 865.0, 0.319),
    (57.4, 1824.7, 1371.6, 0.225), (1302.3, 1497.7, 1041.4, 0.645), (1003.5, 1570.6, 1287.6, 0.540),
    (1297.1, 1577.2, 1545.1, 0.648), (672.2, 1705.8, 2147.3, 0.441), (1307.7, 1624.6, 2402.3, 0.663),
    (1291.3, 2203.6, 2493.0, 0.684), (178.2, 2564.4, 2708.5, 0.339), (1295.0, 1995.4, 2921.6, 0.671),
    (876.3, 1967.6, 2959.9, 0.521), (1305.3, 1464.5, 573.7, 0.644), (850.0, 2024.5, 1048.1, 0.497),
    (80.2, 1401.0, 769.1, 0.222), (327.9, 2330.4, 741.6, 0.339), (409.2, 2645.3, 1097.8, 0.380),
    (207.7, 2972.3, 1939.5, 0.359), (978.6, 1347.6, 679.6, 0.514), (1292.9, 1835.9, 865.2, 0.654),
    (1033.9, 2363.9, 1421.2, 0.585), (952.4, 2224.3, 2624.7, 0.571), (495.1, 2761.9, 2761.0, 0.449),
    (962.5, 2315.8, 2650.1, 0.578), (1271.9, 2618.1, 2942.0, 0.689), (1160.7, 1695.5, 1355.7, 0.605),
    (1130.8, 1783.4, 737.3, 0.584), (84.0, 899.6, 463.7, 0.151),
]
NBLK = len(REF)  # 32


def log(*a):
    print(*a, flush=True)


# ------------------------------------------------------------------ render
def cmd_render(cache, solo=None):
    os.makedirs(cache, exist_ok=True)
    score = sc.build_score()
    kick = score["KICK"]
    ctx = sy.Ctx(0, sc.NBARS)
    jobs = [
        ("01_KICK", lambda: sy.render_kick(ctx, kick)),
        ("02_BASS", lambda: sy.render_bass(ctx, score["BASS"])),
        ("03_HATS", lambda: sy.render_hats(ctx, score["HATS"])),
        ("04_PERC", lambda: sy.render_perc(ctx, score["PERC"])),
        ("05_PAD", lambda: sy.render_pad(ctx, score["PAD"], kick)),
        ("06_ARP", lambda: sy.render_arp(ctx, score["ARP"], kick)),
        ("07_LEAD", lambda: sy.render_lead(ctx, score["LEAD"], kick)),
        ("08_VOCAL", lambda: sy.render_vocal(ctx, score["VOCAL"], kick)),
        ("09_FX", lambda: sy.render_fx(ctx, kick)),
    ]
    for name, fn in jobs:
        if solo and name not in solo:
            continue
        t = time.time()
        x = fn().astype(np.float32)
        np.save(f"{cache}/{name}.npy", x)
        log(f"{name}: {time.time()-t:.0f}s  pico={np.abs(x).max():.2f}  rms={np.sqrt((x**2).mean()):.3f}")


# ------------------------------------------------------------------ medicao
def block_bounds(k, N):
    return min(sy.S(sc.BLOCK * 4 * k), N), min(sy.S(sc.BLOCK * 4 * (k + 1)), N)


def to22(mono):
    return signal.resample_poly(mono.astype(np.float64), 1, 2).astype(np.float32)


def metrics(mono44):
    """Mesmas medidas aplicadas na referencia: (grave, medio, agudo, rms) por bloco de 8 compassos."""
    x = to22(mono44)
    n, hop = 2048, 256
    w = np.hanning(n)
    freqs = np.fft.rfftfreq(n, 1 / 22050)
    bands = [(freqs >= 30) & (freqs < 150), (freqs >= 150) & (freqs < 2500), (freqs >= 2500) & (freqs < 10000)]
    out = []
    N = len(mono44)
    for k in range(NBLK):
        a, b = block_bounds(k, N)
        a, b = a // 2, b // 2
        seg = x[a:b]
        if len(seg) < n * 2:
            out.append((0, 0, 0, 0))
            continue
        fr = np.lib.stride_tricks.sliding_window_view(seg, n)[::hop]
        mag = np.abs(np.fft.rfft(fr * w, axis=1))
        out.append(tuple(float(mag[:, m].sum(1).mean()) for m in bands) + (float(np.sqrt((fr ** 2).mean())),))
    return out


def block_curve(vals, N):
    c = np.empty(N, np.float32)
    for k in range(len(vals)):
        a, b = block_bounds(k, N)
        if b > a:
            c[a:b] = vals[k]
    c[block_bounds(len(vals) - 1, N)[1]:] = vals[-1]
    return uniform_filter1d(c, size=sy.S(2))


def presence():
    """Quais grupos existem em cada bloco (para saber o que calibrar)."""
    pres = []
    for k in range(NBLK):
        tr = sc.BLOCK_TRACKS.get(k + 1, "")
        fx_here = any(bar < (k + 1) * 8 and bar + n > k * 8 for _, bar, n in sc.FX)
        pres.append({"low": any(c in tr for c in "KB"), "mid": any(c in tr for c in "DALVC"),
                     "hi": any(c in tr for c in "HOP")})
    return pres


def write_stem(path, x, mono):
    """FLAC 16 bits com dither triangular; kick e baixo vao em mono."""
    y = x[:, 0] if mono else x
    rng = np.random.default_rng(5)
    d = (rng.random(y.shape, dtype=np.float32) - rng.random(y.shape, dtype=np.float32)) / 32768.0
    sf.write(path, np.clip(y + d, -1.0, 1.0).astype(np.float32), sy.SR, subtype="PCM_16", format="FLAC")


# ------------------------------------------------------------------ master
def cmd_master(cache, outdir, nivel):
    os.makedirs(outdir, exist_ok=True)
    samples = f"{outdir}/{PROJECT}/Samples/Imported"
    os.makedirs(samples, exist_ok=True)
    stems = {n: np.load(f"{cache}/{n}.npy") * TRIM[n] for n in STEMS}
    N = len(stems[STEMS[0]])
    gmono = {g: sum(stems[n].mean(axis=1) for n in STEMS if GROUP[n] == g) for g in ("low", "mid", "hi")}
    fxmono = sum(stems[n].mean(axis=1) for n in STEMS if GROUP[n] == "fx")
    pres = presence()
    gains = {g: np.ones(NBLK + 1, np.float32) for g in gmono}
    target = [tuple(v * nivel for v in r[:3]) for r in REF]

    for it in range(5):
        mono = sum(block_curve(gains[g], N) * gmono[g] for g in gmono) + fxmono
        m = metrics(mono)
        err = []
        for k in range(NBLK):
            for gi, g in enumerate(("low", "mid", "hi")):
                if pres[k][g] and m[k][gi] > 1e-6:
                    ratio = (target[k][gi] / m[k][gi]) ** 0.85
                    lo, hi_ = BOUNDS[g]
                    gains[g][k] = float(np.clip(gains[g][k] * np.clip(ratio, 0.4, 2.5), lo, hi_))
                    err.append(abs(np.log(target[k][gi] / m[k][gi])))
        log(f"calibracao {it+1}: erro medio = {np.mean(err):.3f} (log)")
    gains["low"][NBLK] = gains["mid"][NBLK] = gains["hi"][NBLK] = 0.0 + 1.0

    curves = {g: block_curve(gains[g], N) for g in gains}
    final = {n: stems[n] * (curves[GROUP[n]][:, None] if GROUP[n] in curves else 1.0) for n in STEMS}
    mix = sum(final.values())
    mix = sy.dc_block(mix)
    pk = np.abs(mix).max()
    log(f"mix antes do limitador: pico={pk:.2f}")

    # limitador: mesmo ganho variavel em todos os stems, assim a soma dos stems = master
    peak = np.max(np.abs(mix), axis=1)
    w = max(3, int(0.004 * sy.SR))
    from scipy.ndimage import maximum_filter1d, minimum_filter1d
    tgt = np.minimum(1.0, 0.97 / np.maximum(maximum_filter1d(peak, size=w), 1e-9))
    g = uniform_filter1d(minimum_filter1d(tgt, size=w), size=w)
    g = np.minimum(uniform_filter1d(g, size=int(0.03 * sy.SR)), tgt).astype(np.float32)
    master = mix * g[:, None]
    log(f"reducao media do limitador: {-20*np.log10(g.mean()):.1f} dB (minimo {-20*np.log10(g.min()):.1f} dB)")

    stem_out = {n: sy.dc_block(final[n]) * g[:, None] for n in STEMS}
    mx = max(np.abs(a).max() for a in stem_out.values())
    k = min(1.0, 0.99 / mx)
    if k < 1.0:
        log(f"stem mais alto = {mx:.2f}; reduzindo tudo em {20*np.log10(k):.1f} dB")
    master *= k
    for n in STEMS:
        stem_out[n] = stem_out[n] * k
        write_stem(f"{samples}/{n}.flac", stem_out[n], n in MONO_STEMS)
    sf.write(f"{cache}/master.wav", master, sy.SR, subtype="PCM_24")
    tmp = f"{cache}/master.wav"
    # a previa ganha -2,5 dB para nao estourar na decodificacao do mp3
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", "volume=-2.5dB", "-b:a", "320k",
                    "-id3v2_version", "3", f"{outdir}/PSYTRANCE_142_previa.mp3"], check=True)

    mm = metrics(master.mean(axis=1))
    log("\nbloco | tempo  | grave(ref/mine) | medio(ref/mine) | agudo(ref/mine) | rms(ref/mine)")
    beat_s = 60.0 / sc.BPM
    for k in range(NBLK):
        t0 = k * 8 * 4 * beat_s
        r, o = REF[k], mm[k]
        log(f"{k+1:3d}   | {int(t0//60)}:{int(t0%60):02d} | {r[0]:6.0f}/{o[0]:6.0f} | {r[1]:6.0f}/{o[1]:6.0f} | "
            f"{r[2]:6.0f}/{o[2]:6.0f} | {r[3]:.2f}/{o[3]:.2f}")
    np.save(f"{cache}/gains_low.npy", gains["low"])
    np.save(f"{cache}/gains_mid.npy", gains["mid"])
    np.save(f"{cache}/gains_hi.npy", gains["hi"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["midi", "render", "master"])
    ap.add_argument("a")
    ap.add_argument("b", nargs="?")
    ap.add_argument("--nivel", type=float, default=0.75)
    ap.add_argument("--solo", nargs="*")
    args = ap.parse_args()
    if args.cmd == "midi":
        os.makedirs(args.a, exist_ok=True)
        log(psy_midi.export_all(args.a))
    elif args.cmd == "render":
        cmd_render(args.a, args.solo)
    else:
        cmd_master(args.a, args.b, args.nivel)


if __name__ == "__main__":
    main()
