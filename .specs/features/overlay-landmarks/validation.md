# Overlay de landmarks da mão - Validation

**Verdict**: PASS ✅
**Date**: 2026-09-19
**Spec**: critérios inline fornecidos ao Verifier
**Diff range**: `HEAD` + working tree não commitada, restrita à superfície de landmarks/overlay
**Verifier**: independent sub-agent (author != verifier)

---

## Task Completion

| Entrega | Status | Notes |
| --- | --- | --- |
| Endpoint local de landmarks | ✅ Done | Retorna landmarks normalizados e rejeita data URL inválida. |
| Canvas com pontos e conexões | ✅ Done | Desenha 21 pontos e 21 conexões por mão; alinhamento físico aguarda UAT. |
| Limpeza e pausa do rastreamento | ✅ Done | Limpeza sem mão e pausa com retomada, inclusive após erro, têm teste comportamental. |
| Regressão do reconhecimento | ✅ Verified | O fluxo HTTP de previsão e a suíte completa continuam passando. |

## Spec-Anchored Acceptance Criteria

| Criterion | Spec-defined outcome | `file:line` + assertion/evidence | Result |
| --- | --- | --- | --- |
| AC1: câmera ativa e mão detectada | Desenhar 21 pontos e conexões alinhados sobre o vídeo. | `tests/test_hand_overlay.cjs:25-34` - `assert.equal(context.calls.strokes, 21)`, `assert.equal(context.calls.arcs, 42)` e `assert.equal(context.calls.fills, 42)` comprovam as 21 conexões e os dois círculos de cada um dos 21 pontos. `webapp/static/hand-overlay.js:16-27` aplica a geometria de `object-fit: cover`; `webapp/static/styles.css:149-162` aplica o mesmo espelhamento ao vídeo e ao canvas. | ✅ PASS automatizado; alinhamento perceptual pendente de UAT. |
| AC2: nenhuma mão ou câmera desligada | Overlay vazio. | `tests/test_hand_overlay.cjs:36-42` - `assert.deepEqual(context.calls, { clear: 1, strokes: 0, arcs: 0, fills: 0 })`. `webapp/static/app.js:76-82` limpa o canvas ao parar o rastreamento, e `webapp/static/app.js:269-279` chama essa parada antes de desligar a câmera. | ✅ PASS |
| AC3: rastreamento local, sem persistência, pausado durante previsão | Processar em memória com detector local e não disputar inferência durante `/api/predict`. | `tests/test_hand_overlay.cjs:44-56` - `assert.equal(state.trackingPaused, true)` dentro da operação e `false` após sucesso e erro; `tests/test_hand_overlay.cjs:59-63` - `assert.match(..., /HandOverlay\.withTrackingPaused\(state/)` protege a integração. O callback contém captura e `/api/predict` em `webapp/static/app.js:224-266`. O endpoint apenas delega ao detector em `webapp/application.py:128-129`, sem repositório ou persistência. | ✅ PASS |
| AC4: reconhecimento existente continua funcionando | `/api/predict` mantém status, letra, confiança e versão do modelo. | `tests/test_server.py:219-222` - `self.assertEqual(200, status)`, `self.assertEqual("A", payload["manual_label"])`, `self.assertEqual(0.91, payload["manual_confidence"])` e `self.assertEqual("static-fixture-v1", payload["manual_model_version"])`. | ✅ PASS |

**Status**: 4/4 ACs correspondem ao resultado definido. A parte geométrica de AC1 passou em automação; o alinhamento sobre uma mão real continua como aceite humano explícito.

## API Contract and Wiring

- `tests/test_server.py:130-144` prova HTTP 400 e mensagem de data URL inválida em `/api/landmarks`.
- `tests/test_server.py:224-279` prova HTTP 200, uma mão com exatamente 21 landmarks, valor do primeiro ponto e resposta vazia sem mão.
- `tests/test_server.py:77-82` prova que a página inclui o canvas `hand-overlay` e carrega `hand-overlay.js`.
- `webapp/static/index.html:32-35` sobrepõe o canvas ao vídeo; `webapp/static/index.html:133-134` carrega o módulo antes de `app.js`.
- `recognition/runtime.py:141-151` executa a detecção local sob a mesma trava usada pelo reconhecimento em `recognition/runtime.py:169-183`.

## Discrimination Sensor

As mutações foram feitas somente em `/tmp/ic-overlay-verifier-final.fy2pZr`, removido ao final. O `git status --porcelain` da árvore real permaneceu idêntico ao baseline.

