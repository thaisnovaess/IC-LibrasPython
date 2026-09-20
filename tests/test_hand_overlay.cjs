"use strict";

const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const test = require("node:test");
const overlay = require("../webapp/static/hand-overlay.js");

function fakeContext() {
  const calls = { clear: 0, strokes: 0, arcs: 0, fills: 0 };
  return {
    calls,
    clearRect() { calls.clear += 1; },
    beginPath() {},
    moveTo() {},
    lineTo() {},
    stroke() { calls.strokes += 1; },
    arc() { calls.arcs += 1; },
    fill() { calls.fills += 1; },
  };
}

const viewport = { width: 640, height: 400, videoWidth: 1280, videoHeight: 720 };
const hand = Array.from({ length: 21 }, (_, index) => [index / 20, (index % 5) / 4, 0]);

test("draws 21 landmarks and the complete hand skeleton", () => {
  const context = fakeContext();

  overlay.draw(context, [hand], viewport);

  assert.equal(context.calls.clear, 1);
  assert.equal(context.calls.strokes, 21);
  assert.equal(context.calls.arcs, 42);
  assert.equal(context.calls.fills, 42);
});

test("clears the overlay when no hand is detected", () => {
  const context = fakeContext();

  overlay.draw(context, [], viewport);

  assert.deepEqual(context.calls, { clear: 1, strokes: 0, arcs: 0, fills: 0 });
});

test("pauses tracking during prediction and always resumes it", async () => {
  const state = { trackingPaused: false };

  await overlay.withTrackingPaused(state, async () => {
    assert.equal(state.trackingPaused, true);
  });
  assert.equal(state.trackingPaused, false);

  await assert.rejects(
    overlay.withTrackingPaused(state, async () => { throw new Error("fixture"); }),
    /fixture/,
  );
  assert.equal(state.trackingPaused, false);
});

test("wires the tested pause helper into the prediction flow", () => {
  const application = readFileSync("webapp/static/app.js", "utf8");

  assert.match(application, /HandOverlay\.withTrackingPaused\(state/);
  assert.match(application, /index < 12/);
  assert.match(application, /JSON\.stringify\(\{ frames \}\)/);
  assert.match(application, /HandOverlay\.updatePreview\(state\.previewHistory, preview\)/);
  assert.match(application, /renderLivePreview\(stabilized\.stable\)/);
});

test("shows a preview only after three matching predictions", () => {
  let history = [];
  let result;
  for (const confidence of [0.7, 0.8, 0.9]) {
    result = overlay.updatePreview(history, { letter: "A", confidence });
    history = result.history;
  }

  assert.deepEqual(result.stable, { letter: "A", confidence: 0.8 });
  assert.equal(history.length, 3);
});

test("uses the majority of the last five predictions", () => {
  let result = { history: [], stable: null };
  for (const letter of ["A", "A", "A", "B", "B"]) {
    result = overlay.updatePreview(result.history, { letter, confidence: 0.9 });
  }

  assert.deepEqual(result.stable, { letter: "A", confidence: 0.9 });
  assert.equal(result.history.length, 5);
});

test("accepts exactly sixty percent and rejects values below it", () => {
  let accepted = { history: [], stable: null };
  let rejected = { history: [], stable: null };
  for (let index = 0; index < 3; index += 1) {
    accepted = overlay.updatePreview(accepted.history, { letter: "A", confidence: 0.6 });
    rejected = overlay.updatePreview(rejected.history, { letter: "A", confidence: 0.59 });
  }

  assert.deepEqual(accepted.stable, { letter: "A", confidence: 0.6 });
  assert.equal(rejected.stable, null);
});

test("hides unstable or low-confidence previews and resets without a hand", () => {
  let result = overlay.updatePreview([], { letter: "A", confidence: 0.5 });
  result = overlay.updatePreview(result.history, { letter: "B", confidence: 0.9 });
  result = overlay.updatePreview(result.history, { letter: "A", confidence: 0.5 });
  result = overlay.updatePreview(result.history, { letter: "A", confidence: 0.5 });

  assert.equal(result.stable, null);
  result = overlay.updatePreview(result.history, null);
  assert.deepEqual(result, { history: [], stable: null });
});
