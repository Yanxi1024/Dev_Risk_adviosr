import { formatOutputWithHighlights } from './formatOutputWithHighlights.js';

export function renderDetailedResult() {
  const container = document.getElementById("detailed-result-container");
  if (!container) return;

  const rawJson = container.dataset.json;
  let data;
  try {
    data = JSON.parse(rawJson);
  } catch (e) {
    console.error("❌ Failed to parse JSON:", e);
    return;
  }

  const output2 = formatOutputWithHighlights(data, "output2");
  const output3 = formatOutputWithHighlights(data, "output3");
  const output4 = formatOutputWithHighlights(data, "output4");

  const finalHtml = `${output2}<br>${output3}${output4}`;
  container.innerHTML = finalHtml;
}
