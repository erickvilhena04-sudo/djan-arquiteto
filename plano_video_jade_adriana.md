# Vídeo Jade + Adriana (cavaleira) – Instagram 9:16, ~20s

Configuração no Magnific > Video Generator (ilimitado): **Kling 2.5 · 720p · 5s · 9:16 · Start image**.
Uma imagem inicial por clipe. Imagens (na ordem em que foram enviadas no chat):
- **Img A** – pai de armadura preta, capa preta, capacete na mão, navios na névoa.
- **Img B** – mãe ajoelhada sorrindo, Jade olhando para ela segurando a espada, leão de pelúcia.
- **Img C** – igual à B, mãe séria, brinco de flor (mais parecida com a Adriana).
- **Img D** – mãe agachada estendendo as mãos para a Jade, espada cravada no chão.
- **Img E** – mãe segurando a Jade no colo e apontando para longe.
- **Img F** – pai de costas, de capacete e espada, caminhando pela névoa em direção aos guerreiros e aos navios.
- **Img G** – mãe ajoelhada com a espada, Jade ao lado apontando para longe, as duas olhando na mesma direção.
- **Img I** – Jade sozinha de olhos fechados, rosto encostado no pomo da espada, capa ao vento (abertura, igual à referência).
- **Img H** – mãe de pé de guarda com a espada cravada, Jade ao lado olhando para ela com o leão.

## Estrutura da referência (19s) que vamos copiar
1. 0-4s: close apertado da bebê, espada vertical na frente do rosto, capa ao vento, névoa. Câmera quase parada.
2. 4-6s: a mãe de armadura entra pela direita, passando na frente da câmera, que abre.
3. 6-9s: ela ajoelha ao lado da bebê, olha para baixo, luva na espada.
4. 9-12s: abraça a bebê, que segura o leão de pelúcia; câmera plano médio.
5. 12-15s: a mãe se levanta com a espada, bebê com o leão nos pés dela; câmera abre para plano geral.
6. 15-19s: escurece (fade).
Nosso final extra: a mãe aponta para o pai, que vai para a guerra, e depois fade.

## VENTO (importante)
A referência tem vento forte e constante: capa creme da bebê quase horizontal, fios de cabelo da mãe voando, capa azul balançando, capim se movendo, névoa correndo de lado. Em TODO prompt incluir: `Strong steady wind blowing from the left: the cloak flaps and streams sideways, loose strands of hair whip across the face, the grass bends, the fog races across the field.`
Clipes já gerados com vento fraco (prompts diziam "gently"): w4M3G057EI e rgGJiNqxtc. Regerar com a frase acima se ficarem parados demais.

### 1. Abertura: Jade agarrada na espada com vento forte (igual à referência) – start: Img I
`Tight close-up, handheld feel with a tiny camera sway. The baby girl clings tightly to the upright sword with both small hands gripping the hilt, her face pressed against the lion pommel, eyes closed. A strong, gusting wind hits her: her cream hooded cloak whips and streams sideways, her curly pigtails and pink bows flutter, her little body sways slightly with each gust but she holds on firmly to the sword. Thick fog rushes across the grass field behind her, the blades of grass bend. Cold moody light. Face, hair, bows and clothes stay exactly the same.`

(Substitui o clipe 1 anterior; regerar w4M3G057EI com este prompt.)

## Sequência final (5 clipes, Kling 2.5 · 720p · 9:16)
| # | Cena | Arquivo | Situação |
|---|---|---|---|
| 1 | Close da Jade com a espada (braço entra no fim) | w4M3G057EI | Pronto |
| 2 | A mãe chega andando e ajoelha | ovsuxyp829 | Pronto (conferir) |
| 3 | Corte: o pai olhando para a câmera | GERAR (start: Img A) | Falta |
| 4 | O pai vai embora para a guerra | GERAR (start: Img F) | Falta |
| 5 | Mãe e Jade se abraçam (fecho, fade para preto) | rgGJiNqxtc | Pronto |

Reserva: 6AIWpyyiJO (mãe entra e ajoelha). Não usa mais a mãe se levantando/apontando.

### 3. O pai olha (3-5s) – start: Img A
`The father knight stands in the misty field holding his helmet at his side, looks straight into the camera with a serious, determined and loving expression, then slowly raises the helmet. Camera very slowly pushes in. Strong steady wind makes his black cloak flap and stream sideways, fog racing across the field, longships behind him. Face, armor and clothes stay exactly the same.`

