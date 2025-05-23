// src/todo.ts

export interface Todo {
  id: number;
  task: string;
  completed: boolean;
}

export class TodoList {
  private todos: Todo[] = [];
  private nextId: number = 1;

  add(task: string): Todo {
    const todo: Todo = { id: this.nextId++, task, completed: false };
    this.todos.push(todo);
    return todo;
  }

  toggle(id: number): void {
    const todo = this.todos.find(t => t.id === id);
    if (todo) {
      todo.completed = !todo.completed;
    }
  }

  getAll(): Todo[] {
    return this.todos;
  }
} 
