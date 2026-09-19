# Reconhecimento Integrado de Libras Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill. Local commits remain excluded until the user explicitly authorizes Git commits.

**Design**: `.specs/features/reconhecimento-integrado-libras/design.md`
**Status**: In Progress

## Test Coverage Matrix

| Layer | Scope | Expectation | Location |
| --- | --- | --- | --- |
| Unit | fusão e contratos | completa, parcial, indisponível e nenhuma detecção | `tests/test_recognition.py` |
| Unit | dataset e features | validação, 21/468 pontos, normalização e 30 frames | `tests/test_features.py` |
| Integration | API e SQLite | sucesso, entrada inválida, modelo ausente e persistência | `tests/test_server.py` |
| Contract | CLIs científicos | configuração inválida e ausência de dependências | `tests/test_training_contract.py` |

Proveniência: padrões atuais de `tests/`, instruções do `README.md` e requisitos de `docs/ESCOPO_MVP.md`. Aplica-se cobertura forte de critérios e bordas.

## Gate Check Commands

- **quick**: `PYTHONDONTWRITEBYTECODE=1 python3.14 -m unittest discover -v`
- **full**: `PYTHONDONTWRITEBYTECODE=1 python3.14 -W error -m unittest discover -v`
- **build**: `PYTHONDONTWRITEBYTECODE=1 python3.14 -W error -m unittest discover -v && node --check webapp/static/app.js`

## Execution Plan

### Phase 1: Foundation

```text
T1 -> T2
```

### Phase 2: Scientific Pipeline

```text
T3 -> T4
```

### Phase 3: Product Integration

```text
T5 -> T6 -> T7
```

## Task Breakdown

### T1: Criar contratos integrados e fusão

**What**: Definir resultados manuais, faciais e integrados com estados explícitos.
**Where**: `recognition/contracts.py`, `recognition/fusion.py`
**Depends on**: None
**Reuses**: `models/recognizer.py`
**Requirement**: LIBRAS-03, LIBRAS-05

**Tools**:
- MCP: NONE
- Skill: `senior-fullstack-mentor`, `tlc-spec-driven`

**Done when**:
- [ ] Fusão completa mantém os dois rótulos e confianças
- [ ] Fusão parcial identifica a modalidade ausente
- [ ] Ausência de modelos nunca gera rótulo
- [ ] Gate quick passa com pelo menos 11 testes

**Tests**: unit
**Gate**: quick

### T2: Implementar dataset e pré-processamento

**What**: Validar amostras, normalizar 21/468 landmarks e padronizar 30 frames.
**Where**: `recognition/dataset.py`, `recognition/features.py`
**Depends on**: T1
**Reuses**: estrutura de landmarks de `main.py`
**Requirement**: LIBRAS-01, LIBRAS-02

**Tools**:
- MCP: NONE
- Skill: `senior-fullstack-mentor`, `tlc-spec-driven`

**Done when**:
- [ ] Metadados ausentes são rejeitados antes da captura
- [ ] Canais de mãos e face possuem dimensões fixas
- [ ] Sequências são interpoladas para 30 frames
- [ ] Gate quick passa com pelo menos 16 testes

**Tests**: unit
**Gate**: quick

### T3: Implementar coletor científico

**What**: Capturar mãos e face sincronizadas e salvar amostra em lote.
**Where**: `training/collect.py`
**Depends on**: T2
**Reuses**: câmera e MediaPipe usados por `main.py`
**Requirement**: LIBRAS-01, LIBRAS-05

**Tools**:
- MCP: NONE
- Skill: `senior-fullstack-mentor`, `tlc-spec-driven`

**Done when**:
- [ ] CLI exige participante e os dois rótulos
- [ ] Vídeo só é aberto com `--store-video`
- [ ] Amostra inclui timestamps, resolução, FPS e iluminação
- [ ] Gate full passa com pelo menos 18 testes

**Tests**: unit
**Gate**: full

### T4: Implementar treinamento e avaliação

**What**: Treinar SVMs separados por participante e gerar métricas e matrizes.
**Where**: `training/train.py`
**Depends on**: T3
**Reuses**: contrato de features de `recognition/features.py`
**Requirement**: LIBRAS-02

**Tools**:
- MCP: NONE
- Skill: `senior-fullstack-mentor`, `tlc-spec-driven`

**Done when**:
- [ ] Split não mistura participante entre treino e teste
- [ ] Relatório contém acurácia, precisão, recall, F1 e matriz
- [ ] Classes insuficientes são identificadas
- [ ] Gate full passa com pelo menos 21 testes

**Tests**: unit
**Gate**: full

### T5: Implementar runtime MediaPipe e modelos

**What**: Extrair as duas modalidades, carregar artefatos e produzir previsão integrada.
**Where**: `recognition/runtime.py`, `models/recognizer.py`
**Depends on**: T2, T4
**Reuses**: contrato `RecognitionResult`
**Requirement**: LIBRAS-03, LIBRAS-05

**Tools**:
- MCP: NONE
- Skill: `senior-fullstack-mentor`, `tlc-spec-driven`

**Done when**:
- [ ] Runtime carrega os dois modelos e metadados
- [ ] Dependência ou artefato ausente produz `model_unavailable`
- [ ] Frames processados não são persistidos
- [ ] Gate full passa com pelo menos 24 testes

**Tests**: unit
**Gate**: full

### T6: Integrar API, banco e interface

**What**: Receber sequência de câmera, exibir modalidades e salvar correção completa.
**Where**: `webapp/`, `database/communication.py`
**Depends on**: T1, T5
**Reuses**: sessões, eventos e interface existentes
**Requirement**: LIBRAS-03, LIBRAS-04, LIBRAS-05

**Tools**:
- MCP: NONE
- Skill: `senior-fullstack-mentor`, `tlc-spec-driven`

**Done when**:
- [ ] API valida JPEGs e limite de 2 MB
- [ ] Interface exibe rótulos e confianças separados
- [ ] Correção persiste previsão original e expressão
- [ ] Gate build passa com pelo menos 29 testes

**Tests**: integration
**Gate**: build

### T7: Documentar e validar a entrega

**What**: Documentar ambientes, coleta, treino, execução e evidências verificadas.
**Where**: `README.md`, `docs/`, `.specs/features/reconhecimento-integrado-libras/validation.md`
**Depends on**: T1, T2, T3, T4, T5, T6
**Reuses**: documentação atual do projeto
**Requirement**: LIBRAS-01, LIBRAS-02, LIBRAS-03, LIBRAS-04, LIBRAS-05

**Tools**:
- MCP: NONE
- Skill: `senior-fullstack-mentor`, `tlc-spec-driven`

**Done when**:
- [ ] README distingue validação local de pendências de dataset e câmera
- [ ] Gate build passa com pelo menos 29 testes
- [ ] Sensor de discriminação mata mutações de estado e fusão
- [ ] Relatório de validação contém evidência por requisito

**Tests**: integration
**Gate**: build

## Phase Execution Map

```text
T1 -> T2
T2 -> T3
T3 -> T4
T2 -> T5
T4 -> T5
T1 -> T6
T5 -> T6
T1 -> T7
T2 -> T7
T3 -> T7
T4 -> T7
T5 -> T7
T6 -> T7
```