### 4. O pai vai embora (5s) – start: Img F
`The father knight in a black helmet and black cloak walks away across the misty field toward the warriors and longships in the distance. The camera slowly follows from behind. Strong steady wind: his black cloak streams sideways, the grass bends, fog races across the field. Armor and clothes stay exactly the same.`

## Montagem
Ordem 1→2→3→4→5 (~23s; cortar o excedente para ~19s). Para ficar perto dos 19s da referência, usar só 3-4s de cada clipe ou pular o clipe 2.
Fade para preto no fim, exportar 9:16 para o Instagram.

## Música
Extraída do vídeo de referência: `musica_referencia.mp3` (14,9s; o vídeo original tem 19,1s, então os últimos ~4s ficam sem música).
Depois de baixar os 5 clipes (clip1.mp4 ... clip5.mp4) na mesma pasta, rodar `./montar.sh` para juntar, colocar a música e fazer o fade.

## Montagem final (feita)
`./montar.sh` gera `video_final_instagram.mp4` (20s, 720x1280, música da referência, cortes secos, fade para preto no fim).
Ordem usada (pasta `clips/`): 1 Jade agarrada na espada com vento -> 2 mãe chega e ajoelha -> 3 pai olhando (cortado) -> 4 pai vai embora -> 5 mãe aponta e abraça a Jade.
Reservas na mesma pasta: reserva_pai_vai_embora, reserva_mae_ajoelhada, reserva_abraco.

## Versao cinematografica de 16s (video_final_cinema_16s.mp4)
Montada por `montar_cinema_final.py` (duas passagens de ffmpeg, rabiscos em HTML, grade de cinema, bloom, grao).
Ordem: Jade sozinha no vento (Inicio A, rosto refeito com a Jade_real) -> alguem passa rapido ao lado dela (so um pedaco: manopla e capa)
-> tinta -> a mae chega e ajoelha (tomada continua) -> tinta + seta: ela aponta -> tinta + circulo: o pai aparece rapido e parte
-> dissolve para o plano aberto (pai cruza o quadro, take 10192) -> tinta -> abraco com o leaozinho -> luz quente.
Clips novos em `clips/inicio_novo/` (10193 = Inicio A, 10192 = plano aberto com o pai passando; os outros sao copias/trechos dos takes ja usados).
Pendente: baixar o video "Inicio B" do Space (mae ao lado da Jade com os dois rostos de referencia) para trocar a chegada antiga
(`CHEGA=clips/<novo>.mp4 CHEGA_INI=0 python3 montar_cinema_final.py`).
Correcao tecnica: o Chromium salva quadros 100% opacos como RGB; o ffmpeg trocava de formato no meio da sequencia da tinta e
perdia quadros (piscada). `montar_cinema_final.py` regrava os PNGs como RGBA antes de montar.

### Versao limpa (video_final_cinema_limpo.mp4, 16s) - `montar_cinema_limpo.py`
Pedido do dono: menos cortes e menos efeito. Seis tomadas, cinco passagens: quatro dissolves suaves e uma unica pincelada de tinta
(aponta -> pai). Sem seta, sem circulo, sem zoom, sem bloom, sem aceleracao. A abertura e uma tomada so (Jade + alguem passando).

### Versao com os dois takes completos (video_final_completos.mp4, 16,3s) - `montar_cinema_limpo.py`
Pedido do dono: usar completos o plano aberto (pai passa e parte, mae acolhe a Jade: `n23787`) e o abraco (a mao tira a espada, o leaozinho,
abraco: `n23786`); o resto foi encurtado. Ordem: Jade + alguem passa (4,8s) -> mae chega e ajoelha -> aponta (1s) -> pai rapido (tinta)
-> plano aberto completo (5s) -> abraco completo (3,8s) -> luz quente. Os dois arquivos sao identicos (md5) aos 10192 e 10194.

### Versao fluida (video_final_fluido.mp4, 16,2s) - `montar_fluido.py`
Pedido do dono: tirar os cortes e deixar fluido. Nenhum corte seco e nenhuma tinta: so dissolves de 0,6 a 0,9s com curva suave
(smoothstep via xfade custom). Plano aberto (5s) e abraco (3,8s) completos; sem seta, circulo, zoom ou sons de impacto (so musica e vento).
