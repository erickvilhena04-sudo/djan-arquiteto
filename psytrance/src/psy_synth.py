"""Sintese dos stems (numpy + scipy). Cada render_* devolve um array estereo (N, 2) float32."""
import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d, maximum_filter1d

from psy_score import BPM, FX, LEAD_PHRASE

SR = 44100
SPB = SR * 60.0 / BPM  # amostras por batida


def S(beat):
    return int(round(beat * SPB))


def hz(p):
    return 440.0 * 2.0 ** ((np.asarray(p, dtype=np.float64) - 69.0) / 12.0)


class Ctx:
    """Janela de render [bar0, bar1) em compassos."""

    def __init__(self, bar0, bar1):
        self.bar0, self.bar1 = bar0, bar1
        self.o = S(bar0 * 4)
        self.N = S(bar1 * 4) - self.o

    def pos(self, beat):
        return S(beat) - self.o

    def inrange(self, ev):
        b0, b1 = self.bar0 * 4, self.bar1 * 4
        return [e for e in ev if e[0] < b1 and e[0] + e[1] > b0]


# ---------------------------------------------------------------- utilidades DSP
def add(buf, start, sig, gain=1.0):
    n = len(sig)
    a, b = max(0, start), min(len(buf), start + n)
    if b <= a:
        return
    buf[a:b] += sig[a - start:b - start] * gain


def sos_biquad(kind, fc, q):
    fc = min(fc, SR * 0.45)
    w0 = 2 * np.pi * fc / SR
    cw, alpha = np.cos(w0), np.sin(w0) / (2 * q)
    if kind == "lp":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
    elif kind == "hp":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
    else:  # bp
        b = [alpha, 0.0, -alpha]
    a = [1 + alpha, -2 * cw, 1 - alpha]
    return np.array([b[0] / a[0], b[1] / a[0], b[2] / a[0], 1.0, a[1] / a[0], a[2] / a[0]])


def filt(x, kind, fc, q=0.7, order2=True):
    sos = [sos_biquad(kind, fc, q)]
    if order2:
        sos.append(sos_biquad(kind, fc, 0.7))
    return signal.sosfilt(np.array(sos), x)


def polyblep(t, dt):
    y = np.zeros_like(t)
    dtv = np.broadcast_to(dt, t.shape)
    m = t < dtv
    x = t[m] / dtv[m]
    y[m] = x + x - x * x - 1.0
    m = t > 1.0 - dtv
    x = (t[m] - 1.0) / dtv[m]
    y[m] = x * x + x + x + 1.0
    return y


def saw_osc(freq, n, ph0=0.0):
    if np.isscalar(freq):
        dt = freq / SR
        ph = (ph0 + dt * np.arange(n, dtype=np.float64)) % 1.0
    else:
        dt = np.asarray(freq, dtype=np.float64) / SR
        ph = (ph0 + np.cumsum(dt)) % 1.0
    return 2.0 * ph - 1.0 - polyblep(ph, dt), ph


_BANK_CACHE = {}


def sweep_filter(x, cutoff, kind="lp", q=2.0, nbands=12, fmin=60.0, fmax=14000.0):
    """Filtro com frequencia de corte variavel: mistura de filtros fixos em escala log."""
    key = (kind, round(q, 3), nbands, fmin, fmax)
    if key not in _BANK_CACHE:
        fcs = np.geomspace(fmin, fmax, nbands)
        _BANK_CACHE[key] = (fcs, [np.array([sos_biquad(kind, f, q), sos_biquad(kind, f, 0.7)]) for f in fcs])
    fcs, sos_list = _BANK_CACHE[key]
    lc = np.log(fcs)
    step = lc[1] - lc[0]
    xc = np.log(np.clip(cutoff, fmin, fmax))
    out = np.zeros(len(x), np.float32)
    for k in range(nbands):
        w = np.maximum(0.0, 1.0 - np.abs(xc - lc[k]) / step).astype(np.float32)
        if not w.any():
            continue
        out += w * signal.sosfilt(sos_list[k], x).astype(np.float32)
    return out


def lp16(x_lr):
    """Corte em 16 kHz (como a referencia) para ruidos e hats."""
    return signal.sosfilt(np.array([sos_biquad("lp", 16000.0, 0.7), sos_biquad("lp", 16000.0, 0.7)]), x_lr, axis=0).astype(np.float32)


