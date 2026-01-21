import { Agent, tool, MessageAddedEvent, BeforeToolCallEvent, AfterToolCallEvent } from '@strands-agents/sdk';
import { z } from 'zod';
import { database, type Preferences } from './database.js';

// Tools
const viewCatalog = tool({
  name: 'view_catalog',
  description: 'Shows all available products in the catalog',
  inputSchema: z.object({ _: z.string().optional() }),
  callback: (input) => {
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

const updatePreferences = tool({
  name: 'update_preferences',
  description: 'Updates user preferences',
  inputSchema: z.object({
    paymentMethod: z.string().optional(),
    currency: z.string().optional()
  }),
  callback: (input, context) => {
    const userId = context?.agent.state.get('userId') as string;
    const current = database.getPreferences(userId);
    const updated: Preferences = { ...current, ...input };
    database.savePreferences(userId, updated);
    context?.agent.state.set('preferences', updated);
    return { success: true, preferences: updated };
  }
});

const getPreferences = tool({
  name: 'get_preferences',
  description: 'Gets user preferences',
  inputSchema: z.object({ _: z.string().optional() }),
  callback: (input, context) => {
    const userId = context?.agent.state.get('userId') as string;
    const prefs = database.getPreferences(userId);
    return { preferences: prefs };
  }
});

export function createAgent(userId: string) {
  const savedMessages = database.getMessages(userId);
  const savedPreferences = database.getPreferences(userId);

  const agent = new Agent({
    tools: [viewCatalog, addToCart, viewCart, removeFromCart, updatePreferences, getPreferences],
    systemPrompt: 'You are a shopping assistant. Help users manage their cart and preferences.',
    messages: savedMessages,
    printer: false,
    state: {
      userId,
      preferences: savedPreferences,
      sessionStarted: new Date().toISOString()
    }
  });

  agent.hooks.addCallback(MessageAddedEvent, (event) => {
    const userId = event.agent.state.get('userId') as string;
    database.saveMessage(userId, event.message);
  });

  agent.hooks.addCallback(BeforeToolCallEvent, (event) => {
    console.log(`🛠️ TOOL USE: ${event.toolUse.name}`, event.toolUse.input);
  });

  agent.hooks.addCallback(AfterToolCallEvent, (event) => {
    console.log(`🛠️ TOOL RESULT: ${event.toolUse.name}`, JSON.stringify(event.result.content[0], null, 2));
  });

  return agent;
}
