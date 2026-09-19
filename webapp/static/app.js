"use strict";

const state = {
  sessionId: null,
  stream: null,
  candidate: null,
  recognizerAvailable: false,
  message: "",
};

const elements = {
  systemStatus: document.querySelector("#system-status"),
  cameraState: document.querySelector("#camera-state"),
  cameraFrame: document.querySelector(".camera-frame"),
  video: document.querySelector("#camera"),
  cameraToggle: document.querySelector("#camera-toggle"),
  analyzeFrame: document.querySelector("#analyze-frame"),
  predictionLetter: document.querySelector("#prediction-letter"),
  predictionLabel: document.querySelector("#prediction-label"),
  predictionDetail: document.querySelector("#prediction-detail"),
  facialDetail: document.querySelector("#facial-detail"),
  confirmLetter: document.querySelector("#confirm-letter"),
  correctLetter: document.querySelector("#correct-letter"),
  manualLetter: document.querySelector("#manual-letter"),
  addManual: document.querySelector("#add-manual"),
  messageOutput: document.querySelector("#message-output"),
  saveStatus: document.querySelector("#save-status"),
  addSpace: document.querySelector("#add-space"),
  removeLast: document.querySelector("#remove-last"),
  clearMessage: document.querySelector("#clear-message"),
  speakMessage: document.querySelector("#speak-message"),
  dialog: document.querySelector("#correction-dialog"),
  correctionForm: document.querySelector("#correction-form"),
  correctedValue: document.querySelector("#corrected-value"),
  cancelCorrection: document.querySelector("#cancel-correction"),
  toast: document.querySelector("#toast"),
};

function normalizeLetter(value) {
  const letter = value.trim().toUpperCase();
  return /^[A-Z]$/.test(letter) ? letter : null;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || payload.message || "Não foi possível concluir a operação.");
  return payload;
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.hidden = false;
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => { elements.toast.hidden = true; }, 3200);
}

function renderMessage() {
  elements.messageOutput.textContent = state.message || "Sua mensagem aparecerá aqui.";
  elements.speakMessage.disabled = !state.message.trim();
  elements.removeLast.disabled = !state.message;
  elements.clearMessage.disabled = !state.message;
}

async function refreshSession() {
  const session = await api(`/api/sessions/${state.sessionId}`);
  state.message = session.text;
  renderMessage();
}

async function recordEvent(eventType, extra = {}) {
  elements.saveStatus.textContent = "Salvando";
  try {
    await api("/api/events", {
      method: "POST",
      body: JSON.stringify({ session_id: state.sessionId, event_type: eventType, ...extra }),
    });
    await refreshSession();
    elements.saveStatus.textContent = "Mensagem salva neste dispositivo";
  } catch (error) {
    elements.saveStatus.textContent = "Falha ao salvar";
    showToast(error.message);
    throw error;
  }
}

async function addManualLetter() {
  const letter = normalizeLetter(elements.manualLetter.value);
  if (!letter) {
    showToast("Informe uma única letra entre A e Z.");
    elements.manualLetter.focus();
    return;
  }
  await recordEvent("letter", { confirmed_letter: letter, source: "manual" });
  elements.manualLetter.value = "";
  elements.manualLetter.focus();
}

async function confirmCandidate(confirmedLetter) {
  if (!state.candidate) return;
  await recordEvent("letter", {
    confirmed_letter: confirmedLetter,
    predicted_letter: state.candidate.letter,
    confidence: state.candidate.confidence,
    source: "recognizer",
    model_version: state.candidate.modelVersion,
    facial_expression: state.candidate.facialExpression,
    facial_confidence: state.candidate.facialConfidence,
    facial_model_version: state.candidate.facialModelVersion,
  });
  state.candidate = null;
  elements.predictionLetter.textContent = "?";
  elements.predictionLabel.textContent = "Aguardando um sinal";
  elements.predictionDetail.textContent = "Apresente a próxima letra para continuar.";
  elements.facialDetail.textContent = "Expressão facial: aguardando análise.";
  elements.confirmLetter.disabled = true;
  elements.correctLetter.disabled = true;
}

