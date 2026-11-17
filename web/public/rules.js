// 8-ball rules, shared by the browser and the Worker (a port of eightball.py).
export const TABLE_WIDTH = 1350;   // mm, matches PHYLIB_TABLE_WIDTH
export const TABLE_LENGTH = 2700;  // mm, matches PHYLIB_TABLE_LENGTH
export const BALL_DIAMETER = 57;   // mm, matches PHYLIB_BALL_DIAMETER
export const MAX_SPEED = 5000;     // mm/s
export const MAX_NAME_LENGTH = 20;

const HEAD_SPOT = [TABLE_WIDTH / 2, TABLE_LENGTH * 3 / 4];
const FOOT_SPOT = [TABLE_WIDTH / 2, TABLE_LENGTH / 4];

// Rack rows from the apex (on the foot spot) toward the far cushion, with the 8 in the
// middle and a solid and a stripe on the back corners.
const RACK = [[1], [9, 2], [10, 8, 3], [11, 4, 12, 5], [6, 13, 7, 14, 15]];
const RACK_COLUMN = BALL_DIAMETER + 1;
const RACK_ROW = 51; // rows overlap like a real triangle but stay just clear of touching

export const sameName = (a, b) => a.trim().toLowerCase() === b.trim().toLowerCase();

// Returns an error message, or null when the two names can start a game.
export function checkNames(player1, player2) {
  const a = (player1 || "").trim(), b = (player2 || "").trim();
  if (!a || !b) return "Both players need a name.";
  if (a.length > MAX_NAME_LENGTH || b.length > MAX_NAME_LENGTH) return `Names can be at most ${MAX_NAME_LENGTH} characters.`;
  if (sameName(a, b)) return "That name is taken, pick another.";
  return null;
}

export const inGroup = (n, group) =>
  (group === "solids" && n >= 1 && n <= 7) || (group === "stripes" && n >= 9 && n <= 15);

export function newGame(player1, player2) {
  const balls = [[0, ...HEAD_SPOT]];
  RACK.forEach((numbers, row) => numbers.forEach((n, col) =>
    balls.push([n, FOOT_SPOT[0] + (col - row / 2) * RACK_COLUMN, FOOT_SPOT[1] - row * RACK_ROW])));
  return {
    players: [player1, player2],
    groups: [null, null],
    turn: 0,
    winner: null,
    shots: 0,
    message: `${player1} breaks.`,
    balls,
  };
}

function respotCueBall(balls) {
  let [x, y] = HEAD_SPOT;
  while (balls.some(([, bx, by]) => Math.hypot(x - bx, y - by) < BALL_DIAMETER + 1)) y += BALL_DIAMETER;
  return [0, x, y];
}

// Applies a finished shot: pocketed lists ball numbers in the order they dropped and balls the
// final positions. Returns the next state; the input state is not changed.
export function applyShot(state, pocketed, finalBalls) {
  const next = { ...state, groups: [...state.groups], shots: state.shots + 1 };
  const shooter = state.turn, other = 1 - shooter;
  const name = state.players[shooter];
  const scratch = pocketed.includes(0);
  const objects = pocketed.filter((n) => n !== 0 && n !== 8);
  let balls = finalBalls.filter(([n]) => n !== 0 || !scratch);

  // The first object ball legally pocketed decides who plays which group.
  if (next.groups[shooter] === null && objects.length && !scratch) {
    const group = objects[0] < 8 ? "solids" : "stripes";
    next.groups[shooter] = group;
    next.groups[other] = group === "solids" ? "stripes" : "solids";
  }

  const group = next.groups[shooter];
  const own = objects.filter((n) => group === null || inGroup(n, group));
  const sunk = objects.length ? `Pocketed ${objects.join(", ")}.` : "";

  if (scratch) balls = [...balls, respotCueBall(balls)];
  next.balls = balls;

  if (pocketed.includes(8)) {
    const cleared = group !== null && !balls.some(([n]) => inGroup(n, group));
    if (cleared && !scratch) {
      next.winner = shooter;
      next.message = `${name} sinks the 8 ball and wins!`;
    } else {
      next.winner = other;
      const reason = cleared ? "scratched on the 8" : "sank the 8 ball early";
      next.message = `${name} ${reason}. ${state.players[other]} wins!`;
    }
  } else if (scratch) {
    next.turn = other;
    next.message = `Scratch!${sunk ? " " + sunk : ""} ${state.players[other]}'s turn.`;
  } else if (own.length) {
    next.message = `${sunk} Shoot again, ${name}.`;
  } else {
    next.turn = other;
    next.message = `${sunk ? sunk + " " : ""}${state.players[other]}'s turn.`;
  }
  return next;
}