def stereo(x):
    return np.stack([x, x], axis=1).astype(np.float32)


def make_ir(seconds, seed, hf=6000.0, predelay=0.012):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = []
    for _ in range(2):
        x = rng.standard_normal(n) * np.exp(-6.9 * t / seconds)
        x = filt(x, "lp", hf, 0.7, order2=False)
        x = np.concatenate([np.zeros(int(predelay * SR)), x])
        x /= np.sqrt(np.sum(x ** 2))
        out.append(x)
    return out


def reverb(x_lr, seconds, wet, seed, hf=6000.0):
    """x_lr: (N,2). Devolve seco + umido."""
    irl, irr = make_ir(seconds, seed, hf)
    N = len(x_lr)
    wl = signal.oaconvolve(x_lr[:, 0].astype(np.float64), irl)[:N]
    wr = signal.oaconvolve(x_lr[:, 1].astype(np.float64), irr)[:N]
    # IR com energia unitaria: o umido tem ~a mesma energia do seco; `wet` e a razao de amplitude
    gain = wet * 2.0
    return (x_lr + gain * np.stack([wl, wr], axis=1)).astype(np.float32)


def duck_envelope(ctx, kick_ev, depth=0.8, tau=0.07):
    g = np.ones(ctx.N, np.float32)
    k = np.arange(int(0.4 * SR)) / SR
    shape = (1.0 - depth * np.exp(-k / tau)).astype(np.float32)
    for e in kick_ev:
        s = ctx.pos(e[0])
        a, b = max(0, s), min(ctx.N, s + len(shape))
        if b > a:
            g[a:b] = np.minimum(g[a:b], shape[a - s:b - s])
    return g


def delay(x_lr, beats_l, beats_r, fb_gain):
    N = len(x_lr)
    out = x_lr.copy()
    for ch, bts in ((0, beats_l), (1, beats_r)):
        d = S(bts)
        if d < N:
            out[d:, ch] += fb_gain * x_lr[:N - d, 1 - ch]
            if 2 * d < N:
                out[2 * d:, ch] += fb_gain * fb_gain * x_lr[:N - 2 * d, ch]
    return out


# ---------------------------------------------------------------- bateria
def make_kick():
    n = int(0.26 * SR)
    t = np.arange(n) / SR
    f = 43.65 + (230.0 - 43.65) * np.exp(-t / 0.016) + 12.0 * np.exp(-t / 0.05)
    ph = 2 * np.pi * np.cumsum(f) / SR
    # cauda de sub longa (~0,19 s) que corta seco, como na referencia
    amp = np.exp(-t / 0.2) * np.clip((0.19 - t) / 0.012, 0, 1) * np.minimum(1.0, t / 0.0012)
    body = np.tanh(2.4 * np.sin(ph) * amp)
    rng = np.random.default_rng(3)
    click = filt(rng.standard_normal(n), "hp", 1800, 0.7) * np.exp(-t / 0.003) * 0.16
    y = body + click
    return (y / np.max(np.abs(y)) * 0.95).astype(np.float32)


def make_hat(kind):
    rng = np.random.default_rng({"closed": 11, "open": 12, "shaker": 13}[kind])
    if kind == "closed":
        n, dec, fc = int(0.07 * SR), 0.013, 7500
    elif kind == "open":
        n, dec, fc = int(0.24 * SR), 0.07, 6500
    else:  # "shaker": ruido em 16avos, bem presente (da brilho sem gerar pico)
        n, dec, fc = int(0.1 * SR), 0.034, 4200
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    y = filt(noise, "hp", fc, 0.9)
    env = np.exp(-t / dec) * np.minimum(1.0, t / 0.0006)
    if kind == "open":
        env *= np.clip((0.22 - t) / 0.04, 0, 1)
    y = y * env
    return (y / np.max(np.abs(y)) * 0.9).astype(np.float32)


def make_clap():
    rng = np.random.default_rng(21)
    n = int(0.28 * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    x = filt(x, "bp", 1500, 1.1, order2=False) + 0.6 * filt(x, "bp", 2900, 1.5, order2=False)
    env = np.zeros(n)
    for off in (0.0, 0.009, 0.019):
        m = t >= off
        env[m] += np.exp(-(t[m] - off) / 0.005)
    env += np.where(t >= 0.027, np.exp(-(t - 0.027) / 0.085), 0)
    y = x * env
    return (y / np.max(np.abs(y)) * 0.9).astype(np.float32)


def make_tom(p):
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    f0 = float(hz(p - 12))
    f = f0 * (1.0 + 0.9 * np.exp(-t / 0.018))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.07) * np.minimum(1.0, t / 0.001)
    return (y * 0.9).astype(np.float32)


