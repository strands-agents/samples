/**
 * Case Triage in Strands, TypeScript (migration result)
 *
 * The TypeScript counterpart of `python/migration/langgraph/strands_after.py`,
 * and the "after" side of the Migrate from LangGraph guide. Same three stages, same
 * public entrypoint, same external ID.
 *
 *     npm install && npm run build
 *     node dist/index.js [case-5501]
 *
 * Needs AWS credentials with Bedrock access and AWS_REGION set. Set CASE_MODEL_ID
 * to pin a model.
 * Sessions go to `./cases/` in the working directory; delete it to start a case
 * over.
 */

import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { Agent, Graph, SessionManager, tool } from '@strands-agents/sdk'
import { LocalFileStorage } from '@strands-agents/sdk/storage'
import { z } from 'zod'

// Stand-in for the record system a real deployment would query.
const CASE_RECORDS: Record<string, string> = {
  'case-4127': [
    'Case case-4127 (tenant dispute, filed 2026-03-02)',
    'Summary: Tenant withheld two months rent citing an unrepaired heating system. Landlord filed for possession.',
    'Facts on file:',
    '- Heating fault first reported by tenant on 2025-11-14.',
    '- Landlord sent a contractor on 2025-12-20, 36 days later.',
    '- Tenant withheld rent for January and February 2026.',
    '- Local code requires habitable heat within 14 days of written notice.',
  ].join('\n'),
  'case-5501': [
    'Case case-5501 (deposit withholding, filed 2026-05-19)',
    'Summary: Landlord retained the full deposit for cleaning after a 14-month tenancy.',
    'Facts on file:',
    '- Move-out inspection recorded normal wear on carpets.',
    '- No itemized deduction statement was sent within the statutory 21 days.',
    '- Tenant provided dated move-out photographs.',
  ].join('\n'),
}

const PRECEDENTS: Array<{ topic: string; text: string }> = [
  {
    topic: 'repair delay rent withholding',
    text:
      'P-118: Rent withholding upheld where the landlord exceeded the statutory ' +
      'repair window after written notice.',
  },
  {
    topic: 'deposit itemization deadline',
    text:
      'P-204: Failure to send an itemized deduction statement within the statutory ' +
      'period forfeits the right to withhold.',
  },
  {
    topic: 'normal wear and tear',
    text:
      'P-077: Ordinary carpet wear over a tenancy of more than twelve months is not ' +
      'chargeable to the tenant.',
  },
]

const fetchCaseRecord = tool({
  name: 'fetch_case_record',
  description: 'Fetch the filed record for a case',
  inputSchema: z.object({
    caseId: z.string().describe('Identifier of the case to fetch'),
  }),
  callback: (input) =>
    CASE_RECORDS[input.caseId] ?? `No filed record exists for ${input.caseId}.`,
})

const searchPrecedent = tool({
  name: 'search_precedent',
  description: 'Search prior decisions for relevant precedent',
  inputSchema: z.object({
    question: z.string().describe('What to look for in prior decisions'),
  }),
  callback: (input) => {
    // Strip punctuation from each end only, matching the Python example.
    const words = new Set(
      input.question
        .toLowerCase()
        .split(/\s+/)
        .map((w) => w.replace(/^[.,;:?]+|[.,;:?]+$/g, '')),
    )
    const hits = PRECEDENTS.filter((p) => p.topic.split(' ').some((t) => words.has(t)))
    return (hits.length ? hits : PRECEDENTS).map((p) => p.text).join('\n')
  },
})

// Entrypoint: callers call runCase(caseId, prompt) exactly as before.
export async function runCase(
  caseId: string,
  prompt: string,
  options: { storageDir?: string; maxSteps?: number } = {},
) {
  const { storageDir = './cases/', maxSteps = 10 } = options
  // A string becomes a BedrockModel; undefined means the SDK default.
  const model = process.env.CASE_MODEL_ID

  const researcher = new Agent({
    id: 'research',
    systemPrompt: 'You gather the facts of the case.',
    tools: [fetchCaseRecord],
    model,
  })
  const analyst = new Agent({
    id: 'analysis',
    systemPrompt: 'You weigh the options.',
    tools: [searchPrecedent],
    model,
  })
  const reviewer = new Agent({
    id: 'review',
    systemPrompt: 'You recommend a decision.',
    model,
  })

  const graph = new Graph({
    nodes: [researcher, analyst, reviewer],
    edges: [
      ['research', 'analysis'],
      ['analysis', 'review'],
    ],
    sources: ['research'],
    // Caps node executions, not the tool loop inside each agent. Without a cap
    // or a timeout the SDK logs a warning.
    maxSteps,
    // External ID: caseId is the session id, so an interrupted graph resumes
    // from it on the next call.
    sessionManager: new SessionManager({
      sessionId: caseId,
      storage: new LocalFileStorage(storageDir),
    }),
  })

  // The case id has to reach the agents, so it travels in the task text.
  return graph.invoke(`Case ${caseId}: ${prompt}`)
}

async function main(): Promise<number> {
  const caseId = process.argv[2] ?? 'case-4127'
  const prompt = process.argv[3] ?? 'Assess the dispute and recommend a decision.'

  const result = await runCase(caseId, prompt)

  console.log(`\nCase:   ${caseId}`)
  console.log(`Status: ${result.status}`)
  console.log(`Order:  ${result.results.map((r) => r.nodeId).join(' -> ')}`)
  console.log(`Tokens: ${result.usage.totalTokens}`)

  const text = result.content.find((b) => b.type === 'textBlock')?.text
  console.log(`\nRecommendation:\n${text ?? '(none)'}`)
  return 0
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().then((code) => process.exit(code)).catch((err) => {
    console.error(err)
    process.exit(1)
  })
}
