'use strict';

/**
 * Small shared helper so the command-line scripts report errors consistently.
 *
 * Usage text is only useful when the command line itself was wrong. For every
 * other failure (invalid JSON, missing file, name collision) the usage block
 * would bury the actual message, so it is printed for UsageError only.
 */

/** Raised for bad command-line usage: unknown flag, missing value, missing argument. */
class UsageError extends Error {}

/**
 * Print an error to stderr, appending the usage text for UsageError only.
 *
 * @param {Error} error
 * @param {string} usageText
 */
function reportError(error, usageText) {
  console.error(error instanceof UsageError ? `${error.message}\n\n${usageText}` : error.message);
}

module.exports = { UsageError, reportError };
