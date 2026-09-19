# Escopo do MVP de comunicação por datilologia em Libras

## Objetivo

Permitir que uma pessoa surda soletre uma mensagem pelo alfabeto manual de Libras, confira cada letra identificada, corrija eventuais erros e apresente o texto final na tela ou por voz sintetizada.

O MVP não afirma traduzir toda a Libras. Datilologia, sinais lexicais e expressões não manuais são problemas diferentes. A primeira etapa cobre letras estáticas e prepara o contrato para letras que exigem movimento.

## Fluxo principal

1. O usuário inicia uma sessão local.
2. O navegador solicita permissão para a câmera.
3. O reconhecedor local recebe um quadro ou uma curta sequência de quadros.
4. O sistema apresenta a letra prevista e a confiança.
5. O usuário confirma ou corrige a letra.
6. O evento é salvo no SQLite com previsão, confirmação e versão do modelo.
7. A mensagem é formada na interface e pode ser lida em voz alta.

## Entrega atual

- Interface web responsiva e acessível.
- Visualização da câmera no navegador.
- Sessões e mensagens persistidas como eventos locais.
- Inserção manual, espaço, apagar, limpar e leitura em voz.
- Contrato do reconhecedor e estado explícito de modelo indisponível.
- Estrutura de auditoria para previsão, confiança, correção e versão do modelo.
- Testes do domínio e das rotas HTTP.

## Próximas entregas

1. Definir e versionar o conjunto de dados do alfabeto manual brasileiro.
2. Implementar extração de landmarks com MediaPipe em Python compatível.
3. Treinar e avaliar o classificador por pessoa, iluminação e mão dominante.
4. Exportar o modelo para ONNX e conectá-lo ao contrato existente.
5. Adicionar estabilidade temporal e suporte separado para letras com movimento.
6. Realizar validação de usabilidade com pessoas surdas e profissionais de Libras.

## Critérios de qualidade

- Nenhuma previsão é exibida quando não existe modelo carregado.
- Toda correção mantém a previsão original para análise posterior.
- Imagens não são persistidas por padrão.
- A interface permanece utilizável por teclado e em telas pequenas.
- O modelo só pode ser divulgado com métricas em dados não vistos no treinamento.

## Fora do escopo desta etapa

- Tradução completa e gramatical de Libras para português.
- Diagnóstico facial, leitura labial ou identificação da pessoa.
- Armazenamento de fotografias e vídeos.
- Uso de um modelo generativo como classificador primário dos sinais.
- Implantação pública ou processamento em nuvem.