def render_kick(ctx, ev):
    out = np.zeros(ctx.N, np.float32)
    k = make_kick()
    for e in ctx.inrange(ev):
        add(out, ctx.pos(e[0]), k, e[3] / 110.0)
    return stereo(out)


def render_hats(ctx, ev):
    out = np.zeros(ctx.N, np.float32)
    hats = {42: make_hat("closed"), 46: make_hat("open"), 70: make_hat("shaker")}
    gains = {42: 0.7, 46: 0.75, 70: 0.5}
    for e in ctx.inrange(ev):
        add(out, ctx.pos(e[0]), hats[e[2]], gains[e[2]] * e[3] / 100.0)
    # leve abertura estereo (Haas)
    l = out
    r = np.concatenate([np.zeros(18, np.float32), out[:-18]])
    return lp16(np.stack([l, r], axis=1))


def render_perc(ctx, ev):
    out = np.zeros(ctx.N, np.float32)
    clap = make_clap()
    toms = {47: make_tom(47), 50: make_tom(50)}
    for e in ctx.inrange(ev):
        s = ctx.pos(e[0])
        if e[2] == 39:
            add(out, s, clap, 0.8 * e[3] / 100.0)
        else:
            add(out, s, toms[e[2]], 0.45 * e[3] / 100.0)
    st = stereo(out)
    return lp16(reverb(st, 0.7, 0.05, 31, hf=5000.0))


# ---------------------------------------------------------------- baixo
def render_bass(ctx, ev):
    N = ctx.N
    raw = np.zeros(N, np.float32)
    sub = np.zeros(N, np.float32)
    cut = np.full(N, 150.0, np.float32)
    for e in ctx.inrange(ev):
        s = ctx.pos(e[0])
        n = S(e[0] + e[1]) - S(e[0])
        if s + n <= 0 or s >= N:
            continue
        f = float(hz(e[2]))
        t = np.arange(n) / SR
        osc, ph = saw_osc(f, n)
        env = np.minimum(1.0, t / 0.002) * np.minimum(1.0, (t[-1] - t) / 0.008 + 0.0)
        env = np.clip(env, 0, 1)
        vf = (e[3] / 127.0) ** 2
        c = 140.0 + (350.0 + 1800.0 * vf) * np.exp(-t / 0.04)
        a, b = max(0, s), min(N, s + n)
        raw[a:b] += (osc * env)[a - s:b - s]
        sub[a:b] += (np.sin(2 * np.pi * ph) * env)[a - s:b - s]
        cut[a:b] = c[a - s:b - s]
    y = sweep_filter(raw, cut, "lp", q=3.0, nbands=10, fmin=100, fmax=3000)
    y = np.tanh(1.6 * (0.75 * y + 0.9 * sub))
    return stereo(y.astype(np.float32) * 0.8)


# ---------------------------------------------------------------- sintetizadores
def _supersaw(f, n, cents, rng, vib=None):
    out = np.zeros(n)
    for c in cents:
        fv = f * 2.0 ** (c / 1200.0)
        if vib is not None:
            fv = fv * vib
        o, _ = saw_osc(fv, n, ph0=rng.random())
        out += o
    return out / len(cents)


