import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const WORKSPACE = "/Users/arthurcosta/Documents/Trabalhos/IC-LibrasPython";
const SKILL_DIR = "/Users/arthurcosta/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations";
const RUNTIME_PYTHON = "/Users/arthurcosta/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3";
const BUILD_DIR = path.join(WORKSPACE, ".codex-pptx-build");
const ASSET_DIR = path.join(BUILD_DIR, "assets");
const STAGING_DIR = path.join(BUILD_DIR, ".codex-finalizer");
const FINAL_PPTX = path.join(WORKSPACE, "output", "presentation", "Apresentacao_IC_Libras_Thais.pptx");

const THAIS_PDF = "/tmp/codex-remote-attachments/01a0b679-c818-7730-bc71-715f57a5b598/4B580560-C7A5-4CCD-89A7-34DD698F1D0B/1-IC_Thais-Novaes-Rodrigues-de-Lima_V07-Final.pdf";
const PEDRO_PDF = "/tmp/codex-remote-attachments/01a0b679-c818-7730-bc71-715f57a5b598/4B580560-C7A5-4CCD-89A7-34DD698F1D0B/2-IC_Pedro-Straub-Mantoan_Final.pdf";
const README = path.join(WORKSPACE, "README.md");
const ESCOPO = path.join(WORKSPACE, "docs", "ESCOPO_MVP.md");
const GUIA = path.join(WORKSPACE, "docs", "APRESENTACAO_SEGUNDA.md");

const { resolvePresentationFont, finalizePresentation } = await import(
  pathToFileURL(path.join(SKILL_DIR, "container_tools", "artifact_tool_utils.mjs")).href,
);

await fs.mkdir(STAGING_DIR, { recursive: true });
await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });
const family = resolvePresentationFont();

const W = 1280;
const H = 720;
const C = {
  bg: "#F4F1EA",
  paper: "#FFFDFC",
  ink: "#17201E",
  muted: "#60706B",
  green: "#0F6B57",
  greenDark: "#0A463A",
  mint: "#D7EBE3",
  mint2: "#E8F3EE",
  yellow: "#F4C95D",
  yellowSoft: "#F9E9B8",
  blue: "#315C7D",
  blueSoft: "#DCE8F0",
  red: "#B7544C",
  redSoft: "#F3DEDB",
  gray: "#D7D8D2",
  white: "#FFFFFF",
};

const presentation = Presentation.create({ slideSize: { width: W, height: H } });

function shape(slide, geometry, x, y, w, h, fill = "none", line = "none", radius = undefined) {
  return slide.shapes.add({
    geometry,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: line === "none" ? { fill: "none", width: 0 } : { style: "solid", fill: line, width: 1 },
    ...(radius ? { borderRadius: radius } : {}),
  });
}

function textBox(slide, text, x, y, w, h, opts = {}) {
  const s = shape(slide, "textbox", x, y, w, h, opts.fill ?? "none", opts.line ?? "none", opts.radius);
  s.text = text;
  s.text.style = {
    typeface: family,
    fontSize: opts.size ?? 24,
    bold: opts.bold ?? false,
    italic: opts.italic ?? false,
    color: opts.color ?? C.ink,
    alignment: opts.align ?? "left",
    verticalAlignment: opts.valign ?? "top",
    autoFit: opts.autoFit ?? "shrinkText",
    wrap: "square",
    lineSpacing: opts.lineSpacing ?? 1.08,
    insets: opts.insets ?? { top: 0, right: 0, bottom: 0, left: 0 },
  };
  return s;
}

function addBase(slide, number, section) {
  slide.background.fill = C.bg;
  textBox(slide, "LIBRAS • VISÃO COMPUTACIONAL", 64, 34, 460, 24, { size: 14, bold: true, color: C.green });
  textBox(slide, section.toUpperCase(), 836, 34, 332, 24, { size: 13, bold: true, color: C.muted, align: "right" });
  shape(slide, "line", 64, 684, 1152, 1, "none", C.gray);
  textBox(slide, `0${number}`.slice(-2), 1170, 690, 44, 18, { size: 12, bold: true, color: C.muted, align: "right" });
}

