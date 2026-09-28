import { Agent, tool, MessageAddedEvent, BeforeToolCallEvent, AfterToolCallEvent } from '@strands-agents/sdk';
import { z } from 'zod';
import { database } from './database.js';
import { createEvent, retrieveUserPreferences, loadEvents, retrieveConversationSummary } from './memory.js';

const userPreferenceTool = tool({
  name: 'userPreferenceTool',
  description: 'Lookup user preferences from long-term memory',
  inputSchema: z.object({
    q: z.string().describe('User preference question')
  }),
  callback: async ({ q }, context) => {
    const userId = context?.agent.state.get('userId') as string;
    const preferences = await retrieveUserPreferences(q, userId);
    console.log('\n****PREFERENCES_FROM_LTM****\n', JSON.stringify(preferences));
    return JSON.stringify(preferences);
  }
});

const viewCatalog = tool({
  name: 'view_catalog',
  description: 'Shows all available products in the catalog',
  inputSchema: z.object({ _: z.string().optional() }),
  callback: () => {
    const products = Object.values(database.products);
    return { products, totalProducts: products.length };
  }
});

const addToCart = tool({
  name: 'add_to_cart',
  description: 'Adds an item to the shopping cart',
  inputSchema: z.object({
    productName: z.string(),
    quantity: z.number().default(1)
  }),
  callback: (input, context) => {
    const userId = context?.agent.state.get('userId') as string;
    if (!userId) return { success: false, message: 'User not found', cart: null };

    const product = database.products[input.productName.toLowerCase()];
    if (!product) return { success: false, message: 'Product not found', cart: null };

    const cart = database.getCart(userId);
    const existing = cart.find(item => item.id === product.id);

    if (existing) {
      existing.quantity += input.quantity;
    } else {
      cart.push({ ...product, quantity: input.quantity });
    }

    database.setCart(userId, cart);
    return { success: true, message: `Added ${input.quantity}x ${product.name}`, cart: cart };
  }
});

const viewCart = tool({
  name: 'view_cart',
  description: 'Shows items in cart',
  inputSchema: z.object({ _: z.string().optional() }),
  callback: (input, context) => {
    const userId = context?.agent.state.get('userId') as string;
    if (!userId) return { cart: [], total: 0, itemCount: 0 };

    const cart = database.getCart(userId);
    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    return { cart, total, itemCount: cart.length };
  }
});

const removeFromCart = tool({
  name: 'remove_from_cart',
  description: 'Removes an item from cart',
  inputSchema: z.object({
    productName: z.string()
  }),
  callback: (input, context) => {
    const userId = context?.agent.state.get('userId') as string;
    if (!userId) return { success: false, message: 'User not found', cart: null };

    const cart = database.getCart(userId);
    const filtered = cart.filter(item => 
      item.name.toLowerCase() !== input.productName.toLowerCase()
    );

    database.setCart(userId, filtered);
    return { success: true, message: `Removed ${input.productName}`, cart: filtered };
  }
});

export async function createAgent(userId: string, sessionId: string) {
  console.log('Loading conversation history from agentcore...');
  const messages = await loadEvents(userId, sessionId);
  
  console.log('Retrieving conversation summary from LTM...');
  const summary = await retrieveConversationSummary(userId, sessionId);
  
  const basePrompt = 'You are a shopping assistant. Help users manage their cart. Lookup for user buying related preferences (currency, payment method, prefered delivery times, ...) when relevant.';
  const systemPrompt = summary 
    ? `${basePrompt}\n\nConversation summary:\n${summary}`
    : basePrompt;

  const agent = new Agent({
    tools: [viewCatalog, addToCart, viewCart, removeFromCart, userPreferenceTool],
    systemPrompt,
    messages,
    printer: false,
    state: {
      userId,
      sessionId,
      sessionStarted: new Date().toISOString()
    }
  });

  agent.hooks.addCallback(MessageAddedEvent, async (event) => {
    const userId = event.agent.state.get('userId') as string;
    const sessionId = event.agent.state.get('sessionId') as string;
    const textBlock = event.message.content.find((block: any) => 'text' in block && block.text);
    
    if (textBlock && 'text' in textBlock && textBlock.text) {
      const role = event.message.role === 'assistant' ? 'ASSISTANT' : 'USER';
      await createEvent(textBlock.text as string, role, userId, sessionId);
    }
  });

  return agent;
}