def render_pad(ctx, ev, kick_ev):
    N = ctx.N
    rng = np.random.default_rng(41)
    L = np.zeros(N, np.float32)
    R = np.zeros(N, np.float32)
    cl, cr = [-14, -7, 0, 6, 13], [-12, -5, 2, 8, 15]
    for e in ctx.inrange(ev):
        s = ctx.pos(e[0])
        n = S(e[0] + e[1]) - S(e[0])
        f = float(hz(e[2]))
        t = np.arange(n) / SR
        env = np.minimum(1.0, t / 0.45) * np.minimum(1.0, np.maximum(0.0, (t[-1] - t)) / 0.6)
        a, b = max(0, s), min(N, s + n)
        if b <= a:
            continue
        for buf, cents in ((L, cl), (R, cr)):
            sig = _supersaw(f, n, cents, rng) * env
            buf[a:b] += sig[a - s:b - s].astype(np.float32) * 0.25
    # corte do filtro com movimento lento (periodo de 8 compassos)
    bars = (np.arange(N) + ctx.o) / SPB / 4.0
    cut = (2200.0 + 1500.0 * np.sin(2 * np.pi * bars / 8.0 - 1.2)).astype(np.float32)
    L = sweep_filter(L, cut, "lp", q=1.1, nbands=11, fmin=300, fmax=9000)
    R = sweep_filter(R, cut, "lp", q=1.1, nbands=11, fmin=300, fmax=9000)
    st = np.stack([L, R], axis=1)
    st *= duck_envelope(ctx, kick_ev, 0.75, 0.08)[:, None]
    return reverb(st, 3.0, 0.22, 51)


def render_arp(ctx, ev, kick_ev):
    N = ctx.N
    rng = np.random.default_rng(61)
    raw = np.zeros(N, np.float32)
    cut = np.full(N, 600.0, np.float32)
    for e in ctx.inrange(ev):
        s = ctx.pos(e[0])
        n = S(e[0] + e[1]) - S(e[0])
        a, b = max(0, s), min(N, s + n)
        if b <= a:
            continue
        f = float(hz(e[2]))
        t = np.arange(n) / SR
        o1, _ = saw_osc(f * 2 ** (6 / 1200), n, rng.random())
        o2, _ = saw_osc(f * 2 ** (-6 / 1200), n, rng.random())
        env = np.minimum(1.0, t / 0.001) * np.exp(-t / 0.075) * np.clip((t[-1] - t) / 0.004, 0, 1)
        bar = (e[0]) / 4.0
        sweep = 0.75 + 0.9 * ((bar % 8) / 8.0)
        acc = (e[3] / 127.0) ** 1.5
        c = (900.0 + 7000.0 * acc * np.exp(-t / 0.05)) * sweep
        raw[a:b] += ((o1 + o2) * 0.5 * env)[a - s:b - s]
        cut[a:b] = c[a - s:b - s]
    y = sweep_filter(raw, cut, "lp", q=2.2, nbands=12, fmin=200, fmax=14000)
    st = stereo(y * 0.9)
    st = delay(st, 0.75, 1.5, 0.28)
    st *= duck_envelope(ctx, kick_ev, 0.35, 0.05)[:, None]
    return reverb(st, 1.4, 0.12, 71)


def render_lead(ctx, ev, kick_ev):
    N = ctx.N
    rng = np.random.default_rng(81)
    L = np.zeros(N, np.float32)
    R = np.zeros(N, np.float32)
    cut = np.full(N, 4000.0, np.float32)
    cl, cr = [-16, -8, 0, 7, 15], [-14, -6, 3, 9, 17]
    for e in ctx.inrange(ev):
        s = ctx.pos(e[0])
        n = S(e[0] + e[1]) - S(e[0]) + int(0.12 * SR)
        a, b = max(0, s), min(N, s + n)
        if b <= a:
            continue
        f = float(hz(e[2]))
        t = np.arange(n) / SR
        dur_s = (S(e[0] + e[1]) - S(e[0])) / SR
        vib = 2.0 ** ((0.18 * np.sin(2 * np.pi * 5.6 * t) * np.clip((t - 0.25) / 0.3, 0, 1)) / 12.0)
        env = np.minimum(1.0, t / 0.012) * np.where(t < dur_s, 1.0, np.exp(-(t - dur_s) / 0.05))
        for buf, cents in ((L, cl), (R, cr)):
            sig = _supersaw(f, n, cents, rng, vib) * env
            buf[a:b] += sig[a - s:b - s].astype(np.float32) * 0.3
        cut[a:b] = (3000.0 + 6500.0 * np.exp(-t / 0.18))[a - s:b - s]
    L = sweep_filter(L, cut, "lp", q=1.3, nbands=11, fmin=400, fmax=13000)
    R = sweep_filter(R, cut, "lp", q=1.3, nbands=11, fmin=400, fmax=13000)
    st = np.stack([L, R], axis=1)
    st = delay(st, 0.75, 1.0, 0.3)
    st *= duck_envelope(ctx, kick_ev, 0.55, 0.07)[:, None]
    return reverb(st, 2.2, 0.2, 91)


