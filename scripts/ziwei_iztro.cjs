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

// iztro returns the four 四化 stars positionally ordered [化祿, 化權, 化科, 化忌]
// (vendor/iztro.cjs MUTAGEN = ["sihuaLu","sihuaQuan","sihuaKe","sihuaJi"]; the
// position->type mapping is invariant across all 10 天干). The bare star-name array
// forced LLM consumers to re-derive the type from 天干, so we expose a typed view —
// additively, leaving the original `mutagen` string array intact for 1.0 consumers.
function labeledMutagen(names) {
  const TYPES = ['祿', '權', '科', '忌'];
  if (!Array.isArray(names) || names.length !== TYPES.length) return names;
  return names.map((star, i) => ({ star, type: TYPES[i] }));
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
  if (Array.isArray(section.mutagen)) {
    out.mutagenTyped = labeledMutagen(section.mutagen);
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
  const decadal = horoscopeSection(horoscope.decadal);
  // Surface the current 大限 age range so consumers don't re-derive the decade
  // (which an LLM got wrong: 虛歲 41 → 33-42, mislabelled 43-52). The range lives on
  // the palace that is the 大限命宮, addressed by horoscope.decadal.index.
  if (decadal && typeof decadal.index === 'number') {
    const dp = result.palaces[decadal.index];
    const range = dp && dp.decadal ? dp.decadal.range : null;
    if (Array.isArray(range) && range.length === 2) decadal.ageRange = range;
  }
  const age = horoscope.age
    ? {
        index: horoscope.age.index,
        nominalAge: horoscope.age.nominalAge,
        name: horoscope.age.name,
        heavenlyStem: horoscope.age.heavenlyStem,
        earthlyBranch: horoscope.age.earthlyBranch,
        palaceNames: horoscope.age.palaceNames,
        mutagen: horoscope.age.mutagen,
        mutagenTyped: labeledMutagen(horoscope.age.mutagen),
      }
    : null;
  const out = {
    fiveElementsClass: result.fiveElementsClass,
    soul: result.soul,
    body: result.body,
    palaces: result.palaces.map(palace),
    horoscope: {
      decadal,
      yearly: horoscopeSection(horoscope.yearly),
      age,
    },
  };
  process.stdout.write(`${JSON.stringify(out)}\n`);
}

main().catch((err) => {
  process.stderr.write(`${err && err.stack ? err.stack : String(err)}\n`);
  process.exit(1);
});
