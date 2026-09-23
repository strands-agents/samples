/**
 * # Case Triage in LangGraph.js (migration starting point)
 *
 * The "before" side of the Migrate from LangGraph guide, in TypeScript. Compare
 * with the Strands result in `../strands-after/src/index.ts` and the Python
 * starting point in `python/migration/langgraph/langgraph_before.py`.
 *
 * The graph has five nodes for three stages, because in a `StateGraph` a tool
 * call is a node the graph routes to and back from.
 *
 * Each stage gets its own message window (`researchMessages` and so on). The
 * guide's inline snippet uses one `messages` key for brevity. LangGraph.js's
 * `ToolNode` reads the `messages` key only, so a small node hands it the
 * stage's window instead; Python's `ToolNode` takes a `messages_key` argument.
 *
 *     npm install && npm run build
 *     node dist/index.js [case-5501]
 *
 * Needs AWS credentials with Bedrock access. Set `CASE_MODEL_ID` to pin a model
 * and `CASE_DB` to move the SQLite file from `./cases.db`.
 * Delete that file to start a case over.
 */

import { ChatBedrockConverse, type ChatBedrockConverseToolType } from '@langchain/aws'
import {
  HumanMessage,
  SystemMessage,
  isToolMessage,
  type BaseMessage,
} from '@langchain/core/messages'
import { tool, type StructuredToolInterface } from '@langchain/core/tools'
import {
  END,
  MessagesValue,
  START,
  StateGraph,
  StateSchema,
  type GraphNode,
} from '@langchain/langgraph'
import { SqliteSaver } from '@langchain/langgraph-checkpoint-sqlite'
import { ToolNode, toolsCondition } from '@langchain/langgraph/prebuilt'
import { z } from 'zod'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const MODEL_ID = process.env.CASE_MODEL_ID ?? 'us.anthropic.claude-sonnet-4-5-20250929-v1:0'
const REGION = process.env.AWS_REGION ?? 'us-east-1'

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

const PRECEDENTS: Array<[string, string]> = [
  ['repair delay rent withholding',
    'P-118: Rent withholding upheld where the landlord exceeded the statutory repair window after written notice.'],
  ['deposit itemization deadline',
    'P-204: Failure to send an itemized deduction statement within the statutory period forfeits the right to withhold.'],
  ['normal wear and tear',
    'P-077: Ordinary carpet wear over a tenancy of more than twelve months is not chargeable to the tenant.'],
]

const fetchCaseRecord = tool(
  ({ caseId }) => CASE_RECORDS[caseId] ?? `No filed record exists for ${caseId}.`,
  {
    name: 'fetch_case_record',
    description: 'Fetch the filed record for a case.',
    schema: z.object({ caseId: z.string().describe('Identifier of the case to fetch') }),
  },
)

const searchPrecedent = tool(
  ({ question }) => {
    const words = new Set(
      question.split(/\s+/).map((w) => w.replace(/^[.,;:?]+|[.,;:?]+$/g, '').toLowerCase()),
    )
    const hits = PRECEDENTS
      .filter(([topic]) => topic.split(' ').some((t) => words.has(t)))
      .map(([, text]) => text)
    return (hits.length ? hits : PRECEDENTS.map(([, text]) => text)).join('\n')
  },
  {
    name: 'search_precedent',
    description: 'Search prior decisions for relevant precedent.',
    schema: z.object({ question: z.string().describe('What to look for in prior decisions') }),
  },
)

// One shared state object, as LangGraph expects. Each stage owns a message
// window; see the note in the file header.
const CaseState = new StateSchema({
  researchMessages: MessagesValue,
  analysisMessages: MessagesValue,
  reviewMessages: MessagesValue,
  caseId: z.string(),
  prompt: z.string(),
  researchText: z.string(),
  analysisText: z.string(),
  reviewText: z.string(),
})

type State = typeof CaseState.State
type Update = typeof CaseState.Update
type WindowKey = 'researchMessages' | 'analysisMessages' | 'reviewMessages'
type TextKey = 'researchText' | 'analysisText' | 'reviewText'

const llm = new ChatBedrockConverse({ model: MODEL_ID, region: REGION, temperature: 0 })

function model(tools?: ChatBedrockConverseToolType[]) {
  return tools ? llm.bindTools(tools) : llm
}