# ---------------------------------------------------------------- vocais (sintese por formantes)
VOWEL_F = {
    "a": [(800, 80, 1.0), (1150, 90, 0.5), (2900, 120, 0.25)],
    "e": [(400, 70, 1.0), (1600, 80, 0.55), (2700, 120, 0.25)],
    "o": [(450, 70, 1.0), (800, 80, 0.6), (2830, 120, 0.2)],
    "u": [(325, 60, 1.0), (700, 70, 0.4), (2530, 110, 0.1)],
}


def formant_voice(f0, n, vowel, rng, vib_depth=0.28, breath=0.05, vib_delay=0.3):
    t = np.arange(n) / SR
    vib = 2.0 ** ((vib_depth * np.sin(2 * np.pi * 5.3 * t + rng.random() * 6.28)
                   * np.clip((t - vib_delay) / 0.4, 0, 1)) / 12.0)
    src, _ = saw_osc(f0 * vib, n, rng.random())
    src = signal.lfilter([0.15], [1.0, -0.85], src)
    src = src + rng.standard_normal(n) * breath
    y = np.zeros(n)
    for fc, bw, g in VOWEL_F[vowel]:
        y += g * signal.sosfilt(np.array([sos_biquad("bp", fc, fc / bw)]), src)
    return y


def render_vocal(ctx, ev, kick_ev):
    N = ctx.N
    rng = np.random.default_rng(101)
    L = np.zeros(N, np.float32)
    R = np.zeros(N, np.float32)
    for e in ctx.inrange(ev):
        s = ctx.pos(e[0])
        dur = e[1]
        long_note = dur > 2.0
        n = S(e[0] + dur) - S(e[0]) + (int(0.6 * SR) if long_note else int(0.05 * SR))
        a, b = max(0, s), min(N, s + n)
        if b <= a:
            continue
        f = float(hz(e[2]))
        vowel = e[4] if len(e) > 4 else "a"
        t = np.arange(n) / SR
        dur_s = (S(e[0] + dur) - S(e[0])) / SR
        if long_note:
            env = np.minimum(1.0, t / 0.5) * np.where(t < dur_s, 1.0, np.exp(-(t - dur_s) / 0.25))
            voices = [(-9, 0.8, 0.2), (0, 1.0, 0.5), (9, 0.8, 0.8)]  # (cents, ganho, pan)
            gain = 0.14
        else:
            env = np.minimum(1.0, t / 0.012) * np.where(t < dur_s, 1.0, np.exp(-(t - dur_s) / 0.04))
            voices = [(0, 1.0, 0.4), (12, 0.6, 0.6)]
            gain = 0.34
        for cents, g, pan in voices:
            y = formant_voice(f * 2 ** (cents / 1200.0), n, vowel, rng, vib_delay=0.3 if long_note else 0.05) * env
            if not long_note:  # consoante: ruido filtrado no ataque
                burst = filt(rng.standard_normal(n), "hp", 3500, 0.7, order2=False) * np.exp(-t / 0.012) * 0.5
                y = y + burst
            seg = y[a - s:b - s].astype(np.float32) * g * gain
            L[a:b] += seg * np.cos(pan * np.pi / 2)
            R[a:b] += seg * np.sin(pan * np.pi / 2)
    st = np.stack([L, R], axis=1)
    st *= duck_envelope(ctx, kick_ev, 0.5, 0.07)[:, None]
    st = delay(st, 0.75, 1.5, 0.25)
    return reverb(st, 3.6, 0.28, 111)


# ---------------------------------------------------------------- FX
def _noise_seg(n, seed):
    return np.random.default_rng(seed).standard_normal(n)


