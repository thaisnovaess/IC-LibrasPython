# Reconhecimento Integrado de Libras Specification

## Problem Statement

O projeto possui coleta inicial de landmarks das mãos e uma interface de comunicação, mas não reconhece sinais nem expressões faciais. A solução deve reunir os projetos de Thais e Pedro em um único fluxo local, mantendo os dois classificadores avaliáveis de forma independente.

## Goals

- [ ] Capturar mãos e rosto da mesma sequência de vídeo.
- [ ] Normalizar, treinar, avaliar e carregar modelos manuais e faciais.
- [ ] Combinar previsões com confiança e permitir confirmação ou correção.
- [ ] Operar sem enviar imagens para serviços externos.

## Out of Scope

| Feature | Reason |
| --- | --- |
| Tradução gramatical irrestrita de toda a Libras | Exige corpus linguístico e pesquisa além das duas propostas |
| Identificação biométrica | Não contribui para o reconhecimento linguístico |
| Acurácia mínima garantida antes da coleta | Métrica depende de dados reais não vistos no treinamento |
| Implantação em nuvem | As propostas e o MVP usam processamento local |

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Forma da entrega | Um projeto integrado | Solicitante confirmou que os dois trabalhos se completam | yes |
| Resultado exibido | Sinal/letra e expressão facial em campos separados | Evita esconder incerteza de uma modalidade | assumed |
| Persistência de mídia | Desligada no uso cotidiano e explícita na coleta | Minimiza exposição de dados pessoais | assumed |
| Falta de uma modalidade | Retornar resultado parcial identificado como parcial | Permite uso quando mão ou rosto sai do quadro | assumed |
| Ambiente | Python 3.11 para visão e Python 3.14 compatível apenas com a interface básica | MediaPipe 0.10.21 não atende ao ambiente local 3.14 | evidence-based |

**Open questions:** none - all resolved or logged above.

## User Stories

### P1: Captura integrada

**User Story**: Como pesquisador, quero coletar mãos e face sincronizadas para construir datasets reproduzíveis.

**Acceptance Criteria**:

1. WHEN uma amostra for coletada THEN the system SHALL salvar landmarks de duas mãos e 468 pontos faciais com timestamps comuns.
2. WHEN metadados obrigatórios estiverem ausentes THEN the system SHALL rejeitar a coleta antes de abrir a câmera.
3. WHERE gravação de vídeo estiver habilitada the system SHALL exigir a opção explícita `--store-video`.
4. The system SHALL registrar rótulos manuais, faciais, participante, iluminação, resolução e FPS.

**Independent Test**: Validar uma amostra sintética contra o contrato do dataset.

### P1: Pré-processamento e treinamento

**User Story**: Como pesquisador, quero preparar e avaliar as duas modalidades separadamente para conhecer a qualidade real de cada modelo.

**Acceptance Criteria**:

1. WHEN landmarks manuais forem preparados THEN the system SHALL centralizar, escalar, alinhar e padronizar a sequência para 30 frames.
2. WHEN landmarks faciais forem preparados THEN the system SHALL centralizar no nariz, escalar pela distância interocular, alinhar e padronizar para 30 frames.
3. WHEN o treinamento for executado THEN the system SHALL separar participantes entre treino e teste sem misturar amostras da mesma pessoa.
4. WHEN a avaliação terminar THEN the system SHALL produzir acurácia, precisão, recall, F1 e matriz de confusão para cada modalidade.
5. IF uma classe não possuir amostras suficientes THEN the system SHALL interromper o treinamento com uma mensagem identificando a classe.

**Independent Test**: Treinar em um dataset sintético pequeno e validar artefatos e relatório.

### P1: Inferência e fusão

**User Story**: Como pessoa usuária, quero apresentar um sinal e uma expressão para receber um resultado textual conferível.

**Acceptance Criteria**:

1. WHEN uma sequência válida for recebida THEN the system SHALL retornar rótulo manual, confiança manual, expressão facial e confiança facial.
2. IF modelos ou dependências estiverem ausentes THEN the system SHALL retornar estado `model_unavailable` sem inventar previsão.
3. IF somente uma modalidade for detectada THEN the system SHALL retornar estado `partial` e preservar o resultado disponível.
4. WHEN o usuário corrigir o resultado THEN the system SHALL persistir previsão original, correção, expressão facial e versões dos modelos.
5. WHILE a inferência cotidiana estiver ativa the system SHALL descartar os frames após o processamento.

**Independent Test**: Injetar classificadores determinísticos e conferir o resultado integrado e persistido.

### P1: Interface acessível

**User Story**: Como pessoa surda ou ouvinte, quero visualizar a câmera, conferir resultados e formar uma mensagem.

**Acceptance Criteria**:

1. WHEN o reconhecimento estiver disponível THEN the system SHALL habilitar a captura de uma sequência pela câmera.
2. WHEN uma previsão retornar THEN the system SHALL exibir separadamente sinal/letra, expressão facial e confiança.
3. WHEN o usuário confirmar ou corrigir THEN the system SHALL adicionar o resultado à mensagem e registrar o evento.
4. IF o reconhecimento estiver indisponível THEN the system SHALL manter a inserção manual e explicar o motivo.

**Independent Test**: Executar o fluxo HTTP com reconhecedor injetado e verificar o contrato exibido.

## Edge Cases

- IF nenhum rosto ou mão for detectado THEN the system SHALL retornar `no_detection` sem gravar evento.
- IF uma imagem exceder 2 MB THEN the system SHALL responder HTTP 400.
- IF timestamps estiverem fora de ordem THEN the system SHALL rejeitar a sequência.
- WHEN duas mãos forem detectadas THEN the system SHALL manter canais esquerdo e direito separados.

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| LIBRAS-01 | Captura integrada | Implementation | Implementing |
| LIBRAS-02 | Pré-processamento e treinamento | Implementation | Implementing |
| LIBRAS-03 | Inferência e fusão | Implementation | Implementing |
| LIBRAS-04 | Interface acessível | Implementation | Implementing |
| LIBRAS-05 | Privacidade e falhas | Implementation | Implementing |

**Coverage:** 5 total, 5 mapped to tasks, 0 unmapped.

## Success Criteria

- [ ] O pipeline sintético completo gera e carrega modelos de ambas as modalidades.
- [ ] O sistema nunca retorna previsão quando o modelo está ausente.
- [ ] Os testes automatizados cobrem captura contratual, normalização, fusão, API e persistência.
- [ ] O README distingue código validado localmente de resultados dependentes do dataset real.
