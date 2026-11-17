// Drawing helpers shared by the home and game pages.
const SVG_NS = "http://www.w3.org/2000/svg";
const BALL_COLORS = ["#f6f3ea", "#f2c12e", "#1f4fbf", "#d23a2b", "#5b2a86", "#f07b1d", "#1d7a3a",
                     "#7a1f1f", "#111111", "#f2c12e", "#1f4fbf", "#d23a2b", "#5b2a86", "#f07b1d",
                     "#1d7a3a", "#7a1f1f"];
let ballClipCounter = 0;

function el(name, attrs, parent) {
  const node = document.createElementNS(SVG_NS, name);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (parent) parent.appendChild(node);
  return node;
}

// The shine gradient has to exist once in every SVG that draws balls.
function addBallDefs(svg) {
  const defs = el("defs", {}, svg);
  const shine = el("radialGradient", { id: "shine", cx: "35%", cy: "30%", r: "75%" }, defs);
  [[0, .75, "#fff"], [.18, .15, "#fff"], [.5, 0, "#fff"], [1, .45, "#000"]].forEach(([o, a, c]) =>
    el("stop", { offset: o, "stop-color": c, "stop-opacity": a }, shine));
}

function ballSVG(number, size, withShadow) {
  const g = el("g", {});
  const r = size / 2;
  if (withShadow) el("ellipse", { cx: r * .25, cy: r * .35, rx: r * 1.02, ry: r * .95, fill: "#000", "fill-opacity": .35 }, g);
  if (number >= 9) {
    const clipID = "ballclip" + ballClipCounter++;
    el("clipPath", { id: clipID }, g).appendChild(el("circle", { r }));
    el("circle", { r, fill: BALL_COLORS[0] }, g);
    el("rect", { x: -r, y: -r * .55, width: 2 * r, height: r * 1.1, fill: BALL_COLORS[number],
                 "clip-path": `url(#${clipID})` }, g);
  } else {
    el("circle", { r, fill: BALL_COLORS[number] }, g);
  }
  if (number > 0) {
    el("circle", { r: r * .46, fill: "#fbf9f3" }, g);
    const text = el("text", { "text-anchor": "middle", "dominant-baseline": "central",
                              "font-size": r * .58, "font-weight": 700,
                              "font-family": "Inter, system-ui, sans-serif", fill: "#151515" }, g);
    text.textContent = number;
  }
  el("circle", { r, fill: "url(#shine)" }, g);
  return g;
}

// A standalone <svg> holding one ball, for use in HTML layouts.
function ballIcon(number, size, className) {
  const svg = el("svg", { width: size, height: size, viewBox: `${-size / 2} ${-size / 2} ${size} ${size}` });
  if (className) svg.setAttribute("class", className);
  svg.appendChild(ballSVG(number, size - 1, false));
  return svg;
}

const LAST_GAME_KEY = "eightball:lastGame";
function rememberGame(id) {
  try { localStorage.setItem(LAST_GAME_KEY, String(id)); } catch { /* storage may be blocked */ }
}
function lastGame() {
  try { return localStorage.getItem(LAST_GAME_KEY); } catch { return null; }
}
function forgetGame() {
  try { localStorage.removeItem(LAST_GAME_KEY); } catch { /* storage may be blocked */ }
}

const RULES_HTML = `
  <ul class="rules">
    <li>Players take turns. Player 1 breaks.</li>
    <li>The first player to pocket a ball (without scratching) takes that group: solids (1-7) or stripes (9-15). The other player gets the other group.</li>
    <li>Pocket one of your own balls and you shoot again. Otherwise the turn passes.</li>
    <li>Pocketing the cue ball is a scratch: the turn passes and the cue ball goes back to its starting spot.</li>
    <li>Clear your group, then sink the 8 to win. Sinking the 8 early, or scratching on it, loses the game.</li>
  </ul>
  <p class="description">To shoot, press on the table and drag away from the cue ball. Pull farther for more power and let go to shoot.</p>`;
