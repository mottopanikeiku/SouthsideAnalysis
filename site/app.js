"use strict";

const svgNS = "http://www.w3.org/2000/svg";
const map = document.querySelector("#map");
const groups = document.querySelector("#block-groups");
const yearControl = document.querySelector("#year");
const algorithmControl = document.querySelector("#algorithm");
const summary = document.querySelector("#partition-summary");
const message = document.querySelector("#map-message");
const palette = [
  "#4477aa", "#ee6677", "#228833", "#ccbb44", "#66ccee", "#aa3377",
  "#7755aa", "#dd8844", "#44aa99", "#bb6677", "#669944", "#997744",
  "#557799", "#aa9944", "#995588", "#559999", "#aa6655", "#7799bb",
];
const algorithmNames = { louvain: "Louvain", leiden: "Leiden" };
let data;
let features = [];
let paths = [];
let activeIndex = 0;
let selectedGeoid = null;
let selectedPath = null;
let initialView;
let view;
let drag = null;
let suppressClick = false;

function setView(next) {
  view = next;
  map.setAttribute("viewBox", view.join(" "));
  const scale = initialView[2] / view[2];
  document.querySelector("#zoom-level").textContent = `${Math.round(scale * 100)}%`;
  document.querySelector("#zoom-in").disabled = scale >= 12 - 0.001;
  document.querySelector("#zoom-out").disabled = scale <= 1 + 0.001;
}

function mapPoint(clientX, clientY, inverse = map.getScreenCTM().inverse()) {
  const point = map.createSVGPoint();
  point.x = clientX;
  point.y = clientY;
  return point.matrixTransform(inverse);
}

function zoom(factor, anchor) {
  if (!view) return;
  const oldScale = initialView[2] / view[2];
  const scale = Math.max(1, Math.min(12, oldScale * factor));
  const ratio = oldScale / scale;
  const center = anchor || { x: view[0] + view[2] / 2, y: view[1] + view[3] / 2 };
  setView([
    center.x - (center.x - view[0]) * ratio,
    center.y - (center.y - view[1]) * ratio,
    view[2] * ratio,
    view[3] * ratio,
  ]);
}

function pan(direction) {
  if (!view) return;
  const offsets = { left: [-0.18, 0], right: [0.18, 0], up: [0, -0.18], down: [0, 0.18] };
  const [x, y] = offsets[direction];
  setView([view[0] + x * view[2], view[1] + y * view[3], view[2], view[3]]);
}

function setActive(index, focus = false) {
  if (paths[activeIndex]) paths[activeIndex].setAttribute("tabindex", "-1");
  activeIndex = index;
  paths[index].setAttribute("tabindex", "0");
  if (focus) paths[index].focus({ preventScroll: true });
}

function selectFeature(index, announce = true) {
  const feature = features[index];
  const algorithm = algorithmControl.value;
  selectedGeoid = feature.geoid;
  if (selectedPath) {
    selectedPath.classList.remove("is-selected");
    selectedPath.setAttribute("aria-pressed", "false");
  }
  selectedPath = paths[index];
  selectedPath.classList.add("is-selected");
  selectedPath.setAttribute("aria-pressed", "true");
  const hadFocus = document.activeElement === selectedPath;
  groups.append(selectedPath);
  setActive(index, hadFocus);
  document.querySelector("#selection-empty").hidden = true;
  document.querySelector("#selection-details").hidden = false;
  document.querySelector("#selected-geoid").textContent = feature.geoid;
  document.querySelector("#selected-year").textContent = yearControl.value;
  document.querySelector("#selected-algorithm").textContent = algorithmNames[algorithm];
  document.querySelector("#selected-label").textContent = `Group ${feature[algorithm]}`;
  if (announce) {
    document.querySelector("#selection-announcement").textContent =
      `GEOID ${feature.geoid}, ${yearControl.value} ${algorithmNames[algorithm]}, group ${feature[algorithm]}.`;
  }
}

function renderPartition() {
  const year = yearControl.value;
  const algorithm = algorithmControl.value;
  const partition = data.years[year];
  const metrics = partition[algorithm];
  features = partition.features;
  const counts = new Map();
  for (const feature of features) {
    const label = feature[algorithm];
    counts.set(label, (counts.get(label) || 0) + 1);
  }
  const labels = [...counts.keys()].sort((a, b) => a - b);
  const colors = new Map(labels.map((label, index) => [label, palette[index % palette.length]]));
  summary.textContent = `${features.length.toLocaleString()} block groups · ${metrics.count} groups · Modularity ${metrics.modularity.toFixed(4)}`;
  document.querySelector("#map-title").textContent = `${year} ${algorithmNames[algorithm]} demographic groups`;
  document.querySelector("#objective-note").textContent = algorithm === "louvain"
    ? "This Louvain score uses weighted edges: demographic similarities are edge weights."
    : "This Leiden score uses unweighted edges: each graph edge has equal weight.";

  const fragment = document.createDocumentFragment();
  paths = features.map((feature, index) => {
    const path = document.createElementNS(svgNS, "path");
    const label = `GEOID ${feature.geoid}, ${year} ${algorithmNames[algorithm]}, group ${feature[algorithm]}`;
    path.setAttribute("d", feature.path);
    path.setAttribute("fill", colors.get(feature[algorithm]));
    path.setAttribute("class", "block-group");
    path.setAttribute("role", "button");
    path.setAttribute("aria-label", label);
    path.setAttribute("aria-pressed", "false");
    path.setAttribute("tabindex", index === 0 ? "0" : "-1");
    path.dataset.index = index;
    const title = document.createElementNS(svgNS, "title");
    title.textContent = label;
    path.append(title);
    fragment.append(path);
    return path;
  });
  groups.replaceChildren(fragment);
  activeIndex = 0;
  selectedPath = null;
  const selectedIndex = features.findIndex(feature => feature.geoid === selectedGeoid);
  if (selectedIndex >= 0) {
    selectFeature(selectedIndex);
  } else {
    selectedGeoid = null;
    document.querySelector("#selection-empty").hidden = false;
    document.querySelector("#selection-details").hidden = true;
    document.querySelector("#selection-announcement").textContent = "";
  }

  const legend = document.createDocumentFragment();
  for (const label of labels) {
    const item = document.createElement("li");
    const swatch = document.createElement("span");
    swatch.className = "legend-swatch";
    swatch.style.backgroundColor = colors.get(label);
    swatch.setAttribute("aria-hidden", "true");
    const name = document.createElement("span");
    name.textContent = `Group ${label}`;
    const count = document.createElement("span");
    count.className = "legend-count";
    count.textContent = counts.get(label).toLocaleString();
    count.setAttribute("aria-label", `${counts.get(label)} block groups`);
    item.append(swatch, name, count);
    legend.append(item);
  }
  document.querySelector("#legend").replaceChildren(legend);
}

