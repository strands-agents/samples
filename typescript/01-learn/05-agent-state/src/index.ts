import * as readline from 'readline';
import { createAgent } from './agent.js';
import { database } from './database.js';

const userId = process.argv[2] || 'user-123';
const agent = createAgent(userId);

async function chat() {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  console.log(`Shopping Assistant Ready for ${userId}! (type "exit" to quit)`);
  console.log(`Loaded ${agent.messages.length} previous messages from DB\n`);

  // Reading lines with for-await ends cleanly when input closes (Ctrl+D or piped input).
  process.stdout.write('You: ');
  for await (const input of rl) {
    if (input.trim().toLowerCase() === 'exit') {
      break;
    }
    const result = await agent.invoke(input);
    console.log(`\nAssistant: ${result.toString()}\n`);
    process.stdout.write('You: ');
  }

  console.log('\n[Final State]', agent.appState.getAll());
  console.log('[Final Cart]', database.getCart(userId));
  console.log(`[DB] Total messages saved: ${database.getMessages(userId).length}`);
  rl.close();
}

chat().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
