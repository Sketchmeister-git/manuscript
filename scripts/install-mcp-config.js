#!/usr/bin/env node
'use strict';

/**
 * install-mcp-config.js — register the manuscript MCP servers in Claude Desktop.
 *
 * Merges the servers defined in scripts/mcp-servers.json into the `mcpServers`
 * object of claude_desktop_config.json without disturbing anything else in
 * that file (preferences, session folder grants, unrelated servers).
 *
 * Usage:
 *   node scripts/install-mcp-config.js [--dry-run] [--check] [--force]
 *        [--config <path>] [--servers <path>]
 *
 *   --dry-run   Show what would change; write nothing.
 *   --check     Read-only: confirm the config parses and the servers are registered.
 *   --force     Replace an existing memory/fetch entry that differs from the
 *               definition. The filesystem entry is never replaced: its allowed
 *               directories are always merged so existing grants are preserved.
 *   --config    Config file path (default: %APPDATA%\Claude\claude_desktop_config.json).
 *   --servers   Server definitions (default: scripts/mcp-servers.json).
 *
 * Safety properties:
 *   - Invalid existing JSON aborts the run; the file is left untouched.
 *   - A timestamped .bak copy is written before any change.
 *   - The write is atomic (temp file, then rename).
 *   - The result is re-read and parsed, and every non-mcpServers key is
 *     confirmed unchanged, before the run reports success.
 *   - Re-running is a no-op once the config is up to date.
 *
 * Server notes:
 *   - `fetch` uses the official Python server (`uvx mcp-server-fetch`); the
 *     package "@modelcontextprotocol/server-fetch" does not exist on npm.
 *   - The memory server stores data inside its package directory by default;
 *     set MEMORY_FILE_PATH in its "env" if the data must survive npx cache refreshes.
 *
 * Exit codes: 0 success / nothing to do, 2 usage, parse or filesystem error.
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { isDeepStrictEqual } = require('util');
const { formatLocalFileStamp } = require('./lib/frontmatter');
const { UsageError, reportError } = require('./lib/cli-errors');

const FILESYSTEM_SERVER_NAME = 'filesystem';
const FILESYSTEM_PACKAGE_NAME = '@modelcontextprotocol/server-filesystem';
const DEFAULT_SERVERS_PATH = path.join(__dirname, 'mcp-servers.json');

const UV_INSTALL_HINT =
  'Install uv (provides uvx): powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"';

const USAGE_TEXT = [
  'Usage: node scripts/install-mcp-config.js [--dry-run] [--check] [--force] [--config <path>] [--servers <path>]',
].join('\n');

// ---------------------------------------------------------------------------
// Arguments and file IO
// ---------------------------------------------------------------------------

/**
 * @param {string[]} argumentList process.argv.slice(2)
 * @returns {{configPath: string|null, serversPath: string, dryRun: boolean,
 *            checkOnly: boolean, force: boolean, showHelp: boolean}}
 */
function parseArguments(argumentList) {
  const options = {
    configPath: null,
    serversPath: DEFAULT_SERVERS_PATH,
    dryRun: false,
    checkOnly: false,
    force: false,
    showHelp: false,
  };

  for (let index = 0; index < argumentList.length; index += 1) {
    const argument = argumentList[index];
    if (argument === '--dry-run') {
      options.dryRun = true;
    } else if (argument === '--check') {
      options.checkOnly = true;
    } else if (argument === '--force') {
      options.force = true;
    } else if (argument === '--help' || argument === '-h') {
      options.showHelp = true;
    } else if (argument === '--config' || argument === '--servers') {
      index += 1;
      if (index >= argumentList.length) {
        throw new UsageError(`${argument} requires a path`);
      }
      const resolvedPath = path.resolve(argumentList[index]);
      if (argument === '--config') {
        options.configPath = resolvedPath;
      } else {
        options.serversPath = resolvedPath;
      }
    } else {
      throw new UsageError(`unknown argument: ${argument}`);
    }
  }

  return options;
}

