/** HEART scoring reference logic. No network or storage access. */
function number(name, value) {
  if (value === '' || value === null || value === undefined || typeof value === 'boolean') {
    throw new Error(name + ' must be a number');
  }
  const n = Number(value);
  if (!Number.isFinite(n)) throw new Error(name + ' must be finite');
  return n;
}
function integer(name, value, lo, hi) {
  const n = number(name, value);
  if (!Number.isInteger(n) || n < lo || n > hi) {
    throw new Error(name + ' must be an integer from ' + lo + ' to ' + hi);
  }
  return n;
}
function boolean(name, value, optional = false) {
  if (value === null || value === undefined || value === '') {
    if (optional) return null;
    throw new Error(name + ' must be explicitly true or false');
  }
  if (value === true || value === false) return value;
  if (typeof value === 'string') {
    const v = value.trim().toLowerCase();
    if (['true', 'yes', '1'].includes(v)) return true;
    if (['false', 'no', '0'].includes(v)) return false;
  }
  throw new Error(name + ' must be true or false');
}
export function calculateHeart(input) {
  const h = integer('history', input.history, 0, 2);
  const e = integer('ecg', input.ecg, 0, 2);
  const a = integer('age', input.age, 0, 120);
  const risks = integer('risk_factors', input.risk_factors, 0, 30);
  const ratio = number('troponin_ratio', input.troponin_ratio);
  if (ratio < 0) throw new Error('troponin_ratio must be non-negative');
  const cad = boolean('prior_cad', input.prior_cad);
  const serial = boolean('serial_troponins_negative', input.serial_troponins_negative, true);
  const ischemic = boolean('ischemic_ecg', input.ischemic_ecg, true);
  const agePoints = a < 45 ? 0 : (a < 65 ? 1 : 2);
  const riskPoints = cad || risks >= 3 ? 2 : (risks >= 1 ? 1 : 0);
  const troponinPoints = ratio <= 1 ? 0 : (ratio < 3 ? 1 : 2);
  const hear = h + e + agePoints + riskPoints;
  const score = hear + troponinPoints;
  const classification = score <= 3 ? 'Low (0-3)' : (score <= 6 ? 'Intermediate (4-6)' : 'High (7-10)');
  const pathway = serial === null || ischemic === null
    ? 'Not assessed'
    : hear <= 3 && e !== 2 && ratio <= 1 && serial && !ischemic && !cad
      ? 'Low-risk criteria met'
      : 'Low-risk criteria not met';
  return {
    score, hear_score: hear, classification,
    heart_pathway: pathway,
    components: { history: h, ecg: e, age: agePoints, risk_factors: riskPoints, troponin: troponinPoints }
  };
}
