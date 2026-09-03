// tests/load/players_isolated.js
// Isolation run to confirm/deny cross-endpoint contamination from bcrypt.
// register + login happen ONCE in setup(), before load starts -- the
// measured window (the ramping VU stages) only ever hits players/me.
// If p95 here is fast, it confirms register/login were dragging players/me
// down in the combined sweep. If it's still slow, the bottleneck is elsewhere
// (DB pool, etc.) and the bcrypt theory needs revisiting.
//
// Run:  k6 run tests/load/players_isolated.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const POOL_SIZE = 30;   // more than max VUs, so every VU gets its own token

const getDuration = new Trend('players_get_duration', true);
const patchDuration = new Trend('players_patch_duration', true);
const errorRate = new Rate('errors');

export const options = {
  scenarios: {
    players_only: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 10 },
        { duration: '1m',  target: 10 },
        { duration: '30s', target: 25 },
        { duration: '1m',  target: 25 },
        { duration: '30s', target: 0 },
      ],
    },
  },
  thresholds: {
    players_get_duration: ['p(95)<200'],
    players_patch_duration: ['p(95)<300'],
    errors: ['rate<0.01'],
  },
};

// Runs ONCE, before any VU/stage starts. Not part of the measured load.
export function setup() {
  const tokens = [];
  for (let i = 0; i < POOL_SIZE; i++) {
    const email = `isolated_${i}_${Date.now()}@example.com`;
    const password = 'correct-horse-battery-staple';

    const reg = http.post(
      `${BASE_URL}/v1/auth/register`,
      JSON.stringify({ email, password, display_name: `Isolated ${i}`, platform: 'ios' }),
      { headers: { 'Content-Type': 'application/json' } }
    );
    if (reg.status !== 201) {
      throw new Error(`setup: register failed for user ${i}, status ${reg.status}`);
    }

    const login = http.post(`${BASE_URL}/v1/auth/login`, { username: email, password });
    if (login.status !== 200) {
      throw new Error(`setup: login failed for user ${i}, status ${login.status}`);
    }

    tokens.push(login.json('access_token'));
  }
  return { tokens };
}

// data = whatever setup() returned, passed to every VU
export default function (data) {
  const token = data.tokens[__VU % data.tokens.length];
  const authHeaders = { headers: { Authorization: `Bearer ${token}` } };

  let res = http.get(`${BASE_URL}/v1/players/me`, authHeaders);
  getDuration.add(res.timings.duration);
  errorRate.add(res.status !== 200);

  res = http.patch(
    `${BASE_URL}/v1/players/me`,
    JSON.stringify({ avatar_id: 'avatar_01' }),
    { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } }
  );
  patchDuration.add(res.timings.duration);
  errorRate.add(res.status !== 200);

  sleep(1);
}
