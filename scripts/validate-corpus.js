#!/usr/bin/env node
'use strict';

/**
 * validate-corpus.js — verify frontmatter across the manuscript corpus.
 *
 * Scans every markdown file under `10_projects/` and checks that it carries
 * the YAML frontmatter defined in CLAUDE.md: all required keys, valid
 * ISO 8601 timestamps with a UTC offset, a version matching the workspace
 * pattern, and values drawn from the controlled vocabularies.
 *
 * Usage:
 *   node scripts/validate-corpus.js [--root <workspaceRoot>] [--json]
 *
 * Exit codes:
 *   0  every file is valid (an empty corpus is valid)
 *   1  at least one file failed validation
 *   2  usage or filesystem error (e.g. 10_projects/ not found)
 */

const fs = require('fs');
const path = require('path');
const { extractFrontmatter, parseFlatYaml, validateFrontmatter } = require('./lib/frontmatter');
const { UsageError, reportError } = require('./lib/cli-errors');

const CORPUS_DIRECTORY_NAME = '10_projects';
const DIRECTORIES_TO_SKIP = new Set(['node_modules', '.git']);

const USAGE_TEXT = [
  'Usage: node scripts/validate-corpus.js [--root <workspaceRoot>] [--json]',
  '',
  '  --root <dir>  Workspace root (default: the parent of scripts/)',
  '  --json        Emit a machine-readable JSON report instead of text',
].join('\n');

/**
 * Parse command-line arguments.
 *
 * @param {string[]} argumentList process.argv.slice(2)
 * @returns {{rootDirectory: string, asJson: boolean, showHelp: boolean}}
 */
function parseArguments(argumentList) {
  const options = {
    rootDirectory: path.resolve(__dirname, '..'),
    asJson: false,
    showHelp: false,
  };

  for (let index = 0; index < argumentList.length; index += 1) {
    const argument = argumentList[index];
    if (argument === '--root') {
      index += 1;
      if (index >= argumentList.length) {
        throw new UsageError('--root requires a directory path');
      }
      options.rootDirectory = path.resolve(argumentList[index]);
    } else if (argument === '--json') {
      options.asJson = true;
    } else if (argument === '--help' || argument === '-h') {
      options.showHelp = true;
    } else {
      throw new UsageError(`unknown argument: ${argument}`);
    }
  }

  return options;
}

/**
 * Recursively collect markdown files beneath a directory, in sorted order.
 *
 * @param {string} directoryPath
 * @returns {string[]} Absolute file paths.
 */
function collectMarkdownFiles(directoryPath) {
  const collectedFiles = [];

  const directoryEntries = fs
    .readdirSync(directoryPath, { withFileTypes: true })
    .sort((left, right) => left.name.localeCompare(right.name));

  for (const entry of directoryEntries) {
    const entryPath = path.join(directoryPath, entry.name);
    if (entry.isDirectory()) {
      if (!DIRECTORIES_TO_SKIP.has(entry.name)) {
        collectedFiles.push(...collectMarkdownFiles(entryPath));
      }
    } else if (entry.isFile() && entry.name.toLowerCase().endsWith('.md')) {
      collectedFiles.push(entryPath);
    }
  }

  return collectedFiles;
}

/**
 * Validate a single markdown file.
 *
 * @param {string} filePath Absolute path.
 * @returns {string[]} Issues found; empty when the file is valid.
 */
function validateMarkdownFile(filePath) {
  const fileText = fs.readFileSync(filePath, 'utf8');
  const { hasFrontmatter, block } = extractFrontmatter(fileText);

  if (!hasFrontmatter) {
    return ['no frontmatter block (file must start with a "---" line and close it with "---")'];
  }

  const { fields, parseErrors } = parseFlatYaml(block);
  return [...parseErrors, ...validateFrontmatter(fields)];
}

/**
 * Render the human-readable report.
 *
 * @param {{filesChecked: number, failureCount: number, results: {file: string, issues: string[]}[]}} report
 * @returns {string}
 */
function formatTextReport(report) {
  const reportLines = [];

  for (const result of report.results) {
    if (result.issues.length === 0) {
      reportLines.push(`PASS  ${result.file}`);
    } else {
      reportLines.push(`FAIL  ${result.file}`);
      result.issues.forEach((issue) => reportLines.push(`        - ${issue}`));
    }
  }

  reportLines.push('');
  reportLines.push(
    `${report.filesChecked} file(s) checked, ` +
      `${report.filesChecked - report.failureCount} valid, ${report.failureCount} failing.`
  );
  return reportLines.join('\n');
}

function main() {
  let options;
  try {
    options = parseArguments(process.argv.slice(2));
  } catch (error) {
    reportError(error, USAGE_TEXT);
    return 2;
  }

  if (options.showHelp) {
    console.log(USAGE_TEXT);
    return 0;
  }

  const corpusDirectory = path.join(options.rootDirectory, CORPUS_DIRECTORY_NAME);
  if (!fs.existsSync(corpusDirectory) || !fs.statSync(corpusDirectory).isDirectory()) {
    console.error(`corpus directory not found: ${corpusDirectory}`);
    return 2;
  }

  const results = collectMarkdownFiles(corpusDirectory).map((filePath) => ({
    file: path.relative(options.rootDirectory, filePath),
    issues: validateMarkdownFile(filePath),
  }));
  const failureCount = results.filter((result) => result.issues.length > 0).length;
  const report = {
    root: options.rootDirectory,
    filesChecked: results.length,
    failureCount,
    results,
  };

  console.log(options.asJson ? JSON.stringify(report, null, 2) : formatTextReport(report));
  return failureCount > 0 ? 1 : 0;
}

if (require.main === module) {
  process.exitCode = main();
}

module.exports = { parseArguments, collectMarkdownFiles, validateMarkdownFile };
