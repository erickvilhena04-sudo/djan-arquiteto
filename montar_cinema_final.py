#!/usr/bin/env python3
"""Filme cinematografico (9:16, ~16s): Jade sozinha no vento -> alguem passa rapido ao lado dela (so um pedaco aparece)
-> a mae chega e ajoelha (tomada continua) -> aponta -> o pai aparece rapido e parte -> plano aberto -> abraco em luz quente.
Transicoes: tinta/giz desenhados em HTML (rabiscos/out), dissolves longos onde ha continuidade, push-ins lentos, grade de cor
de cinema, brilho suave (bloom), grao e vinheta. Duas passagens de ffmpeg (base e acabamento).
Antes: (cd rabiscos && NODE_PATH=$(npm root -g):/opt/node-tools/node_modules node render.js)
Saida: env SAIDA (padrao video_final_cinema_16s.mp4)."""
import os, subprocess
os.chdir(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 24

def normaliza_rabiscos():
    """O Chromium salva os quadros 100% opacos como RGB (sem alfa): o ffmpeg troca de formato no meio da sequencia
    e perde/duplica quadros da tinta (piscada). Regrava tudo como RGBA."""
    import glob
    from PIL import Image
    for f in glob.glob("rabiscos/out/*.png"):
        im = Image.open(f)
        if im.mode != "RGBA":
            im.convert("RGBA").save(f)
normaliza_rabiscos()
# grade de cinema: sombras levemente azul-petroleo, altas luzes quentes, contraste suave, pretos levantados
GRADE = ("eq=saturation=0.92:contrast=1.06:gamma=1.02,colorbalance=rs=-0.025:gs=0.0:bs=0.03:rh=0.03:gh=0.005:bh=-0.025,"
         "curves=all='0/0.025 0.5/0.5 1/0.985'")
NOVO = "clips/inicio_novo/"
ABRE = NOVO + "n10193_inicioA_jade_espada.mp4"          # Jade identica (Seedream 5 Pro + Kling 2.5), alguem passa no fim
CHEGA = os.environ.get("CHEGA", "clips/clip2_mae_chega_ajoelha_NOVA_1080p.mp4")
CHEGA_INI = float(os.environ.get("CHEGA_INI", "1.30"))
LONGE = os.environ.get("LONGE", NOVO + "n10192_pai_vai_embora_acolhe.mp4")

# (rotulo, arquivo, ini, fim, velocidade, transicao_de_entrada_em_s [0 = corte seco coberto], push-in (z0, z1, fx, fy) ou None)
CLIPS = [
    ("abre",   ABRE,                                    0.70, 3.00, 1.00, 0.00, (1.00, 1.05, 0.42, 0.30)),   # a Jade e o vento
    ("passa",  ABRE,                                    3.00, 5.04, 1.30, 0.00, (1.05, 1.09, 0.42, 0.30)),   # passa rapido: so um pedaco
    ("chega",  CHEGA,                                   CHEGA_INI, 4.20, 1.00, 0.00, None),                   # a mae chega inteira, sem corte
    ("aponta", "clips/clip8_novo_close_refeito.mp4",    0.00, 1.20, 0.75, 0.00, None),
    ("pai",    "clips/clip4_pai_vira_e_vai_embora.mp4", 0.00, 2.00, 1.00, 0.00, None),                       # aparicao rapida
    ("longe",  LONGE,                                   0.45, 2.85, 1.00, 0.50, (1.00, 1.06, 0.28, 0.62)),   # o pai cruza o quadro, rapido
    ("abraco", "clips/clip8_novo_close_refeito.mp4",    1.25, 4.85, 0.90, 0.00, None),                       # fecha em luz quente
]
SEQ = {
    "inkA": ("rabiscos/out/inkA_%03d.png", 19), "inkB": ("rabiscos/out/inkB_%03d.png", 24),
    "inkC": ("rabiscos/out/inkC_%03d.png", 12), "inkD": ("rabiscos/out/inkD_%03d.png", 22),
    "ring": ("rabiscos/out/ring_%03d.png", 17), "arrow": ("rabiscos/out/arrow_%03d.png", 13),
}

inputs, filt, nfs, starts = [], [], [], {}
for i, (rot, f, a, b, sp, t, push) in enumerate(CLIPS):
    inputs += ["-ss", str(a), "-t", str(round(b - a, 3)), "-i", f]    # busca na entrada: tempo zerado no inicio do trecho
    D = round((b - a) / sp, 3)
    nf = int(round(D * FPS))                                          # quadros exatos: evita offsets do xfade passarem do fim do clipe
    nfs.append(nf)
    if push:
        z0, z1, fx, fy = push
        q = f"(0.5-0.5*cos(PI*min(t/{D}\\,1)))"                        # entra e sai suave
        z = f"({z0}+({z1}-{z0})*{q})"
        sc = (f"scale=w='trunc(iw*max({W}/iw\\,{H}/ih)*{z}/2)*2':h='trunc(ih*max({W}/iw\\,{H}/ih)*{z}/2)*2':eval=frame:flags=lanczos,"
              f"crop={W}:{H}:x='clip({fx}*(iw-{W})\\,0\\,iw-{W})':y='clip({fy}*(ih-{H})\\,0\\,ih-{H})'")
    else:
        sc = f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}"
    filt.append(f"[{i}:v]setpts=(PTS-STARTPTS)/{sp},{sc},fps={FPS},settb=1/{FPS},setsar=1,{GRADE},format=yuv420p,"
                f"tpad=stop_mode=clone:stop_duration=0.6,trim=end_frame={nf},setpts=PTS-STARTPTS[v{i}]")
