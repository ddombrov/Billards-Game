// The Worker: serves the game (public/) and stores games in D1.
//   POST /api/games            { player1, player2 }                  -> new game
//   GET  /api/games/:key                                              -> game
//   POST /api/games/:key/shots { shot, vx, vy, time, pocketed, balls } -> game after the shot
// Physics runs in the browser (phylib.c as WebAssembly); the Worker applies the rules and saves the
// shot and the resting table in the same tables Physics.py uses.
import { applyShot, checkNames, newGame, MAX_SPEED, TABLE_LENGTH, TABLE_WIDTH } from "../public/rules.js";

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
const fail = (status, error) => json({ error }, status);

const KEY_ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789";
function newKey() {
  const bytes = crypto.getRandomValues(new Uint8Array(12));
  return [...bytes].map((b) => KEY_ALPHABET[b % KEY_ALPHABET.length]).join("");
}

async function loadGame(db, key) {
  const row = await db.prepare("SELECT GameState.GAMEID, STATE, GAMENAME FROM GameState JOIN Game ON Game.GAMEID = GameState.GAMEID WHERE KEY = ?")
    .bind(key).first();
  return row && { id: row.GAMEID, name: row.GAMENAME, state: JSON.parse(row.STATE) };
}

const view = (key, game) => ({ key, name: game.name, ...game.state });

async function createGame(db, body) {
  const error = checkNames(body.player1, body.player2);
  if (error) return fail(error.includes("taken") ? 409 : 400, error);
  const player1 = body.player1.trim(), player2 = body.player2.trim();
  const name = `${player1} vs ${player2}`;
  const state = newGame(player1, player2);
  const key = newKey();

  // A D1 batch is one transaction, so MAX(GAMEID) is the game inserted just above.
  await db.batch([
    db.prepare("INSERT INTO Game (GAMENAME) VALUES (?)").bind(name),
    db.prepare("INSERT INTO Player (GAMEID, PLAYERNAME) VALUES ((SELECT MAX(GAMEID) FROM Game), ?)").bind(player1),
    db.prepare("INSERT INTO Player (GAMEID, PLAYERNAME) VALUES ((SELECT MAX(GAMEID) FROM Game), ?)").bind(player2),
    db.prepare("INSERT INTO GameState (GAMEID, KEY, STATE) VALUES ((SELECT MAX(GAMEID) FROM Game), ?, ?)").bind(key, JSON.stringify(state)),
  ]);
  return json({ key, name, ...state }, 201);
}

function checkShot(state, body) {
  if (state.winner !== null) return "The game is over.";
  if (body.shot !== state.shots) return "This shot was already played. Reload the game.";
  if (![body.vx, body.vy, body.time].every(Number.isFinite) || Math.hypot(body.vx, body.vy) > MAX_SPEED + 1) return "Invalid shot.";
  const before = new Set(state.balls.map(([n]) => n));
  if (!Array.isArray(body.pocketed) || !body.pocketed.every((n) => before.has(n))) return "Invalid shot.";
  if (!Array.isArray(body.balls) || body.balls.length + body.pocketed.length !== before.size) return "Invalid shot.";
  const onTable = (b) => Array.isArray(b) && before.has(b[0]) && !body.pocketed.includes(b[0]) &&
    b[1] >= 0 && b[1] <= TABLE_WIDTH && b[2] >= 0 && b[2] <= TABLE_LENGTH;
  if (!body.balls.every(onTable)) return "Invalid shot.";
  return null;
}

async function playShot(db, key, body) {
  const game = await loadGame(db, key);
  if (!game) return fail(404, "Game not found.");
  const error = checkShot(game.state, body);
  if (error) return fail(409, error);

  const next = applyShot(game.state, body.pocketed, body.balls);
  const shooter = game.state.turn;
  const statements = [
    db.prepare(`INSERT INTO Shot (PLAYERID, GAMEID)
                VALUES ((SELECT PLAYERID FROM Player WHERE GAMEID = ?1 ORDER BY PLAYERID LIMIT 1 OFFSET ?2), ?1)`).bind(game.id, shooter),
    db.prepare("INSERT INTO TTable (TIME) VALUES (?)").bind(body.time),
    db.prepare("INSERT INTO TableShot (TABLEID, SHOTID) VALUES ((SELECT MAX(TABLEID) FROM TTable), (SELECT MAX(SHOTID) FROM Shot))"),
  ];
  for (const [n, x, y] of body.balls) {
    statements.push(
      db.prepare("INSERT INTO Ball (BALLNO, XPOS, YPOS) VALUES (?, ?, ?)").bind(n, x, y),
      db.prepare("INSERT INTO BallTable (BALLID, TABLEID) VALUES (last_insert_rowid(), (SELECT MAX(TABLEID) FROM TTable))"),
    );
  }
  statements.push(db.prepare("UPDATE GameState SET STATE = ?, UPDATED = datetime('now') WHERE GAMEID = ?").bind(JSON.stringify(next), game.id));
  await db.batch(statements);
  return json(view(key, { ...game, state: next }));
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const parts = url.pathname.split("/").filter(Boolean); // ["api", "games", key, "shots"]
    if (parts[0] !== "api") return env.ASSETS.fetch(request);

    try {
      const body = request.method === "POST" ? await request.json().catch(() => ({})) : null;
      if (parts[1] === "games" && parts.length === 2 && request.method === "POST") return await createGame(env.DB, body);
      if (parts[1] === "games" && parts.length === 3 && request.method === "GET") {
        const game = await loadGame(env.DB, parts[2]);
        return game ? json(view(parts[2], game)) : fail(404, "Game not found.");
      }
      if (parts[1] === "games" && parts[3] === "shots" && parts.length === 4 && request.method === "POST") {
        return await playShot(env.DB, parts[2], body);
      }
      return fail(404, "Not found.");
    } catch (error) {
      console.error(error);
      return fail(500, "Something went wrong saving the game.");
    }
  },
};
