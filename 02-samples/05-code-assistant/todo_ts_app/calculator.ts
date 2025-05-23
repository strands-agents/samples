// Define a Calculator class with basic arithmetic operations
class Calculator {
  // Method to add two numbers
  add(a: number, b: number): number {
    return a + b;
  }

  // Method to subtract b from a
  subtract(a: number, b: number): number {
    return a - b;
  }

  // Method to multiply two numbers
  multiply(a: number, b: number): number {
    return a * b;
  }

  // Method to divide a by b
  divide(a: number, b: number): number {
    if (b === 0) {
      throw new Error("Division by zero is not allowed");
    }
    return a / b;
  }

  // Method to calculate the remainder of a divided by b
  modulo(a: number, b: number): number {
    if (b === 0) {
      throw new Error("Modulo by zero is not allowed");
    }
    return a % b;
  }

  // Method to raise a to the power of b
  power(a: number, b: number): number {
    return Math.pow(a, b);
  }

  // Method to calculate the square root of a number
  squareRoot(a: number): number {
    if (a < 0) {
      throw new Error("Square root of negative number is not allowed");
    }
    return Math.sqrt(a);
  }
}

// Example usage
const calculator = new Calculator();

try {
  // Test the calculator methods
  console.log("Addition: 5 + 3 =", calculator.add(5, 3));
  console.log("Subtraction: 10 - 4 =", calculator.subtract(10, 4));
  console.log("Multiplication: 6 * 7 =", calculator.multiply(6, 7));
  console.log("Division: 15 / 3 =", calculator.divide(15, 3));
  console.log("Modulo: 17 % 5 =", calculator.modulo(17, 5));
  console.log("Power: 2 ^ 3 =", calculator.power(2, 3));
  console.log("Square Root of 16 =", calculator.squareRoot(16));
  
  // This will throw an error
  // console.log("Division by zero:", calculator.divide(10, 0));
} catch (error) {
  console.error("Error:", error.message);
}