function title(slide, value, subtitle = "") {
  textBox(slide, value, 64, 82, 1152, 64, { size: 40, bold: true, color: C.ink, lineSpacing: 0.98 });
  if (subtitle) textBox(slide, subtitle, 66, 148, 1080, 36, { size: 18, color: C.muted });
}

function pill(slide, value, x, y, w, fill, color) {
  const p = textBox(slide, value, x, y, w, 34, {
    size: 14, bold: true, color, align: "center", valign: "middle", fill, radius: "rounded-full",
    insets: { top: 3, right: 8, bottom: 3, left: 8 },
  });
  return p;
}

function note(slide, body, sources) {
  slide.speakerNotes.textFrame.setText(`${body}\n\nFontes:\n${sources.map((s) => `- ${s}`).join("\n")}`);
}

// 1 — Capa
{
  const slide = presentation.slides.add();
  slide.background.fill = C.greenDark;
  shape(slide, "rect", 704, 0, 576, 720, "#E9E7E0", "none");
  textBox(slide, "DETECÇÃO EM TEMPO REAL", 754, 58, 430, 24, { size: 14, bold: true, color: C.greenDark, align: "center" });
  const img = await fs.readFile(path.join(ASSET_DIR, "hands-detection-clean.png"));
  slide.images.add({
    blob: img,
    contentType: "image/png",
    alt: "Detecção de pontos de referência nas duas mãos usando MediaPipe e OpenCV",
    fit: "contain",
    position: { left: 724, top: 112, width: 536, height: 476 },
  });
  shape(slide, "rect", 680, 0, 56, 720, C.yellow, "none");
  pill(slide, "PROJETO INTEGRADO", 64, 64, 196, C.yellow, C.greenDark);
  textBox(slide, "Reconhecimento\nde sinais manuais\nda Libras", 64, 146, 570, 230, {
    size: 50, bold: true, color: C.white, lineSpacing: 0.92,
  });
  textBox(slide, "Visão computacional e aprendizado de máquina para apoiar uma comunicação mais acessível.", 68, 412, 525, 104, {
    size: 23, color: C.mint, lineSpacing: 1.16,
  });
  textBox(slide, "FOCO DA APRESENTAÇÃO", 68, 590, 250, 22, { size: 13, bold: true, color: C.yellow });
  textBox(slide, "Abordagem manual de Thais Novaes", 68, 619, 500, 36, { size: 20, bold: true, color: C.white });
  note(slide,
    "Apresente o projeto como uma solução integrada. Explique que esta demonstração concentra a etapa manual por ser o recorte mais previsível para validação inicial.",
    [`${THAIS_PDF}, Figura 3`, GUIA],
  );
}

// 2 — Problema e objetivo
{
  const slide = presentation.slides.add();
  addBase(slide, 2, "Contexto");
  title(slide, "Da barreira de comunicação a uma resposta útil", "O sistema transforma uma sequência visual em texto, mantendo a pessoa no controle da mensagem.");
  textBox(slide, "PROBLEMA", 66, 228, 130, 24, { size: 14, bold: true, color: C.red });
  textBox(slide, "A comunicação depende de um intérprete ou de um interlocutor que conheça Libras.", 66, 264, 446, 126, {
    size: 28, bold: true, color: C.ink, lineSpacing: 1.05,
  });
  shape(slide, "line", 550, 230, 1, 312, "none", C.gray);
  textBox(slide, "OBJETIVO DO MVP", 598, 228, 190, 24, { size: 14, bold: true, color: C.green });
  textBox(slide, "Capturar sinais manuais, identificar letras ou sinais conhecidos e permitir confirmação ou correção antes de registrar a mensagem.", 598, 264, 540, 158, {
    size: 28, bold: true, color: C.ink, lineSpacing: 1.05,
  });
  pill(slide, "CAPTURA", 598, 472, 142, C.mint, C.greenDark);
  pill(slide, "RECONHECIMENTO", 754, 472, 190, C.blueSoft, C.blue);
  pill(slide, "VALIDAÇÃO HUMANA", 958, 472, 206, C.yellowSoft, C.greenDark);
  textBox(slide, "Limite assumido", 68, 558, 170, 24, { size: 14, bold: true, color: C.muted });
  textBox(slide, "O protótipo não traduz Libras completa. Ele valida um vocabulário controlado, começando por sinais manuais.", 68, 590, 1058, 56, { size: 20, color: C.muted });
  note(slide,
    "Defina o problema sem prometer tradução completa. O MVP trabalha com vocabulário controlado e validação humana.",
    [THAIS_PDF, ESCOPO],
  );
}

