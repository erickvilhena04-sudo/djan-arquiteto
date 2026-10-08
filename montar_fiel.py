#!/usr/bin/env python3
"""Filme fluido (9:16, ~16s): nenhum corte seco, nenhuma tinta. Todas as passagens sao dissolves longos com curva suave (smoothstep),
sem zoom, sem seta, sem circulo. Jade sozinha + alguem passa -> a mae chega e ajoelha -> aponta -> o pai aparece e parte
-> plano aberto completo -> abraco completo -> luz quente.
Saida: env SAIDA (padrao video_final_fluido.mp4)."""
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
GRADE = ("eq=saturation=0.93:contrast=1.05:gamma=1.02,colorbalance=rs=-0.015:bs=0.02:rh=0.02:bh=-0.015,"
         "curves=all='0/0.025 0.5/0.5 1/0.985'")
NOVO = "clips/inicio_novo/"
ABRE = NOVO + "n10193_inicioA_jade_espada.mp4"          # Jade identica (Seedream 5 Pro + Kling 2.5), alguem passa no fim
CHEGA = os.environ.get("CHEGA", "clips/clip2_mae_chega_ajoelha_NOVA_1080p.mp4")
CHEGA_INI = float(os.environ.get("CHEGA_INI", "1.45"))
LONGE = os.environ.get("LONGE", NOVO + "n23787_completo_b.mp4")
HUG = os.environ.get("HUG", NOVO + "n23786_completo_a.mp4")

# (rotulo, arquivo, ini, fim, velocidade, transicao_de_entrada_em_s [0 = corte seco coberto], push-in (z0, z1, fx, fy) ou None)
B2 = "clips/fiel/b2_mae_se_inclina.mp4"      # Space, painel 6: mae ajoelhada encosta a testa na da Jade (rostos reais)
C2 = "clips/fiel/c2_aponta_leao.mp4"          # Space, painel 6: aponta, a mao entrega o leaozinho, abraco
CLIPS = [
    ("abre",   ABRE,                                    0.00, 4.40, 1.00, 0.00, None),   # Jade sozinha, alguem passa (so um pedaco)
    ("b2",     B2,                                      0.50, 2.90, 1.00, 0.80, None),   # a mae ajoelhada ao lado dela
    ("c2a",    C2,                                      0.00, 2.50, 1.00, 0.50, None),   # aponta e a mao entrega o leaozinho
    ("pai",    "clips/clip4_pai_vira_e_vai_embora.mp4", 0.00, 2.00, 1.00, 0.70, None),   # o pai olha, vira e parte
    ("longe",  LONGE,                                   0.00, 5.04, 1.00, 0.80, None),   # take COMPLETO
    ("c2b",    C2,                                      2.50, 5.04, 0.75, 0.90, None),   # volta ao mesmo take: abraco com o leaozinho
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
    ease = "A*(1-(3*P*P-2*P*P*P))+B*(3*P*P-2*P*P*P)"                 # dissolve com partida e chegada suaves
    filt.append(f"[{cur}][v{i}]xfade=transition=custom:expr='{ease}':duration={round(e / FPS, 4)}:offset={round((T - e) / FPS, 4)}[x{i}]")
    starts[CLIPS[i][0]] = (T - e) / FPS
    T = T + nfs[i] - e
    cur = f"x{i}"
total = round(T / FPS, 3)

def seq_start(name, center):         # o pico de cobertura da tinta (t=0.5) cai em 'center'
    return center - ((SEQ[name][1] - 1) / 2) / FPS

OVERLAYS = []   # nenhum rabisco

BASE = "tmp_base_fiel.mp4"
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
fade_st = round(total - 2.6, 2)
# acabamento discreto: grao, vinheta e fade para luz quente
filt2.append(f"[{cur2}]noise=alls=5:allf=t,vignette=PI/8,fade=t=out:st={fade_st}:d=2.6:color=0xF2E6CE,format=yuv420p[vout]")

mus_idx = 1 + len(OVERLAYS)
filt2.append(f"[{mus_idx}:a]afade=t=in:d=0.4,afade=t=out:st=14.0:d=0.95[m]")
filt2.append(f"anoisesrc=color=brown:amplitude=0.6:duration={total}:sample_rate=44100,lowpass=f=700,highpass=f=50,"
             f"tremolo=f=0.18:d=0.6,volume=0.45,afade=t=in:d=1.5,afade=t=out:st={fade_st}:d=2.6[w]")
filt2.append(f"[m][w]amix=inputs=2:normalize=0:duration=longest,atrim=0:{total},alimiter=limit=0.9[aout]")

SAIDA = os.environ.get("SAIDA", "video_final_fiel.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y"] + inputs2 + ["-i", "musica_referencia.mp3", "-filter_complex", ";".join(filt2),
               "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-crf", "21", "-preset", "medium", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", str(total), SAIDA], check=True)
os.remove(BASE)
print("Pronto: %s (%ss)" % (SAIDA, total))
print({k: round(v, 2) for k, v in starts.items()})