/**
 * Run one turn of a stage. A new call opens with a fresh human turn; a call that
 * follows a ToolMessage continues the tool loop instead.
 */
async function stage(
  state: State,
  key: WindowKey,
  system: string,
  opening: string,
  tools: ChatBedrockConverseToolType[] | undefined,
  field: TextKey,
): Promise<Update> {
  const history = state[key]
  const newMessages: BaseMessage[] = []
  if (!isToolMessage(history.at(-1))) {
    newMessages.push(new HumanMessage(opening))
  }
  const reply = await model(tools).invoke([new SystemMessage(system), ...history, ...newMessages])
  newMessages.push(reply)

  const update: Update = { [key]: newMessages }
  if (!reply.tool_calls?.length) {
    update[field] = reply.text
  }
  return update
}

const research: GraphNode<typeof CaseState> = (state) =>
  stage(state, 'researchMessages', 'You gather the facts of the case.',
    `Case ${state.caseId}: ${state.prompt}`, [fetchCaseRecord], 'researchText')

const analysis: GraphNode<typeof CaseState> = (state) =>
  stage(state, 'analysisMessages', 'You weigh the options.',
    `Facts of case ${state.caseId}:\n${state.researchText}\n\n${state.prompt}`, [searchPrecedent], 'analysisText')

const review: GraphNode<typeof CaseState> = (state) =>
  stage(state, 'reviewMessages', 'You recommend a decision.',
    `Analysis of case ${state.caseId}:\n${state.analysisText}\n\n${state.prompt}`, undefined, 'reviewText')

/** Run a ToolNode against one stage's window and write the results back to it. */
function toolStage(key: WindowKey, tools: StructuredToolInterface[]): GraphNode<typeof CaseState> {
  const node = new ToolNode(tools)
  // Only the window is passed, so tools that read other state fields would not see them.
  return async (state) => ({ [key]: await node.invoke(state[key]) })
}

/** Scope toolsCondition to one stage's message window. */
function route(key: WindowKey) {
  return (state: State) => toolsCondition(state[key])
}

/** Wire the five nodes and compile with a checkpointer. */
function buildGraph(dbPath: string) {
  const builder = new StateGraph(CaseState)
    .addNode('research', research)
    .addNode('research_tools', toolStage('researchMessages', [fetchCaseRecord]))
    .addNode('analysis', analysis)
    .addNode('analysis_tools', toolStage('analysisMessages', [searchPrecedent]))
    .addNode('review', review)
    .addEdge(START, 'research')
    .addConditionalEdges('research', route('researchMessages'), { tools: 'research_tools', [END]: 'analysis' })
    .addEdge('research_tools', 'research')
    .addConditionalEdges('analysis', route('analysisMessages'), { tools: 'analysis_tools', [END]: 'review' })
    .addEdge('analysis_tools', 'analysis')
    .addEdge('review', END)

  return builder.compile({ checkpointer: SqliteSaver.fromConnString(dbPath) })
}

// Entrypoint: callers call runCase(caseId, prompt), and that call does not
// change through the migration.
export async function runCase(
  caseId: string,
  prompt: string,
  options: { dbPath?: string; recursionLimit?: number } = {},
) {
  const graph = buildGraph(options.dbPath ?? 'cases.db')
  // External ID: caseId keys the conversation, and becomes the Strands session id.
  const config = { configurable: { thread_id: caseId }, recursionLimit: options.recursionLimit ?? 25 }
  return graph.invoke(
    {
      researchMessages: [], analysisMessages: [], reviewMessages: [],
      caseId, prompt, researchText: '', analysisText: '', reviewText: '',
    },
    config,
  )
}

async function main(): Promise<number> {
  const caseId = process.argv[2] ?? 'case-4127'
  const prompt = process.argv[3] ?? 'Assess the dispute and recommend a decision.'

  const result = await runCase(caseId, prompt, { dbPath: process.env.CASE_DB })

  const counts = {
    research: result.researchMessages.length,
    analysis: result.analysisMessages.length,
    review: result.reviewMessages.length,
  }
  console.log(`\nCase:     ${caseId}`)
  console.log(`Messages: ${JSON.stringify(counts)}`)
  console.log(`\nRecommendation:\n${result.reviewText}`)
  return 0
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().then((code) => process.exit(code)).catch((err) => {
    console.error(err)
    process.exit(1)
  })
}