cur, T = "v0", nfs[0]
starts[CLIPS[0][0]] = 0.0
for i in range(1, len(CLIPS)):
    d = CLIPS[i][5]
    e = max(1, int(round(d * FPS)))          # corte seco = transicao de 1 quadro (evita problemas de concat apos xfade)
    filt.append(f"[{cur}][v{i}]xfade=transition=fade:duration={round(e / FPS, 4)}:offset={round((T - e) / FPS, 4)}[x{i}]")
    starts[CLIPS[i][0]] = (T - e) / FPS
    T = T + nfs[i] - e
    cur = f"x{i}"
total = round(T / FPS, 3)

def seq_start(name, center):         # o pico de cobertura da tinta (t=0.5) cai em 'center'
    return center - ((SEQ[name][1] - 1) / 2) / FPS

OVERLAYS = [  # (sequencia, tempo de inicio)
    ("inkC",  seq_start("inkC", starts["chega"])),
    ("inkA",  seq_start("inkA", starts["aponta"])),
    ("arrow", starts["aponta"] + 0.65),
    ("inkB",  seq_start("inkB", starts["pai"])),
    ("ring",  starts["pai"] + 0.62),
    ("inkD",  seq_start("inkD", starts["abraco"])),
]

BASE = "tmp_base_cinema.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(filt), "-map", f"[{cur}]",
                "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", "-t", str(total), BASE], check=True)

inputs2 = ["-i", BASE]
filt2 = []
cur2 = "0:v"
for j, (name, st) in enumerate(OVERLAYS):
    pat, nf = SEQ[name]
    inputs2 += ["-framerate", str(FPS), "-start_number", "0", "-i", pat]
    k = 1 + j
    filt2.append(f"[{k}:v]format=rgba,tpad=start_duration={round(max(st, 0.0), 3)}:start_mode=add:color=0x00000000,fps={FPS},setpts=N/({FPS}*TB)[ov{j}]")
    filt2.append(f"[{cur2}][ov{j}]overlay=eof_action=pass:format=auto[o{j}]")
    cur2 = f"o{j}"
