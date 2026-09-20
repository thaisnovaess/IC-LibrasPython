# Operação do modelo manual

Este guia descreve o caminho entre um repositório recém-clonado e o reconhecimento manual ativo na interface web. Ele não substitui a definição científica do dataset nem a validação dos sinais por pessoas com conhecimento de Libras.

## Resultado esperado

Ao final do processo devem existir:

- modelo manual em `artifacts/models/manual.joblib`;
- relatório em `artifacts/models/manual-report.json`;
- endpoint `/api/status` com `available: true` e `manual_available: true`.

O módulo facial pode permanecer indisponível durante a primeira etapa.

## 1. Preparar o ambiente no Windows

Abra o PowerShell na raiz do repositório:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-vision.txt
```

Confirme as dependências:

```powershell
python -c "import cv2, joblib, mediapipe, numpy, sklearn; print('Ambiente científico pronto')"
```

Se a ativação estiver bloqueada, use `.venv\Scripts\python.exe` no lugar de `python` nos comandos seguintes.

## 2. Gerar o modelo bootstrap para a demonstração

Este é o caminho mais rápido para ativar as 21 letras estáticas da apresentação. Baixe a versão 1 do dataset público [Libras, de Willians Oliveira, no Kaggle](https://www.kaggle.com/datasets/williansoliveira/libras) e extraia o conteúdo. O diretório informado ao comando precisa conter as pastas `train/` e `test/`.

O catálogo consultado informa licença `Unknown`. Use os dados e o modelo derivado apenas como bootstrap acadêmico local. Não publique nem versione as imagens ou o artefato treinado sem confirmar a autorização de redistribuição.

Execute:

```powershell
python -m training.bootstrap_alphabet `
  --dataset "C:\caminho\para\libras" `
  --train-per-class 80 `
  --validation-per-class 20 `
  --test-per-class 30
```

O treinamento gera 21 classes estáticas: `A, B, C, D, E, F, G, I, L, M, N, O, P, Q, R, S, T, U, V, W, Y`. As letras dinâmicas `H, J, K, X, Z` não fazem parte desse modelo.

O relatório identifica a avaliação como `provider_split_not_participant_independent`. A acurácia obtida nesse split mede apenas o bootstrap fornecido pelo dataset. Ela não comprova generalização para novas pessoas, câmeras ou condições de iluminação.

Confira os artefatos:

```powershell
Test-Path .\artifacts\models\manual.joblib
Test-Path .\artifacts\models\manual-report.json
```

Os dois comandos devem retornar `True`.

## 3. Coletar dados próprios para avaliação científica

O bootstrap permite demonstrar o fluxo. A avaliação científica exige amostras consentidas e separação por participante.

### Definir o piloto de coleta

Antes de abrir a câmera, registre:

- letras ou sinais incluídos no piloto;
- forma padronizada de execução de cada classe;
- distância aproximada da câmera;
- iluminação e fundo;
- mão dominante;
- quantidade de repetições por classe e participante;
- critérios para descartar uma captura.

Requisitos técnicos mínimos do treinamento atual:

- pelo menos três participantes distintos;
- pelo menos duas classes para que o SVM aprenda uma classificação;
- pelo menos duas amostras por classe dentro do conjunto de treino;
- conjuntos de treino, validação e teste não vazios.

Esses valores são mínimos para o código executar, não evidência de qualidade científica. No piloto mínimo com três participantes, faça cada participante executar as mesmas classes pelo menos duas vezes. Assim, qualquer participante destinado ao treino terá duas amostras por classe. Para uma avaliação útil, colete mais repetições.

Use identificadores não pessoais, como `p01`, `p02` e `p03`. Não use nomes, e-mail ou matrícula como identificador.

### Coletar as amostras

Cada execução coleta uma amostra de três segundos por padrão e salva landmarks e metadados, sem vídeo bruto:

```powershell
python -m training.collect --participant p01 --manual-label A --lighting uniforme
```

Repita o comando para cada combinação de participante, classe e repetição. Exemplo para outra classe:

```powershell
python -m training.collect --participant p01 --manual-label B --lighting uniforme
```

O argumento `--store-video` só deve ser usado com consentimento explícito. Sem esse argumento, o projeto não grava vídeo.

Após a coleta, confira a quantidade de arquivos:

```powershell
(Get-ChildItem .\data\samples\sample-*.json.gz).Count
```

### Treinar o classificador manual com dados próprios

Com a coleta concluída:

```powershell
python -m training.train --modality manual
```

O script separa participantes entre treino, validação e teste, executa busca de hiperparâmetros e gera o modelo e o relatório.

### Revisar o relatório científico

Abra `artifacts/models/manual-report.json` e confira:

- `sample_count`;
- `participant_split`;
- `best_parameters`;
- `validation_accuracy`;
- `test_accuracy`;
- `test_classification`;
- `confusion_matrix`.

Não divulgue apenas a acurácia. Registre também quantidade de participantes, quantidade de amostras, classes avaliadas e separação utilizada.

## 4. Reiniciar e validar a aplicação

Os modelos são carregados quando o servidor inicia. Se ele estava aberto durante o treinamento, encerre-o com `Ctrl+C` e execute novamente:

```powershell
python -m webapp.server
```

Em outro PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/status | ConvertTo-Json -Depth 5
```

Estado esperado para reconhecimento manual ativo:

```json
{
  "service": "ready",
  "recognizer": {
    "available": true,
    "manual_available": true,
    "status": "ready"
  }
}
```

`facial_available: false` continua sendo aceitável nesta etapa.

## 5. Fazer o teste funcional

1. Abra `http://127.0.0.1:8000`.
2. Permita o uso da câmera.
3. Selecione **Identificar sinal** durante a execução de uma classe conhecida.
4. Confira letra e confiança.
5. Confirme ou corrija a letra.
6. Verifique se a mensagem foi atualizada e salva localmente.
7. Repita com uma pessoa que não participou do treinamento.

O detector precisa enxergar uma mão completa, com os dedos visíveis. Para o bootstrap, teste primeiro uma das 21 letras estáticas listadas acima. Fundo simples, boa iluminação e mão próxima da câmera reduzem falhas de detecção.

## Demonstração quando o modelo ainda não existe

Se `/api/status` retornar `model_unavailable`, a demonstração segura é:

1. mostrar a interface e a câmera;
2. explicar o estado explícito do classificador;
3. formar a mensagem pela inserção manual;
4. demonstrar confirmação, correção e persistência;
5. apresentar coleta e treinamento como a próxima etapa experimental.

Não simule uma predição automática usando a entrada manual.
