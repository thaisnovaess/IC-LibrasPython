(function exposeSessionHistory(root, factory) {
  const history = factory();
  if (typeof module === "object" && module.exports) module.exports = history;
  else root.SessionHistory = history;
}(typeof globalThis !== "undefined" ? globalThis : this, () => {
  "use strict";

  function recognizedEvents(events) {
    return events
      .filter((event) => event.event_type === "letter" && event.source === "recognizer")
      .map((event) => ({
        id: event.id,
        predictedLetter: event.predicted_letter,
        confirmedLetter: event.confirmed_letter,
        confidence: event.confidence,
        corrected: Boolean(event.corrected),
        createdAt: event.created_at,
      }))
      .reverse();
  }

  function confidenceLabel(value) {
    return typeof value === "number" && Number.isFinite(value)
      ? `Confiança ${Math.round(value * 100)}%`
      : "Confiança indisponível";
  }

  function timeLabel(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Horário indisponível";
    return new Intl.DateTimeFormat("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).format(date);
  }

  return { recognizedEvents, confidenceLabel, timeLabel };
}));
