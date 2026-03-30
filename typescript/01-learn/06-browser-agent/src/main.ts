/**
 * Browser Agent - Running Strands Agents in the Browser
 *
 * This example demonstrates how to run a Strands Agent entirely in the browser
 * using the TypeScript SDK with Vite as the build tool.
 *
 * Supports both Amazon Bedrock and OpenAI as model providers.
 */

import { Agent, BedrockModel } from "@strands-agents/sdk";
import { OpenAIModel } from "@strands-agents/sdk/openai";
import { marked } from "marked";

// Agent instance (initialized after credentials are provided)
let agent: Agent | null = null;

// DOM Elements
const credentialsSection = document.getElementById("credentials-section")!;
const chatSection = document.getElementById("chat-section")!;
const credentialsForm = document.getElementById("credentials-form") as HTMLFormElement;
const messagesContainer = document.getElementById("messages")!;
const chatForm = document.getElementById("chat-form") as HTMLFormElement;
const inputField = document.getElementById("input") as HTMLInputElement;
const sendButton = document.getElementById("send") as HTMLButtonElement;

// Provider selection elements
const providerSelect = document.getElementById("provider") as HTMLSelectElement;
const bedrockFields = document.getElementById("bedrock-fields")!;
const openaiFields = document.getElementById("openai-fields")!;
const modelInfo = document.getElementById("model-info")!;

// Toggle credential fields based on provider selection
providerSelect.addEventListener("change", () => {
  const isOpenAI = providerSelect.value === "openai";
  bedrockFields.classList.toggle("hidden", isOpenAI);
  openaiFields.classList.toggle("hidden", !isOpenAI);
  modelInfo.textContent = isOpenAI ? "Using GPT-4o" : "Using Claude Sonnet 4";
});

// Handle credentials form submission
credentialsForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const provider = providerSelect.value;
  const connectButton = document.getElementById("connect") as HTMLButtonElement;
  connectButton.disabled = true;
  connectButton.textContent = "Connecting...";

  try {
    let model;

    if (provider === "openai") {
      const apiKey = (document.getElementById("openai-key") as HTMLInputElement).value;
      if (!apiKey) {
        throw new Error("OpenAI API key is required");
      }
      model = new OpenAIModel({
        apiKey,
        modelId: "gpt-4o",
        // Required to allow OpenAI SDK to run in browser environments
        clientConfig: {
          dangerouslyAllowBrowser: true,
        },
      });
    } else {
      // Bedrock provider
      const accessKey = (document.getElementById("access-key") as HTMLInputElement).value;
      const secretKey = (document.getElementById("secret-key") as HTMLInputElement).value;
      const sessionToken = (document.getElementById("session-token") as HTMLInputElement).value;
      const region = (document.getElementById("region") as HTMLSelectElement).value;

      if (!accessKey || !secretKey) {
        throw new Error("AWS Access Key and Secret Key are required");
      }

      model = new BedrockModel({
        region: region,
        clientConfig: {
          credentials: {
            accessKeyId: accessKey,
            secretAccessKey: secretKey,
            ...(sessionToken && { sessionToken }),
          },
        },
      });
    }

    agent = new Agent({
      model,
      systemPrompt:
        "You are a helpful assistant running in the browser. Keep your responses concise and friendly.",
    });

    // Switch to chat view
    credentialsSection.classList.add("hidden");
    chatSection.classList.remove("hidden");
    inputField.focus();

    addMessage("Connected! You can now chat with the agent.", "assistant");
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Connection failed";
    alert(`Failed to connect: ${errorMessage}`);
    connectButton.disabled = false;
    connectButton.textContent = "Connect to Agent";
  }
});

// Add a message to the chat UI
function addMessage(content: string, role: "user" | "assistant") {
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${role}`;
  messageDiv.textContent = content;
  messagesContainer.appendChild(messageDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Handle chat form submission
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  if (!agent) {
    alert("Please connect with your credentials first.");
    return;
  }

  const userMessage = inputField.value.trim();
  if (!userMessage) return;

  // Clear input and disable while processing
  inputField.value = "";
  sendButton.disabled = true;
  inputField.disabled = true;

  // Add user message to chat
  addMessage(userMessage, "user");

  // Add loading indicator
  const loadingDiv = document.createElement("div");
  loadingDiv.className = "message assistant loading";
  loadingDiv.textContent = "Thinking...";
  messagesContainer.appendChild(loadingDiv);

  try {
    // Stream the agent response for real-time updates
    // Replace loading indicator with an empty message we'll populate
    loadingDiv.remove();
    const responseDiv = document.createElement("div");
    responseDiv.className = "message assistant";
    messagesContainer.appendChild(responseDiv);

    let responseText = "";

    // Use streaming to show response as it's generated
    for await (const event of agent.stream(userMessage)) {
      // Handle text deltas for real-time display
      if (
        event.type === "modelContentBlockDeltaEvent" &&
        event.delta.type === "textDelta"
      ) {
        responseText += event.delta.text;
        responseDiv.innerHTML = marked.parse(responseText) as string;
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    }

    // If no text was streamed, show a fallback message
    if (!responseText) {
      responseDiv.textContent = "No response received.";
    }
  } catch (error) {
    // Remove loading indicator if still present
    loadingDiv.remove();

    // Show error message
    const errorMessage =
      error instanceof Error ? error.message : "An error occurred";
    addMessage(`Error: ${errorMessage}`, "assistant");
    console.error("Agent error:", error);
  } finally {
    // Re-enable input
    sendButton.disabled = false;
    inputField.disabled = false;
    inputField.focus();
  }
});