// 3 — Escopo integrado
{
  const slide = presentation.slides.add();
  addBase(slide, 3, "Escopo");
  title(slide, "Um projeto, duas etapas complementares", "A arquitetura comporta mãos e face, mas a validação acontece em fases.");
  textBox(slide, "AGORA", 68, 214, 110, 28, { size: 15, bold: true, color: C.green });
  const now = shape(slide, "roundRect", 64, 252, 516, 284, C.paper, C.green, "rounded-2xl");
  textBox(slide, "01", 94, 282, 72, 60, { size: 44, bold: true, color: C.green });
  textBox(slide, "Sinais manuais", 178, 286, 340, 50, { size: 31, bold: true });
  textBox(slide, "• 21 pontos por mão\n• normalização e sequência temporal\n• classificação com SVM\n• confirmação e correção no front", 96, 362, 424, 136, {
    size: 20, color: C.muted, lineSpacing: 1.18,
  });
  textBox(slide, "PRÓXIMA ETAPA", 704, 214, 176, 28, { size: 15, bold: true, color: C.blue });
  shape(slide, "roundRect", 700, 252, 516, 284, C.blueSoft, C.blue, "rounded-2xl");
  textBox(slide, "02", 730, 282, 72, 60, { size: 44, bold: true, color: C.blue });
  textBox(slide, "Expressões faciais", 814, 286, 340, 50, { size: 31, bold: true, color: C.blue });
  textBox(slide, "• pontos de referência da face\n• sinais não manuais\n• contexto da comunicação\n• fusão posterior com o módulo manual", 732, 362, 424, 136, {
    size: 20, color: C.blue, lineSpacing: 1.18,
  });
  pill(slide, "APRESENTAÇÃO DE SEGUNDA", 470, 576, 336, C.yellow, C.greenDark);
  textBox(slide, "Prioridade: etapa 01, abordagem da Thais", 382, 624, 510, 30, { size: 19, bold: true, color: C.ink, align: "center" });
  note(slide,
    "Explique que os dois trabalhos foram consolidados em uma única arquitetura. O módulo facial permanece no roadmap, sem ser apresentado como validado.",
    [THAIS_PDF, PEDRO_PDF, GUIA],
  );
}

