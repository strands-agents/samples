import { Agent, tool } from '@strands-agents/sdk';
import { BedrockModel } from '@strands-agents/sdk';
import { OpenAIModel } from '@strands-agents/sdk/openai';
import { httpRequest } from '@strands-agents/sdk/vended_tools/http_request'
import { z } from 'zod';

const openaiModel = () => new OpenAIModel({
  modelId: 'gpt-4o',
  apiKey: process.env.OPEN_AI_API_KEY,
  temperature: 0.7,
  maxTokens: 1024
});

const bedrockModel = () => new BedrockModel({
  region: 'us-east-1',
  modelId: 'global.anthropic.claude-sonnet-4-5-20250929-v1:0',
  maxTokens: 1024,
  temperature: 0.7
});

const currentTime = tool({
  name: 'current_time',
  description: 'Shows current time in timezone',
  inputSchema: z.object({ timezone: z.string().describe('Timezone identifier according to TZ Database eg: Europe/Paris, America/Costa_Rica, ...') }),
  callback: (input) => {
    return new Date().toLocaleTimeString('en-US', { timeZone: input.timezone })
  }
});


export const createAgent = (provider: string) => {
  return new Agent({
    model: provider === 'openai' ? openaiModel() : bedrockModel(),
    tools: [currentTime, httpRequest],
    printer: false,
    systemPrompt: `
      You are a simple agent that can tell the time and the weather.
      In order to retrieve the current weather in a specific location, leverage the open-meteo api with the httpRequest tool using the following url: https://api.open-meteo.com/v1/forecast?latitude=LOCATION_LATITUDE&longitude=LOCATION_LONGITUDE&current_weather=true , replacing latitutude and longitude for given location.
      Always introduce you as a ${provider === 'openai' ? 'OpenAI' : 'Bedrock'} based assistant.`,
  })
}