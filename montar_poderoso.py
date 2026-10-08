#!/usr/bin/env python3
"""Montagem final "poderosa": historia da Jade e da Adriana com
 - plano continuo na primeira metade (dissolves curtos so onde ha continuidade),
 - cortes secos ESCONDIDOS por pinceladas de tinta + rabiscos de giz desenhados em HTML (rabiscos/),
 - seta de giz seguindo o dedo da mae, circulo de giz no rosto do pai (aparicao rapida),
 - som de pincel, impacto grave, vento e a musica da referencia, fade longo para preto.
Saida: video_final_poderoso.mp4 (1080x1920, 24fps).
Antes de rodar: (cd rabiscos && node render.js) para gerar rabiscos/out/*.png
"""
import os, subprocess
os.chdir(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 24
GRADE = "eq=saturation=0.93:contrast=1.05:gamma=1.02,curves=all='0/0.02 0.5/0.5 1/0.985'"
CHEGADA = "clips/clip2_chegada_rosto_proximo.mp4"
if not os.path.exists(CHEGADA):
    CHEGADA = "clips/clip2_mae_chega_ajoelha_NOVA_1080p.mp4"

# (rotulo, arquivo, ini, fim, velocidade, transicao_de_entrada_em_s; 0 = corte seco)
# Arco emocional: coragem (Jade com a espada) -> PROTECAO (a mae chega, inteira, sem cortes) -> AMOR (nariz com nariz, o leaozinho,
# tirar a espada, abraco) -> SACRIFICIO (o pai parte, a mae aponta) -> ESPERANCA (abraco final que se dissolve em luz quente).
CLIPS = [
    ("jade",    "clips/clip1_jade_espada_vento.mp4",                1.20, 5.04, 1.0, 0.00),
    ("chega",   "clips/clip2_mae_chega_ajoelha_NOVA_1080p.mp4",     0.00, 5.08, 1.0, 0.12),   # a mae chegando, INTEIRA e continua
    ("perto",   "clips/clip2_chegada_rosto_proximo.mp4",            0.00, 4.20, 1.0, 0.12),   # continua da mesma imagem: o rosto dela chega bem perto da Jade
    ("leao",    "clips/clip3_mae_fala_no_ouvido_e_da_o_leao.mp4",   0.00, 1.90, 1.0, 0.45),   # a mae fala no ouvido: rosto fiel
    ("leao2",   "clips/clip3_mae_fala_no_ouvido_e_da_o_leao.mp4",   3.55, 5.04, 1.0, 0.00),   # pula o trecho em que ela se abaixa (rosto diferente): corte de aproximacao na entrega do leao, abre ate o plano geral
    ("espada",  "clips/clip4_mae_tira_espada_acolhe.mp4",           0.00, 4.80, 1.0, 0.12),
    ("aponta",  "clips/clip8_close_final.mp4",                      0.00, 1.25, 0.70, 0.00),  # corte coberto pela tinta A
    ("pai",     "clips/clip4_pai_vira_e_vai_embora.mp4",            0.00, 2.40, 1.0, 0.00),   # corte coberto pela tinta B (aparicao rapida)
    ("longe",   "clips/clip6_reveal_pai_ao_longe.mp4",              0.00, 2.00, 0.90, 0.50),  # dissolve suave na neblina
    ("abraco",  "clips/clip8_close_final.mp4",                      1.25, 5.04, 0.90, 0.00),  # corte coberto pela tinta D (fecha em luz)
]
ZOOMS = {"leao2": (1.9, 0.26, 0.535)}   # rotulo -> (zoom inicial, foco x, foco y) em fracao do quadro: a Jade e o leao
# sequencias de rabiscos: (nome, arquivo-padrao, nframes)
SEQ = {
    "inkA": ("rabiscos/out/inkA_%03d.png", 19), "inkB": ("rabiscos/out/inkB_%03d.png", 24),
    "inkD": ("rabiscos/out/inkD_%03d.png", 22),
    "ring": ("rabiscos/out/ring_%03d.png", 17), "arrow": ("rabiscos/out/arrow_%03d.png", 13),
}

inputs, filt, durs, starts = [], [], [], {}
for i, (rot, f, a, b, sp, t) in enumerate(CLIPS):
    inputs += ["-i", f]
    durs.append((b - a) / sp)
    zoom = ""
    if rot in ZOOMS:                         # aproximacao que abre devagar ate o plano geral (o rosto so volta no fim)
        Z0, fx, fy = ZOOMS[rot]
        D = round((b - a) / sp, 3)
        q = f"pow(min(t/{D},1),2.4)"
        zoom = (f"scale=w='trunc({W}*(1+{Z0-1}*(1-{q}))/2)*2':h='trunc({H}*(1+{Z0-1}*(1-{q}))/2)*2':eval=frame:flags=bicubic,"
                f"crop={W}:{H}:x='clip(({0.5}+({fx}-0.5)*(1-{q}))*iw-{W}/2,0,iw-{W})':y='clip(({0.5}+({fy}-0.5)*(1-{q}))*ih-{H}/2,0,ih-{H})',"
                f"unsharp=5:5:0.6,setsar=1,")
    filt.append(f"[{i}:v]trim={a}:{b},setpts=(PTS-STARTPTS)/{sp},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop={W}:{H},fps={FPS},settb=1/{FPS},setsar=1,{zoom}{GRADE},format=yuv420p[v{i}]")
cur, total = "v0", durs[0]
starts[CLIPS[0][0]] = 0.0
for i in range(1, len(CLIPS)):
    d = CLIPS[i][5]
    if d > 0:
        filt.append(f"[{cur}][v{i}]xfade=transition=fade:duration={d}:offset={round(total - d, 3)}[x{i}]")
        starts[CLIPS[i][0]] = total - d
        total = total + durs[i] - d
    else:                                   # corte seco = transicao de 1 quadro (evita problemas de concat apos xfade)
        e = 1.0 / FPS
        filt.append(f"[{cur}][v{i}]xfade=transition=fade:duration={round(e, 4)}:offset={round(total - e, 4)}[x{i}]")
        starts[CLIPS[i][0]] = total - e
        total = total + durs[i] - e
    cur = f"x{i}"
total = round(total, 3)

def seq_start(name, center):         # o pico de cobertura da tinta (t=0.5) cai em 'center'
    n = SEQ[name][1]
    return center - ((n - 1) / 2) / FPS

OVERLAYS = [  # (sequencia, tempo de inicio)
    ("inkA",  seq_start("inkA", starts["aponta"])),
    ("arrow", starts["aponta"] + 0.65),
    ("inkB",  seq_start("inkB", starts["pai"])),
    ("ring",  starts["pai"] + 0.62),
    ("inkD",  seq_start("inkD", starts["abraco"])),
]

# ---------- passagem 1: base (clipes + dissolves/cortes), visualmente sem perdas ----------
BASE = "tmp_base.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(filt), "-map", f"[{cur}]",
                "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-pix_fmt", "yuv420p", "-t", str(total), BASE], check=True)

