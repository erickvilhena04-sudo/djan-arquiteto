# Analise de aparencia: Adriana e Jade reais x video de IA

Método: 6 analistas independentes (2 pessoas x 3 lentes: estrutura facial, cabelo/acessorios/pele, impressao geral), 1 supervisor e 1 cetico que revisou as conclusoes.
Dados completos em `analise_aparencia.json`.

## Notas (0-10, semelhanca com a pessoa real)
| Clipe | Adriana | Jade | Veredito |
|---|---|---|---|
| c1 Jade com a espada | - | 6.2 | manter (abertura; ideal: olhos abertos) |
| c2 chegada (1080p) | 5.8 | 6.8 | manter, e o melhor |
| c3 leao | 5.1 | 6.7 | usar so ate ~3s (o quadro final frontal envelhece a Adriana) |
| c4 tirar a espada | 4.1 | 5.6 | refazer |
| c5 close frontal do abraco | 4.7 | 6.4 | refazer (prioridade 1) |
| c6 plano aberto | 3.4 | 5.0 | manter como contexto (rostos minusculos) |

## Principais diferencas
**Adriana**: rosto da IA mais largo e mais velho (real: oval/coracao, queixo pequeno, ~26 anos); cabelo vira rabo/coque (real: longo, ondulado, solto sobre os ombros, risca ao meio); brinco de flor branca de 5 petalas some ou deforma (c4, c5); blush vermelho e delineado em asa mais pesado; olhar baixo/solene; pele cinza ou avermelhada sob a neblina fria.
**Jade**: olhos fechados ou baixos na maioria dos quadros (real: olhao redondo, escuro, bem aberto); flores do cabelo pequenas (real: duas flores grandes de tule rosa claro); brinco dourado (real: perola branca); capa creme vira cinza-lilas manchada, com botinhas marrons (c4, c5); parece mais velha que 1 ano.
Cetico: a ideia de gerar uma "imagem de identidade" so por texto cria duas pessoas novas. Precisa usar as fotos reais como referencia (feito: personagens `Adriana_real` e `Jade_real` na biblioteca do Magnific).

## Ordem para refazer
1. c5 (close frontal): olhos abertos, cabelo solto preto sem tom avermelhado, brinco de flor branca visivel, capa creme, mesma cor dos outros clipes.
2. c4: rostos visiveis em 3/4, comecando na pose do ultimo quadro bom do c3.
3. c3: cortar em ~3s.
4. c1: abrir os olhos da Jade, espada mais baixa, flores maiores.
5. c6: manter.
