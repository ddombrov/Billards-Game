// The Worker: serves the game (public/) and stores games in D1.
//   Games on one device (anyone with the link can play):
//     POST /api/games            { player1, player2 }                  -> new game
//     GET  /api/games/:key                                              -> game
//     POST /api/games/:key/shots { shot, vx, vy, time, pocketed, balls } -> game after the shot
//     POST /api/games/:key/first { player }  -> that player breaks;  POST /api/games/:key/resign { player }
//   Online games: a 5-digit code, and a private token per seat.
//     POST   /api/rooms                 { name }          -> { code, seat: 0, token }
//     POST   /api/rooms/:code/join      { name }          -> { code, seat: 1, token }, or a "full" error with both names
//     POST   /api/rooms/:code/claim     { seat }          -> a new token for that seat, for a player who lost theirs
//     GET    /api/rooms/:code?token=                      -> the game, with "seated" and this tab's seat
//     POST   /api/rooms/:code/shots     { token, ...shot } -> game after the shot, only on the shooter's turn
//     POST   /api/rooms/:code/first     { token, player } -> the host chooses who breaks
//     POST   /api/rooms/:code/resign    { token }         -> that seat resigns
//     DELETE /api/rooms/:code           { token }         -> the host cancels a game nobody has joined
//     POST   /api/quick { name }, GET /api/quick/:ticket, DELETE /api/quick/:ticket -> quick match
// Physics runs in the browser (phylib.c as WebAssembly); the Worker applies the rules and saves the
// shot and the resting table in the same tables Physics.py uses. Each saved game also keeps the last
// shot's cue speed and starting table, so the other player's browser can replay it with the same engine.
import { applyShot, checkNames, chooseFirst, newGame, resign, sameName, MAX_NAME_LENGTH, MAX_SPEED, TABLE_LENGTH, TABLE_WIDTH } from "../public/rules.js";

const WEEK = 7 * 24 * 60 * 60 * 1000;
const QUEUE_WAIT = 70 * 1000; // a waiting quick match ticket older than this is dropped

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
const fail = (status, error, extra = {}) => json({ error, ...extra }, status);
const hex = (bytes) => [...crypto.getRandomValues(new Uint8Array(bytes))].map((b) => b.toString(16).padStart(2, "0")).join("");
const cleanName = (n) => (typeof n === "string" ? n.replace(/\s+/g, " ").trim().slice(0, MAX_NAME_LENGTH) : "");
const isUniqueError = (e) => /UNIQUE|constraint/i.test(String(e?.message ?? e));

const KEY_ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789";
function newKey() {
  const bytes = crypto.getRandomValues(new Uint8Array(12));
  return [...bytes].map((b) => KEY_ALPHABET[b % KEY_ALPHABET.length]).join("");
}

async function loadGame(db, where, value) {
  const row = await db.prepare(`SELECT GameState.GAMEID, KEY, STATE, GAMENAME FROM GameState JOIN Game ON Game.GAMEID = GameState.GAMEID WHERE ${where} = ?`)
    .bind(value).first();
  return row && { id: row.GAMEID, key: row.KEY, name: row.GAMENAME, state: JSON.parse(row.STATE) };
}

const view = (key, game) => ({ key, name: game.name, ...game.state });

// Inserts a game and its players. In a D1 batch, MAX(GAMEID) is the game inserted just above.
function insertGame(db, players, state, key) {
  const name = players.filter(Boolean).join(" vs ");
  return [
    db.prepare("INSERT INTO Game (GAMENAME) VALUES (?)").bind(name),
    ...players.filter(Boolean).map((p) => db.prepare("INSERT INTO Player (GAMEID, PLAYERNAME) VALUES ((SELECT MAX(GAMEID) FROM Game), ?)").bind(p)),
    db.prepare("INSERT INTO GameState (GAMEID, KEY, STATE) VALUES ((SELECT MAX(GAMEID) FROM Game), ?, ?)").bind(key, JSON.stringify(state)),
  ];
}

async function createGame(db, body) {
  const error = checkNames(body.player1, body.player2);
  if (error) return fail(error.includes("taken") ? 409 : 400, error);
  const player1 = body.player1.trim(), player2 = body.player2.trim();
  const state = newGame(player1, player2, body.ruleset, body.ai);
  const key = newKey();
  await db.batch(insertGame(db, [player1, player2], state, key));
  return json({ key, name: `${player1} vs ${player2}`, ...state }, 201);
}

