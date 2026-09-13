import type { Observation } from './thermalEngine';

export const MAX_IMPORT_OBSERVATIONS = 5_000;
export const MAX_IMPORT_BYTES = 2 * 1024 * 1024;

export interface ObservationImportResult {
  observations: Observation[];
  errors: string[];
  warnings: string[];
}

type CsvRow = { cells: string[]; line: number };

/** Parse quoted CSV, preserving physical line numbers for useful error messages. */
function readCsv(text: string): { rows: CsvRow[]; error?: string } {
  const rows: CsvRow[] = [];
  let cells: string[] = [];
  let field = '';
  let quoted = false;
  let afterQuote = false;
  let line = 1;
  let rowLine = 1;

  const pushField = () => {
    cells.push(field);
    field = '';
    afterQuote = false;
  };
  const pushRow = () => {
    pushField();
    if (cells.some((cell) => cell.trim() !== '')) rows.push({ cells, line: rowLine });
    cells = [];
  };

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (quoted) {
      if (character === '"') {
        if (text[index + 1] === '"') {
          field += '"';
          index += 1;
        } else {
          quoted = false;
          afterQuote = true;
        }
      } else {
        field += character;
        if (character === '\n' || (character === '\r' && text[index + 1] !== '\n')) line += 1;
      }
      continue;
    }
    if (character === ',') {
      pushField();
    } else if (character === '\n' || character === '\r') {
      pushRow();
      if (character === '\r' && text[index + 1] === '\n') index += 1;
      line += 1;
      rowLine = line;
    } else if (character === '"') {
      if (field !== '' || afterQuote) return { rows: [], error: `Line ${line}: unexpected quote in an unquoted field.` };
      quoted = true;
    } else if (afterQuote) {
      if (character !== ' ' && character !== '\t') return { rows: [], error: `Line ${line}: unexpected content after a closing quote.` };
    } else {
      field += character;
    }
  }
  if (quoted) return { rows: [], error: `Line ${rowLine}: quoted field is not closed.` };
  pushRow();
  return { rows };
}

const normalizeHeader = (value: string) => value.trim().toLowerCase().replace(/[\s_-]+/g, '');
const decimalPattern = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i;

function numberValue(value: string): number | undefined {
  const trimmed = value.trim();
  if (!trimmed || !decimalPattern.test(trimmed)) return undefined;
  const numeric = Number(trimmed);
  return Number.isFinite(numeric) ? numeric : undefined;
}

function validCalendarDate(year: number, month: number, day: number): boolean {
  const date = new Date(0);
  date.setUTCFullYear(year, month - 1, day);
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
}

function normalizeTimestamp(value: string): string | undefined {
  const parts = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,3}))?)?(Z|[+-]\d{2}:\d{2})$/i.exec(value.trim());
  if (!parts) return undefined;
  const [, year, month, day, hour, minute, second, , offset] = parts;
  if (!validCalendarDate(Number(year), Number(month), Number(day)) || Number(hour) > 23 || Number(minute) > 59 || Number(second ?? 0) > 59) return undefined;
  if (offset.toUpperCase() !== 'Z') {
    const [offsetHours, offsetMinutes] = offset.slice(1).split(':').map(Number);
    if (offsetHours > 23 || offsetMinutes > 59) return undefined;
  }
  const date = new Date(value.trim());
  return Number.isFinite(date.getTime()) ? date.toISOString() : undefined;
}

function firmsTimestamp(date: string, time: string): string | undefined {
  const acquisitionTime = time.trim();
  if (!/^\d{1,4}$/.test(acquisitionTime)) return undefined;
  const paddedTime = acquisitionTime.padStart(4, '0');
  return normalizeTimestamp(`${date.trim()}T${paddedTime.slice(0, 2)}:${paddedTime.slice(2)}:00Z`);
}

function observationSignature(observation: Omit<Observation, 'id'>): string {
  return [observation.latitude, observation.longitude, observation.observedAt, observation.frp, observation.brightness ?? '', observation.source].join('|');
}

function stableId(signature: string): string {
  // Two small independent hashes keep generated IDs stable across file imports.
  let first = 2166136261;
  let second = 5381;
  for (let index = 0; index < signature.length; index += 1) {
    const character = signature.charCodeAt(index);
    first = Math.imul(first ^ character, 16777619);
    second = Math.imul(second, 33) ^ character;
  }
  return `csv-${(first >>> 0).toString(36)}-${(second >>> 0).toString(36)}`;
}

