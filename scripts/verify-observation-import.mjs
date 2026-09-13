import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { parseObservationCsv, exportObservationsCsv, MAX_IMPORT_BYTES, MAX_IMPORT_OBSERVATIONS } from '../src/ai/observationImport.ts';

const appHeader = 'id,latitude,longitude,observed_at,frp,brightness,source';
const appLine = 'one,21.1466,79.0889,2026-09-13T06:00:00Z,8.5,321.2,imported';
const parse = (lines, header = appHeader) => parseObservationCsv([header, ...lines].join('\r\n'));

const firms = parseObservationCsv('\uFEFF LATITUDE , longitude ,frp,acq_date,acq_time,bright_ti4,confidence\r\n21.1,79.1,9.8,2026-09-13,0031,321.7,h\r\n21.2,79.2,0,2024-02-29,31,,l\r\n');
assert.deepEqual(firms.errors, []);
assert.equal(firms.observations.length, 2);
assert.equal(firms.observations[0].observedAt, '2026-09-13T00:31:00.000Z');
assert.equal(firms.observations[0].brightness, 321.7);
assert.equal(firms.observations[0].source, 'imported');
assert.ok(!('confidence' in firms.observations[0]), 'Do not invent or reinterpret source confidence');
assert.ok(!('brightness' in firms.observations[1]), 'Blank optional numbers stay absent');
assert.equal(firms.observations[1].frp, 0);

const app = parse([appLine]);
assert.deepEqual(app.errors, []);
assert.equal(app.observations[0].id, 'one');
assert.equal(app.observations[0].frp, 8.5);
const zone = parse(['zone,-90,180,2026-09-13T11:30:00+05:30,1e1,,demo']);
assert.deepEqual(zone.errors, []);
assert.equal(zone.observations[0].observedAt, '2026-09-13T06:00:00.000Z');
assert.equal(zone.observations[0].frp, 10);
assert.equal(zone.observations[0].source, 'demo');

const quoted = parse(['"site, ""alpha""",21,79,"2026-09-13T06:00:00Z",8.5,,imported']);
assert.deepEqual(quoted.errors, []);
assert.equal(quoted.observations[0].id, 'site, "alpha"');
const multiline = parse(['"line\r\nbreak",21,79,2026-09-13T06:00:00Z,8.5,,imported', 'bad,999,79,2026-09-13T06:00:00Z,8.5,,imported']);
assert.equal(multiline.observations.length, 1);
assert.match(multiline.errors[0], /Line 4:/, 'Row errors use physical CSV line numbers');

for (const invalidLine of [
  'bad,,79,2026-09-13T06:00:00Z,8.5,,imported',
  'bad,21,,2026-09-13T06:00:00Z,8.5,,imported',
  'bad,21,79,2026-09-13T06:00:00Z,,,imported',
  'bad,91,79,2026-09-13T06:00:00Z,8.5,,imported',
  'bad,21,-181,2026-09-13T06:00:00Z,8.5,,imported',
  'bad,0x10,79,2026-09-13T06:00:00Z,8.5,,imported',
  'bad,Infinity,79,2026-09-13T06:00:00Z,8.5,,imported',
  'bad,21,79,2026-09-13T06:00:00Z,-1,,imported',
  'bad,21,79,2026-09-13T06:00:00Z,1000001,,imported',
  'bad,21,79,2026-09-13T06:00:00Z,1e999,,imported',
  'bad,21,79,2026-09-13T06:00:00Z,8.5,NaN,imported',
  'bad,21,79,2026-09-13T06:00:00Z,8.5,0,imported',
  'bad,21,79,2026-09-13T06:00:00Z,8.5,2001,imported',
  'bad,21,79,2026-02-30T06:00:00Z,8.5,,imported',
  'bad,21,79,2026-02-29T06:00:00Z,8.5,,imported',
  'bad,21,79,2026-09-13T24:00:00Z,8.5,,imported',
  'bad,21,79,2026-09-13T06:60:00Z,8.5,,imported',
  'bad,21,79,2026-09-13T06:00:00,8.5,,imported',
  'bad,21,79,2026-09-13T06:00:00+05:90,8.5,,imported',
  'bad,21,79,,8.5,,imported',
  'bad,21,79,2026-09-13T06:00:00Z,8.5,',
]) {
  const result = parse([invalidLine, appLine]);
  assert.equal(result.errors.length, 1, invalidLine);
  assert.equal(result.observations.length, 1, 'Valid rows survive row-level failures');
  assert.match(result.errors[0], /Line 2:/);
}