// 4 — Pipeline
{
  const slide = presentation.slides.add();
  addBase(slide, 4, "Arquitetura");
  title(slide, "Do gesto ao registro: o fluxo completo", "Cada etapa tem uma responsabilidade clara e pode ser validada separadamente.");
  const steps = [
    ["01", "Webcam", "sequência visual", C.green],
    ["02", "MediaPipe", "mãos e face", C.green],
    ["03", "Landmarks", "coordenadas 3D", C.blue],
    ["04", "Normalização", "escala e alinhamento", C.blue],
    ["05", "30 quadros", "sequência padrão", C.yellow],
    ["06", "SVM", "classe + confiança", C.red],
    ["07", "Front + DB", "confirmar ou corrigir", C.green],
  ];
  const startX = 62;
  const gap = 12;
  const bw = 154;
  steps.forEach(([n, name, desc, color], i) => {
    const x = startX + i * (bw + gap);
    shape(slide, "roundRect", x, 256, bw, 238, C.paper, C.gray, "rounded-xl");
    shape(slide, "rect", x, 256, bw, 12, color, "none");
    textBox(slide, n, x + 18, 288, 50, 42, { size: 32, bold: true, color });
    textBox(slide, name, x + 18, 350, bw - 36, 58, { size: 22, bold: true, color: C.ink });
    textBox(slide, desc, x + 18, 426, bw - 36, 48, { size: 15, color: C.muted });
    if (i < steps.length - 1) textBox(slide, "→", x + bw - 3, 330, 28, 30, { size: 24, bold: true, color: C.muted, align: "center" });
  });
  shape(slide, "roundRect", 64, 544, 1152, 80, C.greenDark, "none", "rounded-xl");
  textBox(slide, "Princípio de projeto", 90, 567, 198, 24, { size: 16, bold: true, color: C.yellow });
  textBox(slide, "A predição sugere. A pessoa confirma ou corrige antes de a mensagem ser registrada.", 302, 562, 846, 36, { size: 23, bold: true, color: C.white });
  note(slide,
    "Percorra o fluxo da esquerda para a direita. Destaque que a confirmação humana não é um improviso: ela faz parte do processo e cria rastreabilidade.",
    [README, ESCOPO, THAIS_PDF],
  );
}

// 5 — Landmarks
{
  const slide = presentation.slides.add();
  addBase(slide, 5, "Visão computacional");
  title(slide, "A mão vira uma estrutura mensurável", "O MediaPipe representa cada mão por 21 pontos de referência.");
  const img = await fs.readFile(path.join(ASSET_DIR, "hand-landmarks-clean.png"));
  slide.images.add({
    blob: img,
    contentType: "image/png",
    alt: "Mapa dos 21 pontos de referência de uma mão no MediaPipe",
    fit: "contain",
    position: { left: 64, top: 236, width: 658, height: 300 },
  });
  textBox(slide, "21", 806, 214, 180, 90, { size: 72, bold: true, color: C.green });
  textBox(slide, "pontos por mão", 810, 296, 260, 32, { size: 20, bold: true });
  const facts = [
    ["x, y, z", "posição espacial de cada ponto"],
    ["esquerda / direita", "canais preservados separadamente"],
    ["quadro a quadro", "movimento convertido em sequência"],
  ];
  facts.forEach(([k, v], i) => {
    const y = 364 + i * 78;
    shape(slide, "line", 810, y - 10, 340, 1, "none", C.gray);
    textBox(slide, k, 810, y, 192, 28, { size: 18, bold: true, color: C.blue });
    textBox(slide, v, 1008, y, 164, 40, { size: 16, color: C.muted });
  });
  textBox(slide, "Fonte visual: trabalho de Thais Novaes, Figura 2.", 70, 603, 620, 24, { size: 13, color: C.muted, italic: true });
  note(slide,
    "Mostre que a imagem original deixa de ser o único dado. O modelo trabalha com pontos estruturados, mantendo mão esquerda e direita separadas.",
    [`${THAIS_PDF}, Figura 2`, ESCOPO],
  );
}

