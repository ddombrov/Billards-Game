// Runs a shot with the C physics engine (phylib.c compiled to WebAssembly).
const FRAME_RATE = 0.01; // seconds of simulated time between animation frames

let enginePromise = null;

function loadEngine() {
  if (!enginePromise) {
    // phylib.c only needs memory; any WASI call it links against is answered with "success".
    const wasi = new Proxy({}, { get: () => () => 0 });
    enginePromise = WebAssembly.instantiateStreaming(fetch("/phylib.wasm"), { wasi_snapshot_preview1: wasi })
      .then(({ instance }) => {
        instance.exports._initialize?.();
        return instance.exports;
      });
  }
  return enginePromise;
}

function readBalls(engine, table, dt) {
  const count = engine.table_balls(table, dt);
  const buffer = new Float64Array(engine.memory.buffer, engine.ball_buffer(), count * 3);
  const balls = [];
  for (let i = 0; i < count; i++) {
    balls.push([buffer[i * 3], Math.round(buffer[i * 3 + 1] * 10) / 10, Math.round(buffer[i * 3 + 2] * 10) / 10]);
  }
  return balls;
}

// Same loop as Game.shoot in Physics.py: segment until every ball stops, sampling frames in between.
// Returns { frames, pocketed (in the order they dropped), balls (final positions) }.
async function simulateShot(balls, vx, vy) {
  const engine = await loadEngine();
  let table = engine.table_new();
  for (const [n, x, y] of balls) engine.table_add_ball(table, n, x, y);
  engine.table_shoot(table, vx, vy);

  const frames = [];
  const pocketed = [];
  let onTable = balls.map((b) => b[0]);
  let nextFrameTime = 0;

  for (;;) {
    const segment = engine.table_segment(table);
    if (!segment) break;
    const start = engine.table_time(table);
    const end = engine.table_time(segment);
    while (nextFrameTime < end) {
      frames.push(readBalls(engine, table, nextFrameTime - start));
      nextFrameTime += FRAME_RATE;
    }
    const remaining = readBalls(engine, segment, 0).map((b) => b[0]);
    pocketed.push(...onTable.filter((n) => !remaining.includes(n)));
    onTable = remaining;
    engine.table_free(table);
    table = segment;
  }

  const finalBalls = readBalls(engine, table, 0);
  engine.table_free(table);
  frames.push(finalBalls);
  return { frames, pocketed, balls: finalBalls };
}

export { loadEngine, simulateShot, FRAME_RATE };
