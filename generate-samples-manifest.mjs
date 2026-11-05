// Generates samples.json: a machine-readable index of every sample in this
// repo so downstream consumers (e.g. the docs site) can render a styled,
// grouped, filterable catalog without scraping prose. samples-catalog.json is
// the hand-maintained editorial layer: collections explicitly publish and
// order website samples; every discovered sample omitted from them stays
// repository-only.
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
const CATALOG_PATH = path.join(ROOT, 'samples-catalog.json')
const SAMPLE_METADATA_KEYS = new Set(['family', 'docs'])

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
    langgraph: 'LangGraph',
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

// A category root is exactly `<lang>/<category>` — never a sample itself.
const isCategoryRoot = (relPath) => /^[a-z]+\/[^/]+$/.test(relPath)
const isCategoryDir = (name) => /^\d+[-_]/.test(name) || name === 'migration'

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
    .filter((entry) => entry.isDirectory() && isCategoryDir(entry.name))
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

// Keep the existing version 1 fields stable; the catalog mode and editorial
// fields are additive.
const baseSamples = selected
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
  const categoryDir = segments[1]
  const categorySegments = /^\d+[-_]/.test(categoryDir)
    ? []
    : [categoryDir.replace(/^\d+[-_]/, '')]
  return [
    segments[0],
    ...categorySegments,
    ...segments.slice(2).map((segment) => segment.replace(/^\d+[-_]/, '')),
  ].join('/')
}