// 6 — Preparação
{
  const slide = presentation.slides.add();
  addBase(slide, 6, "Dados");
  title(slide, "Preparar o dado reduz variações que não são o sinal", "O objetivo é comparar o gesto, não a distância da câmera ou o tamanho da mão.");
  const items = [
    ["01", "Centralizar", "pulso como origem", C.green],
    ["02", "Escalonar", "tamanho relativo", C.blue],
    ["03", "Alinhar", "orientação consistente", C.yellow],
    ["04", "Suavizar", "menos ruído entre quadros", C.red],
    ["05", "Reamostrar", "30 quadros por amostra", C.green],
  ];
  items.forEach(([n, label, detail, color], i) => {
    const x = 64 + i * 230;
    shape(slide, "ellipse", x + 55, 242, 94, 94, color, "none");
    textBox(slide, n, x + 55, 264, 94, 45, { size: 28, bold: true, color: i === 2 ? C.greenDark : C.white, align: "center", valign: "middle" });
    textBox(slide, label, x, 370, 204, 42, { size: 23, bold: true, align: "center" });
    textBox(slide, detail, x, 418, 204, 52, { size: 16, color: C.muted, align: "center" });
    if (i < items.length - 1) textBox(slide, "→", x + 190, 269, 38, 32, { size: 26, bold: true, color: C.muted, align: "center" });
  });
  shape(slide, "roundRect", 64, 532, 1152, 100, C.mint2, C.green, "rounded-xl");
  textBox(slide, "Contrato da amostra", 92, 558, 252, 28, { size: 18, bold: true, color: C.greenDark });
  textBox(slide, "sequência comprimida + rótulo + participante + metadados de coleta", 352, 554, 790, 42, { size: 22, bold: true, color: C.greenDark });
  note(slide,
    "Explique que o pré-processamento torna as amostras comparáveis. A sequência final tem duração padronizada e metadados suficientes para auditoria.",
    [THAIS_PDF, ESCOPO, README],
  );
}

// 7 — Treinamento
{
  const slide = presentation.slides.add();
  addBase(slide, 7, "Aprendizado de máquina");
  title(slide, "Treinar sem misturar as pessoas", "A divisão deve impedir que a mesma pessoa apareça em treino e teste.");
  textBox(slide, "DIVISÃO PROPOSTA", 66, 220, 230, 24, { size: 14, bold: true, color: C.green });
  shape(slide, "roundRect", 64, 264, 764, 106, C.paper, C.gray, "rounded-xl");
  shape(slide, "roundRect", 82, 286, 500, 62, C.green, "none", "rounded-lg");
  shape(slide, "roundRect", 588, 286, 108, 62, C.yellow, "none", "rounded-lg");
  shape(slide, "roundRect", 702, 286, 108, 62, C.blue, "none", "rounded-lg");
  textBox(slide, "70% treino", 82, 302, 500, 28, { size: 20, bold: true, color: C.white, align: "center" });
  textBox(slide, "15% val.", 588, 302, 108, 28, { size: 17, bold: true, color: C.greenDark, align: "center" });
  textBox(slide, "15% teste", 702, 302, 108, 28, { size: 17, bold: true, color: C.white, align: "center" });
  textBox(slide, "Regra: participantes diferentes em cada conjunto", 66, 390, 762, 32, { size: 20, bold: true, color: C.red });
  shape(slide, "roundRect", 886, 220, 330, 202, C.greenDark, "none", "rounded-2xl");
  textBox(slide, "MODELO BASELINE", 916, 252, 268, 26, { size: 14, bold: true, color: C.yellow });
  textBox(slide, "SVM", 916, 292, 268, 70, { size: 58, bold: true, color: C.white });
  textBox(slide, "simples, local e adequado ao primeiro experimento", 916, 360, 260, 46, { size: 16, color: C.mint });
  textBox(slide, "COMO AVALIAR", 66, 478, 180, 24, { size: 14, bold: true, color: C.blue });
  const metrics = ["Acurácia", "Precisão", "Recall", "F1-score", "Matriz de confusão"];
  metrics.forEach((m, i) => pill(slide, m, 66 + i * 220, 526, i === 4 ? 244 : 194, i % 2 ? C.mint : C.blueSoft, i % 2 ? C.greenDark : C.blue));
  textBox(slide, "Nenhuma métrica é apresentada antes de existir um conjunto real e separado por participante.", 68, 598, 1080, 34, { size: 18, bold: true, color: C.muted });
  note(slide,
    "Destaque que a validação por participante evita uma métrica artificialmente alta. Não apresente números de desempenho antes do experimento real.",
    [THAIS_PDF, ESCOPO, GUIA],
  );
}