/** Default Claude Desktop config location on Windows. */
function resolveDefaultConfigPath() {
  if (!process.env.APPDATA) {
    throw new UsageError('%APPDATA% is not set; pass --config <path to claude_desktop_config.json>');
  }
  return path.join(process.env.APPDATA, 'Claude', 'claude_desktop_config.json');
}

/**
 * Read and parse a JSON file, tolerating a UTF-8 BOM (Windows editors add one).
 *
 * @param {string} filePath
 * @param {string} description Used in error messages.
 * @returns {object}
 */
function readJsonFile(filePath, description) {
  const fileText = fs.readFileSync(filePath, 'utf8').replace(/^﻿/, '');
  try {
    return JSON.parse(fileText);
  } catch (error) {
    throw new Error(`${description} is not valid JSON (${error.message}): ${filePath}`);
  }
}

/** Write JSON atomically: temp file in the same directory, then rename over the target. */
function writeJsonAtomically(filePath, jsonValue) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const temporaryPath = `${filePath}.tmp-${process.pid}`;
  fs.writeFileSync(temporaryPath, `${JSON.stringify(jsonValue, null, 2)}\n`, 'utf8');
  fs.renameSync(temporaryPath, filePath);
}

/** Copy the existing config to a timestamped .bak sibling; returns the backup path. */
function backUpConfig(configPath) {
  const backupPath = `${configPath}.bak-${formatLocalFileStamp(new Date())}`;
  fs.copyFileSync(configPath, backupPath);
  return backupPath;
}

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

// ---------------------------------------------------------------------------
// Merge logic (pure functions: no IO, easy to reason about)
// ---------------------------------------------------------------------------

