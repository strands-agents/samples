import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const GENERATOR = fileURLToPath(new URL('./generate-samples-manifest.mjs', import.meta.url))
const SAMPLE_ID = 'python/01-learn/01-example'

async function writeCatalog(root, samples, collections = []) {
  await writeFile(
    path.join(root, 'samples-catalog.json'),
    `${JSON.stringify({ version: 1, collections, samples }, null, 2)}\n`
  )
}

async function createFixture(
  t,
  {
    description,
    notebooks = [],
    readme = true,
    metadata = { placement: 'reference', kind: 'concept' },
    collections = [],
  }
) {
  const root = await mkdtemp(path.join(tmpdir(), 'samples-manifest-'))
  t.after(() => rm(root, { recursive: true, force: true }))

  const categoryDir = path.join(root, 'python', '01-learn')
  const sampleDir = path.join(categoryDir, '01-example')
  await mkdir(sampleDir, { recursive: true })
  await mkdir(path.join(root, 'typescript'), { recursive: true })

  await writeFile(
    path.join(categoryDir, 'README.md'),
    `# Learn\n\n| Sample | Description |\n| --- | --- |\n| [Example](./01-example/) | ${description} |\n`
  )
  if (readme) {
    await writeFile(path.join(sampleDir, 'README.md'), '# Example\n\nFallback description.\n')
  }
  for (const notebook of notebooks) {
    await writeFile(path.join(sampleDir, notebook), '{}\n')
  }
  await writeCatalog(root, { [SAMPLE_ID]: metadata }, collections)

  return root
}

function runGenerator(root, ...args) {
  return spawnSync(process.execPath, [GENERATOR, ...args], {
    cwd: root,
    encoding: 'utf8',
  })
}

test('preserves inline code while cleaning Markdown and HTML', async (t) => {
  const root = await createFixture(t, {
    description:
      'Use `foo_bar` in `<workspace>`; calculate `a*b`; read [docs](https://example.com); keep **bold**, _emphasis_, and <strong>HTML</strong>.',
  })

  const result = runGenerator(root)
  assert.equal(result.status, 0, result.stderr)

  const manifest = JSON.parse(await readFile(path.join(root, 'samples.json'), 'utf8'))
  assert.equal(
    manifest.samples[0].description,
    'Use foo_bar in <workspace>; calculate a*b; read docs; keep bold, emphasis, and HTML.'
  )
  assert.equal(manifest.samples[0].slug, 'python/example')
  assert.equal(manifest.samples[0].placement, 'reference')
  assert.equal(manifest.samples[0].kind, 'concept')
})

test('truncates descriptions at a word boundary', async (t) => {
  const root = await createFixture(t, {
    description: Array.from({ length: 80 }, (_, index) => `word${index}`).join(' '),
  })

  const result = runGenerator(root)
  assert.equal(result.status, 0, result.stderr)

  const manifest = JSON.parse(await readFile(path.join(root, 'samples.json'), 'utf8'))
  const description = manifest.samples[0].description
  assert.ok(description.length <= 240)
  assert.match(description, /…$/)
  assert.doesNotMatch(description, /\s…$/)
})

test('rejects multiple notebooks without a root README', async (t) => {
  const root = await createFixture(t, {
    description: 'A multi-part notebook sample',
    notebooks: ['01-introduction.ipynb', '02-advanced.ipynb'],
    readme: false,
  })

  const result = runGenerator(root)
  assert.notEqual(result.status, 0)
  assert.match(result.stderr, /python\/01-learn\/01-example/)
  assert.match(result.stderr, /multiple notebooks but no root README\.md to index them/)
  await assert.rejects(readFile(path.join(root, 'samples.json'), 'utf8'), { code: 'ENOENT' })
})

test('allows nested notebooks folded into a README-bearing sample', async (t) => {
  const root = await createFixture(t, {
    description: 'A sample with supporting notebooks',
  })
  const notebooksDir = path.join(root, 'python', '01-learn', '01-example', 'notebooks')
  await mkdir(notebooksDir)
  await writeFile(path.join(notebooksDir, '01-introduction.ipynb'), '{}\n')
  await writeFile(path.join(notebooksDir, '02-advanced.ipynb'), '{}\n')

  const result = runGenerator(root)
  assert.equal(result.status, 0, result.stderr)

  const manifest = JSON.parse(await readFile(path.join(root, 'samples.json'), 'utf8'))
  assert.deepEqual(
    manifest.samples.map((sample) => sample.path),
    [SAMPLE_ID]
  )
})

test('merges ordered collections and optional editorial metadata', async (t) => {
  const root = await createFixture(t, {
    description: 'A complete application',
    metadata: {
      placement: 'featured',
      kind: 'application',
      family: 'example-family',
      capabilities: ['tools', 'streaming'],
      docs: [{ label: 'Tools', url: 'https://example.com/docs/tools' }],
      program: 'amplifying-ai',
      maturity: 'candidate',
      owner: 'sample-team',
      lastValidated: '2026-11-05',
    },
    collections: [
      {
        id: 'featured',
        label: 'Featured',
        description: 'Complete applications',
        samples: [SAMPLE_ID],
      },
    ],
  })

  const result = runGenerator(root)
  assert.equal(result.status, 0, result.stderr)

  const manifest = JSON.parse(await readFile(path.join(root, 'samples.json'), 'utf8'))
  assert.deepEqual(manifest.collections, [
    {
      id: 'featured',
      label: 'Featured',
      description: 'Complete applications',
      samples: [SAMPLE_ID],
    },
  ])
  assert.deepEqual(
    {
      placement: manifest.samples[0].placement,
      kind: manifest.samples[0].kind,
      family: manifest.samples[0].family,
      collections: manifest.samples[0].collections,
      capabilities: manifest.samples[0].capabilities,
      docs: manifest.samples[0].docs,
      program: manifest.samples[0].program,
      maturity: manifest.samples[0].maturity,
      owner: manifest.samples[0].owner,
      lastValidated: manifest.samples[0].lastValidated,
    },
    {
      placement: 'featured',
      kind: 'application',
      family: 'example-family',
      collections: ['featured'],
      capabilities: ['tools', 'streaming'],
      docs: [{ label: 'Tools', url: 'https://example.com/docs/tools' }],
      program: 'amplifying-ai',
      maturity: 'candidate',
      owner: 'sample-team',
      lastValidated: '2026-11-05',
    }
  )
})

