import { calculateHeart } from './score.mjs';

const form = document.getElementById('heart-form');
const error = document.getElementById('error');
const output = document.getElementById('result');
const score = document.getElementById('score');
const risk = document.getElementById('risk');
const hear = document.getElementById('hear');
const pathway = document.getElementById('pathway');
const parts = document.getElementById('components');

form.addEventListener('submit', (event) => {
  event.preventDefault();
  error.hidden = true;
  output.hidden = true;
  const data = Object.fromEntries(new FormData(form).entries());
  try {
    const result = calculateHeart(data);
    score.textContent = String(result.score) + ' / 10';
    hear.textContent = String(result.hear_score) + ' / 8';
    risk.textContent = result.classification;
    pathway.textContent = result.heart_pathway;
    parts.textContent = Object.entries(result.components)
      .map(([key, value]) => key.replace('_', ' ') + ': ' + value)
      .join(' · ');
    output.hidden = false;
    output.focus();
  } catch (exception) {
    error.textContent = exception.message;
    error.hidden = false;
    error.focus();
  }
});
form.addEventListener('reset', () => {
  output.hidden = true;
  error.hidden = true;
});
