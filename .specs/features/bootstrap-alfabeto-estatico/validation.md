# Validation: Bootstrap do Alfabeto Estático - PASS

**Date**: 2026-09-19
**Spec**: `.specs/features/bootstrap-alfabeto-estatico/spec.md`
**Diff range**: `bf5259c (HEAD/origin/main)..working tree` (alterações locais sem commit por decisão do usuário)
**Verifier**: independent sub-agent (author != verifier)
**Verdict**: PASS

O gate automatizado da feature passou. A validação humana com a câmera do navegador permanece pendente e não está incluída neste PASS.

---

## Task Completion

| Task | Status | Notes |
| --- | --- | --- |
| T1 | Done | Contrato estático de 63 valores implementado e testado. |
| T2 | Done | Treinador, artefato e relatório rastreáveis implementados. |
| T3 | Done | Contrato estático, detector manual e API integrados. |
| T4 | Done | Modelo local gerado e operação documentada. |

## Spec-Anchored Acceptance Criteria

| Criterion | Spec-defined outcome | `file:line` + assertion | Result |
| --- | --- | --- | --- |
| AC1: imagem com mão detectável | Exatamente 63 valores finitos em `manual-static-v1`. | `tests/test_features.py:92` - `self.assertEqual(21 * 3, len(result))`; `tests/test_features.py:93` - `self.assertTrue(all(math.isfinite(value) for value in result))`; `tests/test_bootstrap_alphabet.py:94` - `self.assertEqual("manual-static-v1", artifact["feature_contract"])` | PASS |
| AC2: imagem sem mão | Descartar, contar a rejeição e continuar o lote. | `tests/test_bootstrap_alphabet.py:52` - `self.assertEqual(["A", "B"], labels)`; `tests/test_bootstrap_alphabet.py:53` - `self.assertEqual(2, len(features))`; `tests/test_bootstrap_alphabet.py:54` - `self.assertEqual({"A": 1, "B": 0}, rejected)` | PASS |
| AC3: treinamento concluído | Salvar `manual.joblib` com modelo probabilístico, versão, classes e contrato. | `tests/test_bootstrap_alphabet.py:91` carrega `manual.joblib`; `tests/test_bootstrap_alphabet.py:94` valida o contrato; `tests/test_bootstrap_alphabet.py:95` valida as classes; `tests/test_bootstrap_alphabet.py:96` valida `predict_proba`; `tests/test_bootstrap_alphabet.py:97` valida versão não vazia e prefixada; `tests/test_bootstrap_alphabet.py:98` valida igualdade entre versão retornada e artefato; `tests/test_bootstrap_alphabet.py:100` valida igualdade com o relatório persistido. | PASS |
| AC4: artefato `manual-static-v1` carregado | Usar 63 valores agregados da mão detectada na inferência. | `tests/test_recognition.py:65` seleciona o contrato estático e `tests/test_recognition.py:70` afirma `63`; `tests/test_server.py:153`-`tests/test_server.py:201` persistem o artefato, enviam imagem codificada a `/api/predict` e afirmam letra, confiança e versão. | PASS |
| AC5: servidor com artefato válido | `/api/status` retorna `available: true` e `manual_available: true`. | `tests/test_server.py:142` consulta `/api/status`; `tests/test_server.py:150` - `self.assertTrue(payload["recognizer"]["available"])`; `tests/test_server.py:151` - `self.assertTrue(payload["recognizer"]["manual_available"])`. | PASS |
| AC6: fonte sem identidade de participante | Relatório marca `provider_split_not_participant_independent`. | `tests/test_bootstrap_alphabet.py:99` - `self.assertEqual("provider_split_not_participant_independent", report["evaluation_scope"])` | PASS |

**Status**: 6/6 critérios cobertos por asserções compatíveis com o resultado definido na spec. Nenhuma lacuna de precisão foi encontrada.

## Edge Cases

| Edge case | Evidence | Result |
| --- | --- | --- |
| Nenhuma imagem existente | `tests/test_bootstrap_alphabet.py:21` - `self.assertRaisesRegex(ValueError, "Nenhuma imagem de classe encontrada")`; implementação em `training/bootstrap_alphabet.py:33`-`training/bootstrap_alphabet.py:34`. | PASS |
| Menos de duas classes válidas | `tests/test_bootstrap_alphabet.py:104` - `self.assertRaisesRegex(ValueError, "duas classes")`. | PASS |
| Contrato desconhecido | `tests/test_recognition.py:111` e `tests/test_recognition.py:112` afirmam indisponibilidade; `tests/test_recognition.py:113` afirma a mensagem explícita. | PASS |

## Persisted End-to-End Integration

`tests/test_server.py:153`-`tests/test_server.py:201` cobre a fronteira completa de regressão:

1. persiste `manual.joblib` com contrato, modelo probabilístico e versão;
2. carrega o artefato pelo `IntegratedRecognizer`;
3. codifica uma imagem JPEG como data URL;
4. envia a imagem por HTTP para `/api/predict`;
5. atravessa decodificação, landmarks, 63 features, `predict_proba` e resposta HTTP;
6. afirma `200`, letra `A`, confiança `0.91` e versão `static-fixture-v1`.

O Verifier também repetiu o smoke test com o artefato local real e `test/A/1.png` da fonte: `/api/status` retornou `available=true` e `manual_available=true`; `/api/predict` retornou HTTP 200, letra `A`, confiança `0.9091069920031819` e versão `manual-static-20260919T224222Z`. Esse resultado comprova a integração local atual, não generalização científica.

## Discrimination Sensor

| Mutation | File:line | Description | Killed? |
| --- | --- | --- | --- |
| 1 | `training/bootstrap_alphabet.py:33` | Desativou a falha para diretório sem imagens. | KILLED por `tests/test_bootstrap_alphabet.py:21`: `ValueError not raised`. |
| 2 | `training/bootstrap_alphabet.py:175` | Persistiu `model_version` vazio no artefato. | KILLED por `tests/test_bootstrap_alphabet.py:97`: prefixo `manual-static-` ausente. |
| 3 | `recognition/runtime.py:151` | Descartou a mão detectada antes da extração e predição HTTP. | KILLED por `tests/test_server.py:199`: letra esperada `A`, recebida `None`. |

**Sensor depth**: lightweight, 3 mutações direcionadas aos gaps anteriores e ao caminho de maior risco.
**Result**: 3/3 killed, PASS.
**Isolation**: mutações executadas em worktree descartável e removidas. O hash SHA-256 de `git status --porcelain=v1 -uall` permaneceu `3d321c3c9092bbaf58b3f797905117ec2140246b1ce032f0eb44a08a7867077c` antes e depois do sensor.

## Interactive UAT

| Test | Result | Details |
| --- | --- | --- |
| Câmera real no navegador | PENDING | Uma pessoa ainda precisa confirmar detecção da mão, letra proposta, correção, confirmação e persistência da mensagem. |

O UAT pendente não invalida o gate automatizado. Ele impede afirmar que a experiência ao vivo na câmera já foi validada nesta máquina e condição de iluminação.

## Code Quality

| Principle | Status |
| --- | --- |
| Minimum code | PASS |
| Surgical changes | PASS |
| No scope creep | PASS |
| Matches existing patterns | PASS |
| `git diff --check` | PASS |
| Spec-anchored outcome check | PASS: 6/6 ACs com valores e estados compatíveis com a spec. |
| Per-layer coverage expectation | PASS: features, treinamento e runtime/API cobrem happy path e erros listados. |
| Every test maps to spec, edge case or done-when | PASS |
| Documented guidelines | PASS: `tlc-spec-driven/references/coding-principles.md` |

## Gate Check

- **Gate command**: `PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -W error -m unittest discover -v && node --check webapp/static/app.js`
- **Result**: 43 passed, 0 failed, 0 skipped; JavaScript syntax passed.
- **Test count before feature (`bf5259c`)**: 29 passed.
- **Test count after feature**: 43 passed.
- **Delta**: +14 tests.
- **Structural validation**: `validate_spec.py` retornou 0 erros e 0 avisos; `validate_tasks.py` retornou 0 erros e um aviso esperado para T4 (`Tests: none`).
- **Runtime notes**: MediaPipe emitiu mensagens informativas do TFLite/feedback; nenhuma falha ou warning Python escapou de `-W error`.

## Local Diff and Baseline

- `HEAD` e `origin/main` apontam para `bf5259c6315007f9f7a05c73bb5826c5c48a002e`.
- A feature permanece sem commit, conforme o protocolo de execução e a decisão do usuário.
- Dados públicos e artefatos locais continuam ignorados por `.gitignore:6` e `.gitignore:7`.
- Nenhum arquivo de código ou teste foi alterado pelo Verifier.

## Requirement Traceability Update

| Requirement | Previous Status | Verification Status |
| --- | --- | --- |
| BOOT-01 | Implemented | Verified |
| BOOT-02 | Implemented | Verified |
| BOOT-03 | Implemented | Verified |
| BOOT-04 | Implemented | Verified automatically; browser-camera UAT pending |

## Summary

**Automated gate**: PASS. Os gaps anteriores foram fechados: `model_version` está coberto, o dataset vazio possui regressão persistida e o caminho imagem codificada -> runtime/artefato -> `/api/predict` está coberto e discriminante.

**Human gate**: PENDING. O próximo passo é executar o UAT com a webcam. Até essa confirmação, o software está automatizadamente validado, mas o reconhecimento ao vivo não deve ser apresentado como comprovado.
