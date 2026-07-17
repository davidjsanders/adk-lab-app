# Optimization Plan - Router Agent V2

This document outlines strategies to improve the performance, latency, and token efficiency of the Router Agent V2, particularly after reverting to a hierarchical architecture for UI stability.

---

## 🚀 1. Optimize MCP Connection Management (Connection Pooling)

**Problem:** The `create_dynamic_httpx_client` factory in `app/tools/mcp_tools.py` creates a **new** `httpx.AsyncClient` instance for every operation. Establishing a new TCP connection and performing the TLS handshake (and token generation) for every tool call adds significant latency (hundreds of milliseconds).

**Proposed Solution:**
*   Implement connection pooling or share a singleton `AsyncClient` across the application lifecycle.
*   Update IAM tokens dynamically using an `httpx.Auth` class or middleware rather than recreating the entire client.
*   Ensure proper cleanup of the client on application shutdown.

---

## 🗣️ 2. Reduce Conversational Overhead (Streamline Routing)

**Problem:** In the Hierarchical model, requests often go: `User` ➔ `Coordinator` ➔ `Diagnostic Agent` ➔ `Tool` ➔ `Diagnostic Agent` ➔ `Coordinator` ➔ `User`. The Coordinator acts as a router but requires a full LLM pass to decide to `transfer_to_agent`. This adds latency and token cost.

**Proposed Solution:**
*   **Concise Coordinator Instructions:** Make the Coordinator's instructions extremely concise to minimize output token generation during routing.
*   **Direct Access for Simple Queries:** For high-frequency, simple requests (like "show router X"), consider allowing the Coordinator to invoke the `render_router_card` tool **directly**, bypassing the Diagnostic Agent altogether to save a delegation turn. Keep the Diagnostic Agent for complex troubleshooting sequences.

---

## 🧠 3. Optimize Prompts (Instruction Compression)

**Problem:** Lengthy system instructions mean more input tokens processed on every turn, increasing cost and slightly increasing latency.

**Proposed Solution:**
*   Audit the system prompts for `diagnostic_agent`, `remediation_agent`, and `router_fleet_coordinator`.
*   Remove redundant instructions or conversational fillers.
*   Use clear, imperative bullet points rather than narrative text.
*   *(Constraint: Maintain strict **Verbatim Relay Rules** as they are critical for A2UI rendering).*

---

## 🖼️ 4. Maintain Token Hygiene (Keep Context Clean)

**Problem:** Large payloads (like Base64 encoded images or large JSON blobs) in the conversation history bloat the context window, slowing down subsequent LLM responses significantly and increasing costs.

**Proposed Solution:**
*   Ensure the `intercept_image_card_tool` callback (which extracts Base64 images and replaces them with markers) is applied consistently to **all** agents/tools that might emit large payloads.
*   Audit tool outputs to ensure they return only necessary data to the LLM, moving verbose details to artifacts where appropriate.
