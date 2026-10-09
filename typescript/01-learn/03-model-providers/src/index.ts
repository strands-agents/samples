import * as readline from 'readline';
import { createAgent } from './agent.js';


const provider = process.argv[2] || 'bedrock'
const agent = createAgent(provider)

async function chat() {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  console.log(`Time & Weather Assistant ready! (type "exit" to quit)`);

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
  rl.close();
}

chat().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