function assertObject(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${label} must be an object`)
  }
}

function assertOnlyKeys(value, allowed, label) {
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) throw new Error(`${label} has unsupported field: ${key}`)
  }
}

function assertNonEmptyString(value, label) {
  if (typeof value !== 'string' || !value.trim()) throw new Error(`${label} must be a non-empty string`)
}

function validateStringArray(value, label) {
  if (!Array.isArray(value) || value.length === 0) {
    throw new Error(`${label} must be a non-empty array`)
  }
  const seenValues = new Set()
  for (const item of value) {
    assertNonEmptyString(item, `${label} entry`)
    if (seenValues.has(item)) throw new Error(`${label} contains duplicate value: ${item}`)
    seenValues.add(item)
  }
  return [...value]
}

function validateDocs(value, sampleId) {
  if (!Array.isArray(value) || value.length === 0) {
    throw new Error(`${sampleId}.docs must be a non-empty array`)
  }
  return value.map((doc, index) => {
    const label = `${sampleId}.docs[${index}]`
    assertObject(doc, label)
    assertOnlyKeys(doc, new Set(['label', 'url']), label)
    assertNonEmptyString(doc.label, `${label}.label`)
    assertNonEmptyString(doc.url, `${label}.url`)
    let url
    try {
      url = new URL(doc.url)
    } catch {
      throw new Error(`${label}.url must be an absolute URL`)
    }
    if (url.protocol !== 'https:') {
      throw new Error(`${label}.url must use https`)
    }
    return { label: doc.label, url: doc.url }
  })
}

function readCatalog() {
  if (!existsSync(CATALOG_PATH)) {
    throw new Error('samples-catalog.json is required to define website collections')
  }

  let catalog
  try {
    catalog = JSON.parse(readFileSync(CATALOG_PATH, 'utf8'))
  } catch (error) {
    throw new Error(`unable to parse samples-catalog.json: ${error.message}`)
  }
  assertObject(catalog, 'samples-catalog.json')
  assertOnlyKeys(catalog, new Set(['version', 'collections', 'samples']), 'samples-catalog.json')
  if (catalog.version !== 1) throw new Error('samples-catalog.json.version must be 1')
  if (!Array.isArray(catalog.collections)) throw new Error('samples-catalog.json.collections must be an array')
  assertObject(catalog.samples, 'samples-catalog.json.samples')
  return catalog
}

function validateCatalog(catalog, discoveredSamples) {
  const discoveredIds = new Set(discoveredSamples.map((sample) => sample.id))

  const collectionIds = new Set()
  const membership = new Map()
  const collections = catalog.collections.map((collection, index) => {
    const label = `samples-catalog.json.collections[${index}]`
    assertObject(collection, label)
    assertOnlyKeys(collection, new Set(['id', 'label', 'description', 'samples']), label)
    assertNonEmptyString(collection.id, `${label}.id`)
    if (!/^[a-z0-9][a-z0-9-]*$/.test(collection.id)) {
      throw new Error(`${label}.id must be a lowercase slug`)
    }
    if (collectionIds.has(collection.id)) throw new Error(`duplicate collection id: ${collection.id}`)
    collectionIds.add(collection.id)
    assertNonEmptyString(collection.label, `${label}.label`)
    if (collection.description !== undefined) {
      assertNonEmptyString(collection.description, `${label}.description`)
    }
    const sampleIds = validateStringArray(collection.samples, `${label}.samples`)
    for (const sampleId of sampleIds) {
      if (!discoveredIds.has(sampleId)) {
        throw new Error(`${label}.samples references unknown sample: ${sampleId}`)
      }
      if (membership.has(sampleId)) {
        throw new Error(`${sampleId} belongs to more than one website collection`)
      }
      membership.set(sampleId, collection.id)
    }
    return {
      id: collection.id,
      label: collection.label,
      ...(collection.description ? { description: collection.description } : {}),
      samples: sampleIds,
    }
  })

  const metadataIds = new Set(Object.keys(catalog.samples))
  const unknownMetadataIds = [...metadataIds].filter((sampleId) => !discoveredIds.has(sampleId))
  if (unknownMetadataIds.length > 0) {
    throw new Error(`samples-catalog.json references unknown samples: ${unknownMetadataIds.join(', ')}`)
  }
  const unpublishedMetadataIds = [...metadataIds].filter((sampleId) => !membership.has(sampleId))
  if (unpublishedMetadataIds.length > 0) {
    throw new Error(
      `samples-catalog.json defines website metadata for unpublished samples: ${unpublishedMetadataIds.join(', ')}`
    )
  }
  const publishedIds = [...membership.keys()]
  const missingMetadataIds = publishedIds.filter((sampleId) => !metadataIds.has(sampleId))
  if (missingMetadataIds.length > 0) {
    throw new Error(`samples-catalog.json is missing website metadata for: ${missingMetadataIds.join(', ')}`)
  }

  const metadata = new Map()
  for (const sampleId of publishedIds) {
    const sampleMetadata = catalog.samples[sampleId]
    const label = `samples-catalog.json.samples[${JSON.stringify(sampleId)}]`
    assertObject(sampleMetadata, label)
    assertOnlyKeys(sampleMetadata, SAMPLE_METADATA_KEYS, label)
    const editorial = {}
    if (sampleMetadata.family !== undefined) {
      assertNonEmptyString(sampleMetadata.family, `${sampleId}.family`)
      if (!/^[a-z0-9][a-z0-9-]*$/.test(sampleMetadata.family)) {
        throw new Error(`${sampleId}.family must be a lowercase slug`)
      }
      editorial.family = sampleMetadata.family
    }
    if (sampleMetadata.docs === undefined) {
      throw new Error(`${sampleId} is published but has no documentation links`)
    }
    editorial.docs = validateDocs(sampleMetadata.docs, sampleId)
    metadata.set(sampleId, editorial)
  }

  const samplesById = new Map(discoveredSamples.map((sample) => [sample.id, sample]))
  const families = new Map()
  for (const [sampleId, editorial] of metadata) {
    if (!editorial.family) continue
    const collectionId = membership.get(sampleId)
    const language = samplesById.get(sampleId).language
    const family = families.get(editorial.family)
    if (!family) {
      families.set(editorial.family, { collectionId, languages: new Set([language]) })
      continue
    }
    if (family.collectionId !== collectionId) {
      throw new Error(`family ${editorial.family} spans multiple website collections`)
    }
    if (family.languages.has(language)) {
      throw new Error(`family ${editorial.family} has more than one published ${language} sample`)
    }
    family.languages.add(language)
  }

  return { collections, metadata }
}

const catalog = readCatalog()
const { collections, metadata } = validateCatalog(catalog, baseSamples)
const samples = baseSamples.map((sample) => ({
  ...sample,
  slug: deriveSlug(sample),
  ...(metadata.get(sample.id) ?? {}),
}))

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

    const slug = sample.slug
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
const manifest =
  JSON.stringify({ version: 1, catalog: 'curated', categories, collections, samples }, null, 2) + '\n'

if (process.argv.includes('--check')) {
  const current = existsSync(manifestPath) ? readFileSync(manifestPath, 'utf8') : ''
  if (current !== manifest) {
    console.error('samples.json is out of date; run node generate-samples-manifest.mjs')
    process.exitCode = 1
  } else {
    console.log(
      `samples.json is current — ${samples.length} samples, ${categories.length} categories, ${collections.length} collections`
    )
  }
} else {
  writeFileSync(manifestPath, manifest)
  console.log(
    `wrote samples.json — ${samples.length} samples, ${categories.length} categories, ${collections.length} collections`
  )
}
