# Project State

## Decisions

### AD-001: Um sistema com dois reconhecedores complementares

- **status**: active
- **decision**: Processar mãos e expressões faciais separadamente e combinar os resultados por uma camada de fusão temporal.
- **reason**: Os projetos científicos medem fenômenos distintos e precisam conservar métricas independentes.

### AD-002: Processamento local e coleta consentida

- **status**: active
- **decision**: Executar inferência localmente e não persistir imagens no uso cotidiano. Vídeos só podem ser gravados pelo comando de coleta científica.
- **reason**: Imagens faciais e gestuais são dados sensíveis e não são necessárias para a comunicação depois da inferência.

### AD-003: Demonstração de segunda prioriza sinais manuais

- **status**: active
- **decision**: A entrega demonstrável prioriza o pipeline de Thais. O módulo facial permanece integrado na arquitetura, mas entra após a validação do reconhecimento manual.
- **reason**: Orientação do professor e menor incerteza técnica para a apresentação.

## Handoff

- **feature**: reconhecimento-integrado-libras
- **phase**: implementation and local contract validation
- **completed**: contratos integrados, dataset, normalização, coletor, treino SVM, runtime, API, interface e 29 testes locais
- **in progress**: preparação da demonstração manual orientada pelo professor
- **next step**: criar ambiente Python 3.11, validar câmera e coletar amostras reais de pelo menos três participantes
- **blockers**: câmera/MediaPipe não validados nesta máquina e modelos finais dependem de dataset real rotulado
- **uncommitted files**: toda a implementação do MVP web e do reconhecimento integrado permanece sem commit por decisão do usuário
- **branch**: main