test('rejects a discovered sample without explicit catalog metadata', async (t) => {
  const root = await createFixture(t, { description: 'First sample' })
  const unclassifiedDir = path.join(root, 'python', '01-learn', '02-unclassified')
  await mkdir(unclassifiedDir)
  await writeFile(path.join(unclassifiedDir, 'README.md'), '# Unclassified\n\nA new sample.\n')

  const result = runGenerator(root)
  assert.notEqual(result.status, 0)
  assert.match(result.stderr, /samples-catalog\.json is missing metadata for/)
  assert.match(result.stderr, /python\/01-learn\/02-unclassified/)
})

test('rejects repo-only samples in website collections', async (t) => {
  const root = await createFixture(t, {
    description: 'Repository-only source',
    metadata: { placement: 'repo-only', kind: 'concept' },
    collections: [{ id: 'featured', label: 'Featured', samples: [SAMPLE_ID] }],
  })

  const result = runGenerator(root)
  assert.notEqual(result.status, 0)
  assert.match(result.stderr, /repo-only but belongs to a website collection/)
})

test('requires capabilities and documentation links for featured samples', async (t) => {
  const root = await createFixture(t, {
    description: 'Featured application',
    metadata: { placement: 'featured', kind: 'application' },
    collections: [{ id: 'featured', label: 'Featured', samples: [SAMPLE_ID] }],
  })

  let result = runGenerator(root)
  assert.notEqual(result.status, 0)
  assert.match(result.stderr, /featured but has no capabilities/)

  await writeCatalog(
    root,
    {
      [SAMPLE_ID]: {
        placement: 'featured',
        kind: 'application',
        capabilities: ['tools'],
      },
    },
    [{ id: 'featured', label: 'Featured', samples: [SAMPLE_ID] }]
  )
  result = runGenerator(root)
  assert.notEqual(result.status, 0)
  assert.match(result.stderr, /featured but has no documentation links/)
})

test('requires secure documentation links', async (t) => {
  const root = await createFixture(t, {
    description: 'Application documentation',
    metadata: {
      placement: 'reference',
      kind: 'application',
      docs: [{ label: 'Documentation', url: 'http://example.com/docs' }],
    },
  })

  const result = runGenerator(root)
  assert.notEqual(result.status, 0)
  assert.match(result.stderr, /docs\[0\]\.url must use https/)
})

test('discovers documented migration samples outside numbered categories', async (t) => {
  const root = await createFixture(t, { description: 'A concept sample' })
  const migrationDir = path.join(root, 'python', 'migration', 'langgraph')
  await mkdir(migrationDir, { recursive: true })
  await writeFile(
    path.join(migrationDir, 'README.md'),
    '# LangGraph Migration\n\nCompare an application before and after migration.\n'
  )
  await writeCatalog(root, {
    [SAMPLE_ID]: { placement: 'reference', kind: 'concept' },
    'python/migration/langgraph': { placement: 'reference', kind: 'migration' },
  })

  const result = runGenerator(root)
  assert.equal(result.status, 0, result.stderr)

  const manifest = JSON.parse(await readFile(path.join(root, 'samples.json'), 'utf8'))
  const migration = manifest.samples.find((sample) => sample.id === 'python/migration/langgraph')
  assert.equal(migration.category, 'migration')
  assert.equal(migration.categoryLabel, 'Migration')
  assert.equal(migration.slug, 'python/migration/langgraph')
  assert.equal(migration.kind, 'migration')
})

test('rejects catalog references to unknown variants', async (t) => {
  const root = await createFixture(t, {
    description: 'A concept sample',
    metadata: {
      placement: 'reference',
      kind: 'concept',
      variants: ['typescript/03-ux-demos/missing'],
    },
  })

  const result = runGenerator(root)
  assert.notEqual(result.status, 0)
  assert.match(result.stderr, /variants references unknown sample/)
})

test('requires variants to share a family and reference each other', async (t) => {
  const root = await createFixture(t, { description: 'A concept sample' })
  const variantId = 'python/01-learn/02-variant'
  const variantDir = path.join(root, variantId)
  await mkdir(variantDir)
  await writeFile(path.join(variantDir, 'README.md'), '# Variant\n\nA language variant.\n')
  await writeCatalog(root, {
    [SAMPLE_ID]: {
      placement: 'reference',
      kind: 'application',
      family: 'example-family',
      variants: [variantId],
    },
    [variantId]: {
      placement: 'reference',
      kind: 'application',
      family: 'example-family',
    },
  })

  const result = runGenerator(root)
  assert.notEqual(result.status, 0)
  assert.match(result.stderr, /must reference each other/)
})
