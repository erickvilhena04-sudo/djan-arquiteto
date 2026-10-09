# Psytrance 142 BPM — projeto para o Ableton Live

Faixa de ~7:18 (259 compassos) montada a partir da **análise da referência** (tempo, tom, estrutura e energia por seção).
O material musical é **original**: não reproduz melodia, vocal nem arranjo da referência.

## Como abrir

1. Abra **`Psytrance 142 Project/Psytrance_142.als`** no **Ableton Live 12** (precisa ser 12.0 ou mais novo).
2. Aperte **Tab** para ver o Arrangement. As 9 faixas já estão posicionadas no compasso 1, o tempo é 142 BPM
   e há marcadores (locators) em cada seção: Intro, Build, Break, Drop 1/2/3, Outro.
3. Dê play. Cada faixa é um stem (kick, baixo, hats, perc, pad, arpejo, lead, vocal, fx). A soma deles é a música.

> **Importante:** esse `.als` foi gerado por código a partir de um set real do Live 12 e conferido contra o esquema
> de arquivos do Live, mas **não foi aberto no Ableton** (eu não tenho o programa aqui). Se o Live reclamar do arquivo:
> abra um set vazio, ponha **142 BPM**, arraste os 9 `.flac` de `Psytrance 142 Project/Samples/Imported/` para o Arrangement
> no compasso 1 e arraste os `.mid` da pasta `midi/` para faixas MIDI com o seu synth.

## O que tem em cada pasta

| Caminho | O que é |
|---|---|
| `Psytrance 142 Project/Psytrance_142.als` | Projeto do Live 12 com os stems no Arrangement |
| `Psytrance 142 Project/Samples/Imported/*.flac` | 9 stems (16 bits, 44,1 kHz; kick e baixo em mono) |
| `midi/00_TODAS_AS_FAIXAS.mid` | Todas as faixas num arquivo só, com o tempo e os marcadores das seções |
| `midi/01_KICK.mid` … `09_FX.mid` | Uma faixa por arquivo (as mesmas notas que geraram o áudio) |
| `PSYTRANCE_142_previa.mp3` | Prévia da mix (-2,5 dB abaixo da soma dos stems, para não estourar no mp3) |
| `src/` | O código que gera tudo (Python) |

## Notas sobre os sons

- **O áudio é sintetizado por código**: serve como demo e para você ouvir o arranjo. Para som de produção,
  use os MIDIs com os seus synths (Serum, Sylenth, Pigments…) no lugar dos stems.
- **Vocais:** são vogais sintetizadas por formantes (coro "aah/ooh" nos acordes e "chops" rítmicos). Não há letra
  nem cantor real, e o vocal da referência não está aqui. Para um vocal de verdade, crie uma faixa de áudio e solte a gravação.
- **Warp:** os clipes estão em modo *Re-Pitch* (1:1 em 142 BPM, sem processamento). Se mudar o BPM, troque para *Complex*.
- A sidechain do kick já está gravada nos stems de pad, arpejo, lead, vocal e fx.

## O que foi medido na referência e como esta faixa se compara

| | Referência | Esta faixa |
|---|---|---|
| BPM | ~142 | 142,0 |
| Duração | 437,8 s (259 compassos) | 437,8 s (259 compassos) |
| Tom | Fá maior (corr. 0,90) | Fá maior (corr. 0,87) |
| Estrutura | 3 drops (1:34, 3:09, 4:57), breaks em 1:21 / 2:55 / 4:03, outro em 6:59 | igual, em blocos de 8 compassos |
| Padrão no compasso | kick no tempo, hat aberto no contratempo, baixo nas 2 últimas semicolcheias | igual |
| Energia por bloco de 8 compassos | medida em 32 blocos | o desenho acompanha a referência: correlação 0,95 no grave, 0,71 no médio, 0,87 no agudo, 0,88 no RMS |
| Volume | RMS ~0,65 nos drops (bem esmagada) | RMS ~0,4–0,5 nos drops, cerca de 3 dB abaixo; -8 LUFS (stems somados), prévia mp3 em -10,5 LUFS |

## Regerar

```
pip install numpy scipy soundfile mido
python3 src/gerar_psytrance.py midi   midi
python3 src/gerar_psytrance.py render /caminho/cache
python3 src/gerar_psytrance.py master /caminho/cache . --nivel 1.0
python3 src/gerar_als.py
```

A partitura fica em `src/psy_score.py` (acordes, padrões, estrutura por bloco). `src/modelo/` guarda o set base do Live 12
(do projeto [buildable](https://github.com/kmontag/buildable), licença MIT).