# ---------- passagem 2: rabiscos + granulacao + vinheta + fade para luz + audio ----------
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
filt2.append(f"[{cur2}]noise=alls=6:allf=t,vignette=PI/7,fade=t=out:st={fade_st}:d=3.0:color=0xF2E6CE,format=yuv420p[vout]")

mus_idx = 1 + len(OVERLAYS)
cB = starts["pai"]; cD = starts["abraco"]; cA = starts["aponta"]
filt2.append(f"[{mus_idx}:a]afade=t=in:d=0.4,volume='if(between(t,{round(cB-0.9,2)},{round(cB+0.05,2)}),0.10,1)':eval=frame,afade=t=out:st=14.0:d=0.95[m]")
filt2.append(f"anoisesrc=color=brown:amplitude=0.6:duration={total}:sample_rate=44100,lowpass=f=700,highpass=f=50,"
             f"tremolo=f=0.18:d=0.6,volume=0.45,afade=t=in:d=1.5,afade=t=out:st={fade_st}:d=3.0[w]")
def ms(x): return max(0, int(x * 1000))
def whoosh(label, center, vol):       # pincelada: ruido rosa em crescendo ate o pico da tinta
    filt2.append(f"anoisesrc=color=pink:amplitude=0.5:duration=1.1:sample_rate=44100,highpass=f=1500,lowpass=f=7000,"
                 f"afade=t=in:d=0.5,afade=t=out:st=0.55:d=0.55,volume={vol},adelay={ms(center-0.5)}|{ms(center-0.5)}[{label}]")
whoosh("wa", cA, 0.22); whoosh("wb", cB, 0.34); whoosh("wd", cD, 0.3)
filt2.append(f"aevalsrc='0.9*sin(2*PI*52*t)*exp(-2.6*t)+0.5*sin(2*PI*36*t)*exp(-1.6*t)':d=3:s=44100,adelay={ms(cB)}|{ms(cB)}[boomB]")
filt2.append(f"aevalsrc='0.7*sin(2*PI*46*t)*exp(-3.2*t)':d=2:s=44100,adelay={ms(cD)}|{ms(cD)},volume=0.7[boomD]")
filt2.append(f"aevalsrc='0.45*sin(2*PI*60*t)*exp(-5*t)':d=1:s=44100,adelay={ms(cA)}|{ms(cA)}[boomA]")
filt2.append(f"sine=f=42:d={total}:sample_rate=44100,volume=0.09,afade=t=in:st={round(cB,2)}:d=1.5,afade=t=out:st={fade_st}:d=3.0[drone]")
filt2.append(f"[m][w][wa][wb][wd][boomA][boomB][boomD][drone]amix=inputs=9:normalize=0:duration=longest,atrim=0:{total},alimiter=limit=0.9[aout]")

SAIDA = os.environ.get("SAIDA", "video_final_poderoso.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y"] + inputs2 + ["-i", "musica_referencia.mp3", "-filter_complex", ";".join(filt2),
               "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-crf", "21", "-preset", "medium", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", str(total), SAIDA], check=True)
os.remove(BASE)
print("Pronto: %s (%ss)" % (SAIDA, total))
print({k: round(v, 2) for k, v in starts.items()})
