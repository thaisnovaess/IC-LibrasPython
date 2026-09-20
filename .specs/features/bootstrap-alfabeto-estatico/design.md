# Bootstrap do Alfabeto Estático Design

**Spec**: `.specs/features/bootstrap-alfabeto-estatico/spec.md`
**Status**: Approved by implementation request

## Architecture Overview

```mermaid
flowchart LR
    Images[Imagens A-Y] --> Hands[MediaPipe Hands]
    Hands --> Static[manual-static-v1: 63 valores]
    Static --> SVM[SVM probabilístico]
    SVM --> Artifact[manual.joblib]
    Camera[Câmera] --> Holistic[MediaPipe Holistic]
    Holistic --> Static
    Artifact --> Runtime[IntegratedRecognizer]
    Runtime --> API[/api/predict]
```

## Code Reuse Analysis

| Component | Location | How to Use |
| --- | --- | --- |
| Normalização manual | `recognition/features.py` | Reutilizar `normalize_hand` |
| Contrato de artefato | `training/train.py` | Manter chaves consumidas pelo runtime |
| Runtime integrado | `recognition/runtime.py` | Selecionar features pelo contrato do artefato |
| Dataset externo | cache local do Kaggle | Ler sem copiar ou versionar imagens |

## Components

### Static hand features

- **Purpose**: Agregar uma mão detectada em um vetor fixo de 63 valores.
- **Location**: `recognition/features.py`
- **Interface**: `static_manual_features(frames) -> list[float]`.

### Bootstrap trainer

- **Purpose**: Extrair landmarks de imagens, treinar e avaliar o modelo local.
- **Location**: `training/bootstrap_alphabet.py`
- **Interfaces**: CLI com dataset, limites por classe, seed e diretório de saída.

### Runtime contract selection

- **Purpose**: Usar `manual-static-v1` quando declarado no artefato e rejeitar contratos desconhecidos.
- **Location**: `recognition/runtime.py`

## Error Handling Strategy

| Error Scenario | Handling | User Impact |
| --- | --- | --- |
| Imagem sem mão | Contabilizar e continuar | Lote aproveita imagens válidas |
| Dataset vazio | `ValueError` explícito | Nenhum modelo enganoso é criado |
| Contrato desconhecido | Runtime indisponível | Entrada manual permanece ativa |
| Modelo ausente | Estado existente `model_unavailable` | Sem previsão inventada |

## Risks & Concerns

| Concern | Location | Impact | Mitigation |
| --- | --- | --- | --- |
| Dataset sem licença declarada | catálogo Kaggle | Impede redistribuição segura | Uso local, sem versionar dados/modelo, origem documentada |
| Dataset sem participante | fonte externa | Métrica pode conter vazamento de identidade | Relatório marca limitação explicitamente |
| Imagens 64x64 | fonte externa | MediaPipe falha em parte das amostras | Redimensionar para 512x512 e contar rejeições |
| Letras dinâmicas ausentes | classes da fonte | Cobertura incompleta de A-Z | Exibir 21 classes suportadas e manter coleta futura |

## Tech Decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Detector do bootstrap | MediaPipe Hands | Melhor detecção nas imagens recortadas que Holistic |
| Feature | mão normalizada média, 63 valores | Mesmo contrato em imagem e sequência ao vivo |
| Classificador | SVM RBF probabilístico | Compatível com o baseline atual e fornece confiança |
| Persistência | joblib + relatório JSON | Já consumido pelo runtime e ignorado pelo Git |