function wait(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

async function analyzeSequence() {
  if (!state.stream || !state.recognizerAvailable) return;
  elements.analyzeFrame.disabled = true;
  elements.analyzeFrame.textContent = "Analisando sequência";
  const canvas = document.createElement("canvas");
  canvas.width = 640;
  canvas.height = 360;
  const context = canvas.getContext("2d");
  const frames = [];
  try {
    for (let index = 0; index < 12; index += 1) {
      context.drawImage(elements.video, 0, 0, canvas.width, canvas.height);
      frames.push(canvas.toDataURL("image/jpeg", 0.65));
      await wait(80);
    }
    const prediction = await api("/api/predict", {
      method: "POST",
      body: JSON.stringify({ frames }),
    });
    if (!prediction.manual_label) {
      elements.predictionLetter.textContent = "?";
      elements.predictionLabel.textContent = "Sinal não identificado";
      elements.predictionDetail.textContent = prediction.message;
      elements.facialDetail.textContent = prediction.facial_expression
        ? `Expressão facial: ${prediction.facial_expression}`
        : "Expressão facial: não identificada.";
      return;
    }
    state.candidate = {
      letter: prediction.manual_label,
      confidence: prediction.manual_confidence,
      modelVersion: prediction.manual_model_version,
      facialExpression: prediction.facial_expression,
      facialConfidence: prediction.facial_confidence,
      facialModelVersion: prediction.facial_model_version,
    };
    elements.predictionLetter.textContent = prediction.manual_label;
    elements.predictionLabel.textContent = `Sinal identificado: ${prediction.manual_label}`;
    elements.predictionDetail.textContent = `Confiança manual: ${Math.round(prediction.manual_confidence * 100)}%`;
    elements.facialDetail.textContent = prediction.facial_expression
      ? `Expressão facial: ${prediction.facial_expression} (${Math.round(prediction.facial_confidence * 100)}%)`
      : "Expressão facial: segunda etapa do projeto.";
    elements.confirmLetter.disabled = prediction.manual_label.length !== 1;
    elements.correctLetter.disabled = prediction.manual_label.length !== 1;
  } catch (error) {
    showToast(error.message);
  } finally {
    elements.analyzeFrame.disabled = false;
    elements.analyzeFrame.textContent = "Identificar sinal";
  }
}

async function toggleCamera() {
  if (state.stream) {
    state.stream.getTracks().forEach((track) => track.stop());
    state.stream = null;
    elements.video.srcObject = null;
    elements.cameraFrame.classList.remove("is-active");
    elements.cameraState.textContent = "Câmera desligada";
    elements.cameraToggle.textContent = "Ativar câmera";
    elements.analyzeFrame.disabled = true;
    return;
  }

  if (!navigator.mediaDevices?.getUserMedia) {
    showToast("Este navegador não oferece acesso à câmera.");
    return;
  }

  try {
    state.stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    elements.video.srcObject = state.stream;
    elements.cameraFrame.classList.add("is-active");
    elements.cameraState.textContent = "Câmera ativa";
    elements.cameraToggle.textContent = "Desativar câmera";
    elements.analyzeFrame.disabled = !state.recognizerAvailable;
  } catch (_error) {
    showToast("Não foi possível acessar a câmera. Confira a permissão do navegador.");
  }
}

async function initialize() {
  renderMessage();
  try {
    const [status, session] = await Promise.all([
      api("/api/status"),
      api("/api/sessions", { method: "POST" }),
    ]);
    state.sessionId = session.session_id;
    state.recognizerAvailable = status.recognizer.available;
    elements.systemStatus.textContent = state.recognizerAvailable
      ? `Reconhecimento local ativo: ${status.recognizer.model_version}`
      : "Interface pronta, classificador ainda não configurado";
    elements.predictionDetail.textContent = status.recognizer.message;
    elements.saveStatus.textContent = "Sessão local iniciada";
  } catch (error) {
    elements.systemStatus.textContent = "Serviço indisponível";
    elements.saveStatus.textContent = "Não foi possível iniciar a sessão";
    showToast(error.message);
  }
}

elements.cameraToggle.addEventListener("click", toggleCamera);
elements.analyzeFrame.addEventListener("click", analyzeSequence);
elements.addManual.addEventListener("click", addManualLetter);
elements.manualLetter.addEventListener("keydown", (event) => {
  if (event.key === "Enter") addManualLetter();
});
elements.addSpace.addEventListener("click", () => recordEvent("space", { source: "manual" }));
elements.removeLast.addEventListener("click", () => recordEvent("backspace", { source: "manual" }));
elements.clearMessage.addEventListener("click", () => recordEvent("clear", { source: "manual" }));
elements.confirmLetter.addEventListener("click", () => confirmCandidate(state.candidate?.letter));
elements.correctLetter.addEventListener("click", () => {
  elements.correctedValue.value = "";
  elements.dialog.showModal();
  elements.correctedValue.focus();
});
elements.cancelCorrection.addEventListener("click", () => elements.dialog.close());
elements.correctionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const corrected = normalizeLetter(elements.correctedValue.value);
  if (!corrected) {
    showToast("Informe uma única letra entre A e Z.");
    return;
  }
  await confirmCandidate(corrected);
  elements.dialog.close();
});
elements.speakMessage.addEventListener("click", () => {
  if (!state.message.trim() || !("speechSynthesis" in window)) {
    showToast("A leitura em voz não está disponível neste navegador.");
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(state.message);
  utterance.lang = "pt-BR";
  window.speechSynthesis.speak(utterance);
});

window.addEventListener("beforeunload", () => {
  state.stream?.getTracks().forEach((track) => track.stop());
});

initialize();
