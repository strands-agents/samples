/** Serves the web client and a single chat endpoint. */
import { fileURLToPath } from "node:url";
import express from "express";
import { Chat } from "./agent.js";

const app = express();
const chats = new Map<string, Chat>();

app.use(express.json());

app.post("/api/chat", async (req, res) => {
  const { chat, message } = req.body ?? {};
  if (typeof chat !== "string" || typeof message !== "string") {
    res.status(400).json({ error: "Expected { chat: string, message: string }" });
    return;
  }
  if (!chats.has(chat)) chats.set(chat, new Chat());
  try {
    res.json(await chats.get(chat)!.send(message));
  } catch (error) {
    // A failed turn can leave the conversation history incomplete, so start this chat over.
    chats.delete(chat);
    console.error(error);
    res.status(500).json({ error: "The agent hit an error, so this conversation was reset. Please try again." });
  }
});

app.use(express.static(fileURLToPath(new URL("../web", import.meta.url))));

const port = Number(process.env.PORT ?? 8000);
// Local demo with no authentication, so it only listens on loopback.
app.listen(port, "127.0.0.1", () => console.log(`Open http://127.0.0.1:${port}`));
