import * as readline from 'readline';
import { createAgent } from './agent.js';


const provider = process.argv[2] || 'bedrock'
const agent = createAgent(provider)

async function chat() {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  console.log(`Time & Weather Assistant ready! (type "exit" to quit)`);

  const question = (prompt: string): Promise<string> => 
    new Promise((resolve) => rl.question(prompt, resolve));

  while (true) {
    const input = await question('You: ');
    if (input.toLowerCase() === 'exit') {
      rl.close();
      break;
    }
    const result = await agent.invoke(input);
    console.log(`\nAssistant: ${result.toString()}\n`);
  }
}

chat();

