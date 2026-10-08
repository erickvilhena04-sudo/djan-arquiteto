#!/bin/bash
# Junta clip1..clip5.mp4 (9:16), corta em ~19s, aplica fade e a música da referência.
set -e
cd "$(dirname "$0")"
DUR=${1:-19}
for i in 1 2 3 4; do
  ffmpeg -v error -y -i clip$i.mp4 -an -vf "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=30" -c:v libx264 -pix_fmt yuv420p n$i.mp4
  echo "file 'n$i.mp4'" >> lista.tmp
done
ffmpeg -v error -y -f concat -safe 0 -i lista.tmp -c copy juntos.mp4
FADE=$(echo "$DUR - 2" | bc)
ffmpeg -v error -y -i juntos.mp4 -i musica_referencia.mp3 -t "$DUR" \
  -vf "fade=t=out:st=$FADE:d=2" -af "afade=t=out:st=$((DUR-3)):d=3" \
  -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest video_final_instagram.mp4
rm -f lista.tmp n?.mp4 juntos.mp4
echo "Pronto: video_final_instagram.mp4"
