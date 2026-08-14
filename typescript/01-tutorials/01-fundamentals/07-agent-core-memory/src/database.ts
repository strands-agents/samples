import { readFileSync, writeFileSync, existsSync } from 'fs';

const DB_FILE = './database.json';

export type Product = {
  id: string;
  name: string;
  price: number;
  stock: number;
}

export type CartItem = {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

type DatabaseData = {
  carts: Record<string, CartItem[]>;
}

class Database {
  products: Record<string, Product> = {
    'laptop': { id: 'prod-1', name: 'Laptop', price: 999, stock: 10 },
    'mouse': { id: 'prod-2', name: 'Mouse', price: 29, stock: 50 },
    'keyboard': { id: 'prod-3', name: 'Keyboard', price: 79, stock: 30 },
    'monitor': { id: 'prod-4', name: 'Monitor', price: 299, stock: 15 },
    'headphones': { id: 'prod-5', name: 'Headphones', price: 149, stock: 25 }
  };

  private data: DatabaseData;

  constructor() {
    this.data = this.load();
  }

  private load(): DatabaseData {
    if (existsSync(DB_FILE)) {
      try {
        return JSON.parse(readFileSync(DB_FILE, 'utf-8'));
      } catch {}
    }
    return { carts: {} };
  }

  private save() {
    writeFileSync(DB_FILE, JSON.stringify(this.data, null, 2));
  }

  getCart(userId: string): CartItem[] {
    return this.data.carts[userId] || [];
  }

  setCart(userId: string, cart: CartItem[]) {
    this.data.carts[userId] = cart;
    this.save();
  }
}

export const database = new Database();
