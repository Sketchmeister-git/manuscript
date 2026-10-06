#!/usr/bin/env node
'use strict';

/**
 * checkpoint.js — snapshot a draft's state into a session-handoff record.
 *
 * Reads a manuscript draft, extracts its frontmatter metadata, measures it,
 * and writes an ISO 8601 checkpoint record to
 *   40_logs/checkpoints/checkpoint_YYYY-MM-DD_HHmmss.json
 *
 * Usage:
 *   node scripts/checkpoint.js <draftPath>
 *        [--tension "<active thematic tension / unresolved aporia>"]
 *        [--pending "<pending primary source citation>"]   (repeatable)
 *        [--last-section "<heading of last completed section>"]
 *        [--destination <path where work resumes>]
 *        [--root <workspaceRoot>]
 *
 * Notes on what is computed versus supplied:
 *   - Title, edition, version, volume and status come from the draft's frontmatter.
 *   - "Last completed section" defaults to the last heading in the draft, because
 *     "completed" is the author's judgement; override it with --last-section.
 *   - The thematic tension and pending citations cannot be inferred from the text;
 *     supply them with --tension and --pending (the create-checkpoint skill does).
 *
 * Exit codes: 0 success, 2 usage or filesystem error.
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const {
  extractFrontmatter,
  parseFlatYaml,
  formatLocalIso8601,
  formatLocalFileStamp,
} = require('./lib/frontmatter');
const { UsageError, reportError } = require('./lib/cli-errors');

const CHECKPOINT_SCHEMA_VERSION = 1;
const CHECKPOINT_DIRECTORY = path.join('40_logs', 'checkpoints');
const HEADING_PATTERN = /^\s{0,3}(#{1,6})\s+(.*?)(?:\s+#+)?\s*$/;

const USAGE_TEXT = [
  'Usage: node scripts/checkpoint.js <draftPath> [options]',
  '',
  '  --tension "<text>"       Active thematic tension / unresolved aporia',
  '  --pending "<text>"       Pending primary source citation (repeatable)',
  '  --last-section "<text>"  Override the detected last completed section',
  '  --destination <path>     File where work resumes, relative to the root (default: the draft itself)',
  '  --root <dir>             Workspace root (default: the parent of scripts/)',
].join('\n');

// ---------------------------------------------------------------------------
// Argument parsing
// ---------------------------------------------------------------------------

/**
 * @param {string[]} argumentList process.argv.slice(2)
 * @returns {{draftPath: string|null, rootDirectory: string, activeTension: string|null,
 *            pendingCitations: string[], lastSectionOverride: string|null,
 *            destinationPath: string|null, showHelp: boolean}}
 */
function parseArguments(argumentList) {
  const options = {
    draftPath: null,
    rootDirectory: path.resolve(__dirname, '..'),
    activeTension: null,
    pendingCitations: [],
    lastSectionOverride: null,
    destinationPath: null,
    showHelp: false,
  };

  const readFlagValue = (flagName, index) => {
    if (index + 1 >= argumentList.length) {
      throw new UsageError(`${flagName} requires a value`);
    }
    return argumentList[index + 1];
  };

  for (let index = 0; index < argumentList.length; index += 1) {
    const argument = argumentList[index];
    switch (argument) {
      case '--tension':
        options.activeTension = readFlagValue(argument, index);
        index += 1;
        break;
      case '--pending':
        options.pendingCitations.push(readFlagValue(argument, index));
        index += 1;
        break;
      case '--last-section':
        options.lastSectionOverride = readFlagValue(argument, index);
        index += 1;
        break;
      case '--destination':
        options.destinationPath = readFlagValue(argument, index);
        index += 1;
        break;
      case '--root':
        options.rootDirectory = path.resolve(readFlagValue(argument, index));
        index += 1;
        break;
      case '--help':
      case '-h':
        options.showHelp = true;
        break;
      default:
        if (argument.startsWith('--')) {
          throw new UsageError(`unknown argument: ${argument}`);
        }
        if (options.draftPath !== null) {
          throw new UsageError(`unexpected extra argument: ${argument}`);
        }
        options.draftPath = argument;
    }
  }

  return options;
}

// ---------------------------------------------------------------------------
// Measurement
// ---------------------------------------------------------------------------

/**
 * Return the body's lines with fenced code blocks removed, so code samples
 * and fence markers do not count as prose.
 *
 * @param {string} bodyText
 * @returns {string[]}
 */
function getProseLines(bodyText) {
  const proseLines = [];
  let insideFence = false;

  for (const line of bodyText.split('\n')) {
    const trimmedLine = line.trim();
    if (trimmedLine.startsWith('```') || trimmedLine.startsWith('~~~')) {
      insideFence = !insideFence;
    } else if (!insideFence) {
      proseLines.push(line);
    }
  }

  return proseLines;
}

/**
 * Count words: whitespace-delimited tokens containing at least one letter or
 * digit. Markdown markers such as "#", "-", ">" and "---" are therefore ignored.
 *
 * @param {string[]} lines
 * @returns {number}
 */
function countWords(lines) {
  let wordCount = 0;
  for (const line of lines) {
    for (const token of line.split(/\s+/)) {
      if (/[\p{L}\p{N}]/u.test(token)) {
        wordCount += 1;
      }
    }
  }
  return wordCount;
}

/**
 * Find the last markdown heading and the words that follow it.
 *
 * @param {string[]} proseLines
 * @returns {{heading: string|null, wordsInSection: number}}
 */
