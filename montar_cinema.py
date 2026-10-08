#!/usr/bin/env python3
"""Edicao final estilo cinema: transicoes suaves (dissolves), grade de cor unica, grao, vinheta,
musica da referencia + vento ambiente, fade para preto. Saida: video_final_cinema.mp4 (1080x1920, 24fps)."""
import subprocess, sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# (arquivo, inicio, fim, transicao_de_entrada_em_segundos)
CLIPS = [
    ("clips/clip1_jade_espada_vento.mp4",            1.00, 5.04, 0.00),
    ("clips/clip2_mae_chega_ajoelha_NOVA_1080p.mp4", 0.00, 5.08, 0.12),  # continua exatamente do ultimo quadro do clipe 1
    ("clips/clip3_mae_aponta_jade_olha.mp4",         0.00, 3.60, 0.45),
    ("clips/clip4_pai_vira_e_vai_embora.mp4",        0.00, 3.00, 0.60),  # pai aparece rapido
    ("clips/clip5_mae_aponta_e_abraca.mp4",          1.00, 5.04, 0.60),  # so a parte do abraco
]
W, H, FPS = 1080, 1920, 24
GRADE = "eq=saturation=0.93:contrast=1.04:gamma=1.02,curves=all='0/0.025 0.5/0.5 1/0.985'"
inputs, filt, lens = [], [], []
for i, (f, a, b, t) in enumerate(CLIPS):
    inputs += ["-i", f]
    filt.append(f"[{i}:v]trim={a}:{b},setpts=PTS-STARTPTS,scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop={W}:{H},fps={FPS},setsar=1,{GRADE},format=yuv420p[v{i}]")
    lens.append(b - a)
cur, total = "v0", lens[0]
for i in range(1, len(CLIPS)):
    d = CLIPS[i][3]
    off = round(total - d, 3)
    filt.append(f"[{cur}][v{i}]xfade=transition=fade:duration={d}:offset={off}[x{i}]")
    cur = f"x{i}"
    total = total + lens[i] - d
total = round(total, 3)
filt.append(f"[{cur}]noise=alls=6:allf=t,vignette=PI/7,fade=t=out:st={round(total-2.0,2)}:d=2.0,format=yuv420p[vout]")
mus = len(CLIPS)
filt.append(f"[{mus}:a]afade=t=in:d=0.4,afade=t=out:st=12.9:d=2.0,volume=1.0[m]")
filt.append(f"anoisesrc=color=brown:amplitude=0.6:duration={total}:sample_rate=44100,lowpass=f=700,highpass=f=50,"
            f"tremolo=f=0.18:d=0.6,volume=0.5,afade=t=in:d=1.5,afade=t=out:st={round(total-2.5,2)}:d=2.5[w]")
filt.append(f"[m][w]amix=inputs=2:normalize=0:duration=longest,atrim=0:{total},alimiter=limit=0.95[aout]")
cmd = ["ffmpeg", "-v", "error", "-y"] + inputs + ["-i", "musica_referencia.mp3",
       "-filter_complex", ";".join(filt), "-map", "[vout]", "-map", "[aout]",
       "-c:v", "libx264", "-crf", "21", "-preset", "medium", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", str(total), "video_final_cinema.mp4"]
subprocess.run(cmd, check=True)
print("Pronto: video_final_cinema.mp4 (%ss)" % total)