// 8 — Interface
{
  const slide = presentation.slides.add();
  addBase(slide, 8, "Experiência");
  title(slide, "A interface mantém a decisão com o usuário", "O reconhecimento é uma sugestão, não um registro automático irreversível.");
  const stages = [
    ["1", "Câmera", "captura a sequência", C.green],
    ["2", "Predição", "letra + confiança", C.blue],
    ["3", "Revisão", "confirmar ou corrigir", C.yellow],
    ["4", "Mensagem", "compor e registrar", C.red],
  ];
  stages.forEach(([n, label, desc, color], i) => {
    const x = 64 + i * 288;
    shape(slide, "roundRect", x, 244, 250, 218, C.paper, color, "rounded-2xl");
    shape(slide, "ellipse", x + 24, 270, 54, 54, color, "none");
    textBox(slide, n, x + 24, 282, 54, 28, { size: 20, bold: true, color: i === 2 ? C.greenDark : C.white, align: "center" });
    textBox(slide, label, x + 24, 344, 194, 38, { size: 28, bold: true });
    textBox(slide, desc, x + 24, 394, 194, 44, { size: 17, color: C.muted });
    if (i < stages.length - 1) textBox(slide, "→", x + 250, 328, 38, 36, { size: 30, bold: true, color: C.muted, align: "center" });
  });
  shape(slide, "roundRect", 64, 522, 1152, 104, C.yellowSoft, "none", "rounded-xl");
  textBox(slide, "Rastreabilidade", 94, 550, 190, 28, { size: 19, bold: true, color: C.greenDark });
  textBox(slide, "o banco preserva a predição original, a correção aplicada e a versão do modelo", 308, 546, 820, 42, { size: 22, bold: true, color: C.greenDark });
  note(slide,
    "Mostre que a opção de correção melhora a comunicação e também cria dados para analisar erros futuros. O banco registra a decisão humana e o contexto técnico.",
    [README, ESCOPO],
  );
}

// 9 — Estado atual
{
  const slide = presentation.slides.add();
  addBase(slide, 9, "Evidências");
  title(slide, "O que já está validado e o que ainda falta", "Separar implementação de evidência real torna a apresentação tecnicamente honesta.");
  shape(slide, "roundRect", 64, 220, 548, 380, C.mint2, C.green, "rounded-2xl");
  textBox(slide, "VALIDADO LOCALMENTE", 96, 252, 300, 26, { size: 15, bold: true, color: C.green });
  textBox(slide, "29", 96, 294, 120, 76, { size: 64, bold: true, color: C.greenDark });
  textBox(slide, "testes automatizados aprovados", 218, 318, 330, 38, { size: 20, bold: true, color: C.greenDark });
  textBox(slide, "✓ API, banco e interface\n✓ contrato das amostras\n✓ normalização e sequência de 30 quadros\n✓ coletor sincronizado de mãos e face\n✓ script de treinamento e métricas", 98, 390, 454, 168, {
    size: 19, color: C.greenDark, lineSpacing: 1.22,
  });
  shape(slide, "roundRect", 668, 220, 548, 380, C.redSoft, C.red, "rounded-2xl");
  textBox(slide, "EVIDÊNCIA PENDENTE", 700, 252, 300, 26, { size: 15, bold: true, color: C.red });
  textBox(slide, "REAL", 700, 294, 202, 76, { size: 54, bold: true, color: C.red });
  textBox(slide, "coleta e uso com participantes", 884, 318, 286, 42, { size: 20, bold: true, color: C.red });
  textBox(slide, "○ ambiente científico em Python 3.11\n○ base com pelo menos 3 participantes\n○ modelo manual treinado e versionado\n○ métricas em conjunto de teste separado\n○ validação com usuários da comunidade surda", 702, 390, 454, 168, {
    size: 19, color: C.red, lineSpacing: 1.22,
  });
  textBox(slide, "Status do modelo na interface: indisponível até existir um artefato treinado válido.", 70, 626, 1100, 30, { size: 18, bold: true, color: C.muted });
  note(slide,
    "Apresente os 29 testes como validação de software, não como acurácia do reconhecimento. A câmera, o modelo e o uso com participantes ainda exigem o ambiente científico e dados reais.",
    [README, GUIA, ESCOPO],
  );
}

