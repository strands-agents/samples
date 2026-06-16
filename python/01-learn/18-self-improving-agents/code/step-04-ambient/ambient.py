"""AmbientMode - background thread that keeps the agent working during idle time."""
import threading
import time


class AmbientMode:
    def __init__(self, agent, idle_seconds: float = 20, max_iterations: int = 3):
        self.agent = agent
        self.idle_seconds = idle_seconds
        self.max_iterations = max_iterations

        self.last_interaction = time.time()
        self.last_query = None
        self.pending_result = None
        self.iterations = 0
        self.running = False
        self._interrupted = False
        self._thread = None

    def record_interaction(self, query: str):
        self.last_interaction = time.time()
        self.last_query = query
        self.iterations = 0
        self._interrupted = False

    def interrupt(self):
        self._interrupted = True

    def consume_pending(self):
        r, self.pending_result = self.pending_result, None
        return r

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False

    def _loop(self):
        while self.running:
            idle = time.time() - self.last_interaction
            should_run = (
                self.last_query
                and idle > self.idle_seconds
                and self.iterations < self.max_iterations
                and not self._interrupted
            )
            if should_run:
                prompt = (
                    f"[Ambient mode: iteration {self.iterations + 1}/{self.max_iterations}]\n"
                    f"User's last query: '{self.last_query}'.\n"
                    f"Continue exploring this topic. Find edge cases, related topics, "
                    f"improvements. Be concise. Output findings only."
                )
                print(f"\n🌙 [ambient iter {self.iterations + 1}/{self.max_iterations}] thinking...")
                try:
                    result = self.agent(prompt)
                    if not self._interrupted:
                        prior = self.pending_result or ""
                        self.pending_result = f"{prior}\n\n{result}".strip()
                        self.iterations += 1
                        print(f"🌙 [ambient] result queued ({len(str(result))} chars)\n🦆 ", end="", flush=True)
                except Exception as e:
                    print(f"🌙 [ambient] error: {e}")
            time.sleep(3)
