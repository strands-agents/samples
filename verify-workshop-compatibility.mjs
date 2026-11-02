// Protects the path-based workshop import contract during ordinary pull requests.

import { execFileSync } from 'node:child_process'
import { readFileSync } from 'node:fs'

const base = process.argv[2]
const protectedPaths = ['python/01-learn', 'typescript/01-learn']

if (!base) {
  console.error('usage: node verify-workshop-compatibility.mjs <base-revision>')
  process.exit(2)
}

function git(...args) {
  return execFileSync('git', args, { encoding: 'utf8' })
}

let changed
try {
  changed = git('diff', '--name-status', `${base}...HEAD`, '--', ...protectedPaths).trim()
} catch (error) {
  console.error(`could not compare workshop content with ${base}: ${error.message}`)
  process.exit(2)
}

if (changed) {
  console.error(
    [
      'Protected workshop content changed.',
      'Coordinate downstream verification and apply the workshop-compatible-change label:',
      changed,
    ].join('\n')
  )
  process.exit(1)
}

function workshopContract(manifestText) {
  const manifest = JSON.parse(manifestText)
  return {
    categories: (manifest.categories ?? []).filter(
      (category) =>
        category.id === 'learn' &&
        (category.language === 'python' || category.language === 'typescript')
    ),
    samples: (manifest.samples ?? []).filter((sample) =>
      protectedPaths.some((prefix) => sample.path.startsWith(`${prefix}/`))
    ),
  }
}

let baseManifest
try {
  baseManifest = git('show', `${base}:samples.json`)
} catch (error) {
  console.error(`could not read samples.json from ${base}: ${error.message}`)
  process.exit(2)
}

const baseContract = JSON.stringify(workshopContract(baseManifest))
const currentContract = JSON.stringify(workshopContract(readFileSync('samples.json', 'utf8')))

if (baseContract !== currentContract) {
  console.error(
    'Protected workshop categories or records in samples.json changed. Coordinate downstream verification and apply the workshop-compatible-change label.'
  )
  process.exit(1)
}

console.log('Protected workshop trees and version-1 manifest records are unchanged.')
