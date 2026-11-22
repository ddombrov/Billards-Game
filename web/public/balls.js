// Drawing helpers shared by the home and game pages.
const SVG_NS = "http://www.w3.org/2000/svg";
// The classic look is the original Python version's: plain circles in these named colours, the stripes
// drawn in a lighter shade of their solid.
const BALL_COLORS = ["WHITE", "YELLOW", "BLUE", "RED", "PURPLE", "ORANGE", "GREEN", "BROWN", "BLACK",
                     "LIGHTYELLOW", "LIGHTBLUE", "PINK", "MEDIUMPURPLE", "LIGHTSALMON", "LIGHTGREEN", "SANDYBROWN"];

function el(name, attrs, parent) {
  const node = document.createElementNS(SVG_NS, name);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (parent) parent.appendChild(node);
  return node;
}

function ballSVG(number, size) {
  return el("circle", { r: size / 2, fill: BALL_COLORS[number] });
}

// A standalone ball for HTML layouts: the ball artwork in the modern look, a drawn ball in the classic one.
function ballIcon(number, size, className) {
  if (getLook() === "modern") {
    const img = document.createElement("img");
    img.src = ballArt(number, true);
    img.width = img.height = size;
    img.alt = number ? `${number} ball` : "Cue ball";
    if (className) img.className = className;
    return img;
  }
  const svg = el("svg", { width: size, height: size, viewBox: `${-size / 2} ${-size / 2} ${size} ${size}` });
  if (className) svg.setAttribute("class", className);
  svg.appendChild(ballSVG(number, size - 1));
  return svg;
}

const ballArt = (n, flat) => `/img/${flat ? "balls-flat" : "balls"}/ball-${n === 0 ? "cue" : n}.svg`;

// The look of the table, balls and cue, chosen in Settings and kept in this browser, like Splendor Duel's.
const LOOK_KEY = "eightball:look";
function getLook() {
  try { return localStorage.getItem(LOOK_KEY) === "classic" ? "classic" : "modern"; } catch { return "modern"; }
}
function setLook(look) {
  try { localStorage.setItem(LOOK_KEY, look); } catch { /* storage may be blocked */ }
}

// The name this browser last played under, so it does not have to be typed again.
const NAME_KEY = "eightball:name";
function savedName() {
  try { return localStorage.getItem(NAME_KEY) || ""; } catch { return ""; }
}
function rememberName(name) {
  try { if (name) localStorage.setItem(NAME_KEY, name.trim()); } catch { /* storage may be blocked */ }
}

// A tab remembers its seat in each online game, so two tabs of one browser can be the two players.
const seatKey = (code) => `eightball:seat:${code}`;
function readSeat(code) {
  try { return JSON.parse(sessionStorage.getItem(seatKey(code))); } catch { return null; }
}
function saveSeat(code, seat, token) {
  try { sessionStorage.setItem(seatKey(code), JSON.stringify({ seat, token })); } catch { /* storage may be blocked */ }
}

// Calls the Worker. Throws an Error carrying the server's message, reason and names.
async function api(method, path, body) {
  const response = await fetch("/api" + path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw Object.assign(new Error(data.error || "The server could not be reached."), { reason: data.reason, names: data.names });
  return data;
}

function celebrate() {
  if (typeof confetti === "function") {
    confetti({ particleCount: 160, spread: 85, origin: { y: 0.6 }, colors: ["#d9b15a", "#2f8f5d", "#d23a2b", "#1f4fbf", "#ffffff"] });
  }
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

// Creates a game in the database and opens it. Throws with the server's message, e.g. for a taken name.
async function startGame(player1, player2) {
  const response = await fetch("/api/games", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player1, player2 }),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(result.error || "Could not start the game.");
  location.href = "/play.html?game=" + encodeURIComponent(result.key);
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
