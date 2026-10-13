import test from 'node:test';
import assert from 'node:assert/strict';
import { calculateHeart } from './score.mjs';

const baseline = {
  history: 0, ecg: 0, age: 44, risk_factors: 0,
  troponin_ratio: .5, prior_cad: false,
};

test('zero score requires explicit pathway observations', () => {
  const result = calculateHeart(baseline);
  assert.equal(result.score, 0);
  assert.equal(result.heart_pathway, 'Not assessed');
});

test('age, risk, and troponin thresholds are exact', () => {
  const age = [44, 45, 64, 65].map(a => calculateHeart({ ...baseline, age: a }).components.age);
  assert.deepEqual(age, [0, 1, 1, 2]);
  const troponin = [1, 1.01, 2.99, 3].map(r => calculateHeart({ ...baseline, troponin_ratio: r }).components.troponin);
  assert.deepEqual(troponin, [0, 1, 1, 2]);
  assert.equal(calculateHeart({ ...baseline, prior_cad: true }).components.risk_factors, 2);
  assert.equal(calculateHeart({ ...baseline, risk_factors: 3 }).components.risk_factors, 2);
});

test('maximum and boundary classifications', () => {
  const result = calculateHeart({ ...baseline, history: 2, ecg: 2, age: 65, risk_factors: 3, troponin_ratio: 3 });
  assert.equal(result.score, 10);
  assert.equal(result.classification, 'High (7-10)');
});

test('all low-risk criteria are mandatory', () => {
  const ok = { ...baseline, serial_troponins_negative: true, ischemic_ecg: false };
  assert.equal(calculateHeart(ok).heart_pathway, 'Low-risk criteria met');
  assert.equal(calculateHeart({ ...ok, prior_cad: true }).heart_pathway, 'Low-risk criteria not met');
  assert.equal(calculateHeart({ ...ok, ischemic_ecg: true }).heart_pathway, 'Low-risk criteria not met');
  assert.equal(calculateHeart({ ...ok, serial_troponins_negative: false }).heart_pathway, 'Low-risk criteria not met');
  assert.equal(calculateHeart({ ...ok, history: 2, ecg: 2 }).heart_pathway, 'Low-risk criteria not met');
  assert.equal(calculateHeart({ ...ok, troponin_ratio: 1.5 }).heart_pathway, 'Low-risk criteria not met');
});

test('rejects missing, nonfinite, unknown, and out-of-range inputs', () => {
  for (const changes of [
    { age: 44.5 }, { history: 3 }, { risk_factors: -1 },
    { troponin_ratio: NaN }, { troponin_ratio: Infinity },
    { prior_cad: '' }, { prior_cad: 'maybe' }
  ]) {
    assert.throws(() => calculateHeart({ ...baseline, ...changes }));
  }
});
