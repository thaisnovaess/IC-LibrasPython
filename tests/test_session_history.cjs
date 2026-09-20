"use strict";

const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const test = require("node:test");
const {
  recognizedEvents,
  confidenceLabel,
  timeLabel,
} = require("../webapp/static/session-history.js");

test("keeps only confirmed recognizer letters in newest-first order", () => {
  const events = [
    { id: 1, event_type: "letter", source: "manual", confirmed_letter: "M" },
    { id: 2, event_type: "space", source: "manual" },
    {
      id: 3,
      event_type: "letter",
      source: "recognizer",
      predicted_letter: "A",
      confirmed_letter: "A",
      confidence: 0.91,
      corrected: false,
      created_at: "2026-09-20T10:00:00.000+00:00",
    },
    {
      id: 4,
      event_type: "letter",
      source: "recognizer",
      predicted_letter: "D",
      confirmed_letter: "B",
      confidence: 0.72,
      corrected: true,
      created_at: "2026-09-20T10:01:00.000+00:00",
    },
  ];

  assert.deepEqual(recognizedEvents(events), [
    {
      id: 4,
      predictedLetter: "D",
      confirmedLetter: "B",
      confidence: 0.72,
      corrected: true,
      createdAt: "2026-09-20T10:01:00.000+00:00",
    },
    {
      id: 3,
      predictedLetter: "A",
      confirmedLetter: "A",
      confidence: 0.91,
      corrected: false,
      createdAt: "2026-09-20T10:00:00.000+00:00",
    },
  ]);
});

test("returns an empty history when no camera signal was confirmed", () => {
  assert.deepEqual(recognizedEvents([
    { id: 1, event_type: "letter", source: "manual", confirmed_letter: "A" },
    { id: 2, event_type: "clear", source: "manual" },
  ]), []);
});

test("formats missing history metadata without breaking the interface", () => {
  assert.equal(confidenceLabel(0.914), "Confiança 91%");
  assert.equal(confidenceLabel(null), "Confiança indisponível");
  assert.equal(timeLabel("not-a-date"), "Horário indisponível");
});

test("wires session events into the history renderer", () => {
  const application = readFileSync("webapp/static/app.js", "utf8");

  assert.match(application, /renderSignalHistory\(session\.events\)/);
  assert.match(application, /SessionHistory\.recognizedEvents\(events\)/);
});
