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
