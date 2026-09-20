# Prévia de Letra e Frase Manual Specification

## Problem Statement

A interface só apresenta a letra depois do comando de identificação e a entrada manual aceita um único caractere. O usuário precisa de retorno visual durante o posicionamento da mão e de uma alternativa rápida para inserir uma frase completa.

## Goals

- [x] Exibir uma prévia estável da letra durante o rastreamento da mão.
- [x] Manter a identificação por sequência como resultado confirmável.
- [x] Permitir inserir e persistir uma frase manual de uma só vez.

## Out of Scope

| Feature | Reason |
| --- | --- |
| Confirmar automaticamente a prévia | A confirmação humana continua obrigatória |
| Persistir frames da câmera | A operação cotidiana não grava imagens |
| Alterar o esquema SQLite existente | A frase será decomposta atomicamente nos eventos atuais |

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Janela da prévia | Cinco leituras | Equilibra estabilidade e resposta visual | assumed |
| Estabilidade | Três rótulos iguais e confiança mediana mínima de 60% | Evita exibir cada oscilação instantânea | assumed |
| Frase manual | Até 500 caracteres; espaços internos normalizados | Limita payload e preserva texto legível | assumed |
| Persistência | Um evento existente por caractere, em uma transação | Mantém compatibilidade com sessões atuais | assumed |

**Open questions:** none - defaults are explicit and reversible.

## User Stories

### P1: Prévia contínua e estável

**User Story**: Como usuário da câmera, quero visualizar a provável letra enquanto posiciono a mão para ajustar o sinal antes da análise final.

**Acceptance Criteria**:

1. WHEN uma mão for detectada THEN the system SHALL retornar landmarks e uma previsão provisória sem processar a imagem duas vezes.
2. WHEN pelo menos três das últimas cinco previsões tiverem o mesmo rótulo e confiança mediana mínima de 0,60 THEN the system SHALL exibir a letra e a confiança como prévia.
3. IF a estabilidade mínima não for atingida THEN the system SHALL ocultar a prévia; IF a mão desaparecer ou a câmera desligar THEN the system SHALL também limpar o histórico.
4. WHEN o usuário acionar `Identificar sinal` THEN the system SHALL pausar a prévia e manter a análise confirmável de 12 frames.

### P1: Entrada manual de frase

**User Story**: Como usuário, quero digitar uma frase completa para complementar a comunicação sem inserir letra por letra.

**Acceptance Criteria**:

1. WHEN o usuário enviar uma frase válida THEN the system SHALL persistir letras, acentos, pontuação e espaços normalizados na ordem original dentro de uma transação.
2. IF o texto estiver vazio ou ultrapassar 500 caracteres THEN the system SHALL rejeitar a entrada com mensagem explícita.
3. WHEN a sessão for consultada depois da inserção THEN the system SHALL reconstruir a frase integral e manter compatibilidade com os eventos anteriores.

## Edge Cases

- IF a previsão provisória for nula THEN the system SHALL limpar o histórico de estabilidade.
- IF a persistência de qualquer caractere falhar THEN the system SHALL reverter toda a frase.
- IF a frase contiver quebras de linha ou espaços repetidos THEN the system SHALL normalizá-los para um único espaço.

## Requirement Traceability

| Requirement ID | Story | Status |
| --- | --- | --- |
| PREVIEW-01 | Prévia contínua e estável | Verified |
| TEXT-01 | Entrada manual de frase | Verified |

**Coverage:** 2 total, 2 mapped, 0 unmapped.

## Success Criteria

- [x] Prévia estável aparece antes do botão de identificação.
- [x] Frase com acentos e pontuação é persistida e reconstruída.
- [x] Testes Python e JavaScript permanecem verdes.
