// The agent replies with { text, ui }. `ui` is a list of components it chose
// from the catalog the server defines; this file turns each one into DOM.

const chat = crypto.randomUUID();
const transcript = document.getElementById("transcript");
const composer = document.getElementById("composer");
const prompt = document.getElementById("prompt");
const suggestions = document.getElementById("suggestions");

// --- Component renderers: one function per catalog `type` ---------------

const renderers = {
  text: (c) => el("p", { class: "text" }, c.content),

  stat: (c) =>
    el("div", { class: "card stat" },
      el("span", { class: "label" }, c.label),
      el("strong", {}, c.value),
      c.hint && el("span", { class: "hint" }, c.hint),
    ),

  table: (c) =>
    el("div", { class: "card" },
      c.title && el("h3", {}, c.title),
      el("table", {},
        el("thead", {}, el("tr", {}, ...c.columns.map((col) => el("th", {}, col)))),
        el("tbody", {}, ...c.rows.map((row) => el("tr", {}, ...row.map((cell) => el("td", {}, cell))))),
      ),
    ),

  bar_chart: (c) => {
    const max = Math.max(...c.bars.map((b) => b.value), 1);
    return el("div", { class: "card" },
      c.title && el("h3", {}, c.title),
      ...c.bars.map((b) =>
        el("div", { class: "bar" },
          el("span", { class: "label" }, b.label),
          el("span", { class: "track" }, el("span", { class: "fill", style: `width:${(b.value / max) * 100}%` })),
          el("span", { class: "value" }, `${b.value}${c.unit ? ` ${c.unit}` : ""}`),
        ),
      ),
    );
  },

  form: (c) => {
    const form = el("form", { class: "card form" },
      c.title && el("h3", {}, c.title),
      ...c.fields.map(renderField),
      el("button", { type: "submit" }, c.submit || "Submit"),
    );
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      sendAction(c.action, Object.fromEntries(new FormData(form)), c.submit || "Submitted");
      form.querySelectorAll("input, select, button").forEach((node) => (node.disabled = true));
    });
    return form;
  },

  button: (c) => {
    const button = el("button", { type: "button", class: "action" }, c.label);
    button.addEventListener("click", () => sendAction(c.action, {}, c.label));
    return button;
  },

  row: (c) => el("div", { class: "row" }, ...c.items.map(renderComponent)),
};

function renderField(field) {
  const control =
    field.kind === "select"
      ? el("select", { name: field.name }, ...(field.options ?? []).map((o) => el("option", { selected: o === field.value }, o)))
      : el("input", { name: field.name, type: field.kind, value: field.value ?? "", step: field.kind === "number" ? "any" : null });
  return el("label", {}, field.label, control);
}

function renderComponent(component) {
  const render = renderers[component.type];
  if (!render) {
    console.warn("No renderer for component type", component.type);
    return null;
  }
  return render(component);
}

// --- Talking to the agent ------------------------------------------------

// Interactions go back to the agent as a normal chat message with a
// recognizable prefix, so the agent can act on them and render again.
function sendAction(action, values, label) {
  send(`[ui action] ${action} ${JSON.stringify(values)}`, label);
}

async function send(message, label = message) {
  suggestions.hidden = true;
  addTurn("user", el("p", {}, label));
  const pending = addTurn("agent", el("p", { class: "thinking" }, "Thinking..."));
  setBusy(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat, message }),
    });
    const { text, ui, error } = await response.json();
    if (!response.ok) throw new Error(error ?? `HTTP ${response.status}`);
    pending.replaceChildren(...[text && el("p", {}, text), ...ui.map(renderComponent)].filter(Boolean));
  } catch (error) {
    pending.replaceChildren(el("p", { class: "error" }, error.message));
  } finally {
    setBusy(false);
  }
}

function addTurn(role, ...children) {
  const turn = el("div", { class: `turn ${role}` }, ...children);
  transcript.append(turn);
  turn.scrollIntoView({ behavior: "smooth", block: "end" });
  return turn;
}

function setBusy(busy) {
  composer.querySelectorAll("input, button").forEach((node) => (node.disabled = busy));
  if (!busy) prompt.focus();
}

composer.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = prompt.value.trim();
  if (!message) return;
  prompt.value = "";
  send(message);
});

suggestions.querySelectorAll("button").forEach((button) =>
  button.addEventListener("click", () => send(button.textContent)),
);

// --- Tiny DOM helper -----------------------------------------------------

// Text is always set with text nodes, never innerHTML, so model output can't
// inject markup.
function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === null || value === undefined || value === false) continue;
    node.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children) {
    if (child === null || child === undefined || child === false || child === "") continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}
