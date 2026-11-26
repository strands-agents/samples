import { BedrockAgentCoreClient, CreateEventCommand, ListEventsCommand, RetrieveMemoryRecordsCommand } from "@aws-sdk/client-bedrock-agentcore";

const client = new BedrockAgentCoreClient({ region: process.env.AWS_REGION || 'us-east-1' });

export const MEMORY_ID = process.env.MEMORY_ID || 'strands_js_memory';
export const PREFERENCE_STRATEGY_ID = process.env.PREFERENCE_STRATEGY_ID || 'preference_builtin';
export const SUMMARY_STRATEGY_ID = process.env.SUMMARY_STRATEGY_ID || 'summary_builtin';
export const STM_TURNS = parseInt(process.env.STM_TURNS || '3');

export const createEvent = async (text: string, role: 'ASSISTANT' | 'USER', actorId: string, sessionId: string) => {
  const command = new CreateEventCommand({
    memoryId: MEMORY_ID,
    actorId,
    sessionId,
    eventTimestamp: new Date(),
    payload: [{
      conversational: {
        content: { text },
        role,
      }
    }]
  });
  await client.send(command);
};

export const loadEvents = async (actorId: string, sessionId: string) => {
  const command = new ListEventsCommand({
    memoryId: MEMORY_ID,
    actorId,
    sessionId,
    maxResults: STM_TURNS * 2,
  });
  const result = await client.send(command);
  const messages = result.events?.sort((a, b) => 
    (a.eventTimestamp?.getTime() || 0) - (b.eventTimestamp?.getTime() || 0)
  ).map(e => {
    const message = e.payload![0].conversational!;
    return {
      type: 'message' as const,
      role: (message.role === 'ASSISTANT' ? 'assistant' : 'user') as 'user' | 'assistant',
      content: [{ type: "textBlock" as const, text: message.content!.text! }]
    };
  }) || [];

  console.log(`Loaded ${messages.length} messages (${STM_TURNS} turns)`);
  return messages;
};

export const retrieveConversationSummary = async (actorId: string, sessionId: string) => {
  const command = new RetrieveMemoryRecordsCommand({
    memoryId: MEMORY_ID,
    namespace: `/strategies/${SUMMARY_STRATEGY_ID}/actors/${actorId}/sessions/${sessionId}`,
    searchCriteria: {
      searchQuery: "conversation summary",
      topK: 5
    },
  });
  const result = await client.send(command);
  const summaries = result.memoryRecordSummaries?.map(sum => sum.content?.text).filter(Boolean) || [];
  return summaries.join('\n\n');
};

export const retrieveUserPreferences = async (q: string, actorId: string) => {
  const command = new RetrieveMemoryRecordsCommand({
    memoryId: MEMORY_ID,
    namespace: `/strategies/${PREFERENCE_STRATEGY_ID}/actors/${actorId}`,
    searchCriteria: {
      searchQuery: q,
      topK: 5
    },
  });
  const result = await client.send(command);
  return result.memoryRecordSummaries?.map(sum => sum.content?.text) || [];
};
