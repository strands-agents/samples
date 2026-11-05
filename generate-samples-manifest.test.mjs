import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const GENERATOR = fileURLToPath(new URL('./generate-samples-manifest.mjs', import.meta.url))
const SAMPLE_ID = 'python/01-learn/01-example'
const DOCS = [{ label: 'Documentation', url: 'https://example.com/docs' }]

async function writeCatalog(root, { samples = {}, collections = [] }) {
  await writeFile(
    path.join(root, 'samples-catalog.json'),
    `${JSON.stringify({ version: 1, collections, samples }, null, 2)}\n`
  )
}

async function addSample(root, sampleId, title = 'Variant') {
  const sampleDir = path.join(root, sampleId)
  await mkdir(sampleDir, { recursive: true })
  await writeFile(path.join(sampleDir, 'README.md'), `# ${title}\n\nA complete sample.\n`)
}

async function createFixture(
  t,
  { description, notebooks = [], readme = true, metadata, collections = [] }
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
  await writeCatalog(root, {
    samples: metadata ? { [SAMPLE_ID]: metadata } : {},
    collections,
  })

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
  assert.equal(manifest.catalog, 'curated')
  assert.equal(
    manifest.samples[0].description,
    'Use foo_bar in <workspace>; calculate a*b; read docs; keep bold, emphasis, and HTML.'
  )
  assert.equal(manifest.samples[0].slug, 'python/example')
  assert.equal('placement' in manifest.samples[0], false)
  assert.equal('kind' in manifest.samples[0], false)
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

test('merges ordered collections and website metadata', async (t) => {
  const root = await createFixture(t, {
    description: 'A complete application',
    metadata: {
      family: 'example-family',
      docs: [{ label: 'Tools', url: 'https://example.com/docs/tools' }],
    },
    collections: [
      {
        id: 'learn',
        label: 'Learn',
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
      id: 'learn',
      label: 'Learn',
      description: 'Complete applications',
      samples: [SAMPLE_ID],
    },
  ])
  assert.deepEqual(
    {
      family: manifest.samples[0].family,
      docs: manifest.samples[0].docs,
    },
    {
      family: 'example-family',
      docs: [{ label: 'Tools', url: 'https://example.com/docs/tools' }],
    }
  )
})

test('treats samples omitted from collections as unpublished', async (t) => {
  const root = await createFixture(t, { description: 'First sample' })
  const unpublishedId = 'python/01-learn/02-unpublished'
  await addSample(root, unpublishedId, 'Unpublished')

  const result = runGenerator(root)
  assert.equal(result.status, 0, result.stderr)

  const manifest = JSON.parse(await readFile(path.join(root, 'samples.json'), 'utf8'))
  assert.deepEqual(manifest.collections, [])
  assert.deepEqual(
    manifest.samples.map((sample) => sample.id),
    [SAMPLE_ID, unpublishedId]
  )
  assert.equal('repositoryOnly' in manifest, false)
})

test('requires published samples to belong to exactly one collection', async (t) => {
  const root = await createFixture(t, {
    description: 'Published application',
    metadata: { docs: DOCS },
    collections: [
      { id: 'learn', label: 'Learn', samples: [SAMPLE_ID] },
      { id: 'deploy', label: 'Deploy', samples: [SAMPLE_ID] },
    ],
  })

  const result = runGenerator(root)
  assert.notEqual(result.status, 0)
  assert.match(result.stderr, /belongs to more than one website collection/)
})

test('requires documentation links for published samples', async (t) => {
  const root = await createFixture(t, {
    description: 'Published application',
    collections: [{ id: 'learn', label: 'Learn', samples: [SAMPLE_ID] }],
  })

  let result = runGenerator(root)
  assert.notEqual(result.status, 0)
  assert.match(result.stderr, /missing website metadata/)

  await writeCatalog(root, {
    collections: [{ id: 'learn', label: 'Learn', samples: [SAMPLE_ID] }],
    samples: { [SAMPLE_ID]: {} },
  })
  result = runGenerator(root)
  assert.notEqual(result.status, 0)
  assert.match(result.stderr, /published but has no documentation links/)
})

test('requires secure documentation links', async (t) => {
  const root = await createFixture(t, {
    description: 'Application documentation',
    metadata: {
      docs: [{ label: 'Documentation', url: 'http://example.com/docs' }],
    },
    collections: [{ id: 'learn', label: 'Learn', samples: [SAMPLE_ID] }],
  })

  const result = runGenerator(root)
  assert.notEqual(result.status, 0)
  assert.match(result.stderr, /docs\[0\]\.url must use https/)
})

test('rejects catalog references that do not match published samples', async (t) => {
  const root = await createFixture(t, { description: 'A complete application' })
  const unknownId = 'python/01-learn/02-missing'
  const cases = [
    {
      catalog: {
        collections: [{ id: 'learn', label: 'Learn', samples: [unknownId] }],
      },
      message: /collection.*references unknown sample/i,
    },
    {
      catalog: { samples: { [unknownId]: { docs: DOCS } } },
      message: /references unknown samples/,
    },
    {
      catalog: { samples: { [SAMPLE_ID]: { docs: DOCS } } },
      message: /website metadata for unpublished samples/,
    },
  ]

  for (const { catalog, message } of cases) {
    await writeCatalog(root, catalog)
    const result = runGenerator(root)
    assert.notEqual(result.status, 0)
    assert.match(result.stderr, message)
  }
})

test('discovers documented migration samples outside numbered categories', async (t) => {
  const root = await createFixture(t, { description: 'A concept sample' })
  const migrationId = 'python/migration/langgraph'
  await addSample(root, migrationId, 'LangGraph Migration')

  const result = runGenerator(root)
  assert.equal(result.status, 0, result.stderr)

  const manifest = JSON.parse(await readFile(path.join(root, 'samples.json'), 'utf8'))
  const migration = manifest.samples.find((sample) => sample.id === migrationId)
  assert.equal(migration.category, 'migration')
  assert.equal(migration.categoryLabel, 'Migration')
  assert.equal(migration.slug, 'python/migration/langgraph')
})

test('rejects multiple published samples for one family and language', async (t) => {
  const root = await createFixture(t, { description: 'A complete application' })
  const secondId = 'python/01-learn/02-variant'
  await addSample(root, secondId)
  await writeCatalog(root, {
    collections: [{ id: 'learn', label: 'Learn', samples: [SAMPLE_ID, secondId] }],
    samples: {
      [SAMPLE_ID]: { family: 'example-family', docs: DOCS },
      [secondId]: { family: 'example-family', docs: DOCS },
    },
  })

  const result = runGenerator(root)
  assert.notEqual(result.status, 0)
  assert.match(result.stderr, /family example-family has more than one published python sample/)
})

test('requires a family to stay within one website collection', async (t) => {
  const root = await createFixture(t, { description: 'A complete application' })
  const typescriptId = 'typescript/01-learn/01-variant'
  await addSample(root, typescriptId)
  await writeCatalog(root, {
    collections: [
      { id: 'learn', label: 'Learn', samples: [SAMPLE_ID] },
      { id: 'deploy', label: 'Deploy', samples: [typescriptId] },
    ],
    samples: {
      [SAMPLE_ID]: { family: 'example-family', docs: DOCS },
      [typescriptId]: { family: 'example-family', docs: DOCS },
    },
  })

  const result = runGenerator(root)
  assert.notEqual(result.status, 0)
  assert.match(result.stderr, /family example-family spans multiple website collections/)
})
