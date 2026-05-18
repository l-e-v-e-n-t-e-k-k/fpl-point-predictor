import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 5 },
    { duration: '30s', target: 20 },
    { duration: '30s', target: 50 },
    { duration: '30s', target: 0 },
  ],
};

export default function () {
  const res = http.get('http://fpl.local/predict');

  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  if (res.status !== 200) {
    console.log(`load-test non-200 response: status=${res.status} body=${String(res.body).slice(0, 200)}`);
  }

  sleep(1);
}
