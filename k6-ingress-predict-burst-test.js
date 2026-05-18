import http from 'k6/http';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '1s', target: 0 },
    { duration: '2s', target: 100 },  // spike
    { duration: '10s', target: 100 },
    { duration: '2s', target: 0 },
  ],
};

export default function () {
  const res = http.get('http://fpl.local/predict');

  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  if (res.status !== 200) {
    console.log(`burst-test non-200 response: status=${res.status} body=${String(res.body).slice(0, 200)}`);
  }
}
