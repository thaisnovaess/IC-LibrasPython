# Reconhecimento Integrado de Libras Context

**Gathered:** 2026-09-19
**Spec:** `.specs/features/reconhecimento-integrado-libras/spec.md`
**Status:** Ready for design

## Feature Boundary

Um projeto local integra reconhecimento manual e facial, coleta dataset, treina e avalia os modelos e apresenta os resultados para confirmação humana.

## Implementation Decisions

### Integração

- Os dois projetos serão módulos do mesmo produto.
- As previsões permanecem separadas até a camada de fusão.
- A correção humana é a autoridade sobre a mensagem final.
- A apresentação de segunda concentra-se no pipeline manual da Thais.
- O pipeline facial de Pedro permanece como segunda etapa do mesmo produto.

### Privacidade

- O fluxo cotidiano não grava mídia.
- O coletor científico grava vídeo somente com opção explícita.

### Agent's Discretion

- Estrutura interna de módulos, formato dos artefatos e composição visual.
- Modelo baseline, desde que as métricas sejam independentes e reproduzíveis.

### Declined / Undiscussed Gray Areas -> Assumptions

- O sistema retornará resultado parcial quando somente uma modalidade estiver visível.
- O primeiro modelo treinável será um baseline SVM; redes temporais ficam plugáveis.

## Specific References

- Projeto de Thais para sinais manuais.
- Projeto de Pedro para expressões faciais.

## Deferred Ideas

- Tradução gramatical completa de Libras para português.
