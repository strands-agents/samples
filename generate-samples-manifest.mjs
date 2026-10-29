// Generates samples.json: a machine-readable index of every sample in this
// repo so downstream consumers (e.g. the docs site) can render a styled,
// grouped, filterable catalog without scraping prose.
//
// A "sample" is the shallowest README- or notebook-bearing directory under
// a category (nested apps inside a sample are folded into it). Titles come
// from the folder name; descriptions/tags are lifted from the curated README
// tables when a row links to the sample, else from the sample README's first
// paragraph.

import { existsSync, readFileSync, readdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'

const ROOT = path.resolve('.')
const LANGS = ['python', 'typescript']
const IGNORED_DIRS = new Set(['__pycache__', 'node_modules', 'venv'])

const TITLE_WORDS = new Map(
  Object.entries({
    ab: 'A/B',
    a2a: 'A2A',
    ag: 'AG',
    agentcore: 'AgentCore',
    ai: 'AI',
    api: 'API',
    aws: 'AWS',
    cdk: 'CDK',
    copilotkit: 'CopilotKit',
    dsql: 'DSQL',
    fastapi: 'FastAPI',
    genai: 'GenAI',
    hitl: 'HITL',
    http: 'HTTP',
    hvac: 'HVAC',
    llm: 'LLM',
    mcp: 'MCP',
    nextjs: 'Next.js',
    nvidia: 'NVIDIA',
    rag: 'RAG',
    sdk: 'SDK',
    sql: 'SQL',
    sre: 'SRE',
    ui: 'UI',
    ux: 'UX',
    whatsapp: 'WhatsApp',
  })
)

const titleCase = (s) =>
  s
    .replace(/^\d+[-_]/, '')
    .replace(/[-_]+/g, ' ')
    .split(' ')
    .map((word) => TITLE_WORDS.get(word.toLowerCase()) ?? word.replace(/^\w/, (c) => c.toUpperCase()))
    .join(' ')
    .trim()

function cleanDescription(value) {
  const codeSpans = []
  const protectedValue = value.replace(/(`+)(.*?)\1/g, (_match, _fence, code) => {
    const index = codeSpans.push(code) - 1
    return `\uE000${index}\uE001`
  })
  const cleaned = protectedValue
    .replace(/<br\s*\/?>/gi, ' ')
    .replace(/<[^>]+>/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/\*\*([^*\n]+)\*\*/g, '$1')
    .replace(/__([^_\n]+)__/g, '$1')
    .replace(/(^|[\s(])\*([^*\n]+)\*(?=$|[\s).,!?;:])/g, '$1$2')
    .replace(/(^|[\s(])_([^_\n]+)_(?=$|[\s).,!?;:])/g, '$1$2')
    .replace(/\uE000(\d+)\uE001/g, (_match, index) => codeSpans[Number(index)])
    .replace(/\s+/g, ' ')
    .trim()
  if (cleaned.length <= 240) return cleaned
  const prefix = cleaned.slice(0, 239)
  const boundary = prefix.lastIndexOf(' ')
  return `${prefix.slice(0, boundary > 160 ? boundary : 239).replace(/[,:;.!-]+$/, '')}…`
}

// ── collect every directory that has a README.md, under a language dir ──
function walkDirs(dir, acc = []) {
  const entries = readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))
  for (const entry of entries) {
    if (!entry.isDirectory()) continue
    if (entry.name.startsWith('.') || IGNORED_DIRS.has(entry.name)) continue
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

// ── parse category README tables into a { resolvedPath -> {description, tags} } map ──
// Rows look like: | [`folder`](./path/) | Feature | Description |  (2 or 3 cols)
function buildEnrichment(categoryDirs) {
  const map = new Map()
  for (const dir of categoryDirs) {
    if (!existsSync(path.join(dir, 'README.md'))) continue
    const md = readFileSync(path.join(dir, 'README.md'), 'utf8')
    for (const line of md.split('\n')) {
      const m = line.match(/^\|\s*\[[^\]]*\]\(([^)]+)\)\s*\|(.*)\|\s*$/)
      if (!m) continue
      if (!m[1].startsWith('./')) continue
      const href = m[1].slice(2).replace(/\/$/, '')
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
      if (!description) continue
      if (map.has(resolved)) throw new Error(`duplicate catalog metadata for ${resolved}`)
      map.set(resolved, { description, tags })
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
    if (line.startsWith('>') || line.startsWith('![') || line.startsWith('|') || line.startsWith('<')) continue
    para.push(line)
  }
  return para.join(' ')
}

const categoryDirs = LANGS.flatMap((language) =>
  readdirSync(path.join(ROOT, language), { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && /^\d+[-_]/.test(entry.name))
    .map((entry) => path.join(ROOT, language, entry.name))
    .sort((a, b) => a.localeCompare(b))
)
const allDirs = categoryDirs.flatMap((dir) => [dir, ...walkDirs(dir)])
const enrichment = buildEnrichment(categoryDirs)

// Greedy shallowest-first selection: a README or notebook dir is a sample
// unless it sits inside an already-selected sample (its nested apps fold in).
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

// Keep the version 1 record shape stable for downstream consumers.
const samples = selected
  .map((r) => {
    const parts = r.split('/')
    const language = parts[0]
    const categoryDir = parts[1]
    const dir = path.join(ROOT, r)
    const readme = hasReadme(dir)
    const notebooks = readdirSync(dir)
      .filter((file) => file.endsWith('.ipynb'))
      .sort()
    if (!readme && notebooks.length > 1) {
      throw new Error(`${r} has multiple notebooks but no root README.md to index them`)
    }
    const notebook = notebooks[0]
    const enrich = enrichment.get(r)
    const categoryId = categoryDir.replace(/^\d+[-_]/, '')
    return {
      id: r,
      language,
      category: categoryId,
      categoryLabel: LABEL_OVERRIDES[categoryId] ?? titleCase(categoryDir),
      title: titleCase(parts[parts.length - 1]),
      description: cleanDescription(enrich?.description || (readme ? readmeBlurb(dir) : '')),
      tags: enrich?.tags ?? [],
      path: r,
      url: `https://github.com/strands-agents/samples/tree/main/${r}`,
      ...(notebook ? { notebook } : {}),
    }
  })
  .sort((a, b) => a.id.localeCompare(b.id))

function deriveSlug(sample) {
  const segments = sample.path.split('/')
  return [segments[0], ...segments.slice(2).map((segment) => segment.replace(/^\d+-/, ''))].join('/')
}

// Categories in numbered order, with friendly labels, for grouped rendering.
const categories = []
const seen = new Set()
for (const s of samples) {
  const key = `${s.language}/${s.category}`
  if (seen.has(key)) continue
  seen.add(key)
  categories.push({
    language: s.language,
    id: s.category,
    label: s.categoryLabel,
  })
}

function validateManifest() {
  const categoryKeys = new Set(categories.map((category) => `${category.language}/${category.id}`))
  const paths = new Set()
  const ids = new Set()
  const slugs = new Set()

  for (const sample of samples) {
    if (ids.has(sample.id)) throw new Error(`duplicate sample id: ${sample.id}`)
    ids.add(sample.id)
    if (!sample.title.trim()) throw new Error(`${sample.path} has no generated title`)
    if (!sample.description.trim()) {
      throw new Error(`${sample.path} has no description; add a README introduction or parent catalog entry`)
    }
    if (paths.has(sample.path)) throw new Error(`duplicate sample path: ${sample.path}`)
    paths.add(sample.path)

    const slug = deriveSlug(sample)
    if (!/^[a-z0-9][a-z0-9/-]*$/.test(slug)) throw new Error(`${sample.path} generates an invalid slug: ${slug}`)
    if (slugs.has(slug)) throw new Error(`duplicate generated sample slug: ${slug}`)
    slugs.add(slug)

    const categoryKey = `${sample.language}/${sample.category}`
    if (!categoryKeys.has(categoryKey)) throw new Error(`${sample.path} references unknown category ${categoryKey}`)

    const sampleDir = path.join(ROOT, sample.path)
    if (!hasReadme(sampleDir) && !sample.notebook) {
      throw new Error(`${sample.path} has no root README.md or generated notebook guide`)
    }
    if (sample.notebook && !existsSync(path.join(sampleDir, sample.notebook))) {
      throw new Error(`${sample.path} references a missing notebook guide`)
    }
  }
}

validateManifest()

const manifestPath = path.join(ROOT, 'samples.json')
const manifest = JSON.stringify({ version: 1, categories, samples }, null, 2) + '\n'

if (process.argv.includes('--check')) {
  const current = existsSync(manifestPath) ? readFileSync(manifestPath, 'utf8') : ''
  if (current !== manifest) {
    console.error('samples.json is out of date; run node generate-samples-manifest.mjs')
    process.exitCode = 1
  } else {
    console.log(`samples.json is current — ${samples.length} samples, ${categories.length} categories`)
  }
} else {
  writeFileSync(manifestPath, manifest)
  console.log(`wrote samples.json — ${samples.length} samples, ${categories.length} categories`)
}
