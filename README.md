# IC-LibrasPython

Aplicação local para apoiar a comunicação por datilologia em Libras, com câmera no navegador, confirmação ou correção de letras, formação de mensagem e persistência em SQLite.

> **Estado atual:** a interface web e o fluxo de confirmação estão implementados. O classificador visual ainda não possui um modelo treinado e, por isso, a aplicação apresenta esse estado claramente e oferece inserção manual. O coletor legado com MediaPipe continua disponível para estudos e preparação de dados.

## Início rápido da interface web

A primeira versão web usa apenas a biblioteca padrão do Python e funciona no ambiente atual:

```bash
python3.14 -m webapp.server
```

Depois, abra `http://127.0.0.1:8000` no navegador. A câmera depende da permissão do navegador e permanece local; fotografias e vídeos não são gravados.

Para executar a validação automatizada:

```bash
python3.14 -m unittest discover -v
```

O escopo funcional, os limites do MVP e as próximas etapas estão em [`docs/ESCOPO_MVP.md`](docs/ESCOPO_MVP.md).

Para a demonstração acadêmica focada no trabalho de Thais, consulte [`docs/APRESENTACAO_SEGUNDA.md`](docs/APRESENTACAO_SEGUNDA.md).

## Ambiente de visão computacional

O coletor e o treinamento usam um ambiente separado com Python 3.11:

```bash
python3.11 -m venv venv
source venv/bin/activate
python -m pip install -r requirements-vision.txt
```

Coleta manual com expressão facial neutra, sem armazenar vídeo:

```bash
python -m training.collect \
  --participant p01 \
  --manual-label A \
  --lighting uniforme
```

Treinamento prioritário do classificador manual:

```bash
python -m training.train --modality manual
```

O modelo será salvo em `artifacts/models/manual.joblib`. O relatório de avaliação será salvo ao lado do modelo. Não divulgue acurácia antes de coletar participantes suficientes e avaliar pessoas que não apareceram no treinamento.

## Estado das capacidades

| Recurso | Situação atual |
| --- | --- |
| Interface web responsiva e acessível | Implementado |
| Câmera no navegador | Implementado |
| Inserção, espaço, exclusão e limpeza | Implementado |
| Persistência de sessão e eventos | Implementado |
| Leitura da mensagem em voz alta | Implementado pelo navegador |
| Registro da previsão e da correção | Implementado no contrato e no banco |
| Reconhecimento automático de letras | Aguardando dataset e modelo validado |
| Tradução completa de Libras | Fora do escopo do MVP |

## Protótipo legado de coleta

O código original coleta coordenadas das mãos pela webcam e as armazena em SQLite, como base para estudos de reconhecimento de sinais da Língua Brasileira de Sinais (Libras).

Esta documentação descreve o código fornecido em `IC-LibrasPython-main.zip`. As propostas de evolução estão identificadas separadamente das funcionalidades existentes.

## Sumário

- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Instalação](#instalação)
- [Execução e controles](#execução-e-controles)
- [Fluxo de processamento](#fluxo-de-processamento)
- [Documentação dos módulos](#documentação-dos-módulos)
- [Banco de dados](#banco-de-dados)
- [Formato dos dados](#formato-dos-dados)
- [Configurações](#configurações)
- [Verificação manual](#verificação-manual)
- [Problemas comuns](#problemas-comuns)
- [Limitações e evolução](#limitações-e-evolução)
- [Contribuição e licença](#contribuição-e-licença)
- [Referências](#referências)

## Funcionalidades

| Recurso | Situação na versão analisada |
| --- | --- |
| Abrir a webcam e exibir imagens | Implementado |
| Detectar até duas mãos | Implementado |
| Desenhar pontos e conexões das mãos | Implementado |
| Informar o nome do sinal no terminal | Implementado |
| Iniciar e interromper a coleta por teclado | Implementado |
| Salvar coordenadas por mão e frame em SQLite | Implementado |
| Criar um array NumPy ao encerrar | Implementado, somente em memória |
| Consultar registros pelo terminal | Implementado |
| Capturar pontos faciais | Arquivo reservado, vazio |
| Treinar ou executar um classificador de Libras | Não implementado |
| Exportar dataset para CSV ou arquivo NumPy | Não implementado |

O banco recebe coordenadas e rótulos. O código não grava fotografias, vídeos ou áudio em arquivos.

## Tecnologias

| Tecnologia | Papel no projeto |
| --- | --- |
| Python | Linguagem dos scripts |
| OpenCV (`cv2`) | Acesso à câmera, conversão de cores, desenho de texto, janela e teclado |
| MediaPipe (`mediapipe`) | Detecção e rastreamento de pontos das mãos pela API `mp.solutions.hands` |
| NumPy (`numpy`) | Conversão da lista de pontos em um array ao finalizar |
| SQLite / `sqlite3` | Banco local e acesso SQL |
| `pathlib` | Construção do caminho do banco em `database/db.py` e `teste_sqlite.py` |

`sqlite3` e `pathlib` fazem parte da biblioteca padrão do Python. Não é necessário instalar um servidor de banco. PyTorch não é usado na versão atual.

## Estrutura do projeto

Os caminhos abaixo são relativos à pasta `IC-LibrasPython-main`.

| Caminho | Responsabilidade |
| --- | --- |
| `main.py` | Ponto de entrada; câmera, rastreamento, controles, coleta e array final |
| `database/db.py` | Conexão, criação de tabelas e inserções |
| `camera/hand_tracking.py` | Função auxiliar para abrir a câmera; não utilizada pelo `main.py` |
| `camera/face_tracking.py` | Vazio; sem implementação de rastreamento facial |
| `funcoes/helpers.py` | Vazio; reservado para funções auxiliares |
| `models/model.py` | Vazio; sem rede neural ou classificador |
| `teste_sqlite.py` | Demonstração independente de criação, inserção e consulta no SQLite |
| `ver_dados.py` | Exibe sinais e até dez landmarks no terminal |
| `.gitignore` | Ignora `venv/`, `__pycache__/`, `*.pyc`, `*.sqlite` e `*.db` |
| `.vscode/settings.json` | Configuração do gerenciador de ambientes Python no VS Code |
| `dados_libras.sqlite` | Gerado durante a execução; não acompanha o ZIP |

O projeto não fornece `requirements.txt`, `pyproject.toml`, testes automatizados ou arquivo de licença. Este README deve ser colocado na raiz, ao lado de `main.py`.

## Instalação

### Pré-requisitos

- Computador com webcam e permissão para utilizá-la.
- Ambiente gráfico local para abrir a janela do OpenCV.
- Python e `pip` disponíveis no terminal.
- Acesso à internet para instalar as dependências.

**Ambiente sugerido:** Python 3.11 de 64 bits. O repositório não declara uma versão oficial do Python nem versões testadas das dependências.

O código utiliza a API legada `mp.solutions.hands`. Como ponto de partida para reproduzir essa API, os comandos abaixo fixam MediaPipe 0.10.21. Essa distribuição disponibiliza pacotes para Python 3.9 a 3.12 em plataformas específicas; consulte os [arquivos oficiais da versão](https://pypi.org/project/mediapipe/0.10.21/#files). A instalação completa e a câmera precisam ser validadas no computador de uso.

### 1. Extrair e acessar o projeto

Extraia `IC-LibrasPython-main.zip` e abra um terminal na pasta extraída:

```bash
cd IC-LibrasPython-main
```

### 2. Criar um ambiente virtual

Windows, usando o Prompt de Comando:

```bat
py -3.11 -m venv venv
venv\Scripts\activate.bat
```

Windows, usando PowerShell, após criar o ambiente:

```powershell
.\venv\Scripts\Activate.ps1
```

Se a ativação do PowerShell estiver bloqueada, use o Prompt de Comando ou execute diretamente `venv\Scripts\python.exe` no lugar de `python` nos comandos seguintes.

Linux ou macOS, com Python 3.11 instalado:

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Instalar as dependências

Com o ambiente virtual ativo:

```bash
python -m pip install --upgrade pip
python -m pip install "mediapipe==0.10.21" "numpy<2" "opencv-contrib-python<4.12"
python -m pip check
```

Esta é uma configuração inicial sugerida, não um conjunto de versões já homologado pelo projeto. O pacote `opencv-contrib-python` fornece o módulo `cv2`; evite instalar várias distribuições do OpenCV no mesmo ambiente. Não use uma distribuição exclusivamente `headless`, pois o programa depende de janelas.

### 4. Conferir os imports

```bash
python -c "import cv2, mediapipe as mp, numpy as np; print('OpenCV:', cv2.__version__); print('MediaPipe:', mp.__version__); print('NumPy:', np.__version__); print('Hands:', mp.solutions.hands.Hands)"
```

Esse comando verifica os imports e o acesso à API utilizada; não testa a webcam.

## Execução e controles

Na raiz do projeto, execute:

```bash
python main.py
```

1. Informe no terminal o nome do sinal, por exemplo `bom_dia`, e pressione Enter.
2. Aguarde a janela **LIBRAS - Coleta**.
3. Mantenha a janela da câmera em foco e posicione as mãos no enquadramento.
4. Pressione **`g` minúsculo** para iniciar a gravação das coordenadas.
5. Execute o sinal e pressione **`s` minúsculo** para parar.
6. Para repetir a coleta com o mesmo nome, pressione `g` novamente.
7. Pressione **Esc** para encerrar.

| Tecla | Efeito exato |
| --- | --- |
| `g` | Ativa a coleta, reinicia o contador e cria um novo registro em `sinais` |
| `s` | Desativa a coleta e remove o ID ativo da memória; os dados já salvos permanecem |
| Esc | Sai do laço, cria e imprime o array acumulado, libera a câmera e fecha as janelas |

Embora as mensagens do terminal mostrem `G` e `S`, o código compara `ord('g')` e `ord('s')`. Use as letras minúsculas.

A janela mostra `PARADO` ou `GRAVANDO`. O rastreamento e o desenho das mãos continuam mesmo em `PARADO`, mas os pontos só são armazenados em `GRAVANDO`.

**Comportamentos importantes:**

- O nome é solicitado uma única vez por execução. Reinicie o programa para coletar outro nome.
- Pressionar `g` durante uma gravação cria outra coleta imediatamente, com novo ID e contador reiniciado.
- Cada acionamento de `g` cria uma linha em `sinais`, mesmo que nenhuma mão seja detectada depois.
- O programa remove espaços das extremidades do nome com `.strip()`, mas permite nome vazio.
- Não é obrigatório pressionar `s` antes de Esc: cada ponto já inserido foi confirmado no banco.

Para consultar o resultado, execute **na raiz do projeto**:

```bash
python ver_dados.py
```

## Fluxo de processamento

1. `main.py` importa as bibliotecas e as funções de persistência.
2. Configura `Hands` para vídeo, até duas mãos e confiança mínima de 0,5.
3. Solicita a câmera de índice `0` e cria as tabelas, se necessário.
4. Lê o nome do sinal no terminal.
5. Para cada imagem, converte BGR para RGB e chama `hands.process()`.
6. Desenha os pontos detectados sobre a imagem original.
7. Se a coleta estiver ativa, adiciona cada ponto à lista e grava uma linha no SQLite.
8. Mostra o status e processa a tecla pressionada.
9. Incrementa o contador se a gravação estiver ativa.
10. Ao sair normalmente do laço, converte os dados acumulados em NumPy e libera os recursos de câmera e janela.

A persistência acontece durante a captura, ponto a ponto. O array final é uma segunda representação dos dados, em memória.

## Documentação dos módulos

### `main.py`

O script executa no nível do módulo, sem função `main()` ou proteção `if __name__ == '__main__'`. Importá-lo também inicia a configuração, abre a câmera e solicita entrada.

| Variável | Finalidade |
| --- | --- |
| `mp_hands` | Referência à solução de mãos do MediaPipe |
| `mp_draw` | Utilitário de desenho dos landmarks |
| `hands` | Processador de detecção e rastreamento |
| `camera` | Objeto `cv2.VideoCapture(0)` |
| `nome_sinal` | Rótulo informado pelo operador |
| `gravando` | Indica se deve persistir os pontos |
| `sinal_id` | ID da coleta ativa, ou `None` |
| `numero_frame` | Contador da coleta ativa |
| `dados_landmarks` | Lista com todos os pontos coletados na execução |
| `array_landmarks` | Array construído a partir da lista ao encerrar |

A lista não é esvaziada entre gravações: pode conter diferentes `sinal_id` da mesma execução.

### `database/db.py`

`DB_PATH` aponta para `dados_libras.sqlite` na raiz do projeto, calculada a partir da localização do módulo. Portanto, esse caminho independe da pasta de onde o terminal executa o programa.

| Função | Parâmetros e retorno | Comportamento |
| --- | --- | --- |
| `conectar()` | Retorna `sqlite3.Connection` | Imprime o caminho e abre o banco; o SQLite cria o arquivo se necessário |
| `criar_tabelas()` | Sem parâmetros; retorna `None` | Cria `sinais` e `hand_landmarks` se não existirem, confirma e fecha a conexão |
| `inserir_sinal(nome_sinal, observacao=None)` | Nome e observação opcional; retorna o ID inteiro inserido | Insere uma coleta em `sinais` |
| `inserir_landmark(sinal_id, frame_num, hand_id, landmark_id, x, y, z)` | Identificadores e coordenadas; retorna `None` | Insere um ponto, confirma e fecha a conexão |

As inserções usam placeholders `?` e parâmetros separados. Cada função de inserção abre sua própria conexão e executa `commit()`.

Exemplo de uso independente, na raiz do projeto:

```python
from database.db import criar_tabelas, inserir_sinal, inserir_landmark

criar_tabelas()
sinal_id = inserir_sinal("exemplo_manual", "dado sintético para demonstração")
inserir_landmark(sinal_id, 1, 0, 0, 0.5, 0.4, 0.0)
```

O exemplo grava um ponto fictício no banco real do projeto. Não o misture com amostras destinadas a treinamento.

### `camera/hand_tracking.py`

`iniciar_camera()` não recebe parâmetros e retorna `cv2.VideoCapture(0)`. Apesar do nome do arquivo, a função apenas abre a câmera: não detecta mãos. Atualmente `main.py` abre a câmera diretamente, sem chamar essa função.

### Arquivos reservados

`camera/face_tracking.py`, `funcoes/helpers.py` e `models/model.py` estão vazios. Não possuem classes, funções ou comportamento em execução.

### `teste_sqlite.py`

```bash
python teste_sqlite.py
```

Abre o banco na raiz do projeto, cria a tabela `teste`, insere `bom_dia` e imprime todos os registros dessa tabela. Cada execução insere outra linha. Não valida as tabelas de coleta e não é um teste automatizado com asserções.

### `ver_dados.py`

Abre `dados_libras.sqlite` por caminho relativo ao diretório atual, imprime todos os registros de `sinais` e até dez registros de `hand_landmarks`. A consulta não define ordenação. Execute na raiz para acessar o mesmo banco usado por `main.py`.

## Banco de dados

### Tabela `sinais`

Cada registro corresponde a um acionamento de `g`, e não necessariamente a uma classe única de sinal.

| Coluna | Tipo e restrição | Significado |
| --- | --- | --- |
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Identificador da coleta |
| `nome_sinal` | `TEXT NOT NULL` | Rótulo manual; nomes repetidos são permitidos |
| `observacao` | `TEXT` | Informação opcional; `main.py` utiliza `coleta manual` |

### Tabela `hand_landmarks`

Cada linha armazena **um ponto de uma mão em um frame**.

| Coluna | Tipo e restrição | Significado |
| --- | --- | --- |
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Identificador do ponto armazenado |
| `sinal_id` | `INTEGER NOT NULL`, FK declarada | Referência a `sinais.id` |
| `frame_num` | `INTEGER NOT NULL` | Contador do frame na coleta |
| `hand_id` | `INTEGER NOT NULL` | Índice da mão no resultado, normalmente 0 ou 1 |
| `landmark_id` | `INTEGER NOT NULL` | Índice do ponto, de 0 a 20 |
| `x` | `REAL NOT NULL` | Coordenada horizontal |
| `y` | `REAL NOT NULL` | Coordenada vertical |
| `z` | `REAL NOT NULL` | Profundidade relativa estimada |

A relação é de uma coleta para vários landmarks. Não existe restrição `UNIQUE` sobre coleta, frame, mão e ponto. A chave estrangeira aparece no DDL, mas o código não ativa `PRAGMA foreign_keys = ON`; não se deve presumir que a relação está sendo fiscalizada pela conexão.

### Consultas úteis

Execute estas consultas em um cliente SQLite conectado a `dados_libras.sqlite`.

Quantidade de pontos e frames com detecção por coleta, incluindo coletas vazias:

```sql
SELECT
    s.id,
    s.nome_sinal,
    COUNT(h.id) AS total_pontos,
    COUNT(DISTINCT h.frame_num) AS frames_com_deteccao
FROM sinais AS s
LEFT JOIN hand_landmarks AS h ON h.sinal_id = s.id
GROUP BY s.id, s.nome_sinal
ORDER BY s.id;
```

Pontos da coleta de ID 1, ordenados para análise:

```sql
SELECT frame_num, hand_id, landmark_id, x, y, z
FROM hand_landmarks
WHERE sinal_id = 1
ORDER BY frame_num, hand_id, landmark_id;
```

Substitua `1` pelo ID desejado. `frames_com_deteccao` não mede duração nem total de frames capturados, pois imagens sem mãos não produzem linhas.

## Formato dos dados

### Landmarks e coordenadas

Um landmark é um ponto de referência estimado na mão. O MediaPipe Hands produz 21 por mão:

| Índices | Região |
| --- | --- |
| 0 | Punho |
| 1–4 | Polegar |
| 5–8 | Indicador |
| 9–12 | Dedo médio |
| 13–16 | Anelar |
| 17–20 | Dedo mínimo |

`x` e `y` são normalizados pela largura e altura da imagem. `z` representa profundidade relativa ao punho; valores menores indicam maior proximidade da câmera. Não são medidas em metros. Veja a [documentação da API Hands](https://chuoling.github.io/mediapipe/solutions/hands.html#output).

`hand_id` vem de `enumerate(resultado.multi_hand_landmarks)`: não significa mão esquerda ou direita e não garante identidade consistente entre frames. O programa não salva a classificação de lateralidade.

### Contagem dos frames

Ao pressionar `g`, `numero_frame` recebe zero e é incrementado no fim da mesma iteração. Assim, em uma coleta iniciada do estado parado, o primeiro frame seguinte pode ser salvo com número **1**.

O contador também avança durante a gravação quando nenhuma mão é detectada. Podem existir lacunas entre os números gravados. Não há timestamp, FPS registrado ou preenchimento de pontos ausentes.

### Array NumPy

Cada linha da lista segue esta ordem:

```python
[sinal_id, numero_frame, id_mao, id_ponto, ponto.x, ponto.y, ponto.z]
```

Se houver pontos, o array resultante tem formato `(N, 7)`, em que `N` é a quantidade de landmarks acumulados. Como mistura inteiros e coordenadas reais, o NumPy normalmente converte todos os valores para um tipo de ponto flutuante. Sem pontos, `np.array([])` tem formato `(0,)`.

O array é impresso e não é salvo em `.npy` ou `.csv`. As linhas já persistidas permanecem no SQLite depois do encerramento.

Duas mãos completas produzem até 42 linhas por frame e 126 valores de coordenadas (`2 × 21 × 3`). **O código atual não constrói um vetor de 126 posições por frame.** Isso exigiria uma etapa adicional de agrupamento, ordenação e tratamento de mãos ausentes.

## Configurações

Não existem arquivo `.env`, opções de linha de comando ou tela de configuração. Os valores são alterados diretamente no código.

| Local | Configuração atual | Efeito |
| --- | --- | --- |
| `main.py` | `cv2.VideoCapture(0)` | Seleciona a câmera de índice 0 |
| `main.py` | `static_image_mode=False` | Usa rastreamento para sequência de imagens |
| `main.py` | `max_num_hands=2` | Limita a detecção a duas mãos |
| `main.py` | `min_detection_confidence=0.5` | Limiar mínimo de detecção |
| `main.py` | `min_tracking_confidence=0.5` | Limiar mínimo de rastreamento |
| `database/db.py` | `DB_PATH` | Caminho do banco usado pelas funções de persistência |

Se alterar o caminho do banco, ajuste também `ver_dados.py` e `teste_sqlite.py`, pois ambos definem seus próprios caminhos. Alterar a câmera em `camera/hand_tracking.py` não afeta `main.py`, que não usa o módulo auxiliar.

## Verificação manual

1. Confira os imports com o comando da instalação.
2. Execute `python main.py`, informe um nome e verifique se a janela abre.
3. Mostre uma mão e confira o desenho dos pontos.
4. Pressione `g`, movimente a mão e pressione `s`.
5. Repita a coleta e finalize com Esc.
6. Execute `python ver_dados.py` na raiz.
7. Confira os novos IDs e a existência de landmarks com esses IDs.
8. Use a consulta de contagem para identificar coletas sem pontos.

O ZIP não contém uma suíte automatizada. A documentação foi produzida a partir da análise do código; instalação gráfica, qualidade da detecção e captura com hardware precisam ser verificadas localmente.

## Problemas comuns

| Sintoma | Causa possível e ação |
| --- | --- |
| `ModuleNotFoundError` | Ative o ambiente correto e instale as dependências com `python -m pip` |
| `mediapipe` não possui `solutions` | A distribuição instalada pode não expor a API legada; confira a versão e o comando de imports |
| `No matching distribution found` | Confira versão e arquitetura do Python e os pacotes disponíveis para o sistema |
| Não foi possível acessar a câmera | Confira permissões, uso por outro aplicativo e o índice em `main.py` |
| Janela não abre ou erro em `imshow` | Use ambiente gráfico local e uma distribuição OpenCV com interface gráfica |
| `g` e `s` não respondem | Coloque a janela da câmera em foco e use letras minúsculas |
| `no such table: sinais` | Inicialize as tabelas com `main.py` e execute a consulta a partir da raiz; `teste_sqlite.py` cria somente `teste` |
| Banco aparentemente vazio | Confira o caminho: `ver_dados.py` usa o diretório atual e pode abrir outro arquivo |
| Coleta sem landmarks | Houve acionamento de `g`, mas nenhum ponto foi detectado enquanto a coleta estava ativa |
| Captura lenta e muitas mensagens no terminal | Cada ponto abre uma conexão, imprime o caminho e confirma uma inserção |
| `database is locked` | Verifique outros processos ou clientes mantendo transações de escrita abertas |

## Limitações e evolução

### Limitações identificadas no código

- Não há reconhecimento semântico, tradução, métricas de acurácia ou modelo treinado próprio.
- Não há captura facial ou corporal implementada.
- Não há validação de nome vazio, duração mínima ou qualidade da amostra.
- Não há identificação de participante, lateralidade persistida ou timestamps.
- Cada ponto gera conexão e transação próprias, o que pode reduzir a taxa de captura.
- A lista cresce durante toda a execução e só é convertida em array ao sair.
- Não há normalização adicional, segmentação temporal, padronização de tamanho ou divisão de dataset.
- Não há transação única por coleta, tratamento estruturado de exceções ou recuperação automática.
- A liberação da câmera está depois do laço, sem `try/finally`; uma exceção pode impedir a limpeza normal. Não há chamada explícita a `hands.close()`.
- O banco é ignorado pelo Git. Versionar o código não inclui as amostras; faça cópia do banco separadamente quando necessário.

### Próximos passos propostos — ainda não implementados

1. Validar o ambiente e registrar versões reproduzíveis das dependências.
2. Separar captura, interface, persistência e preparação do dataset em funções ou classes.
3. Reutilizar a conexão e inserir pontos em lotes, com transações controladas.
4. Validar os rótulos e registrar metadados das coletas.
5. Definir critérios de coleta e conferir os rótulos com pessoas com conhecimento de Libras.
6. Padronizar lateralidade, coordenadas, pontos ausentes e sequências de frames.
7. Separar treino, validação e teste por participante ou sessão, evitando distribuir frames quase idênticos entre conjuntos.
8. Implementar treinamento, avaliação e inferência em `models/`, escolhendo o modelo conforme o tipo de sinal e os dados disponíveis.
9. Ampliar as informações capturadas conforme as necessidades dos sinais estudados.

Um futuro modelo deve receber características preparadas a partir das coordenadas. IDs do banco e rótulos não devem ser tratados como coordenadas de entrada. Essa preparação e o treinamento não fazem parte do código entregue.

## Contribuição e licença

Para contribuir, descreva o problema, mantenha exemplos compatíveis com o banco e atualize esta documentação ao alterar controles, dependências ou dados. Ao relatar falhas, informe sistema operacional, versão do Python, dependências, comando executado e mensagem de erro.

O arquivo fornecido não contém `LICENSE` nem declaração de autoria no código. Uma licença deve ser definida pelos responsáveis antes de apresentar o projeto como licenciado para redistribuição. Este README não atribui uma licença por suposição.

## Referências

- [MediaPipe Hands — API legada usada no projeto](https://chuoling.github.io/mediapipe/solutions/hands.html)
- [MediaPipe 0.10.21 — distribuição e arquivos por plataforma](https://pypi.org/project/mediapipe/0.10.21/)

A fonte de verdade para o comportamento específico deste projeto são os scripts listados neste README. Recursos propostos não devem ser interpretados como funcionalidades concluídas.
