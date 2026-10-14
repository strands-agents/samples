// Generates samples.json: a machine-readable index of every sample in this
// repo so downstream consumers (e.g. the docs site) can render a styled,
// grouped, filterable catalog without scraping prose.
//
// A "sample" is the shallowest README-bearing directory under a category
// (nested apps inside a sample are folded into it). Titles come from the
// folder name; descriptions/tags are lifted from the curated README tables
// when a row links to the sample, else from the sample README's first
// paragraph.

import { readFileSync, readdirSync, writeFileSync, statSync, existsSync } from 'node:fs'
import path from 'node:path'

const ROOT = path.resolve('.')
const LANGS = ['python', 'typescript']

const titleCase = (s) =>
  s
    .replace(/^\d+[-_]/, '')
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .trim()

// ── collect every directory that has a README.md, under a language dir ──
function walkDirs(dir, acc = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue
    if (entry.name.startsWith('.')) continue
    const full = path.join(dir, entry.name)
    acc.push(full)
    walkDirs(full, acc)
  }
  return acc
}

const hasReadme = (d) => existsSync(path.join(d, 'README.md'))
const hasNotebook = (d) => readdirSync(d).some((f) => f.endsWith('.ipynb'))
const rel = (d) => path.relative(ROOT, d).split(path.sep).join('/')

// A category root is exactly `<lang>/<NN-name>` — never a sample itself.
const isCategoryRoot = (relPath) => /^[a-z]+\/[^/]+$/.test(relPath)

// A handful of category labels want casing the title-caser can't infer.
const LABEL_OVERRIDES = { 'ux-demos': 'UX Demos' }

// ── parse README tables into a { resolvedPath -> {description, tags} } map ──
// Rows look like: | [`folder`](./path/) | Feature | Description |  (2 or 3 cols)
function buildEnrichment(allDirs) {
  const map = new Map()
  const readmes = [ROOT, ...allDirs].filter((d) => existsSync(path.join(d, 'README.md')))
  for (const dir of readmes) {
    const md = readFileSync(path.join(dir, 'README.md'), 'utf8')
    for (const line of md.split('\n')) {
      const m = line.match(/^\|\s*\[[^\]]*\]\(([^)]+)\)\s*\|(.*)\|\s*$/)
      if (!m) continue
      const href = m[1].replace(/^\.\//, '').replace(/\/$/, '')
      const cells = m[2].split('|').map((c) => c.trim())
      const description = cells[cells.length - 1]
      const tags =
        cells.length > 1
          ? cells
              .slice(0, -1)
              .join(', ')
              .replace(/`/g, '')
              .split(',')
              .map((t) => t.trim())
              .filter(Boolean)
          : []
      const resolved = rel(path.resolve(dir, href))
      if (description) map.set(resolved, { description, tags })
    }
  }
  return map
}

// First real paragraph of a README, minus the H1, as a one-line fallback blurb.
function readmeBlurb(dir) {
  const md = readFileSync(path.join(dir, 'README.md'), 'utf8')
  const lines = md.split('\n')
  let started = false
  const para = []
  for (const raw of lines) {
    const line = raw.trim()
    if (line.startsWith('#')) {
      started = true
      continue
    }
    if (!started) continue
    if (!line) {
      if (para.length) break
      continue
    }
    if (line.startsWith('![') || line.startsWith('|') || line.startsWith('<')) continue
    para.push(line)
  }
  return para
    .join(' ')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[`*_]/g, '')
    .slice(0, 240)
    .trim()
}

const allDirs = LANGS.flatMap((l) => walkDirs(path.join(ROOT, l)))
const enrichment = buildEnrichment(allDirs)

// Greedy shallowest-first selection: a README dir is a sample unless it sits
// inside an already-selected sample (its nested apps fold into it).
const candidates = allDirs
  .map(rel)
  .filter((r) => {
    const d = path.join(ROOT, r)
    return (hasReadme(d) || hasNotebook(d)) && !isCategoryRoot(r)
  })
  .sort((a, b) => a.split('/').length - b.split('/').length || a.localeCompare(b))

const selected = []
for (const r of candidates) {
  if (selected.some((s) => r === s || r.startsWith(s + '/'))) continue
  selected.push(r)
}

const samples = selected
  .map((r) => {
    const parts = r.split('/')
    const language = parts[0]
    const categoryDir = parts[1]
    const dir = path.join(ROOT, r)
    const notebook = readdirSync(dir).find((f) => f.endsWith('.ipynb'))
    const enrich = enrichment.get(r)
    const categoryId = categoryDir.replace(/^\d+[-_]/, '')
    return {
      id: r,
      language,
      category: categoryId,
      categoryLabel: LABEL_OVERRIDES[categoryId] ?? titleCase(categoryDir),
      title: titleCase(parts[parts.length - 1]),
      description: enrich?.description || (hasReadme(dir) ? readmeBlurb(dir) : ''),
      tags: enrich?.tags ?? [],
      path: r,
      url: `https://github.com/strands-agents/samples/tree/main/${r}`,
      ...(notebook ? { notebook } : {}),
    }
  })
  .sort((a, b) => a.id.localeCompare(b.id))

// Categories in numbered order, with friendly labels, for grouped rendering.
const categories = []
const seen = new Set()
for (const s of samples) {
  const key = `${s.language}/${s.category}`
  if (seen.has(key)) continue
  seen.add(key)
  categories.push({ language: s.language, id: s.category, label: s.categoryLabel })
}

writeFileSync(
  path.join(ROOT, 'samples.json'),
  JSON.stringify({ version: 1, categories, samples }, null, 2) + '\n',
)
console.log(`wrote samples.json — ${samples.length} samples, ${categories.length} categories`)