/** Uploaded provenance is unverified: only an explicit demo label is preserved. */
export function parseObservationCsv(text: string): ObservationImportResult {
  const result: ObservationImportResult = { observations: [], errors: [], warnings: [] };
  if (text.length > MAX_IMPORT_BYTES || new TextEncoder().encode(text).byteLength > MAX_IMPORT_BYTES) {
    result.errors.push('CSV exceeds the 2 MB import limit. Split the file into smaller batches.');
    return result;
  }

  const parsed = readCsv(text.replace(/^\uFEFF/, ''));
  if (parsed.error) {
    result.errors.push(parsed.error);
    return result;
  }
  if (parsed.rows.length === 0) {
    result.errors.push('CSV is empty. Include a header row and at least one observation.');
    return result;
  }
  if (parsed.rows.length - 1 > MAX_IMPORT_OBSERVATIONS) {
    result.errors.push(`CSV exceeds the ${MAX_IMPORT_OBSERVATIONS.toLocaleString('en-US')} observation limit. No rows were imported; split the file into smaller batches.`);
    return result;
  }

  const headers = parsed.rows[0].cells.map(normalizeHeader);
  if (headers.some((header) => !header)) result.errors.push('Header row contains an empty column name.');
  if (new Set(headers).size !== headers.length) result.errors.push('Header row contains duplicate column names.');

  const column = (label: string, aliases: string[]) => {
    const matches = headers.flatMap((header, index) => aliases.includes(header) ? [index] : []);
    if (matches.length > 1) result.errors.push(`Header row has multiple columns for ${label}. Keep one matching column.`);
    return matches[0] ?? -1;
  };
  const latitudeColumn = column('latitude', ['latitude', 'lat']);
  const longitudeColumn = column('longitude', ['longitude', 'lon', 'lng', 'long']);
  const frpColumn = column('FRP', ['frp', 'fireradiativepower']);
  const timestampColumn = column('observation time', ['observedat', 'timestamp']);
  const dateColumn = column('acquisition date', ['acqdate', 'acquisitiondate']);
  const timeColumn = column('acquisition time', ['acqtime', 'acquisitiontime']);
  // FIRMS products use different thermal bands. Prefer I4, with brightness as a fallback.
  const ti4Column = column('I4 brightness', ['brightti4']);
  const brightnessColumn = column('brightness', ['brightness', 'brightnessk']);
  const sourceColumn = column('source', ['source']);
  const idColumn = column('ID', ['id', 'observationid']);

  for (const [label, index] of [['latitude', latitudeColumn], ['longitude', longitudeColumn], ['frp', frpColumn]] as const) {
    if (index < 0) result.errors.push(`Missing required column: ${label}.`);
  }
  if (timestampColumn < 0 && (dateColumn < 0 || timeColumn < 0)) {
    result.errors.push('Include observed_at with an ISO timestamp and timezone, or both acq_date and acq_time (UTC HHMM).');
  }
  if (result.errors.length > 0) return result;
  if (parsed.rows.length === 1) {
    result.errors.push('CSV contains a header but no observations.');
    return result;
  }

  const signatures = new Set<string>();
  const identifiers = new Map<string, string>();
  let relabelledSource = false;

  for (const row of parsed.rows.slice(1)) {
    if (row.cells.length !== headers.length) {
      result.errors.push(`Line ${row.line}: expected ${headers.length} columns, found ${row.cells.length}.`);
      continue;
    }
    const cell = (index: number) => index < 0 ? '' : row.cells[index].trim();
    const rowErrors: string[] = [];
    const latitude = numberValue(cell(latitudeColumn));
    const longitude = numberValue(cell(longitudeColumn));
    const frp = numberValue(cell(frpColumn));
    const rawBrightness = cell(ti4Column) || cell(brightnessColumn);
    const brightness = rawBrightness ? numberValue(rawBrightness) : undefined;
    const observedAt = cell(timestampColumn)
      ? normalizeTimestamp(cell(timestampColumn))
      : firmsTimestamp(cell(dateColumn), cell(timeColumn));
    if (latitude === undefined || latitude < -90 || latitude > 90) rowErrors.push('latitude must be a number from -90 to 90');
    if (longitude === undefined || longitude < -180 || longitude > 180) rowErrors.push('longitude must be a number from -180 to 180');
    if (frp === undefined || frp < 0 || frp > 1_000_000) rowErrors.push('frp must be a finite number from 0 to 1,000,000 MW');
    if (rawBrightness && (brightness === undefined || brightness <= 0 || brightness > 2_000)) rowErrors.push('brightness must be greater than 0 and no more than 2,000 K, or blank');
    if (!observedAt) rowErrors.push('invalid observation date/time; use ISO with timezone or a valid acq_date and UTC HHMM acq_time');
    const givenId = cell(idColumn);
    if (givenId.length > 200) rowErrors.push('id must be no more than 200 characters');
    if (rowErrors.length > 0) {
      result.errors.push(`Line ${row.line}: ${rowErrors.join('; ')}.`);
      continue;
    }

    const rawSource = cell(sourceColumn).toLowerCase();
    const source = rawSource === 'demo' ? 'demo' : 'imported';
    if (rawSource && rawSource !== 'demo' && rawSource !== 'imported') relabelledSource = true;
    const values: Omit<Observation, 'id'> = {
      latitude: latitude!, longitude: longitude!, observedAt: observedAt!, frp: frp!, source,
      ...(brightness !== undefined ? { brightness } : {}),
    };
    const signature = observationSignature(values);
    const id = givenId || stableId(signature);
    if (identifiers.has(id) && identifiers.get(id) !== signature) {
      result.errors.push(`Line ${row.line}: id is already used by a different observation. Use unique IDs.`);
      continue;
    }
    if (signatures.has(signature)) {
      result.warnings.push(`Line ${row.line}: duplicate observation skipped.`);
      continue;
    }
    signatures.add(signature);
    identifiers.set(id, signature);
    result.observations.push({ id, ...values });
  }

  if (relabelledSource) result.warnings.push('Uploaded source labels other than demo were marked imported. CSV uploads do not establish verified live-feed provenance.');
  return result;
}

function csvText(value: string): string {
  // Spreadsheet applications may execute text starting with these characters.
  const safe = /^[\u0000-\u0020]*[=+\-@]/.test(value) || /^[\t\r\n]/.test(value) ? `'${value}` : value;
  return /[",\r\n]/.test(safe) ? `"${safe.replace(/"/g, '""')}"` : safe;
}

export function exportObservationsCsv(observations: Observation[]): string {
  const header = 'id,latitude,longitude,observed_at,frp,brightness,source';
  const lines = observations.map((observation) => [
    csvText(observation.id),
    observation.latitude,
    observation.longitude,
    csvText(observation.observedAt),
    observation.frp,
    observation.brightness ?? '',
    csvText(observation.source),
  ].join(','));
  return [header, ...lines].join('\r\n') + '\r\n';
}