function checkShot(state, body) {
  if (state.winner !== null) return "The game is over.";
  if (state.awaitingFirst) return "Choose who breaks first.";
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

// Applies and saves one shot. Returns the next state, or an error message.
async function saveShot(db, game, body, extra = []) {
  const error = checkShot(game.state, body);
  if (error) return { error };
  const next = applyShot(game.state, body.pocketed, body.balls);
  next.last = { shot: game.state.shots, vx: body.vx, vy: body.vy, from: game.state.balls };
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
  // Only one save per shot number wins, so two tabs cannot both play the same shot.
  statements.push(db.prepare("UPDATE GameState SET STATE = ?, UPDATED = datetime('now') WHERE GAMEID = ? AND json_extract(STATE, '$.shots') = ?")
    .bind(JSON.stringify(next), game.id, game.state.shots), ...extra);
  await db.batch(statements);
  return { next };
}

// Saves a change that is not a shot (choosing who breaks, resigning), unless a shot was saved in between.
async function saveState(db, game, next) {
  const result = await db.prepare("UPDATE GameState SET STATE = ?, UPDATED = datetime('now') WHERE GAMEID = ? AND json_extract(STATE, '$.shots') = ?")
    .bind(JSON.stringify(next), game.id, game.state.shots).run();
  return result.meta.changes === 1;
}

async function gameAction(db, key, action, body) {
  const game = await loadGame(db, "KEY", key);
  if (!game) return fail(404, "Game not found.");
  if (await db.prepare("SELECT 1 FROM Room WHERE GAMEID = ?").bind(game.id).first()) return fail(403, "That is an online game.");
  const next = action === "first" ? chooseFirst(game.state, body.player) : resign(game.state, body.player);
  if (next === game.state) return fail(409, "That can't be done now.");
  if (!(await saveState(db, game, next))) return fail(409, "The game changed. Reload it.");
  return json(view(key, { ...game, state: next }));
}

async function playShot(db, key, body) {
  const game = await loadGame(db, "KEY", key);
  if (!game) return fail(404, "Game not found.");
  if (await db.prepare("SELECT 1 FROM Room WHERE GAMEID = ?").bind(game.id).first()) return fail(403, "That is an online game.");
  const { error, next } = await saveShot(db, game, body);
  return error ? fail(409, error) : json(view(key, { ...game, state: next }));
}

// ---------- online games ----------

const getRoom = (db, code) => db.prepare("SELECT * FROM Room WHERE CODE = ?").bind(code).first();
const seatOf = (room, token) => (token && room.SEAT0 === token ? 0 : token && room.SEAT1 && room.SEAT1 === token ? 1 : null);
// The game as a seated player sees it. The game's link key is left out, so the room can only be played with a token.
const roomView = (room, game, seat) => ({ code: room.CODE, seat, seated: !!room.SEAT1, name: game.name, ...game.state });

async function createRoom(db, names, paired, ruleset) {
  for (let tries = 0; tries < 60; tries++) {
    const code = String(Math.floor(Math.random() * 100000)).padStart(5, "0");
    const tokens = [hex(16), paired ? hex(16) : null];
    const state = newGame(names[0], names[1] || "", ruleset);
    const now = Date.now();
    try {
      await db.batch([
        ...insertGame(db, names, state, newKey()),
        db.prepare("INSERT INTO Room (CODE, GAMEID, SEAT0, SEAT1, ACTIVE0, ACTIVE1, CREATED, LAST_MOVE) VALUES (?, (SELECT MAX(GAMEID) FROM Game), ?, ?, ?, ?, ?, ?)")
          .bind(code, tokens[0], tokens[1], now, paired ? now : 0, now, now),
      ]);
      return { code, tokens };
    } catch (e) {
      if (!isUniqueError(e)) throw e;
    }
  }
  throw new Error("no free game code");
}

async function handleRooms(db, request, parts, url, body) {
  const method = request.method;
  if (method === "POST" && parts.length === 2) {
    const name = cleanName(body.name);
    if (!name) return fail(400, "Choose a name to start.");
    const { code, tokens } = await createRoom(db, [name], false, body.ruleset);
    return json({ code, seat: 0, token: tokens[0] }, 201);
  }

  const code = parts[2];
  if (!/^\d{5}$/.test(code || "")) return fail(404, "No game has that code.");
  const room = await getRoom(db, code);

  if (method === "POST" && parts[3] === "join") {
    if (!room) return fail(404, "No game has that code.");
    const game = await loadGame(db, "GameState.GAMEID", room.GAMEID);
    // A full game cannot be joined, but a player who lost their seat can take it back (see claim).
    if (room.SEAT1) return fail(409, "That game is already full.", { reason: "full", names: game.state.players });
    const name = cleanName(body.name);
    if (!name) return fail(400, "Choose a name to join.", { reason: "needname" });
    if (sameName(name, game.state.players[0])) return fail(409, "That name is taken, pick another.", { reason: "taken" });
    const token = hex(16);
    const state = { ...game.state, players: [game.state.players[0], name] };
    const results = await db.batch([
      db.prepare("UPDATE Room SET SEAT1 = ?, ACTIVE1 = ? WHERE CODE = ? AND SEAT1 IS NULL").bind(token, Date.now(), code),
      db.prepare("INSERT INTO Player (GAMEID, PLAYERNAME) SELECT ?, ? WHERE changes() = 1").bind(room.GAMEID, name),
      db.prepare("UPDATE GameState SET STATE = ? WHERE GAMEID = ? AND (SELECT SEAT1 FROM Room WHERE CODE = ?) = ?").bind(JSON.stringify(state), room.GAMEID, code, token),
      db.prepare("UPDATE Game SET GAMENAME = ? WHERE GAMEID = ? AND (SELECT SEAT1 FROM Room WHERE CODE = ?) = ?").bind(`${state.players[0]} vs ${name}`, room.GAMEID, code, token),
    ]);
    if (results[0].meta.changes !== 1) return fail(409, "That game is already full.", { reason: "full", names: game.state.players });
    return json({ code, seat: 1, token });
  }

  // Take over a seat in a full game. The old holder's token stops working, so it is whoever asked last.
  if (method === "POST" && parts[3] === "claim") {
    if (!room) return fail(404, "No game has that code.");
    if (!room.SEAT1) return fail(409, "That game is still waiting for a second player.");
    if (body.seat !== 0 && body.seat !== 1) return fail(400, "Pick a player.");
    const token = hex(16);
    await db.prepare(`UPDATE Room SET SEAT${body.seat} = ?, ACTIVE${body.seat} = ? WHERE CODE = ?`).bind(token, Date.now(), code).run();
    return json({ code, seat: body.seat, token });
  }

  if (method === "GET" && parts.length === 3) {
    if (!room) return fail(404, "That game no longer exists.", { reason: "notfound" });
    const seat = seatOf(room, url.searchParams.get("token"));
    if (seat === null) return fail(403, "You are not in that game.", { reason: "forbidden" });
    await db.prepare(`UPDATE Room SET ACTIVE${seat} = ? WHERE CODE = ?`).bind(Date.now(), code).run();
    const game = await loadGame(db, "GameState.GAMEID", room.GAMEID);
    return json(roomView(room, game, seat));
  }

  if (method === "POST" && parts[3] === "shots") {
    if (!room) return fail(404, "That game no longer exists.", { reason: "notfound" });
    const seat = seatOf(room, body.token);
    if (seat === null) return fail(403, "You are not in that game.", { reason: "forbidden" });
    if (!room.SEAT1) return fail(409, "Wait for the second player to join.");
    const game = await loadGame(db, "GameState.GAMEID", room.GAMEID);
    if (game.state.turn !== seat) return fail(409, "It is not your turn.");
    const now = Date.now();
    const { error, next } = await saveShot(db, game, body,
      [db.prepare(`UPDATE Room SET LAST_MOVE = ?, ACTIVE${seat} = ? WHERE CODE = ?`).bind(now, now, code)]);
    return error ? fail(409, error) : json(roomView(room, { ...game, state: next }, seat));
  }

  if (method === "POST" && (parts[3] === "first" || parts[3] === "resign")) {
    if (!room) return fail(404, "That game no longer exists.", { reason: "notfound" });
    const seat = seatOf(room, body.token);
    if (seat === null) return fail(403, "You are not in that game.", { reason: "forbidden" });
    if (parts[3] === "first" && seat !== 0) return fail(403, "Player 1 chooses who breaks.");
    const game = await loadGame(db, "GameState.GAMEID", room.GAMEID);
    const next = parts[3] === "first" ? chooseFirst(game.state, body.player) : resign(game.state, seat);
    if (next === game.state) return fail(409, "That can't be done now.");
    if (!(await saveState(db, game, next))) return fail(409, "The game changed. Reload it.");
    await db.prepare("UPDATE Room SET LAST_MOVE = ? WHERE CODE = ?").bind(Date.now(), code).run();
    return json(roomView(room, { ...game, state: next }, seat));
  }

  if (method === "DELETE" && parts.length === 3) {
    if (!room) return json({ ok: true });
    if (seatOf(room, body.token) !== 0) return fail(403, "Only the host can cancel a game.");
    if (room.SEAT1) return fail(409, "Someone has already joined.");
    await db.prepare("DELETE FROM Room WHERE CODE = ?").bind(code).run();
    return json({ ok: true });
  }
  return fail(404, "Not found.");
}

async function handleQuick(db, request, parts, body) {
  const method = request.method;
  if (method === "POST" && parts.length === 2) {
    const now = Date.now();
    await db.prepare("DELETE FROM Queue WHERE CODE IS NULL AND AT < ?").bind(now - QUEUE_WAIT).run();
    const ticket = hex(8);
    const name = cleanName(body.name) || "Player";
    const waiting = await db.prepare("SELECT TICKET, NAME FROM Queue WHERE CODE IS NULL ORDER BY AT LIMIT 1").first();
    // Claim the waiting ticket so two newcomers cannot both pair with it.
    const claimed = waiting && (await db.prepare("UPDATE Queue SET CODE = 'pending' WHERE TICKET = ? AND CODE IS NULL").bind(waiting.TICKET).run()).meta.changes === 1;
    if (claimed) {
      const second = sameName(name, waiting.NAME) ? `${name} (2)` : name;
      const { code, tokens } = await createRoom(db, [waiting.NAME, second], true);
      await db.batch([
        db.prepare("UPDATE Queue SET CODE = ?, SEAT = 0, TOKEN = ? WHERE TICKET = ?").bind(code, tokens[0], waiting.TICKET),
        db.prepare("INSERT INTO Queue (TICKET, AT, CODE, SEAT, TOKEN) VALUES (?, ?, ?, 1, ?)").bind(ticket, now, code, tokens[1]),
      ]);
    } else {
      await db.prepare("INSERT INTO Queue (TICKET, AT, NAME) VALUES (?, ?, ?)").bind(ticket, now, name).run();
    }
    return json({ ticket });
  }
  const ticket = parts[2];
  if (method === "GET" && ticket) {
    const row = await db.prepare("SELECT * FROM Queue WHERE TICKET = ?").bind(ticket).first();
    if (!row) return json({ gone: true });
    if (!row.CODE || row.CODE === "pending") {
      await db.prepare("UPDATE Queue SET AT = ? WHERE TICKET = ? AND CODE IS NULL").bind(Date.now(), ticket).run();
      return json({ waiting: true });
    }
    await db.prepare("DELETE FROM Queue WHERE TICKET = ?").bind(ticket).run();
    return json({ code: row.CODE, seat: row.SEAT, token: row.TOKEN });
  }
  if (method === "DELETE" && ticket) {
    await db.prepare("DELETE FROM Queue WHERE TICKET = ? AND CODE IS NULL").bind(ticket).run();
    return json({ ok: true });
  }
  return fail(404, "Not found.");
}

// The weekly job: forget online games with no shot for seven days, and old quick match tickets.
// The games and shots themselves stay in the history tables.
export async function cleanup(env, now = Date.now()) {
  await env.DB.prepare("DELETE FROM Room WHERE LAST_MOVE < ?").bind(now - WEEK).run();
  await env.DB.prepare("DELETE FROM Queue WHERE AT < ?").bind(now - 10 * 60 * 1000).run();
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const parts = url.pathname.split("/").filter(Boolean); // ["api", "games", key, "shots"]
    if (parts[0] !== "api") return env.ASSETS.fetch(request);

    try {
      const body = ["POST", "DELETE"].includes(request.method) ? await request.json().catch(() => ({})) : null;
      if (parts[1] === "games" && parts.length === 2 && request.method === "POST") return await createGame(env.DB, body);
      if (parts[1] === "games" && parts.length === 3 && request.method === "GET") {
        const game = await loadGame(env.DB, "KEY", parts[2]);
        return game ? json(view(parts[2], game)) : fail(404, "Game not found.");
      }
      if (parts[1] === "games" && parts[3] === "shots" && parts.length === 4 && request.method === "POST") {
        return await playShot(env.DB, parts[2], body);
      }
      if (parts[1] === "games" && (parts[3] === "first" || parts[3] === "resign") && parts.length === 4 && request.method === "POST") {
        return await gameAction(env.DB, parts[2], parts[3], body);
      }
      if (parts[1] === "rooms") return await handleRooms(env.DB, request, parts, url, body);
      if (parts[1] === "quick") return await handleQuick(env.DB, request, parts, body);
      return fail(404, "Not found.");
    } catch (error) {
      console.error(error);
      return fail(500, "Something went wrong saving the game.");
    }
  },

  async scheduled(event, env) {
    await cleanup(env);
  },
};
