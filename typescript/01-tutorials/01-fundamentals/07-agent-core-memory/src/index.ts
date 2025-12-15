import * as readline from 'readline';
import { createAgent } from './agent.js';
import { database } from './database.js';

const userId = process.argv[2] || 'USER_1';
const sessionId = process.argv[3] || `SESSION_${Date.now()}`;

async function chat() {
  const agent = await createAgent(userId, sessionId);

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  console.log(`Shopping Assistant Ready for ${userId}! (type "exit" to quit)\n`);

  const question = (prompt: string): Promise<string> => 
    new Promise((resolve) => rl.question(prompt, resolve));

  while (true) {
    const input = await question('You: ');
    if (input.toLowerCase() === 'exit') {
      console.log('\n[Final Cart]', database.getCart(userId));
      rl.close();
      break;
    }

    const result = await agent.invoke(input);
    const textBlock = result.lastMessage.content.find(block => 'text' in block);
    const text = textBlock && 'text' in textBlock ? textBlock.text : 'No response';
    console.log(`\nAssistant: ${text}\n`);
  }
}

chat();
