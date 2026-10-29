import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const GENERATOR = fileURLToPath(new URL('./generate-samples-manifest.mjs', import.meta.url))

async function createFixture(t, { description, notebooks = [], readme = true }) {
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
    ['python/01-learn/01-example']
  )
})
