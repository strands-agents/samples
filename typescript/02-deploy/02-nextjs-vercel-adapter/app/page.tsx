"use client";

/**
 * Chat client — owned by the Vercel AI SDK.
 *
 * `useChat` manages the conversation state and streams responses from
 * `/api/chat`, where Strands runs the agent loop. We keep this deliberately
 * minimal (create-next-app-shaped) so it's easy to restyle.
 */
import { useState } from "react";
import Image from "next/image";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport, type UIMessage } from "ai";

// A stable id lets the server persist this conversation across requests.
const CHAT_ID = "demo-conversation";

export default function Home() {
  const [input, setInput] = useState("");
  const { messages, sendMessage, status, error, stop } = useChat({
    id: CHAT_ID,
    transport: new DefaultChatTransport({ api: "/api/chat" }),
  });

  const isBusy = status === "submitted" || status === "streaming";

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || isBusy) return;
    sendMessage({ text });
    setInput("");
  }

  return (
    <main className="mx-auto flex h-dvh w-full max-w-2xl flex-col px-4">
      <header className="border-b border-black/10 py-4 dark:border-white/10">
        <div className="flex items-center gap-3">
          <Image
            src="/strands-wordmark.png"
            alt="Strands"
            width={140}
            height={20}
            priority
            className="h-5 w-auto"
          />
          <span className="text-lg opacity-30">×</span>
          <Image
            src="/vercel-logo.svg"
            alt="Vercel"
            width={110}
            height={25}
            priority
            className="h-5 w-auto"
          />
        </div>
        <p className="mt-3 text-sm opacity-70">
          Next.js template — the AI SDK owns the client &amp; providers; Strands
          runs the loop, tools, sessions &amp; hooks via the VercelModel adapter.
        </p>
      </header>

      <section className="flex-1 space-y-4 overflow-y-auto py-6">
        {messages.length === 0 && (
          <p className="text-sm opacity-60">
            Ask something. Try &quot;what is 128 divided by 4?&quot; or
            &quot;what time is it in America/Mexico_City?&quot; to see tool calls.
          </p>
        )}

        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {error && (
          <p className="rounded-md bg-red-500/10 p-3 text-sm text-red-600 dark:text-red-400">
            {error.message}
          </p>
        )}
      </section>

      <form
        onSubmit={handleSubmit}
        className="flex gap-2 border-t border-black/10 py-4 dark:border-white/10"
      >
        <input
          className="flex-1 rounded-md border border-black/15 bg-transparent px-3 py-2 text-sm outline-none focus:border-black/40 dark:border-white/20 dark:focus:border-white/50"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Send a message…"
          disabled={isBusy}
        />
        {isBusy ? (
          <button
            type="button"
            onClick={stop}
            className="rounded-md bg-black px-4 py-2 text-sm font-medium text-white dark:bg-white dark:text-black"
          >
            Stop
          </button>
        ) : (
          <button
            type="submit"
            disabled={!input.trim()}
            className="rounded-md bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-40 dark:bg-white dark:text-black"
          >
            Send
          </button>
        )}
      </form>
    </main>
  );
}

function MessageBubble({ message }: { message: UIMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={isUser ? "text-right" : "text-left"}>
      <div
        className={`inline-block max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm ${
          isUser
            ? "bg-black text-white dark:bg-white dark:text-black"
            : "bg-black/5 dark:bg-white/10"
        }`}
      >
        {message.parts.map((part, i) => {
          if (part.type === "text") {
            return <span key={i}>{part.text}</span>;
          }
          // Tool activity surfaces as dynamic-tool or tool-<name> parts.
          if (part.type === "dynamic-tool" || part.type.startsWith("tool-")) {
            const toolPart = part as {
              type: string;
              toolName?: string;
              state?: string;
              input?: unknown;
              output?: unknown;
            };
            const name =
              toolPart.toolName ?? part.type.replace(/^tool-/, "");
            return (
              <div
                key={i}
                className="my-1 rounded-md border border-black/10 bg-black/5 p-2 font-mono text-xs dark:border-white/10 dark:bg-white/5"
              >
                <div className="opacity-70">🔧 {name}</div>
                {toolPart.input != null && (
                  <div>input: {JSON.stringify(toolPart.input)}</div>
                )}
                {toolPart.output != null && (
                  <div>output: {JSON.stringify(toolPart.output)}</div>
                )}
              </div>
            );
          }
          return null;
        })}
      </div>
    </div>
  );
}
