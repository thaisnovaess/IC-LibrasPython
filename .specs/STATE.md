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

### AD-004: Modelo público serve apenas como bootstrap local

- **status**: active
- **decision**: Usar o dataset Kaggle `williansoliveira/libras` para ativar 21 letras estáticas localmente, sem versionar ou redistribuir os dados e o modelo derivado.
- **reason**: A fonte permite demonstrar o fluxo completo, mas o catálogo informa licença desconhecida e não fornece identidade de participantes para avaliação científica.

## Handoff

- **feature**: preview-letra-frase-manual
- **phase**: implementação concluída; UAT no navegador
- **completed**: ambiente Python 3.11, modelo local de 21 letras, overlay dos 21 landmarks, prévia estável por maioria de 3 em 5 com confiança mediana mínima de 60%, identificação confirmável em 12 frames, inserção transacional de frases até 500 caracteres, 50 testes Python, 8 testes JavaScript e verificação independente PASS
- **in progress**: validar visualmente a prévia e a limpeza imediata ao desligar a câmera
- **next step**: executar UAT da câmera e da frase; depois, coletar amostras consentidas de pelo menos três participantes para a avaliação científica
- **blockers**: a generalização ao vivo ainda depende do UAT na câmera; o modelo bootstrap e os dados não serão versionados por restrição de licença
- **uncommitted files**: a feature permanece sem commit por decisão explícita do usuário
- **branch**: main