function findLastSection(proseLines) {
  let lastHeadingIndex = -1;
  let lastHeadingText = null;

  proseLines.forEach((line, lineIndex) => {
    const headingMatch = HEADING_PATTERN.exec(line);
    if (headingMatch) {
      lastHeadingIndex = lineIndex;
      lastHeadingText = headingMatch[2];
    }
  });

  return {
    heading: lastHeadingText,
    wordsInSection: countWords(proseLines.slice(lastHeadingIndex + 1)),
  };
}

/** First level-1 heading, used as a title fallback when frontmatter has none. */
function findFirstTopLevelHeading(proseLines) {
  for (const line of proseLines) {
    const headingMatch = HEADING_PATTERN.exec(line);
    if (headingMatch && headingMatch[1].length === 1) {
      return headingMatch[2];
    }
  }
  return null;
}

// ---------------------------------------------------------------------------
// Record construction and output
// ---------------------------------------------------------------------------

/** Workspace-relative path with forward slashes, stable across Windows and POSIX. */
function toWorkspaceRelativePath(rootDirectory, absolutePath) {
  return path.relative(rootDirectory, absolutePath).split(path.sep).join('/');
}

/**
 * Build the checkpoint record for a draft.
 *
 * @param {object} options Parsed arguments.
 * @param {Date} captureTime
 * @returns {object} JSON-serialisable checkpoint record.
 */
function buildCheckpointRecord(options, captureTime) {
  const absoluteDraftPath = path.resolve(options.draftPath);
  if (!fs.existsSync(absoluteDraftPath) || !fs.statSync(absoluteDraftPath).isFile()) {
    throw new Error(`draft not found or not a file: ${absoluteDraftPath}`);
  }

  const draftBuffer = fs.readFileSync(absoluteDraftPath);
  const draftStats = fs.statSync(absoluteDraftPath);
  const { hasFrontmatter, block, body } = extractFrontmatter(draftBuffer.toString('utf8'));
  const { fields } = hasFrontmatter ? parseFlatYaml(block) : { fields: {} };

  const proseLines = getProseLines(body);
  const lastSection = findLastSection(proseLines);
  const warnings = [];

  if (!hasFrontmatter) {
    warnings.push('draft has no frontmatter; title/edition/version fall back to null or detected values');
  }
  if (lastSection.heading === null && options.lastSectionOverride === null) {
    warnings.push('no markdown heading found; last_completed_section is null');
  }

  const relativeDraftPath = toWorkspaceRelativePath(options.rootDirectory, absoluteDraftPath);
  if (relativeDraftPath.startsWith('..')) {
    warnings.push(`draft is outside the workspace root (${options.rootDirectory}); paths are relative to the root`);
  }
  // A destination is recorded workspace-relative, so a relative one is read as relative to the root.
  const destinationPath = options.destinationPath
    ? toWorkspaceRelativePath(options.rootDirectory, path.resolve(options.rootDirectory, options.destinationPath))
    : relativeDraftPath;

  return {
    schema_version: CHECKPOINT_SCHEMA_VERSION,
    created_at: formatLocalIso8601(captureTime),
    working_title: fields.title || findFirstTopLevelHeading(proseLines) || path.basename(absoluteDraftPath),
    edition: fields.edition || null,
    semantic_version: fields.version || null,
    volume: fields.volume || null,
    status: fields.status || null,
    last_completed_section: options.lastSectionOverride || lastSection.heading,
    word_count: countWords(proseLines),
    last_section_word_count: lastSection.wordsInSection,
    active_thematic_tension: options.activeTension,
    pending_primary_source_citations: options.pendingCitations,
    destination_file_path: destinationPath,
    source: {
      file: relativeDraftPath,
      size_bytes: draftStats.size,
      modified: formatLocalIso8601(draftStats.mtime),
      sha256: crypto.createHash('sha256').update(draftBuffer).digest('hex'),
    },
    warnings,
  };
}

/**
 * Write the record to 40_logs/checkpoints/. Refuses to overwrite an existing
 * file (two checkpoints in the same second would otherwise collide).
 *
 * @param {object} record
 * @param {string} rootDirectory
 * @param {Date} captureTime
 * @returns {string} Absolute path of the written file.
 */
function writeCheckpointRecord(record, rootDirectory, captureTime) {
  const checkpointDirectory = path.join(rootDirectory, CHECKPOINT_DIRECTORY);
  fs.mkdirSync(checkpointDirectory, { recursive: true });

  const outputPath = path.join(
    checkpointDirectory,
    `checkpoint_${formatLocalFileStamp(captureTime)}.json`
  );
  try {
    fs.writeFileSync(outputPath, `${JSON.stringify(record, null, 2)}\n`, { flag: 'wx' });
  } catch (error) {
    if (error.code === 'EEXIST') {
      throw new Error(`checkpoint already exists for this second: ${outputPath} (retry in a moment)`);
    }
    throw error;
  }
  return outputPath;
}

function main() {
  let options;
  try {
    options = parseArguments(process.argv.slice(2));
    if (options.showHelp) {
      console.log(USAGE_TEXT);
      return 0;
    }
    if (options.draftPath === null) {
      throw new UsageError('missing <draftPath>');
    }

    const captureTime = new Date();
    const record = buildCheckpointRecord(options, captureTime);
    const outputPath = writeCheckpointRecord(record, options.rootDirectory, captureTime);

    console.log(`Checkpoint written: ${outputPath}`);
    console.log(JSON.stringify(record, null, 2));
    return 0;
  } catch (error) {
    reportError(error, USAGE_TEXT);
    return 2;
  }
}

if (require.main === module) {
  process.exitCode = main();
}

module.exports = { parseArguments, countWords, getProseLines, findLastSection, buildCheckpointRecord };
