(function exposeHandOverlay(root, factory) {
  const overlay = factory();
  if (typeof module === "object" && module.exports) module.exports = overlay;
  else root.HandOverlay = overlay;
}(typeof globalThis !== "undefined" ? globalThis : this, () => {
  "use strict";

  const connections = [
    [0, 1], [1, 2], [2, 3], [3, 4],
    [0, 5], [5, 6], [6, 7], [7, 8],
    [5, 9], [9, 10], [10, 11], [11, 12],
    [9, 13], [13, 14], [14, 15], [15, 16],
    [13, 17], [17, 18], [18, 19], [19, 20], [0, 17],
  ];

  function coordinates(point, viewport) {
    const scale = Math.max(
      viewport.width / viewport.videoWidth,
      viewport.height / viewport.videoHeight,
    );
    const renderedWidth = viewport.videoWidth * scale;
    const renderedHeight = viewport.videoHeight * scale;
    return {
      x: (viewport.width - renderedWidth) / 2 + point[0] * renderedWidth,
      y: (viewport.height - renderedHeight) / 2 + point[1] * renderedHeight,
    };
  }

  function draw(context, hands, viewport) {
    context.clearRect(0, 0, viewport.width, viewport.height);
    for (const hand of hands) {
      const points = hand.map((point) => coordinates(point, viewport));
      context.lineCap = "round";
      context.lineJoin = "round";
      context.strokeStyle = "#72f0c0";
      context.lineWidth = 3;
      for (const [start, end] of connections) {
        context.beginPath();
        context.moveTo(points[start].x, points[start].y);
        context.lineTo(points[end].x, points[end].y);
        context.stroke();
      }
      for (const point of points) {
        context.beginPath();
        context.arc(point.x, point.y, 5, 0, Math.PI * 2);
        context.fillStyle = "#08251d";
        context.fill();
        context.beginPath();
        context.arc(point.x, point.y, 3, 0, Math.PI * 2);
        context.fillStyle = "#9effd9";
        context.fill();
      }
    }
  }

  async function withTrackingPaused(state, operation) {
    state.trackingPaused = true;
    try {
      return await operation();
    } finally {
      state.trackingPaused = false;
    }
  }

  function updatePreview(history, preview, options = {}) {
    const windowSize = options.windowSize || 5;
    const minimumAgreement = options.minimumAgreement || 3;
    const minimumConfidence = options.minimumConfidence || 0.6;
    if (
      !preview
      || typeof preview.letter !== "string"
      || typeof preview.confidence !== "number"
    ) return { history: [], stable: null };

    const nextHistory = [...history, preview].slice(-windowSize);
    const counts = new Map();
    for (const item of nextHistory) {
      counts.set(item.letter, (counts.get(item.letter) || 0) + 1);
    }
    const candidate = [...counts.entries()]
      .sort((left, right) => right[1] - left[1])[0][0];
    const matching = nextHistory.filter((item) => item.letter === candidate);
    if (matching.length < minimumAgreement) {
      return { history: nextHistory, stable: null };
    }
    const confidences = matching.map((item) => item.confidence).sort((a, b) => a - b);
    const middle = Math.floor(confidences.length / 2);
    const median = confidences.length % 2
      ? confidences[middle]
      : (confidences[middle - 1] + confidences[middle]) / 2;
    return {
      history: nextHistory,
      stable: median >= minimumConfidence
        ? { letter: candidate, confidence: median }
        : null,
    };
  }

  return { connections, coordinates, draw, updatePreview, withTrackingPaused };
}));
