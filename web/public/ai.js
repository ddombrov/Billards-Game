// The computer player. For each ball it may play and each pocket it aims the cue ball at the spot that sends
// the ball into the pocket, tries the most promising of those shots at a few speeds with the real physics engine,
// scores what would happen under the game's rules, and takes the best one, with some wobble on the easier levels.
import { shotOutcome } from "/engine.js";
import { applyShot, inGroup, BALL_DIAMETER, MAX_SPEED, TABLE_LENGTH, TABLE_WIDTH } from "/rules.js";

const POCKETS = [[0, 0], [TABLE_WIDTH, 0], [0, TABLE_LENGTH / 2], [TABLE_WIDTH, TABLE_LENGTH / 2], [0, TABLE_LENGTH], [TABLE_WIDTH, TABLE_LENGTH]];
// How far off the computer's aim can be, in degrees, and how many of the best-looking shots it tries.
const LEVELS = { easy: { wobble: 4, tries: 6 }, medium: { wobble: 1.5, tries: 12 }, hard: { wobble: 0.3, tries: 20 } };

function targets(state) {
  const me = state.turn;
  const objects = state.balls.map(([n]) => n).filter((n) => n !== 0);
  if (state.ruleset === "allred") return objects;
  const group = state.groups[me];
  if (!group) return objects.filter((n) => n !== 8);
  const own = objects.filter((n) => inGroup(n, group));
  return own.length ? own : objects.filter((n) => n === 8);
}

function score(state, next, me) {
  if (next.winner === me) return 1000;
  if (next.winner !== null) return -1000;
  const mine = next.ruleset === "allred" ? next.potted[me].length - state.potted[me].length
    : next.balls.length < state.balls.length && next.turn === me ? state.balls.length - next.balls.length : 0;
  return (next.turn === me ? 100 : 0) + mine * 20 - (next.message.startsWith("Scratch") ? 60 : 0);
}

export async function chooseShot(state, level = "medium") {
  const { wobble, tries } = LEVELS[level] ?? LEVELS.medium;
  const me = state.turn;
  const cue = state.balls.find(([n]) => n === 0);
  const aims = [];
  for (const n of targets(state)) {
    const [, bx, by] = state.balls.find(([m]) => m === n);
    for (const [px, py] of POCKETS) {
      const dx = px - bx, dy = py - by, d = Math.hypot(dx, dy);
      const gx = bx - (dx / d) * BALL_DIAMETER, gy = by - (dy / d) * BALL_DIAMETER; // where the cue ball must hit
      const ax = gx - cue[1], ay = gy - cue[2], a = Math.hypot(ax, ay);
      const cut = (ax * dx + ay * dy) / (a * d); // 1 is straight on
      if (a < 1 || cut < 0.3) continue;
      aims.push({ ux: ax / a, uy: ay / a, look: cut / (a + d), reach: a + d });
    }
  }
  // The break, or nothing lined up: hit the nearest ball it may play.
  if (!aims.length) {
    const [n] = targets(state);
    const [, bx, by] = state.balls.find(([m]) => m === n);
    const ax = bx - cue[1], ay = by - cue[2], a = Math.hypot(ax, ay) || 1;
    aims.push({ ux: ax / a, uy: ay / a, look: 0, reach: a });
  }
  aims.sort((p, q) => q.look - p.look);
  let best = null;
  for (const aim of aims.slice(0, tries)) {
    for (const factor of [0.9, 1.3, 1.8]) {
      const speed = Math.min(MAX_SPEED, 700 + aim.reach * factor);
      const out = await shotOutcome(state.balls, aim.ux * speed, aim.uy * speed);
      const value = score(state, applyShot(state, out.pocketed, out.balls), me);
      if (!best || value > best.value) best = { ...aim, speed, value };
    }
  }
  const turn = ((Math.random() * 2 - 1) * wobble * Math.PI) / 180;
  const ux = best.ux * Math.cos(turn) - best.uy * Math.sin(turn), uy = best.ux * Math.sin(turn) + best.uy * Math.cos(turn);
  return { vx: ux * best.speed, vy: uy * best.speed };
}
