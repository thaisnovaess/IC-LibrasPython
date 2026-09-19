# Roteiro da apresentação: abordagem de sinais manuais

## Mensagem principal

O projeto transforma movimentos das mãos em dados estruturados para criar um reconhecedor local de sinais manuais da Libras. A arquitetura também está preparada para receber expressões faciais, mas a demonstração concentra-se na abordagem manual proposta por Thais.

## Fluxo demonstrado

```text
Webcam
  -> MediaPipe Holistic
  -> 21 landmarks por mão
  -> centralização, escala e alinhamento
  -> sequência padronizada em 30 frames
  -> classificador SVM
  -> letra ou sinal + confiança
  -> confirmação/correção na interface
  -> registro local em SQLite
```

## O que já pode ser mostrado

1. Interface web com câmera, mensagem e correção manual.
2. Coletor que captura mãos e rosto no mesmo timestamp.
3. Estrutura comprimida das amostras e seus metadados.
4. Normalização dos 21 landmarks de cada mão.
5. Padronização temporal para 30 frames.
6. Script de treinamento SVM e geração de métricas.
7. Estado explícito quando o modelo ainda não foi treinado.

## O que não deve ser afirmado

- Não afirmar que o sistema já traduz toda a Libras.
- Não apresentar uma acurácia sem dataset real e conjunto de teste independente.
- Não dizer que o módulo facial está validado.
- Não usar a inserção manual como se fosse uma previsão da inteligência artificial.

## Demonstração segura sem modelo treinado

1. Abrir a interface e ativar a câmera.
2. Mostrar que o sistema informa que o classificador ainda não está configurado.
3. Formar uma mensagem pela entrada manual e explicar a confirmação humana.
4. Mostrar o comando do coletor e o contrato dos dados.
5. Explicar que as próximas coletas alimentarão o treinamento e a avaliação.

## Demonstração com modelo treinado

1. Coletar amostras de pelo menos três participantes, mantendo pessoas diferentes entre treino, validação e teste.
2. Executar o treinamento manual.
3. Iniciar a interface com `manual.joblib` em `artifacts/models/`.
4. Ativar a câmera, executar uma letra e selecionar **Identificar sinal**.
5. Confirmar ou corrigir o resultado e mostrar o evento salvo.

## Perguntas prováveis

### Por que começar pelas mãos?

Porque o pipeline manual possui 21 pontos por mão e um problema inicial mais controlado. Isso reduz o risco da primeira demonstração sem impedir a integração facial posterior.

### Por que ainda existe correção humana?

Porque classificadores podem errar. A correção melhora a comunicação e cria evidência para evolução do dataset.

### Como evitar que o modelo memorize uma pessoa?

O projeto separa participantes entre treino, validação e teste. Uma pessoa usada no treinamento não aparece no teste final.

### Onde entra o projeto de Pedro?

O rosto já é capturado de forma sincronizada e possui contrato próprio. Depois da validação manual, o classificador facial será conectado à mesma camada de fusão.
