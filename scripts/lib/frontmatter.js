'use strict';

/**
 * Shared frontmatter utilities for the manuscript workspace scripts.
 *
 * Responsibilities:
 *   - split a markdown file into frontmatter block and body (CRLF-safe, since
 *     the workspace lives on Windows);
 *   - parse the flat YAML subset used by the workspace frontmatter standard
 *     (scalars, quoted strings, and [a, b] flow lists);
 *   - validate a parsed frontmatter object against the standard defined in
 *     CLAUDE.md ("File Naming & Frontmatter Standards");
 *   - format timestamps as ISO 8601 with the machine's real UTC offset.
 *
 * Zero dependencies on purpose: the workspace should not need `npm install`.
 */

// ---------------------------------------------------------------------------
// Standard definition (mirrors CLAUDE.md)
// ---------------------------------------------------------------------------

/** Every key that must appear in a draft's frontmatter. */
const REQUIRED_FIELDS = [
  'id',
  'title',
  'volume',
  'edition',
  'version',
  'status',
  'created',
  'last_modified',
  'stratum',
  'tags',
  'aliases',
];

const ALLOWED_VOLUMES = ['Vol I', 'Vol II', 'Vol III'];
const ALLOWED_EDITIONS = ['FULL', 'CORE', 'ESSAY'];
const ALLOWED_STATUSES = ['Working', 'Superseded', 'Canonical'];

/** Fields whose values must be ISO 8601 timestamps carrying a UTC offset. */
const TIMESTAMP_FIELDS = ['id', 'created', 'last_modified'];

/**
 * ISO 8601 date-time with a mandatory offset (Z or +hh:mm / -hh:mm).
 * Capture groups: year, month, day, hour, minute, second, offset.
 * The offset is deliberately NOT pinned to -05:00: the template in CLAUDE.md
 * uses -05:00 (EST), but the same author writes -04:00 during daylight time.
 */
const ISO_8601_WITH_OFFSET =
  /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(Z|[+-]\d{2}:\d{2})$/;

/**
 * Version pattern: MAJOR.MINOR[.PATCH][-prerelease][+build], optional leading "v".
 * PATCH is optional because the standard's own example is "v4.0".
 */
