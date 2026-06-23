#!/usr/bin/env node
'use strict';

const path = require('node:path');

const { astro } = require(path.resolve(__dirname, '..', 'vendor', 'iztro.cjs'));

function readStdin() {
  return new Promise((resolve, reject) => {
    let body = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => {
      body += chunk;
    });
    process.stdin.on('end', () => resolve(body));
    process.stdin.on('error', reject);
  });
}

function star(starObj) {
  return {
    name: starObj && starObj.name ? starObj.name : '',
    brightness: starObj && starObj.brightness ? starObj.brightness : '',
    mutagen: starObj && starObj.mutagen ? starObj.mutagen : '',
  };
}

function adjectiveStar(starObj) {
  return {
    name: starObj && starObj.name ? starObj.name : '',
  };
}

function horoscopeStar(starObj) {
  const out = { name: starObj && starObj.name ? starObj.name : '' };
  for (const key of ['type', 'scope', 'brightness', 'mutagen']) {
    if (starObj && starObj[key]) out[key] = starObj[key];
  }
  return out;
}

function horoscopeSection(section) {
  if (!section) return null;
  const out = {};
  for (const key of [
    'index',
    'name',
    'heavenlyStem',
    'earthlyBranch',
    'palaceNames',
    'mutagen',
    'yearlyDecStar',
  ]) {
    if (Object.prototype.hasOwnProperty.call(section, key)) out[key] = section[key];
  }
  out.stars = Array.isArray(section.stars)
    ? section.stars.map((group) => (Array.isArray(group) ? group.map(horoscopeStar) : []))
    : [];
  return out;
}

function palace(palaceObj) {
  const range = palaceObj.decadal && palaceObj.decadal.range ? palaceObj.decadal.range : [];
  return {
    name: palaceObj.name,
    heavenlyStem: palaceObj.heavenlyStem,
    earthlyBranch: palaceObj.earthlyBranch,
    isOriginalPalace: Boolean(palaceObj.isOriginalPalace),
    isBodyPalace: Boolean(palaceObj.isBodyPalace),
    majorStars: (palaceObj.majorStars || []).map(star),
    minorStars: (palaceObj.minorStars || []).map(star),
    adjectiveStars: (palaceObj.adjectiveStars || []).map(adjectiveStar),
    decadal: { range },
  };
}

async function main() {
  const body = await readStdin();
  const req = JSON.parse(body || '{}');
  const result = astro.bySolar(
    req.date,
    req.timeIndex,
    req.gender,
    req.fixLeap,
    req.language
  );
  if (!req.target) {
    process.stderr.write('Missing required target date for horoscope.\n');
    process.exit(1);
  }
  const horoscope = result.horoscope(req.target);
  const out = {
    fiveElementsClass: result.fiveElementsClass,
    soul: result.soul,
    body: result.body,
    palaces: result.palaces.map(palace),
    horoscope: {
      decadal: horoscopeSection(horoscope.decadal),
      yearly: horoscopeSection(horoscope.yearly),
    },
  };
  process.stdout.write(`${JSON.stringify(out)}\n`);
}

main().catch((err) => {
  process.stderr.write(`${err && err.stack ? err.stack : String(err)}\n`);
  process.exit(1);
});