/** Normalise a Windows directory path for comparison: case, slashes, trailing separator. */
function normalizeDirectoryForComparison(directoryPath) {
  return directoryPath.replace(/\//g, '\\').replace(/\\+$/, '').toLowerCase();
}

/**
 * Directory arguments of a filesystem server entry: everything after the package name.
 * Returns null when the entry does not launch the official filesystem package.
 */
function getFilesystemDirectories(serverEntry) {
  const argumentList = Array.isArray(serverEntry.args) ? serverEntry.args : [];
  const packageIndex = argumentList.indexOf(FILESYSTEM_PACKAGE_NAME);
  return packageIndex === -1 ? null : argumentList.slice(packageIndex + 1);
}

/**
 * Merge allowed directories into an existing filesystem entry. Existing
 * directories keep their order and are never removed.
 *
 * @returns {{entry: object, addedDirectories: string[]}|null} null if the entry is not mergeable.
 */
function mergeFilesystemEntry(existingEntry, desiredEntry) {
  const existingDirectories = getFilesystemDirectories(existingEntry);
  if (existingDirectories === null) {
    return null;
  }

  const knownDirectories = new Set(existingDirectories.map(normalizeDirectoryForComparison));
  const addedDirectories = (getFilesystemDirectories(desiredEntry) || []).filter(
    (directory) => !knownDirectories.has(normalizeDirectoryForComparison(directory))
  );

  return {
    entry: { ...existingEntry, args: [...existingEntry.args, ...addedDirectories] },
    addedDirectories,
  };
}

/**
 * Compute the merged config and a list of per-server outcomes.
 *
 * @param {object} existingConfig Parsed claude_desktop_config.json.
 * @param {object} desiredServers Map of server name to definition.
 * @param {{force: boolean}} mergeOptions
 * @returns {{mergedConfig: object, outcomes: {server: string, status: string, detail: string}[]}}
 */
function mergeMcpServers(existingConfig, desiredServers, mergeOptions) {
  if (existingConfig.mcpServers !== undefined && !isPlainObject(existingConfig.mcpServers)) {
    throw new Error('existing "mcpServers" is not an object; refusing to modify the file');
  }

  const mergedServers = { ...(existingConfig.mcpServers || {}) };
  const outcomes = [];

  for (const [serverName, desiredEntry] of Object.entries(desiredServers)) {
    const existingEntry = mergedServers[serverName];

    if (existingEntry === undefined) {
      mergedServers[serverName] = desiredEntry;
      outcomes.push({ server: serverName, status: 'added', detail: 'new entry' });
      continue;
    }

    if (serverName === FILESYSTEM_SERVER_NAME) {
      const mergeResult = mergeFilesystemEntry(existingEntry, desiredEntry);
      if (mergeResult === null) {
        outcomes.push({
          server: serverName,
          status: 'kept',
          detail: `existing entry does not launch ${FILESYSTEM_PACKAGE_NAME}; left as is`,
        });
      } else if (mergeResult.addedDirectories.length === 0) {
        outcomes.push({ server: serverName, status: 'unchanged', detail: 'all directories already granted' });
      } else {
        mergedServers[serverName] = mergeResult.entry;
        outcomes.push({
          server: serverName,
          status: 'merged',
          detail: `added ${mergeResult.addedDirectories.length} director${mergeResult.addedDirectories.length === 1 ? 'y' : 'ies'}: ${mergeResult.addedDirectories.join('; ')}`,
        });
      }
      continue;
    }

    if (isDeepStrictEqual(existingEntry, desiredEntry)) {
      outcomes.push({ server: serverName, status: 'unchanged', detail: 'already registered' });
    } else if (mergeOptions.force) {
      mergedServers[serverName] = desiredEntry;
      outcomes.push({ server: serverName, status: 'replaced', detail: 'differing entry replaced (--force)' });
    } else {
      outcomes.push({
        server: serverName,
        status: 'kept',
        detail: 'existing entry differs from the definition; left as is (use --force to replace)',
      });
    }
  }

  return { mergedConfig: { ...existingConfig, mcpServers: mergedServers }, outcomes };
}

// ---------------------------------------------------------------------------
// Verification and preflight (read-only checks that report, never block)
// ---------------------------------------------------------------------------

/**
 * Confirm a written config parses, contains every desired server, and left all
 * other top-level keys exactly as they were.
 *
 * @returns {string[]} Problems; empty when verification passes.
 */
function verifyConfigFile(configPath, desiredServers, originalConfig) {
  const problems = [];
  let writtenConfig;
  try {
    writtenConfig = readJsonFile(configPath, 'config');
  } catch (error) {
    return [error.message];
  }

  for (const serverName of Object.keys(desiredServers)) {
    if (!isPlainObject(writtenConfig.mcpServers) || writtenConfig.mcpServers[serverName] === undefined) {
      problems.push(`server not registered: ${serverName}`);
    }
  }

  if (originalConfig !== null) {
    for (const [key, originalValue] of Object.entries(originalConfig)) {
      if (key !== 'mcpServers' && !isDeepStrictEqual(writtenConfig[key], originalValue)) {
        problems.push(`top-level key changed unexpectedly: ${key}`);
      }
    }
  }
  return problems;
}

/** True if `<command> --version` runs successfully (shell needed for npx.cmd on Windows). */
function isCommandAvailable(commandName) {
  const probeResult = spawnSync(commandName, ['--version'], { shell: true, encoding: 'utf8' });
  return probeResult.status === 0;
}

/**
 * Warn about allowed directories that do not exist and launchers that are not
 * on PATH. Directory checks only run on Windows, where the paths are meaningful.
 */
function collectPreflightWarnings(serversToRegister) {
  const warnings = [];

  const filesystemEntry = serversToRegister[FILESYSTEM_SERVER_NAME];
  if (filesystemEntry && process.platform === 'win32') {
    for (const directory of getFilesystemDirectories(filesystemEntry) || []) {
      if (!fs.existsSync(directory)) {
        warnings.push(`allowed directory does not exist (server will skip it): ${directory}`);
      }
    }
  } else if (filesystemEntry) {
    warnings.push('not running on Windows: allowed-directory existence check skipped');
  }

  const launchers = new Set(Object.values(serversToRegister).map((entry) => entry.command));
  for (const launcher of launchers) {
    if (!isCommandAvailable(launcher)) {
      const hint = launcher === 'uvx' ? ` ${UV_INSTALL_HINT}` : launcher === 'npx' ? ' Install Node.js from https://nodejs.org' : '';
      warnings.push(`launcher "${launcher}" not found on PATH.${hint}`);
    }
  }
  return warnings;
}

function printRestartInstructions() {
  console.log(
    [
      '',
      'To activate the servers:',
      '  1. Fully quit Claude Desktop: right-click its icon in the system tray and choose Quit.',
      '     (Closing the window leaves it running and the new servers will not load.)',
      '  2. Relaunch Claude Desktop.',
      '  3. Open Settings > Developer and confirm filesystem, memory and fetch show as running.',
      '  4. If a server fails, read %APPDATA%\\Claude\\logs\\mcp-server-<name>.log.',
    ].join('\n')
  );
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

function main() {
  const options = parseArguments(process.argv.slice(2));
  if (options.showHelp) {
    console.log(USAGE_TEXT);
    return 0;
  }

  const configPath = options.configPath || resolveDefaultConfigPath();
  const serverDefinitions = readJsonFile(options.serversPath, 'server definitions');
  const desiredServers = serverDefinitions.mcpServers;
  if (!isPlainObject(desiredServers) || Object.keys(desiredServers).length === 0) {
    throw new Error(`server definitions must contain a non-empty "mcpServers" object: ${options.serversPath}`);
  }

  const configExists = fs.existsSync(configPath);
  const existingConfig = configExists ? readJsonFile(configPath, 'existing config') : null;
  if (existingConfig !== null && !isPlainObject(existingConfig)) {
    throw new Error(`existing config is not a JSON object: ${configPath}`);
  }

  const creationNote = configExists || options.checkOnly ? '' : ' (does not exist yet; will be created)';
  console.log(`Config: ${configPath}${creationNote}`);

  if (options.checkOnly) {
    if (!configExists) {
      throw new Error('--check: config file does not exist');
    }
    const problems = verifyConfigFile(configPath, desiredServers, null);
    problems.forEach((problem) => console.error(`  PROBLEM: ${problem}`));
    console.log(problems.length === 0 ? 'OK: valid JSON and all servers registered.' : 'Check failed.');
    return problems.length === 0 ? 0 : 2;
  }

  const { mergedConfig, outcomes } = mergeMcpServers(existingConfig || {}, desiredServers, {
    force: options.force,
  });
  outcomes.forEach((outcome) => console.log(`  ${outcome.status.toUpperCase().padEnd(9)} ${outcome.server}: ${outcome.detail}`));

  collectPreflightWarnings(desiredServers).forEach((warning) => console.warn(`  WARNING: ${warning}`));

  const hasChanges = outcomes.some((outcome) => ['added', 'merged', 'replaced'].includes(outcome.status));
  if (!hasChanges) {
    console.log('Nothing to change: config is already up to date.');
    return 0;
  }

  if (options.dryRun) {
    console.log('\n--dry-run: resulting "mcpServers" (nothing written):');
    console.log(JSON.stringify(mergedConfig.mcpServers, null, 2));
    return 0;
  }

  if (configExists) {
    console.log(`Backup written: ${backUpConfig(configPath)}`);
  }
  writeJsonAtomically(configPath, mergedConfig);

  const problems = verifyConfigFile(configPath, desiredServers, existingConfig);
  if (problems.length > 0) {
    problems.forEach((problem) => console.error(`  PROBLEM: ${problem}`));
    console.error('Verification failed. Restore the .bak file listed above.');
    return 2;
  }
  console.log('Verified: config is valid JSON, servers registered, all other settings unchanged.');
  printRestartInstructions();
  return 0;
}

if (require.main === module) {
  try {
    process.exitCode = main();
  } catch (error) {
    reportError(error, USAGE_TEXT);
    process.exitCode = 2;
  }
}

module.exports = { mergeMcpServers, mergeFilesystemEntry, normalizeDirectoryForComparison };