// 10 — Demonstração e próximos passos
{
  const slide = presentation.slides.add();
  addBase(slide, 10, "Apresentação");
  title(slide, "Demonstração segura para segunda-feira", "Mesmo sem modelo treinado, o fluxo pode ser apresentado sem simular uma predição inexistente.");
  const demo = [
    ["01", "Abrir a interface", "mostrar câmera e área da mensagem"],
    ["02", "Exibir o estado", "modelo indisponível de forma explícita"],
    ["03", "Compor manualmente", "demonstrar confirmação e correção"],
    ["04", "Mostrar a coleta", "estrutura dos dados e metadados"],
    ["05", "Fechar com o experimento", "coletar, treinar e medir"],
  ];
  demo.forEach(([n, label, desc], i) => {
    const y = 226 + i * 76;
    shape(slide, "ellipse", 66, y, 48, 48, i < 3 ? C.green : C.blue, "none");
    textBox(slide, n, 66, y + 10, 48, 24, { size: 15, bold: true, color: C.white, align: "center" });
    textBox(slide, label, 138, y - 2, 310, 30, { size: 22, bold: true });
    textBox(slide, desc, 458, y, 380, 32, { size: 17, color: C.muted });
  });
  shape(slide, "roundRect", 874, 224, 342, 390, C.greenDark, "none", "rounded-2xl");
  textBox(slide, "PRÓXIMOS PASSOS", 906, 258, 270, 24, { size: 14, bold: true, color: C.yellow });
  textBox(slide, "Coletar", 906, 306, 240, 38, { size: 28, bold: true, color: C.white });
  textBox(slide, "→ treinar o módulo manual", 906, 348, 266, 32, { size: 18, color: C.mint });
  textBox(slide, "Medir", 906, 402, 240, 38, { size: 28, bold: true, color: C.white });
  textBox(slide, "→ validar por participante", 906, 444, 266, 32, { size: 18, color: C.mint });
  textBox(slide, "Integrar", 906, 498, 240, 38, { size: 28, bold: true, color: C.white });
  textBox(slide, "→ incorporar sinais faciais", 906, 540, 266, 32, { size: 18, color: C.mint });
  textBox(slide, "Resultado esperado: uma comunicação assistida, corrigível e evolutiva.", 66, 633, 770, 30, { size: 20, bold: true, color: C.greenDark });
  note(slide,
    "Siga este roteiro se o modelo ainda não estiver treinado. Não apresente a entrada manual como resultado da inteligência artificial. Finalize com o plano de coleta, treinamento e integração facial.",
    [GUIA, ESCOPO, PEDRO_PDF],
  );
}

const candidatePath = path.join(STAGING_DIR, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const requirements = {
  explicitTotalSlideCount: 10,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
};

const result = await finalizePresentation({
  ...requirements,
  workspaceDir: WORKSPACE,
  candidatePath,
  finalPath: FINAL_PPTX,
  pythonExecutable: RUNTIME_PYTHON,
  integrityValidatorPath: path.join(SKILL_DIR, "container_tools", "inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(SKILL_DIR, "container_tools", "inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu", "12192000,6858000",
    "--validate-bullet-geometry",
    "--validate-heading-fit",
  ],
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  fontPolicy: { basis: "design", families: [family] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(STAGING_DIR, `${path.basename(FINAL_PPTX)}.validation.json`),
});

console.log(JSON.stringify({ family, candidatePath, finalPath: FINAL_PPTX, result }, null, 2));
