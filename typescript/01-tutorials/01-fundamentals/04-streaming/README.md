# Streaming in Strands Agents

Strands Agents allows you to intercept and process events as they happen during agent execution using two methods:

1. **Async iterators**: ideal for asynchronous frameworks like Express. For these environments, the SDK offers the `stream()` method which returns an asynchronous iterator.
2. **Hooks**: allow you to intercept and process events as they happen during agent execution. This enables real-time monitoring, custom output formatting, and integration with external systems.

In this example, we will show you how to use both methods to handle calls on your agent.

## Agent Details

|Feature|Description|
|-------|-----------|
|Feature used|async iterators, hooks|
|Agent Structure|single agent architecture|
|Native tools used|calculator|
|Custom tools created|Weather forecast|


## Architecture
![Architecture](/architecture.png "Architecture")

## Project Structure

```
src/
├── async-sample-1.ts      # A simple async agent
├── async-sample-2.ts      # An agent that listens to events asynchronously
├── streaming-sample-1.ts  # A simple async agent served over HTTP
├── hooks-sample.ts        # A simple agent that listens to events via hooks
```

## Getting Started

### Prerequisites

- Node.js 20+
- AWS Bedrock access

### Installation

```bash
npm install
```

### Configuration

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

### Build

```bash
npm run build
```



## Method 1 - Async Iterators for Streaming
Strands Agents provides support for asynchronous iterators through the `stream()` method, enabling real-time streaming of agent responses in asynchronous environments like web servers, APIs, and other async applications.

### Async Sample 1

This first agent (async-sample-1.ts) logs all events emitted by the agent:

```typescript
// invoke the agent
const eventStream = agent.stream("Calculate 2+2");

for await (const event of eventStream) {
  console.log("Event: ", event.type);
}
```

Run your agent

```bash
AWS_REGION=us-east-1 npm run runAsync1
```

You should see output like:

```
Event:  beforeInvocationEvent
Event:  beforeModelEvent
Event:  modelMessageStartEvent
Event:  modelContentBlockDeltaEvent
...
Event:  afterModelEvent
Event:  afterInvocationEvent
```

### Async Sample 2 - Tracking event loop lifecycle

This example illustrates the event loop lifecycle and how events relate to each other. It's useful for understanding the flow of execution in the Strands Agent.

Let's create some printing format code to better analyse the agent stream events. We will continue to use the same agent for it.

```typescript
const processStreamingResponse = async (
  eventStream: AsyncGenerator<AgentStreamEvent, AgentResult, undefined>
) => {
  for await (const event of eventStream) {
    console.log("Event: ", event.type);

    if (event.type === "toolUseBlock") {
      console.log(`🔧 Using tool: ${event.name}, input: ${JSON.stringify(event.input)}`
      );
    } else if (event.type === "textBlock") {
      console.log(`📟 Text: ${event.text}`);
    }
  }
}
```

Run your agent

```bash
AWS_REGION=us-east-1 npm run runAsync2
```

You should see output like:

```
📟 Text: I can help you calculate 2+2 using the calculator function.
🔧 Using tool: calculator, input: {"operation":"add","a":2,"b":2}
📟 Text: The result of 2+2 is 4.
```

### Streaming Sample 2 - Express Integration

You can also integrate your stream_async with Express to create a streaming endpoint to your applications. For this, we will add a WeatherForecast tool to our agent. The architecture update looks as following:

![Architecture2](/architecture2.png "Architecture2")

The code snippet below shows some how the asynchronous iterator from the invoking the `stream()` function can be fed into a HTTP response progressively:

```typescript
// simplified version below
app.post("/stream", async (req, res) => {
  res.setHeader("Content-Type", "text/plain");
  res.setHeader("Transfer-Encoding", "chunked");
  /// ...
  const agent = new Agent({
    model,
    tools: [weatherForecast],
    printer: false,
  });
  // ...
  const eventStream = agent.stream(input.prompt);
  for await (const ev of eventStream) {
    if (ev.type === "textBlock") {
      res.write(ev.text.toString());
    }
  }
  res.end();
});
```

Run your agent

```bash
AWS_REGION=us-east-1 npm run runStreaming 
```

You should see output like:

```
✅ Server is running at http://127.0.0.1:8001
```

To test the server, open another terminal and issue a HTTP request and observe the result:

```bash
curl -X POST --no-buffer -H "Content-Type: application/json" -d '{"prompt": "What is weather in NYC?"}' http://127.0.0.1:8001/stream
```
```
I'll check the weather forecast for New York City for you.Good news! The weather forecast for NYC for the next 3 days shows clear skies with a temperature of 25 degrees.
```

Notice how the output is produced progressively as the Agent (and in particular the Bedrock model) generates it.
