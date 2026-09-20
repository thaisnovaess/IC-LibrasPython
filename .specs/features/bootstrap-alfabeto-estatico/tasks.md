# Bootstrap do Alfabeto Estático Tasks

## Execution Protocol

Implementar com `tlc-spec-driven`. Commits locais permanecem excluídos até autorização explícita do usuário.

**Design**: `.specs/features/bootstrap-alfabeto-estatico/design.md`
**Status**: Verified automatically; browser-camera UAT pending

## Test Coverage Matrix

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Features | unit | Todas as branches e bordas de BOOT-01 | `tests/test_features.py` | `.venv/bin/python -m unittest tests.test_features -v` |
| Treinamento | unit | Entrada válida, descarte e falhas de BOOT-02/03 | `tests/test_bootstrap_alphabet.py` | `.venv/bin/python -m unittest tests.test_bootstrap_alphabet -v` |
| Runtime/API | integration | Artefato válido, contrato desconhecido e status | `tests/test_recognition.py`, `tests/test_server.py` | `.venv/bin/python -m unittest discover -v` |
| Documentação/configuração | none | Build gate | - | build gate only |

## Gate Check Commands

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Quick | Features ou treinamento | `PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -v` |
| Full | Runtime e API | `PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -W error -m unittest discover -v` |
| Build | Conclusão | `PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -W error -m unittest discover -v && node --check webapp/static/app.js` |

## Execution Plan

### Phase 1: Contrato

```text
T1
```

### Phase 2: Treinamento

```text
T1 -> T2
```

### Phase 3: Integração

```text
T2 -> T3 -> T4
```

## Task Breakdown

### T1: Adicionar features estáticas

**Status**: Done
**What**: Produzir 63 valores finitos a partir de uma mão normalizada.
**Where**: `recognition/features.py`
**Depends on**: None
**Requirement**: BOOT-01
**Tests**: unit
**Gate**: quick

### T2: Implementar treinador bootstrap

**Status**: Done
**What**: Extrair imagens, treinar SVM e gerar artefato e relatório rastreáveis.
**Where**: `training/bootstrap_alphabet.py`
**Depends on**: T1
**Requirement**: BOOT-02, BOOT-03
**Tests**: unit
**Gate**: quick

### T3: Selecionar contrato no runtime

**Status**: Done
**What**: Executar `manual-static-v1` e rejeitar contratos desconhecidos.
**Where**: `recognition/runtime.py`
**Depends on**: T2
**Requirement**: BOOT-04
**Tests**: integration
**Gate**: full

### T4: Gerar modelo e documentar operação

**Status**: Done
**What**: Treinar o artefato local, registrar origem, limitações e comandos reproduzíveis.
**Where**: `docs/OPERACAO_MODELO_MANUAL.md`
**Depends on**: T3
**Requirement**: BOOT-02, BOOT-03, BOOT-04
**Tests**: none
**Gate**: build

## Phase Execution Map

```text
T1 -> T2 -> T3 -> T4
```

## Diagram-Definition Cross-Check

| Task | Depends On | Diagram Shows | Status |
| --- | --- | --- | --- |
| T1 | None | None | match |
| T2 | T1 | T1 -> T2 | match |
| T3 | T2 | T2 -> T3 | match |
| T4 | T3 | T3 -> T4 | match |

## Test Co-location Validation

| Task | Layer | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1 | Features | unit | unit | OK |
| T2 | Treinamento | unit | unit | OK |
| T3 | Runtime/API | integration | integration | OK |
| T4 | Documentação | none | none | OK |
