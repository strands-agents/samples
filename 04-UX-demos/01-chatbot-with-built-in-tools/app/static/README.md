# Chatbot Frontend

This is a simple frontend for interacting with the Strands Agent Service. It provides a user interface for sending messages to the chatbot and displaying responses.

## Features

- Chat interface for interacting with the agent
- User ID management to maintain sessions
- Display of response metrics (latency and token usage)
- Responsive design

## Setup

1. Make sure the backend server is running (default: http://localhost:8003)
2. Open the frontend in a web browser

## Usage

1. Enter a User ID to maintain your session across page reloads
2. Type your message in the input box and press Enter or click Send
3. View the agent's response and performance metrics

## Files

- `index.html` - Main HTML structure
- `styles.css` - CSS styling for the interface
- `app.js` - JavaScript for handling user interactions and API calls