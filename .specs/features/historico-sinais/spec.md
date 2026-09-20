# Histórico de Sinais Specification

## Problem Statement

A interface mantém a mensagem construída, mas não mostra quais sinais da câmera foram confirmados nem quais previsões precisaram de correção.

## Goals

- [x] Exibir no front o histórico de sinais confirmados na sessão atual.
- [x] Diferenciar previsões aceitas de previsões corrigidas.
- [x] Manter entradas manuais fora do histórico de reconhecimento.

## Out of Scope

| Feature | Reason |
| --- | --- |
| Histórico entre sessões | A interface cria uma sessão local nova a cada carregamento |
| Exibir prévias não confirmadas | A prévia não representa um resultado confirmado |
| Excluir eventos pelo histórico | A solicitação exige somente consulta visual |

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Ordem | Mais recente primeiro | Facilita acompanhar a última identificação | assumed |
| Conteúdo | Letra prevista, confirmada, confiança e horário | Explica o resultado sem expor imagens | assumed |
| Escopo | Somente eventos `letter` com origem `recognizer` | Separa reconhecimento de digitação manual | assumed |

**Open questions:** none - defaults are explicit and reversible.

## User Stories

### P1: Consultar sinais identificados

**User Story**: Como usuário, quero consultar os sinais confirmados pela câmera para entender a sequência de reconhecimentos e correções da sessão.

**Acceptance Criteria**:

1. WHEN um sinal reconhecido for confirmado THEN the system SHALL exibi-lo no histórico com letra prevista, letra confirmada, confiança e horário.
2. WHEN houver mais de um sinal confirmado THEN the system SHALL ordenar os registros do mais recente para o mais antigo.
3. IF a letra confirmada for diferente da prevista THEN the system SHALL indicar visualmente a correção e preservar os dois valores.
4. IF um evento vier de inserção manual, controle da mensagem ou prévia não confirmada THEN the system SHALL não incluí-lo no histórico.
5. IF nenhum sinal tiver sido confirmado THEN the system SHALL apresentar um estado vazio explícito.

## Edge Cases

- IF a confiança estiver ausente THEN the system SHALL exibir que a confiança não está disponível.
- IF o horário for inválido THEN the system SHALL preservar o item sem interromper a renderização do histórico.

## Requirement Traceability

| Requirement ID | Story | Status |
| --- | --- | --- |
| HISTORY-01 | Consultar sinais identificados | Verified |

**Coverage:** 1 total, 1 mapped, 0 unmapped.

## Success Criteria

- [x] O histórico é atualizado depois de confirmar ou corrigir uma letra.
- [x] Entradas manuais não aparecem como reconhecimento.
- [x] Testes JavaScript e Python permanecem verdes.