| Mutation | File:line | Description | Killed? |
| --- | --- | --- | --- |
| 1 | `webapp/static/hand-overlay.js:57` | Pausa removida ao trocar `trackingPaused = true` por `false`. | ✅ Killed por `tests/test_hand_overlay.cjs:48`: `false !== true`. |
| 2 | `webapp/static/hand-overlay.js:30` | Limpeza do canvas removida. | ✅ Killed por `tests/test_hand_overlay.cjs:30` e `tests/test_hand_overlay.cjs:41`: zero limpezas em vez de uma. |
| 3 | `webapp/application.py:129` | Endpoint alterado para sempre retornar `{"hands": []}`. | ✅ Killed por `tests/test_server.py:275`: zero mãos em vez de uma. |

**Sensor depth**: lightweight, 3 mutações
**Result**: 3/3 killed - PASS ✅

## Interactive UAT

**Status**: ⏭️ Pendente.

O teste automatizado confirma quantidade de pontos, esqueleto, transformação de coordenadas usada pelo código, limpeza e pausa. Ele não observa uma mão real. Para o aceite visual, ativar a câmera e confirmar que os 21 pontos acompanham punho, juntas e pontas dos dedos ao mover a mão e redimensionar a janela. Também confirmar que o overlay some quando a mão sai do quadro e quando a câmera é desligada.

Essa pendência não representa falha automatizada. Ela limita a conclusão ao ambiente local testado até a confirmação humana.

## Code Quality

| Principle | Status |
| --- | --- |
| Minimum code | ✅ Funções pequenas e isoladas em `hand-overlay.js`. |
| Surgical changes | ✅ Alterações restritas ao detector, endpoint, wiring visual e testes. |
| No scope creep | ✅ Não há persistência, envio externo ou nova dependência. |
| Matches patterns | ✅ API usa o mesmo servidor e contrato JSON existentes. |
| Thread safety | ✅ `recognition/runtime.py:141-151` e `recognition/runtime.py:169-183` compartilham `_vision_lock`. |
| Spec-anchored outcome check | ✅ As asserções verificam os valores exigidos. |
| Per-layer coverage expectation | ✅ Helper visual, integração por wiring e rota HTTP têm cobertura de sucesso, vazio e erro. |
| Every test maps to a requirement | ✅ Testes novos mapeiam AC1-AC4 e o contrato inválido da rota. |
| Documented guidelines | ✅ `/Users/arthurcosta/.codex/skills/tlc-spec-driven/references/coding-principles.md`. |

## Edge Cases

- [x] Detector retorna nenhuma mão: API responde `hands: []` e o desenho apenas limpa o canvas.
- [x] Data URL inválida: API responde HTTP 400 com mensagem do contrato.
- [x] Câmera desligada: rastreamento é cancelado e o overlay é limpo.
- [x] Erro na previsão: a pausa é revertida em `finally`.
- [x] Resposta atrasada após desligar: `trackingGeneration` impede redesenho obsoleto.
- [ ] Movimento real, resize e variações de webcam: aguardam UAT humano.

## Gate Check

- **Python gate**: `.venv/bin/python -m unittest discover -s tests -v`
- **JavaScript gate**: `node --check webapp/static/hand-overlay.js && node --check webapp/static/app.js && node --test tests/test_hand_overlay.cjs`
- **Diff gate**: `git diff --check`
- **Result**: 45 testes Python e 4 testes JavaScript passaram; 0 falharam; 0 foram ignorados. As duas verificações de sintaxe e o diff check passaram.
- **Test count before feature**: 43 testes Python e nenhum teste JavaScript dedicado ao overlay.
- **Test count after feature**: 45 testes Python + 4 testes JavaScript.
- **Delta**: +6 testes.
- **Warnings**: mensagens informativas do MediaPipe/TFLite; não alteraram o exit code.

## Requirement Traceability

| Requirement | Status |
| --- | --- |
| AC1 | ✅ Verified em automação; UAT físico pendente |
| AC2 | ✅ Verified |
| AC3 | ✅ Verified |
| AC4 | ✅ Verified |

## Summary

**Overall**: ✅ Ready for human UAT.

**Spec-anchored check**: 4/4 ACs correspondem ao resultado definido.
**Sensor**: 3/3 mutações eliminadas.
**Gate**: 49 testes passaram.

O overlay está integrado, limpa corretamente, pausa durante a previsão e preserva o reconhecimento. Falta apenas o aceite visual com a câmera real para confirmar o alinhamento perceptual em movimento e resize.