const VERSION_PATTERN =
  /^v?(0|[1-9]\d*)\.(0|[1-9]\d*)(?:\.(0|[1-9]\d*))?(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$/;

// ---------------------------------------------------------------------------
// Splitting and parsing
// ---------------------------------------------------------------------------

/**
 * Split markdown text into its frontmatter block and body.
 *
 * Frontmatter must start on the very first line with `---` and be closed by a
 * later line containing only `---`. A UTF-8 BOM and CRLF line endings are
 * tolerated.
 *
 * @param {string} markdownText Raw file contents.
 * @returns {{hasFrontmatter: boolean, block: string, body: string}}
 */
function extractFrontmatter(markdownText) {
  const normalizedText = markdownText.replace(/^﻿/, '').replace(/\r\n/g, '\n');
  const lines = normalizedText.split('\n');

  if (lines[0] !== '---') {
    return { hasFrontmatter: false, block: '', body: normalizedText };
  }

  const closingIndex = lines.indexOf('---', 1);
  if (closingIndex === -1) {
    return { hasFrontmatter: false, block: '', body: normalizedText };
  }

  return {
    hasFrontmatter: true,
    block: lines.slice(1, closingIndex).join('\n'),
    body: lines.slice(closingIndex + 1).join('\n'),
  };
}

/**
 * Remove one pair of matching surrounding quotes from a scalar, if present.
 *
 * @param {string} rawValue
 * @returns {string}
 */
function stripSurroundingQuotes(rawValue) {
  const trimmedValue = rawValue.trim();
  const firstCharacter = trimmedValue[0];
  const lastCharacter = trimmedValue[trimmedValue.length - 1];
  const isQuoted =
    trimmedValue.length >= 2 &&
    (firstCharacter === '"' || firstCharacter === "'") &&
    firstCharacter === lastCharacter;

  return isQuoted ? trimmedValue.slice(1, -1) : trimmedValue;
}

/**
 * Parse one YAML value: a [a, b] flow list or a (possibly quoted) scalar.
 *
 * @param {string} rawValue Everything after "key:" on a line.
 * @returns {string | string[]}
 */
function parseYamlValue(rawValue) {
  const trimmedValue = rawValue.trim();

  if (trimmedValue.startsWith('[') && trimmedValue.endsWith(']')) {
    const listContents = trimmedValue.slice(1, -1).trim();
    if (listContents === '') {
      return [];
    }
    return listContents
      .split(',')
      .map((item) => stripSurroundingQuotes(item))
      .filter((item) => item !== '');
  }

  return stripSurroundingQuotes(trimmedValue);
}

/**
 * Parse the flat YAML subset used by workspace frontmatter.
 *
 * @param {string} frontmatterBlock Text between the two `---` fences.
 * @returns {{fields: Object<string, string | string[]>, parseErrors: string[]}}
 */
function parseFlatYaml(frontmatterBlock) {
  const fields = {};
  const parseErrors = [];

  frontmatterBlock.split('\n').forEach((line, lineIndex) => {
    const isBlankOrComment = line.trim() === '' || line.trim().startsWith('#');
    if (isBlankOrComment) {
      return;
    }

    const keyValueMatch = /^([A-Za-z_][A-Za-z0-9_]*):(.*)$/.exec(line);
    if (!keyValueMatch) {
      parseErrors.push(`frontmatter line ${lineIndex + 1} is not "key: value": ${line.trim()}`);
      return;
    }

    const [, key, rawValue] = keyValueMatch;
    if (Object.prototype.hasOwnProperty.call(fields, key)) {
      parseErrors.push(`duplicate frontmatter key: ${key}`);
      return;
    }
    fields[key] = parseYamlValue(rawValue);
  });

  return { fields, parseErrors };
}

// ---------------------------------------------------------------------------
// Timestamp helpers
// ---------------------------------------------------------------------------

function isLeapYear(year) {
  return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
}

/** True when year-month-day names a day that exists on the calendar. */
function isRealCalendarDate(year, month, day) {
  const daysInEachMonth = [31, isLeapYear(year) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return month >= 1 && month <= 12 && day >= 1 && day <= daysInEachMonth[month - 1];
}

/**
 * Check that text is a real ISO 8601 date-time with a UTC offset.
 * Rejects impossible values such as 2026-02-30 or 25:00:00.
 *
 * @param {string} timestampText
 * @returns {boolean}
 */
function isValidIso8601WithOffset(timestampText) {
  if (typeof timestampText !== 'string') {
    return false;
  }

  const match = ISO_8601_WITH_OFFSET.exec(timestampText);
  if (!match) {
    return false;
  }

  const [, year, month, day, hour, minute, second, offset] = match;
  const calendarIsValid = isRealCalendarDate(Number(year), Number(month), Number(day));
  const clockIsValid = Number(hour) <= 23 && Number(minute) <= 59 && Number(second) <= 59;

  let offsetIsValid = true;
  if (offset !== 'Z') {
    const [offsetHours, offsetMinutes] = offset.slice(1).split(':').map(Number);
    offsetIsValid = offsetHours <= 14 && offsetMinutes <= 59;
  }

  return calendarIsValid && clockIsValid && offsetIsValid;
}

function padTwoDigits(value) {
  return String(value).padStart(2, '0');
}

/**
 * Format a Date as ISO 8601 using the machine's actual UTC offset.
 * Uses the offset in force at that instant, so daylight time is handled.
 *
 * @param {Date} [date]
 * @returns {string} e.g. "2026-10-06T14:05:09-04:00"
 */
function formatLocalIso8601(date = new Date()) {
  const offsetMinutesEastOfUtc = -date.getTimezoneOffset();
  const offsetSign = offsetMinutesEastOfUtc >= 0 ? '+' : '-';
  const absoluteOffsetMinutes = Math.abs(offsetMinutesEastOfUtc);
  const offsetText =
    `${offsetSign}${padTwoDigits(Math.floor(absoluteOffsetMinutes / 60))}` +
    `:${padTwoDigits(absoluteOffsetMinutes % 60)}`;

  return (
    `${date.getFullYear()}-${padTwoDigits(date.getMonth() + 1)}-${padTwoDigits(date.getDate())}` +
    `T${padTwoDigits(date.getHours())}:${padTwoDigits(date.getMinutes())}:${padTwoDigits(date.getSeconds())}` +
    offsetText
  );
}

/**
 * Format a Date as a local-time file stamp: YYYY-MM-DD_HHmmss.
 *
 * @param {Date} [date]
 * @returns {string}
 */
function formatLocalFileStamp(date = new Date()) {
  return (
    `${date.getFullYear()}-${padTwoDigits(date.getMonth() + 1)}-${padTwoDigits(date.getDate())}` +
    `_${padTwoDigits(date.getHours())}${padTwoDigits(date.getMinutes())}${padTwoDigits(date.getSeconds())}`
  );
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

/**
 * Validate parsed frontmatter against the workspace standard.
 *
 * @param {Object<string, string | string[]>} fields Output of parseFlatYaml().
 * @returns {string[]} Human-readable issues; empty when the frontmatter is valid.
 */
function validateFrontmatter(fields) {
  const issues = [];

  const missingFields = REQUIRED_FIELDS.filter(
    (fieldName) => !Object.prototype.hasOwnProperty.call(fields, fieldName)
  );
  if (missingFields.length > 0) {
    issues.push(`missing required field(s): ${missingFields.join(', ')}`);
  }

  // Free-text fields must be present and non-empty.
  ['title', 'stratum'].forEach((fieldName) => {
    if (fields[fieldName] !== undefined && (typeof fields[fieldName] !== 'string' || fields[fieldName] === '')) {
      issues.push(`${fieldName} must be a non-empty string`);
    }
  });

  // ISO 8601 timestamps with an offset.
  TIMESTAMP_FIELDS.forEach((fieldName) => {
    if (fields[fieldName] !== undefined && !isValidIso8601WithOffset(fields[fieldName])) {
      issues.push(
        `${fieldName} is not a valid ISO 8601 timestamp with offset ` +
          `(expected YYYY-MM-DDTHH:mm:ss±hh:mm): ${JSON.stringify(fields[fieldName])}`
      );
    }
  });

  // Chronology: a draft cannot be modified before it was created.
  if (isValidIso8601WithOffset(fields.created) && isValidIso8601WithOffset(fields.last_modified)) {
    if (Date.parse(fields.last_modified) < Date.parse(fields.created)) {
      issues.push('last_modified is earlier than created');
    }
  }

  // Version pattern.
  if (fields.version !== undefined && !VERSION_PATTERN.test(fields.version)) {
    issues.push(
      `version does not match MAJOR.MINOR[.PATCH][-pre][+build] with optional "v": ${JSON.stringify(fields.version)}`
    );
  }

  // Controlled vocabularies.
  [
    ['volume', ALLOWED_VOLUMES],
    ['edition', ALLOWED_EDITIONS],
    ['status', ALLOWED_STATUSES],
  ].forEach(([fieldName, allowedValues]) => {
    if (fields[fieldName] !== undefined && !allowedValues.includes(fields[fieldName])) {
      issues.push(
        `${fieldName} must be one of [${allowedValues.join(' | ')}], got ${JSON.stringify(fields[fieldName])}`
      );
    }
  });

  // Lists.
  if (fields.tags !== undefined && (!Array.isArray(fields.tags) || fields.tags.length === 0)) {
    issues.push('tags must be a non-empty list, e.g. [manuscript, philosophy]');
  }
  if (fields.aliases !== undefined && !Array.isArray(fields.aliases)) {
    issues.push('aliases must be a list (use [] when there are none)');
  }

  return issues;
}

module.exports = {
  REQUIRED_FIELDS,
  ALLOWED_VOLUMES,
  ALLOWED_EDITIONS,
  ALLOWED_STATUSES,
  TIMESTAMP_FIELDS,
  ISO_8601_WITH_OFFSET,
  VERSION_PATTERN,
  extractFrontmatter,
  parseFlatYaml,
  isValidIso8601WithOffset,
  formatLocalIso8601,
  formatLocalFileStamp,
  validateFrontmatter,
};
