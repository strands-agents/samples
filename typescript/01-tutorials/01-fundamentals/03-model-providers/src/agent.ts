import { Agent, tool } from '@strands-agents/sdk';
import { BedrockModel } from '@strands-agents/sdk';
import { OpenAIModel } from '@strands-agents/sdk/openai';
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

// Tools
const currentWeather = tool({
  name: 'current_weather',
  description: 'Shows current weather in specific city',
  inputSchema: z.object({ city: z.string() }),
  callback: (input) => {
    const weather = ['rainy', 'cloudy', 'sunny', 'foggy'];
    const random = weather[Math.floor(Math.random() * weather.length)];
    return random
  }
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
    tools: [currentTime, currentWeather],
    printer: false,
    systemPrompt: `You are a simple agent that can tell the time and the weather. Always introduce you as a ${provider === 'openai' ? 'OpenAI' : 'Bedrock'} based assistant.`,
  })
}