yearControl.addEventListener("change", renderPartition);
algorithmControl.addEventListener("change", renderPartition);
document.querySelector("#zoom-in").addEventListener("click", () => zoom(1.5));
document.querySelector("#zoom-out").addEventListener("click", () => zoom(1 / 1.5));
document.querySelector("#reset-view").addEventListener("click", () => setView([...initialView]));
for (const button of document.querySelectorAll("[data-pan]")) {
  button.addEventListener("click", () => pan(button.dataset.pan));
}

map.addEventListener("click", event => {
  if (suppressClick) {
    suppressClick = false;
    return;
  }
  const path = event.target.closest(".block-group");
  if (path) selectFeature(Number(path.dataset.index));
});
map.addEventListener("focusin", event => {
  const path = event.target.closest(".block-group");
  if (path) setActive(Number(path.dataset.index));
});
map.addEventListener("keydown", event => {
  if (!view) return;
  const path = event.target.closest(".block-group");
  const arrows = { ArrowLeft: "left", ArrowRight: "right", ArrowUp: "up", ArrowDown: "down" };
  if (path && (event.key === "Enter" || event.key === " ")) {
    event.preventDefault();
    selectFeature(Number(path.dataset.index));
  } else if (arrows[event.key]) {
    event.preventDefault();
    if (path) {
      const offset = event.key === "ArrowLeft" || event.key === "ArrowUp" ? -1 : 1;
      setActive((Number(path.dataset.index) + offset + paths.length) % paths.length, true);
    } else {
      pan(arrows[event.key]);
    }
  } else if (event.key === "+" || event.key === "=") {
    event.preventDefault();
    zoom(1.5);
  } else if (event.key === "-") {
    event.preventDefault();
    zoom(1 / 1.5);
  } else if (event.key === "Home") {
    event.preventDefault();
    if (path) setActive(0, true);
    else setView([...initialView]);
  } else if (path && event.key === "End") {
    event.preventDefault();
    setActive(paths.length - 1, true);
  }
});
map.addEventListener("wheel", event => {
  if (!view) return;
  event.preventDefault();
  const delta = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? map.clientHeight : 1);
  zoom(Math.exp(-Math.max(-150, Math.min(150, delta)) * 0.003), mapPoint(event.clientX, event.clientY));
}, { passive: false });
map.addEventListener("pointerdown", event => {
  if (!view || !event.isPrimary || event.button !== 0) return;
  suppressClick = false;
  drag = {
    pointerId: event.pointerId,
    x: event.clientX,
    y: event.clientY,
    inverse: map.getScreenCTM().inverse(),
    view: [...view],
    moved: false,
  };
});
map.addEventListener("pointermove", event => {
  if (!drag || event.pointerId !== drag.pointerId) return;
  if (!drag.moved && Math.hypot(event.clientX - drag.x, event.clientY - drag.y) < 5) return;
  if (!drag.moved) {
    drag.moved = true;
    suppressClick = true;
    map.setPointerCapture(event.pointerId);
    map.classList.add("is-dragging");
  }
  const start = mapPoint(drag.x, drag.y, drag.inverse);
  const current = mapPoint(event.clientX, event.clientY, drag.inverse);
  setView([drag.view[0] + start.x - current.x, drag.view[1] + start.y - current.y, drag.view[2], drag.view[3]]);
});
function endDrag(event) {
  if (!drag || event.pointerId !== drag.pointerId) return;
  if (map.hasPointerCapture(event.pointerId)) map.releasePointerCapture(event.pointerId);
  drag = null;
  map.classList.remove("is-dragging");
}
map.addEventListener("pointerup", endDrag);
map.addEventListener("pointercancel", endDrag);
map.addEventListener("pointerleave", event => {
  if (drag && !drag.moved) endDrag(event);
});

async function loadMap() {
  try {
    const response = await fetch("data.json");
    if (!response.ok) throw new Error(`data.json returned HTTP ${response.status}`);
    data = await response.json();
    const [x, y, width, height] = data.viewBox;
    const padding = Math.max(width, height) * 0.025;
    initialView = [x - padding, y - padding, width + 2 * padding, height + 2 * padding];
    renderPartition();
    for (const control of document.querySelectorAll("button, select")) control.disabled = false;
    setView([...initialView]);
    message.hidden = true;
  } catch (error) {
    summary.textContent = "Map data could not be loaded.";
    message.textContent = `${error.message}. Serve the site directory over HTTP; opening index.html directly may block the local data request.`;
    message.setAttribute("role", "alert");
  }
}

loadMap();
