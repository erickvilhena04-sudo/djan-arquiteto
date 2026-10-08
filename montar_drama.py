#!/usr/bin/env python3
"""Montagem dramatica: plano continuo (Jade -> mae chega -> beijo/abraco), depois pausa de silencio,
CORTE SECO com impacto grave, plano aberto do pai indo embora em camera lenta, corte para o push-in na mae e na Jade,
fade longo. Saida: video_final_drama.mp4 (1080x1920, 24fps)."""
import subprocess, os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 24
GRADE = "eq=saturation=0.93:contrast=1.05:gamma=1.02,curves=all='0/0.02 0.5/0.5 1/0.985'"
# (arquivo, ini, fim, velocidade(1=normal, 0.8=camera lenta), transicao_entrada_em_s; 0 = corte seco)
CLIPS = [
    ("clips/clip1_jade_espada_vento.mp4",                 1.40, 5.04, 1.0, 0.00),
    ("clips/clip2_mae_chega_ajoelha_NOVA_1080p.mp4",      0.00, 4.70, 1.0, 0.12),
    ("clips/clip5_mae_fala_no_ouvido_beija_abraca.mp4",   0.00, 4.40, 1.0, 0.12),
    ("clips/clip6_reveal_pai_ao_longe.mp4",               0.00, 2.60, 0.80, 0.00),   # CORTE SECO + camera lenta
    ("clips/clip7_pushin_mae_e_jade.mp4",                 0.00, 3.00, 0.75, 0.00),   # CORTE SECO + camera lenta
]
inputs, filt, durs = [], [], []
for i, (f, a, b, sp, t) in enumerate(CLIPS):
    inputs += ["-i", f]
    d = (b - a) / sp
    durs.append(d)
    filt.append(f"[{i}:v]trim={a}:{b},setpts=(PTS-STARTPTS)/{sp},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop={W}:{H},fps={FPS},setsar=1,{GRADE},format=yuv420p[v{i}]")
cur, total, cuts = "v0", durs[0], []
for i in range(1, len(CLIPS)):
    t = CLIPS[i][4]
    if t > 0:
        filt.append(f"[{cur}][v{i}]xfade=transition=fade:duration={t}:offset={round(total - t, 3)}[x{i}]")
        total = total + durs[i] - t
    else:
        filt.append(f"[{cur}][v{i}]concat=n=2:v=1:a=0[x{i}]")
        cuts.append(round(total, 3))
        total = total + durs[i]
    cur = f"x{i}"
total = round(total, 3)
cut1 = cuts[0]  # primeiro corte seco = o grande impacto
filt.append(f"[{cur}]noise=alls=6:allf=t,vignette=PI/7,fade=t=out:st={round(total-2.6,2)}:d=2.6,format=yuv420p[vout]")
n = len(CLIPS)
# musica: abaixa 0.45s antes do corte (silencio de tensao), volta depois, some no fim
filt.append(f"[{n}:a]afade=t=in:d=0.4,volume='if(between(t,{cut1-0.5},{cut1+0.05}),0.12,1)':eval=frame,afade=t=out:st=14.0:d=0.95[m]")
filt.append(f"anoisesrc=color=brown:amplitude=0.6:duration={total}:sample_rate=44100,lowpass=f=700,highpass=f=50,"
            f"tremolo=f=0.18:d=0.6,volume=0.45,afade=t=in:d=1.5,afade=t=out:st={round(total-2.6,2)}:d=2.6[w]")
ms = int(cut1 * 1000)
filt.append(f"aevalsrc='0.85*sin(2*PI*52*t)*exp(-2.6*t)+0.5*sin(2*PI*36*t)*exp(-1.6*t)':d=3:s=44100,adelay={ms}|{ms},volume=1.0[boom]")
filt.append(f"anoisesrc=color=pink:amplitude=0.5:duration=1.2:sample_rate=44100,highpass=f=1800,afade=t=in:d=0.5,afade=t=out:st=0.5:d=0.7,volume=0.25,adelay={max(0,ms-450)}|{max(0,ms-450)}[whoosh]")
filt.append(f"sine=f=42:d={total}:sample_rate=44100,volume=0.10,afade=t=in:st={cut1}:d=1.5,afade=t=out:st={round(total-2.6,2)}:d=2.6[drone]")
filt.append(f"[m][w][boom][whoosh][drone]amix=inputs=5:normalize=0:duration=longest,atrim=0:{total},alimiter=limit=0.95[aout]")
cmd = ["ffmpeg", "-v", "error", "-y"] + inputs + ["-i", "musica_referencia.mp3",
       "-filter_complex", ";".join(filt), "-map", "[vout]", "-map", "[aout]",
       "-c:v", "libx264", "-crf", "21", "-preset", "medium", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", str(total), "video_final_drama.mp4"]
subprocess.run(cmd, check=True)
print("Pronto: video_final_drama.mp4 (%ss) | corte de impacto em %ss" % (total, cut1))
