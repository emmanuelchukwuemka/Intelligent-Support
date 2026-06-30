// Minimal dependency-free SVG line chart (no CDN needed) for the
// Progress Tracking dashboard (Chapter 4.3.4).
function renderLineChart(svgEl, series, opts) {
  opts = opts || {};
  const width = opts.width || 640;
  const height = opts.height || 220;
  const padding = { top: 16, right: 16, bottom: 28, left: 32 };
  const colors = opts.colors || ["#2952a3", "#e2691b"];

  svgEl.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svgEl.innerHTML = "";

  if (!series.length || !series[0].data.length) {
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", width / 2);
    text.setAttribute("y", height / 2);
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("fill", "#9ca3af");
    text.setAttribute("font-size", "13");
    text.textContent = "No data yet";
    svgEl.appendChild(text);
    return;
  }

  const allValues = series.flatMap(s => s.data.map(p => p.y));
  const minY = Math.min(0, ...allValues);
  const maxY = Math.max(10, ...allValues);
  const n = series[0].data.length;

  const xAt = (i) => padding.left + (i / Math.max(1, n - 1)) * (width - padding.left - padding.right);
  const yAt = (v) => height - padding.bottom - ((v - minY) / (maxY - minY || 1)) * (height - padding.top - padding.bottom);

  const ns = "http://www.w3.org/2000/svg";

  // Axis line
  const axis = document.createElementNS(ns, "line");
  axis.setAttribute("x1", padding.left);
  axis.setAttribute("y1", height - padding.bottom);
  axis.setAttribute("x2", width - padding.right);
  axis.setAttribute("y2", height - padding.bottom);
  axis.setAttribute("stroke", "#e2e8f0");
  svgEl.appendChild(axis);

  series.forEach((s, idx) => {
    const color = colors[idx % colors.length];
    const points = s.data.map((p, i) => `${xAt(i)},${yAt(p.y)}`).join(" ");
    const polyline = document.createElementNS(ns, "polyline");
    polyline.setAttribute("points", points);
    polyline.setAttribute("fill", "none");
    polyline.setAttribute("stroke", color);
    polyline.setAttribute("stroke-width", "2.5");
    svgEl.appendChild(polyline);

    s.data.forEach((p, i) => {
      const circle = document.createElementNS(ns, "circle");
      circle.setAttribute("cx", xAt(i));
      circle.setAttribute("cy", yAt(p.y));
      circle.setAttribute("r", "3.5");
      circle.setAttribute("fill", color);
      const title = document.createElementNS(ns, "title");
      title.textContent = `${p.label}: ${p.y}`;
      circle.appendChild(title);
      svgEl.appendChild(circle);
    });
  });

  // Legend
  series.forEach((s, idx) => {
    const color = colors[idx % colors.length];
    const ly = 12 + idx * 14;
    const rect = document.createElementNS(ns, "rect");
    rect.setAttribute("x", width - padding.right - 90);
    rect.setAttribute("y", ly - 8);
    rect.setAttribute("width", "10");
    rect.setAttribute("height", "10");
    rect.setAttribute("fill", color);
    svgEl.appendChild(rect);
    const text = document.createElementNS(ns, "text");
    text.setAttribute("x", width - padding.right - 75);
    text.setAttribute("y", ly + 1);
    text.setAttribute("font-size", "11");
    text.setAttribute("fill", "#374151");
    text.textContent = s.name;
    svgEl.appendChild(text);
  });
}
