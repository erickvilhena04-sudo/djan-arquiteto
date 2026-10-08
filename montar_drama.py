#!/usr/bin/env python3
"""Montagem dramatica: plano continuo (Jade -> mae chega -> beijo/abraco), depois pausa de silencio,
CORTE SECO com impacto grave, plano aberto do pai indo embora em camera lenta, corte para o push-in na mae e na Jade,
fade longo. Saida: video_final_drama.mp4 (1080x1920, 24fps)."""
import subprocess, os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 24
GRADE = "eq=saturation=0.93:contrast=1.05:gamma=1.02,curves=all='0/0.02 0.5/0.5 1/0.985'"
# (arquivo, ini, fim, velocidade(1=normal, 0.8=camera lenta), transicao_entrada_em_s; 0 = corte seco)
# (arquivo, ini, fim, velocidade, transicao_entrada_em_s (0 = corte seco), crop opcional "w:h:x:y" para aproximacao digital)
CLIPS = [
    ("clips/clip1_jade_espada_vento.mp4",                 2.60, 5.04, 1.0,  0.00, None),   # Jade com a espada, como se fosse para a guerra
    ("clips/clip2_mae_chega_ajoelha_NOVA_1080p.mp4",      0.00, 5.05, 1.0,  0.12, None),   # a mae chega e ajoelha (termina na imagem aprovada)
    ("clips/clip3_mae_fala_no_ouvido_e_da_o_leao.mp4",    0.00, 5.04, 1.0,  0.12, None),   # fala no ouvido, pega o leaozinho e da para a Jade
    ("clips/clip4_mae_tira_espada_acolhe.mp4",            0.00, 4.80, 1.0,  0.12, None),   # tira a espada, a Jade abraca o leao, a mae acolhe
    # o mesmo plano aberto em 3 tempos, tempo sempre avancando:
    ("clips/clip6_reveal_pai_ao_longe.mp4",               0.00, 2.30, 0.85, 0.00, None),   # CORTE SECO: pai partindo para a guerra
    ("clips/clip5_mae_aponta_e_abraca.mp4",               1.30, 4.60, 0.90, 0.00, None),   # CORTE SECO: close frontal da mae e da Jade abracadas (sem a parte do aponte)
    ("clips/clip6_reveal_pai_ao_longe.mp4",               3.90, 5.04, 0.85, 0.00, None),   # CORTE SECO: neblina engole o pai
]
inputs, filt, durs = [], [], []
for i, (f, a, b, sp, t, cr) in enumerate(CLIPS):
    inputs += ["-i", f]
    d = (b - a) / sp
    durs.append(d)
    crop = f"crop={cr}," if cr else ""
    extra = ",noise=alls=5:allf=t" if cr else ""
    filt.append(f"[{i}:v]trim={a}:{b},setpts=(PTS-STARTPTS)/{sp},{crop}scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop={W}:{H},fps={FPS},setsar=1,{GRADE}{extra},format=yuv420p[v{i}]")
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
cut2 = cuts[1]
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
ms2 = int(cut2 * 1000)
filt.append(f"aevalsrc='0.7*sin(2*PI*46*t)*exp(-4*t)':d=1.5:s=44100,adelay={ms2}|{ms2},volume=0.55[boom2]")
filt.append(f"[m][w][boom][whoosh][drone][boom2]amix=inputs=6:normalize=0:duration=longest,atrim=0:{total},alimiter=limit=0.9[aout]")
cmd = ["ffmpeg", "-v", "error", "-y"] + inputs + ["-i", "musica_referencia.mp3",
       "-filter_complex", ";".join(filt), "-map", "[vout]", "-map", "[aout]",
       "-c:v", "libx264", "-crf", "21", "-preset", "medium", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", str(total), "video_final_drama.mp4"]
subprocess.run(cmd, check=True)
print("Pronto: video_final_drama.mp4 (%ss) | corte de impacto em %ss" % (total, cut1))