for (const time of ['', '2400', '1260', '-1', '12.5', '12345', '12:30']) {
  const result = parse([`21,79,8.5,2026-09-13,${time}`], 'latitude,longitude,frp,acq_date,acq_time');
  assert.equal(result.observations.length, 0, `Reject invalid HHMM: ${time}`);
  assert.equal(result.errors.length, 1);
}
for (const broken of [
  '',
  appHeader,
  'latitude,longitude,frp\n21,79,8.5',
  'latitude,longitude,frp,observed_at,LATITUDE\n21,79,8.5,2026-09-13T06:00:00Z,21',
  'latitude,lat,longitude,frp,observed_at\n21,21,79,8.5,2026-09-13T06:00:00Z',
  'latitude,longitude,frp,observed_at,\n21,79,8.5,2026-09-13T06:00:00Z,',
  `${appHeader}\n"unclosed,21,79,2026-09-13T06:00:00Z,8.5,,demo`,
  `${appHeader}\nname"bad,21,79,2026-09-13T06:00:00Z,8.5,,demo`,
  `${appHeader}\n"closed"bad,21,79,2026-09-13T06:00:00Z,8.5,,demo`,
]) {
  const result = parseObservationCsv(broken);
  assert.ok(result.errors.length > 0, broken);
  assert.equal(result.observations.length, 0);
}

const duplicates = parse([appLine, appLine, appLine.replace('one,', 'other,')]);
assert.equal(duplicates.observations.length, 1);
assert.equal(duplicates.warnings.length, 2);
assert.deepEqual(duplicates.errors, []);
const conflict = parse([appLine, appLine.replace('8.5', '99')]);
assert.equal(conflict.errors.length, 1);
assert.equal(conflict.observations.length, 1);
const generated = parse(['21,79,8.5,2026-09-13T06:00:00Z'], 'latitude,longitude,frp,observed_at');
assert.equal(generated.observations[0].id, parse(['21,79,8.5,2026-09-13T06:00:00Z'], 'latitude,longitude,frp,observed_at').observations[0].id);

const spoofed = parse([appLine.replace('imported', 'firms'), appLine.replace('one,', 'manual,').replace('8.5', '10').replace('imported', 'manual')]);
assert.equal(spoofed.observations.length, 2);
assert.ok(spoofed.observations.every((observation) => observation.source === 'imported'));
assert.equal(spoofed.warnings.length, 1);

const template = parseObservationCsv(await readFile(new URL('../public/data/thermal-observation-template.csv', import.meta.url), 'utf8'));
assert.deepEqual(template.errors, []);
assert.equal(template.observations.length, 3);
assert.ok(template.observations.every((observation) => observation.source === 'demo'));
assert.deepEqual(parseObservationCsv(exportObservationsCsv(template.observations)).observations, template.observations);
assert.deepEqual(parseObservationCsv(exportObservationsCsv(quoted.observations)).observations, quoted.observations);
for (const dangerousId of ['=1+1', '+cmd', '-cmd', '@SUM(A1)', '  =1+1', '\tformula', '\rformula', '\nformula', '=HYPERLINK("https://example.com","click")']) {
  const csv = exportObservationsCsv([{ ...app.observations[0], id: dangerousId }]);
  const roundTrip = parseObservationCsv(csv);
  assert.deepEqual(roundTrip.errors, []);
  assert.equal(roundTrip.observations[0].id, `'${dangerousId}`, 'Export escapes spreadsheet formulas');
}
assert.equal(exportObservationsCsv([]), `${appHeader}\r\n`);

assert.match(parseObservationCsv('x'.repeat(MAX_IMPORT_BYTES + 1)).errors[0], /2 MB/);
assert.match(parseObservationCsv('अ'.repeat(Math.floor(MAX_IMPORT_BYTES / 2))).errors[0], /2 MB/, 'Limit encoded bytes too');
const tooMany = parse(Array(MAX_IMPORT_OBSERVATIONS + 1).fill(appLine));
assert.equal(tooMany.observations.length, 0);
assert.match(tooMany.errors[0], /5,000/);
const atLimit = parse(Array.from({ length: MAX_IMPORT_OBSERVATIONS }, (_, index) => `row-${index},21,79,2026-09-13T06:00:00Z,${index},,imported`));
assert.deepEqual(atLimit.errors, []);
assert.equal(atLimit.observations.length, MAX_IMPORT_OBSERVATIONS);

console.log('PASS: FIRMS/app CSV parsing, strict dates and numbers, quoted records, row errors, duplicates, provenance, size limits, synthetic template, and formula-safe export.');