fade_st = round(total - 3.0, 2)
# bloom suave (altas luzes brilham), grao, vinheta e fade para luz quente
filt2.append(f"[{cur2}]split[bA][bB];[bB]gblur=sigma=22,eq=brightness=-0.06:contrast=1.1[bBl];[bA][bBl]blend=c0_mode=screen:c0_opacity=0.20:c1_opacity=0:c2_opacity=0,"
             f"noise=alls=6:allf=t,vignette=PI/7,fade=t=out:st={fade_st}:d=3.0:color=0xF2E6CE,format=yuv420p[vout]")

mus_idx = 1 + len(OVERLAYS)
cB = starts["pai"]; cD = starts["abraco"]; cA = starts["aponta"]; cC = starts["chega"]; cP = starts["passa"]
filt2.append(f"[{mus_idx}:a]afade=t=in:d=0.4,volume='if(between(t,{round(cB-0.9,2)},{round(cB+0.05,2)}),0.10,1)':eval=frame,afade=t=out:st=14.0:d=0.95[m]")
filt2.append(f"anoisesrc=color=brown:amplitude=0.6:duration={total}:sample_rate=44100,lowpass=f=700,highpass=f=50,"
             f"tremolo=f=0.18:d=0.6,volume=0.45,afade=t=in:d=1.5,afade=t=out:st={fade_st}:d=3.0[w]")
def ms(x): return max(0, int(x * 1000))
def whoosh(label, center, vol):       # pincelada: ruido rosa em crescendo ate o pico da tinta
    filt2.append(f"anoisesrc=color=pink:amplitude=0.5:duration=1.1:sample_rate=44100,highpass=f=1500,lowpass=f=7000,"
                 f"afade=t=in:d=0.5,afade=t=out:st=0.55:d=0.55,volume={vol},adelay={ms(center-0.5)}|{ms(center-0.5)}[{label}]")
whoosh("wc", cC, 0.26); whoosh("wa", cA, 0.22); whoosh("wb", cB, 0.34); whoosh("wd", cD, 0.3)
filt2.append(f"aevalsrc='0.9*sin(2*PI*52*t)*exp(-2.6*t)+0.5*sin(2*PI*36*t)*exp(-1.6*t)':d=3:s=44100,adelay={ms(cB)}|{ms(cB)}[boomB]")
filt2.append(f"aevalsrc='0.7*sin(2*PI*46*t)*exp(-3.2*t)':d=2:s=44100,adelay={ms(cD)}|{ms(cD)},volume=0.7[boomD]")
filt2.append(f"aevalsrc='0.45*sin(2*PI*60*t)*exp(-5*t)':d=1:s=44100,adelay={ms(cA)}|{ms(cA)}[boomA]")
filt2.append(f"aevalsrc='0.5*sin(2*PI*48*t)*exp(-4*t)':d=1:s=44100,adelay={ms(cC)}|{ms(cC)}[boomC]")
# passo pesado, rapido, ao lado da Jade (o pedaco de armadura que cruza o quadro)
filt2.append(f"anoisesrc=color=brown:amplitude=0.7:duration=1.4:sample_rate=44100,lowpass=f=400,highpass=f=60,"
             f"afade=t=in:d=0.6,afade=t=out:st=0.8:d=0.6,volume=0.5,adelay={ms(cP+0.2)}|{ms(cP+0.2)}[pass]")
filt2.append(f"sine=f=42:d={total}:sample_rate=44100,volume=0.09,afade=t=in:st={round(cB,2)}:d=1.5,afade=t=out:st={fade_st}:d=3.0[drone]")
filt2.append(f"[m][w][wc][wa][wb][wd][boomA][boomB][boomC][boomD][pass][drone]amix=inputs=12:normalize=0:duration=longest,atrim=0:{total},alimiter=limit=0.9[aout]")

SAIDA = os.environ.get("SAIDA", "video_final_cinema_16s.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y"] + inputs2 + ["-i", "musica_referencia.mp3", "-filter_complex", ";".join(filt2),
               "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-crf", "21", "-preset", "medium", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", str(total), SAIDA], check=True)
os.remove(BASE)
print("Pronto: %s (%ss)" % (SAIDA, total))
print({k: round(v, 2) for k, v in starts.items()})
