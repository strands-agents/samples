import * as readline from 'readline';
import { createAgent } from './agent.js';
import { database } from './database.js';

const userId = process.argv[2] || 'user-123';
const agent = createAgent(userId);

async function chat() {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  console.log(`Shopping Assistant Ready for ${userId}! (type "exit" to quit)`);
  console.log(`Loaded ${agent.messages.length} previous messages from DB\n`);

  const question = (prompt: string): Promise<string> => 
    new Promise((resolve) => rl.question(prompt, resolve));

  while (true) {
    const input = await question('You: ');
    if (input.toLowerCase() === 'exit') {
      console.log('\n[Final State]', agent.state.getAll());
      console.log('[Final Cart]', database.getCart(userId));
      console.log(`[DB] Total messages saved: ${database.getMessages(userId).length}`);
      rl.close();
      break;
    }
    const result = await agent.invoke(input);
    console.log(`\nAssistant: ${result.toString()}\n`);
  }
}

chat();
