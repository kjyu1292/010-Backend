// tests/load/auth_load_test.js
// Run with:  k6 run tests/load/auth_load_test.js
// Against a different target:  k6 run -e E2E_BASE_URL=http://staging:8000 tests/load/auth_load_test.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.E2E_BASE_URL; // || 'http://localhost:8000';

const errorRate = new Rate('errors');
const loginDuration = new Trend('login_duration', true);

export const options = {
  scenarios: {
    steady_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 20 },   // ramp up
        { duration: '1m',  target: 20 },   // hold
        { duration: '30s', target: 50 },   // step up
        { duration: '1m',  target: 50 },   // hold
        { duration: '30s', target: 0 },    // ramp down
      ],
    },
  },
  thresholds: {
    // Fail the run if these SLOs aren't met -- automated pass/fail bar
    http_req_duration: ['p(50)<200', 'p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],   // error rate under 1%
    errors: ['rate<0.01'],
  },
};

export default function () {
  const tag = `${__VU}_${__ITER}_${Date.now()}`;
  const payload = JSON.stringify({
    email: `loadtest_${tag}@example.com`,
    password: 'correct-horse-battery-staple',
    display_name: `Load Test ${tag}`,
    platform: 'ios',
  });
  const jsonHeaders = { headers: { 'Content-Type': 'application/json' } };

  // Register
  const registerRes = http.post(`${BASE_URL}/v1/auth/register`, payload, jsonHeaders);
  check(registerRes, { 'register succeeded': (r) => r.status === 201 }) || errorRate.add(1);

  // Login
  const loginStart = Date.now();
  const loginRes = http.post(
    `${BASE_URL}/v1/auth/login`,
    { username: `loadtest_${tag}@example.com`, password: 'correct-horse-battery-staple' }
  );
  loginDuration.add(Date.now() - loginStart);
  const loginOk = check(loginRes, { 'login succeeded': (r) => r.status === 200 });
  errorRate.add(!loginOk);

  if (loginOk) {
    const accessToken = loginRes.json('access_token');

    // Authenticated request
    const meRes = http.get(`${BASE_URL}/v1/auth/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    check(meRes, { 'me succeeded': (r) => r.status === 200 }) || errorRate.add(1);
  }

  sleep(1);
}