def render_fx(ctx, kick_ev):
    N = ctx.N
    out = np.zeros((N, 2), np.float32)
    bar_s = S(4)
    for kind, bar, nb in FX:
        s0 = ctx.pos(bar * 4)
        n = nb * bar_s
        if s0 + n + 3 * SR <= 0 or s0 >= N:
            continue
        seed = bar * 7 + nb
        if kind == "riser":
            t = np.arange(n) / n
            cutoff = 250.0 * (9000.0 / 250.0) ** t
            segs = []
            for ch in range(2):
                x = _noise_seg(n, seed + ch)
                segs.append(sweep_filter(x, cutoff, "hp", q=1.5, nbands=12, fmin=150, fmax=12000) * (t ** 2.2) * 0.5)
            f = 175.0 * (1760.0 / 175.0) ** t
            tone, _ = saw_osc(f, n)
            tone = sweep_filter(tone, 300.0 * (6000.0 / 300.0) ** t, "lp", q=1.5, nbands=10, fmin=200, fmax=8000)
            tone = tone * t ** 1.6 * 0.18
            seg = np.stack([segs[0] + tone, segs[1] + tone], axis=1).astype(np.float32)
        elif kind == "roll":
            seg = np.zeros((n, 2), np.float32)
            hit_n = int(0.12 * SR)
            tt = np.arange(hit_n) / SR
            x = _noise_seg(hit_n, 5)
            snare = (filt(x, "bp", 2200, 0.8, order2=False) * np.exp(-tt / 0.045)
                     + np.sin(2 * np.pi * 190 * tt) * np.exp(-tt / 0.03) * 0.6)
            snare = (snare / np.max(np.abs(snare))).astype(np.float32)
            t_beats, step = 0.0, 0.5
            while t_beats < nb * 4:
                prog = t_beats / (nb * 4)
                if prog > 0.5:
                    step = 0.25
                if prog > 0.75:
                    step = 0.125
                if prog > 0.9:
                    step = 0.0625
                add(seg[:, 0], S(t_beats), snare, 0.25 + 0.75 * prog)
                add(seg[:, 1], S(t_beats), snare, 0.25 + 0.75 * prog)
                t_beats += step
        elif kind == "impact":
            n = 3 * SR
            tt = np.arange(n) / SR
            boom = np.sin(2 * np.pi * np.cumsum(38.0 + 60.0 * np.exp(-tt / 0.12)) / SR) * np.exp(-tt / 0.7)
            crash = filt(_noise_seg(n, seed), "hp", 3500, 0.8) * np.exp(-tt / 0.9)
            y = (boom * 0.9 + crash * 0.3).astype(np.float32)
            seg = stereo(y)
        elif kind == "revcrash":
            tt = np.arange(n) / SR
            crash = filt(_noise_seg(n, seed), "hp", 2500, 0.8) * np.exp(-tt / 0.5)
            y = crash[::-1] * np.linspace(0.2, 1.0, n) * 0.35
            seg = stereo(y)
        elif kind == "down":
            t = np.arange(n) / n
            x = _noise_seg(n, seed)
            y = sweep_filter(x, 9000.0 * (200.0 / 9000.0) ** t, "lp", q=1.5, nbands=12, fmin=150, fmax=12000)
            y = y * (1 - t) ** 1.5 * 0.35
            seg = stereo(y)
        else:  # atmos: ruido grave + bordao
            t = np.arange(n) / SR
            x = filt(_noise_seg(n, seed), "lp", 1200, 0.9) * 0.25
            drone = sum(saw_osc(float(hz(p)), n)[0] for p in (41, 48, 53)) * 0.08
            drone = filt(drone, "lp", 700, 0.9)
            swell = np.sin(np.pi * np.arange(n) / n) ** 1.5
            lfo = 0.65 + 0.35 * np.sin(2 * np.pi * t / (S(8) / SR))
            seg = stereo(((x + drone) * swell * lfo).astype(np.float32))
        add(out[:, 0], s0, seg[:, 0])
        add(out[:, 1], s0, seg[:, 1])
    out *= duck_envelope(ctx, kick_ev, 0.3, 0.05)[:, None]
    return lp16(reverb(out, 3.2, 0.18, 121))


# ---------------------------------------------------------------- master
def limiter(x, ceiling=0.97, hold=0.004):
    peak = np.max(np.abs(x), axis=1)
    w = max(3, int(hold * SR))
    tgt = np.minimum(1.0, ceiling / np.maximum(maximum_filter1d(peak, size=w), 1e-9))
    g = uniform_filter1d(minimum_filter1d(tgt, size=w), size=w)
    g = uniform_filter1d(g, size=int(0.03 * SR))
    g = np.minimum(g, tgt)  # garante teto
    return (x * g[:, None]).astype(np.float32)


def dc_block(x):
    sos = np.array([sos_biquad("hp", 22.0, 0.7)])
    return signal.sosfilt(sos, x, axis=0).astype(np.float32)
