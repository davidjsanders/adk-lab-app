# GEMINI.md - Rules and Development Guidelines

## 🧠 Core Engineering Principles

### 1. Think Before Coding (Scientific Skepticism)
*   **No Guessing:** Never assume directory paths, package versions, or configuration schemas. If any detail is ambiguous, stop immediately and ask for clarification.
*   **Acknowledge Uncertainty:** If multiple implementations exist or a task is ambiguous, list 2-3 logical paths, explain the tradeoffs, and ask for guidance before writing any code.
*   **Simplicity First:** Write the absolute minimum code required to solve the immediate problem. Do not introduce speculative abstractions or helper methods for "future use."
*   **Surgical Changes:** Modify only the files and lines necessary for the task. Do not reformat or clean up adjacent files unless explicitly requested.

### 2. Validation & Feedback Loops
*   **Verify, Don't Assume:** You must always run local validation checks or tests before declaring a task finished. 
*   **Analyze Real Logs:** If a deployment or run fails, analyze the actual compiler/runtime errors step-by-step. Do not attempt "creative fixes" based on guessing.
*   **Validate Commands:** Always check that any command you intend to execute (e.g., `blaze test`, `pytest`, `adk deploy`) is supported in the current environment before executing.

---

## ⚙️ ADK & Agent Platform Specifics

### 3. State Management & Lifecycle
*   **Dedicated Toolsets:** Always instantiate a unique, separate instance of `MCPToolset` (or equivalent tool handlers) for each agent run. Never share a single socket/toolset connection across concurrent agent instances, as this triggers race conditions and premature socket closures during shutdown.
*   **Strict Typing:** Ensure all agent tool signatures and parameter definitions use strict Pydantic models or clean type annotations. Do not allow loose typing like `Any` or `dict`, as this causes tool-call execution errors.

### 4. Asynchronous Lifecycles & Graceful Shutdown
*   **Structure Async Lifecycles:** When launching async ADK applications, always utilize `anyio.run(main)` instead of `asyncio.run()`. This ensures that all nested exception/cancellation scopes exit in a structured, clean manner.
*   **Avoid Scope Derailments:** Ensure that any shared context managers or async client connections (e.g., HTTP clients, DB connections) are wrapped in robust `try...finally` blocks or async context managers to prevent hanging processes on your cloudtop.

### 5. Deployment Setup
*   **Credential Verification:** Before attempting a deployment to Agent Engine via `adk deploy`, verify that you are authenticated against the correct GCP project. Ensure you run verification checks like `gcloud config get-value project` and output the current active project before attempting deployment.
