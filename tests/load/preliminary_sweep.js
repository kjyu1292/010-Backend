// Purpose: find which endpoint(s) look bad, NOT why. Deep-dive profiling
// only gets attached to whatever this flags.
//
// Run:  k6 run tests/load/preliminary_sweep.js
// Against another target:  k6 run -e BASE_URL=http://staging:8000 tests/load/preliminary_sweep.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// One Trend per endpoint -- k6 prints p(50)/p(90)/p(95)/p(99) for each
// automatically in the end-of-run summary, no extra tooling needed.
const registerDuration     = new Trend('register_duration', true);
const loginDuration        = new Trend('login_duration', true);
const authMeDuration       = new Trend('auth_me_duration', true);
const playersGetDuration   = new Trend('players_get_duration', true);
const playersPatchDuration = new Trend('players_patch_duration', true);
const errorRate            = new Rate('errors');

export const options = {
  scenarios: {
    preliminary_sweep: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 10 },   // warm up
        { duration: '1m',  target: 10 },   // baseline hold
        { duration: '30s', target: 25 },   // step up
        { duration: '1m',  target: 25 },   // moderate hold
        { duration: '30s', target: 0 },    // ramp down
      ],
    },
  },
  thresholds: {
    // Loose, sanity-check thresholds for a baseline run -- not final SLOs.
    // A fail here just means "worth a closer look", not "broken".
    register_duration:     ['p(95)<800'],
    login_duration:        ['p(95)<500'],
    auth_me_duration:      ['p(95)<200'],
    players_get_duration:  ['p(95)<200'],
    players_patch_duration:['p(95)<300'],
    errors:                ['rate<0.01'],
  },
};

export default function () {
  const tag = `${__VU}_${__ITER}_${Date.now()}`;
  const email = `sweep_${tag}@example.com`;
  const password = 'correct-horse-battery-staple';
  const jsonHeaders = { headers: { 'Content-Type': 'application/json' } };

  // 1. Register
  let res = http.post(
    `${BASE_URL}/v1/auth/register`,
    JSON.stringify({ email, password, display_name: `Sweep ${tag}`, platform: 'ios' }),
    { ...jsonHeaders, tags: { endpoint: 'register' } }
  );
  registerDuration.add(res.timings.duration);
  errorRate.add(res.status !== 201);

  // 2. Login
  res = http.post(
    `${BASE_URL}/v1/auth/login`,
    { username: email, password },
    { tags: { endpoint: 'login' } }
  );
  loginDuration.add(res.timings.duration);
  const loginOk = check(res, { 'login succeeded': (r) => r.status === 200 });
  errorRate.add(!loginOk);
  if (!loginOk) { sleep(1); return; }

  const accessToken = res.json('access_token');
  const authHeaders = { headers: { Authorization: `Bearer ${accessToken}` } };

  // 3. GET /auth/me
  res = http.get(`${BASE_URL}/v1/auth/me`, { ...authHeaders, tags: { endpoint: 'auth_me' } });
  authMeDuration.add(res.timings.duration);
  errorRate.add(res.status !== 200);

  // 4. GET /players/me
  res = http.get(`${BASE_URL}/v1/players/me`, { ...authHeaders, tags: { endpoint: 'players_get' } });
  playersGetDuration.add(res.timings.duration);
  errorRate.add(res.status !== 200);

  // 5. PATCH /players/me
  res = http.patch(
    `${BASE_URL}/v1/players/me`,
    JSON.stringify({ avatar_id: 'avatar_01' }),
    { headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' }, tags: { endpoint: 'players_patch' } }
  );
  playersPatchDuration.add(res.timings.duration);
  errorRate.add(res.status !== 200);

  sleep(1);
}
