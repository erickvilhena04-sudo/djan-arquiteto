#!/bin/bash
# Monta o video final (9:16, ~20s) igual a referencia: cortes secos, musica e fade para preto.
# Uso: ./montar.sh
set -e
cd "$(dirname "$0")"
# arquivo:inicio:fim (segundos)
CLIPS="clips/clip1_jade_espada_vento.mp4:0:4.2
clips/clip2_mae_chega_ajoelha.mp4:0:4.6
clips/clip3_pai_olhando.mp4:0.4:3.2
clips/clip4_pai_vai_embora.mp4:0:3.6
clips/clip5_mae_aponta_e_abraca.mp4:0:4.8"
INPUTS=""; FILT=""; N=0
while IFS=: read -r f a b; do
  INPUTS="$INPUTS -i $f"
  FILT="$FILT[$N:v]trim=$a:$b,setpts=PTS-STARTPTS,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=30,setsar=1[v$N];"
  CAT="$CAT[v$N]"; N=$((N+1))
done <<< "$CLIPS"
TOTAL=$(python3 -c "
t=0
for l in '''$CLIPS'''.split('\n'):
    f,a,b=l.rsplit(':',2); t+=float(b)-float(a)
print(round(t,2))")
FADE=$(python3 -c "print(round($TOTAL-2,2))")
ffmpeg -v error -y $INPUTS -i musica_referencia.mp3 -filter_complex "${FILT}${CAT}concat=n=$N:v=1:a=0,fade=t=out:st=$FADE:d=2[v]" \
  -map "[v]" -map "$N:a" -af "afade=t=out:st=12.5:d=2.4" -t "$TOTAL" -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac video_final_instagram.mp4
echo "Pronto: video_final_instagram.mp4 ($TOTAL s)"
