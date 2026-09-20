# Bootstrap do Alfabeto Estático Specification

## Problem Statement

O pipeline científico funciona em Python 3.11, mas a interface permanece bloqueada porque não existe `manual.joblib`. A primeira demonstração precisa reconhecer letras estáticas sem apresentar dados públicos como validação científica do produto.

## Goals

- [x] Gerar localmente um modelo para as 21 letras estáticas disponíveis no dataset público.
- [x] Usar o mesmo contrato de features no treinamento e na inferência pela câmera.
- [x] Expor o reconhecedor como disponível e manter limitações e origem rastreáveis.

## Out of Scope

| Feature | Reason |
| --- | --- |
| Letras dinâmicas H, J, K, X e Z | Exigem trajetória validada e não existem na fonte escolhida |
| Reconhecimento facial | A apresentação prioriza o módulo manual |
| Alegação de acurácia científica | A fonte não identifica participantes e informa licença desconhecida |
| Versionar imagens ou modelos derivados | Dados e artefatos permanecem locais e ignorados pelo Git |

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Fonte | Kaggle `williansoliveira/libras`, versão 1 | Contém 21 classes estáticas e já foi baixada localmente | yes |
| Uso da fonte | Bootstrap acadêmico local | O catálogo informa licença `Unknown`; não haverá redistribuição | assumed |
| Feature manual | 21 landmarks normalizados e agregados pela média temporal | Mantém treino e câmera no mesmo contrato | assumed |
| Avaliação | Split fornecido pelo dataset, identificado como não científico | Não há identidade de participante para split por pessoa | assumed |
| Confiança mínima | O classificador sempre retorna a melhor classe e a confiança probabilística | A confirmação humana já existe na interface | assumed |

**Open questions:** none - all resolved or logged above.

## User Stories

### P1: Modelo bootstrap para a demonstração

**User Story**: Como apresentador, quero executar o projeto localmente e identificar letras estáticas pela câmera para demonstrar o fluxo completo.

**Acceptance Criteria**:

1. WHEN o bootstrap processar uma imagem com uma mão detectável THEN the system SHALL produzir exatamente 63 valores finitos no contrato `manual-static-v1`.
2. IF uma imagem não contiver uma mão detectável THEN the system SHALL descartá-la e contabilizar a rejeição sem interromper o lote.
3. WHEN o treinamento terminar THEN the system SHALL salvar `artifacts/models/manual.joblib` com modelo probabilístico, versão, classes e contrato de features.
4. WHEN o artefato `manual-static-v1` for carregado THEN the system SHALL usar 63 valores agregados da mão detectada na inferência.
5. WHEN o servidor iniciar com o artefato válido THEN the system SHALL retornar `available: true` e `manual_available: true` em `/api/status`.
6. IF a fonte não oferecer identidade de participante THEN the system SHALL marcar o relatório como `provider_split_not_participant_independent`.

**Independent Test**: Treinar um artefato reduzido, carregá-lo no runtime e executar uma predição em imagem do conjunto de teste.

## Edge Cases

- IF nenhum arquivo de imagem existir THEN the system SHALL interromper o bootstrap com mensagem explícita.
- IF menos de duas classes tiverem amostras válidas THEN the system SHALL interromper o treinamento.
- IF o artefato declarar um contrato desconhecido THEN the system SHALL retornar `model_unavailable` sem inventar previsão.

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| BOOT-01 | Modelo bootstrap | Validate | Verified |
| BOOT-02 | Modelo bootstrap | Validate | Verified |
| BOOT-03 | Modelo bootstrap | Validate | Verified |
| BOOT-04 | Modelo bootstrap | Validate | Verified automatically; browser-camera UAT pending |

**Coverage:** 4 total, 4 mapped to tasks, 0 unmapped.

## Success Criteria

- [x] `manual.joblib` é gerado com 21 classes estáticas.
- [x] `/api/status` informa reconhecimento manual disponível.
- [x] Uma imagem de teste não usada no treino recebe letra e confiança.
- [x] Todos os testes automatizados passam no Python 3.11.
