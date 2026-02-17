# OpenAI Agents SDK (Python) — Memory & Sessions Guide (Beginner-Friendly)

This guide explains **how “memory” works** in the OpenAI Agents SDK (Python), the **different session types**, **when to use which**, and how to build **self‑learning agents** (learning from human interaction) using the right mix of memory stores and databases.

---

## 1) What “memory” means in the Agents SDK

In this SDK, the default built-in “memory” is **Session Memory**:

- A **Session** stores conversation history (user messages, assistant outputs, and run items).
- When you pass the same `session=` into `Runner.run(...)` across turns, the SDK automatically:
  1. loads history before the run, and
  2. appends new items after the run.

So “memory” here primarily means: **multi-turn continuity without manually passing message history**.

### A simple mental model

Think of agent memory as **layers**:

1. **Working memory (context window)**  
   What the model can “see” right now: the prompt + the current session items + any retrieved content.

2. **Session memory (short-term, thread-level)**  
   The conversation log and tool outputs stored for a `session_id`.

3. **Long-term memory (persistent, user/app-level)**  
   Things that should outlive a chat thread: preferences, stable facts, learned policies, user profile notes, etc.

4. **Semantic / retrieval memory (searchable knowledge)**  
   Embeddings + vector search over documents, notes, FAQs, tickets, etc.

In real products, you typically use **(2) + (3) + (4)** together.

---

## 2) Sessions: built-in memory interface

Most sessions support these operations:

- `get_items(limit=...)` → fetch history (optionally last N)
- `add_items(items)` → append items
- `pop_item()` → remove the latest item (useful for “undo/correction”)
- `clear_session()` → wipe history

---

## 3) Session types (memory backends) and when to use them

Below are the major session implementations commonly used in the SDK.

### A) `SQLiteSession` (default, lightweight)

**What it is:** A SQLite-backed session store.

**When to use:**
- Local development
- CLI prototypes
- Single-user tooling on one machine
- Quick demos

**Notes:**
- By default it can be in-memory (lost on process end) or file-backed (persistent).

---

### B) `SQLAlchemySession` (production-ready, choose your DB)

**What it is:** A session implementation built on SQLAlchemy, so you can use **any SQLAlchemy-supported database**.

**When to use:**
- Production services
- Multi-instance deployments (multiple servers)
- Need reliability, backups, migrations, HA, etc.

**Common DB choices:**
- **PostgreSQL** (most common for production)
- MySQL / MariaDB
- SQLite (still supported, but usually not ideal for multi-instance production)

---

### C) `AdvancedSQLiteSession` (branching + analytics)

**What it is:** An enhanced SQLite session that supports:
- conversation branching (alternate paths),
- usage tracking, and
- structured queries (e.g., tool usage stats).

**When to use:**
- Debugging and experimentation with “what-if” branches
- Agent evaluation workflows
- “Replay” and analysis of agent traces in SQLite

**Best fit:** Development / research workflows (not your first pick for scaled production).

---

### D) `EncryptedSession` (wraps any session with encryption + TTL)

**What it is:** A wrapper that adds:
- transparent encryption,
- per-session keys, and
- automatic expiration (TTL); expired items are skipped.

**When to use:**
- If session history includes sensitive data (PII, financial info, internal docs)
- If you need retention limits (“keep only last X days/minutes”)
- If you want defense-in-depth even when your DB is already encrypted-at-rest

**Operational note:**
- TTL expiry depends on your server clock → keep clocks synced (e.g., NTP).

---

### E) `OpenAIConversationsSession` (OpenAI-hosted conversation storage)

**What it is:** A session backed by OpenAI’s Conversations API.

**When to use:**
- You want a hosted conversation store without managing your own DB
- You are comfortable with an OpenAI-managed persistence layer for chat history

**Tradeoffs:**
- Less control than owning your database
- Review your org’s data governance requirements

---

### F) `OpenAIResponsesCompactionSession` (automatic compression of long sessions)

**What it is:** A wrapper that **compacts** session history using the Responses API compaction mechanism.
- Useful to keep history small and “clean” over long threads.
- Can be configured to auto-compact after thresholds, or compact manually.

**When to use:**
- Long-running chats where latency/cost grows due to huge histories
- Customer support threads, long investigations, iterative workflows

**Important streaming note:**
- Auto-compaction can delay “run completion” in streaming mode; if low-latency streaming is critical, compact during idle time or manually between turns.

---

## 4) Which session should I pick? (Quick decision guide)

### Start here

- **Just prototyping locally?** → `SQLiteSession`
- **Building a real backend service?** → `SQLAlchemySession` on **PostgreSQL**
- **Need encryption + retention limits?** → `EncryptedSession(underlying_session=SQLAlchemySession(...))`
- **Need “what-if” conversation branches and usage analytics?** → `AdvancedSQLiteSession`
- **Threads get very long and noisy?** → add `OpenAIResponsesCompactionSession(...)` on top of your underlying session
- **Want hosted storage for conversation threads?** → `OpenAIConversationsSession`

### Common production stack (recommended)
A very typical production pattern is:

- `SQLAlchemySession` (Postgres)  
  wrapped by  
- `EncryptedSession` (TTL + encryption)  
  optionally wrapped by  
- `OpenAIResponsesCompactionSession` (compaction)

This gives you:
- scalable storage,
- security + retention,
- manageable context over long chats.

---

## 5) “Self-learning” agents: what it actually means (and how to build it)

### Important clarification
An agent “self-learning” from human interaction usually **does not** mean the model weights are changing automatically.

It usually means:
- the agent **captures interaction signals** (feedback, corrections, preferences),
- **distills** them into durable “notes,” and
- **injects** those notes into future runs (so behavior improves over time).

This is typically called:
- **personalization**, **long-term memory**, or **continuous improvement** (without re-training).

### A practical self-learning architecture (recommended)

#### Step 1 — Collect signals during a run
Examples of signals:
- User corrections: “No, I meant X”
- Preferences: “Use bullet points”, “Keep it short”
- Task outcomes: “This worked”, “This failed”
- Human ratings or approvals: thumbs up/down, QA review notes

#### Step 2 — Distill signals into memory objects
Convert raw chat to structured “memories”, e.g.:
- `UserPreference { tone: "concise", format: "markdown", ... }`
- `Fact { key: "company_policy.retention", value: "...", confidence: ... }`
- `Procedure { task: "onboarding", steps: [...], last_verified: ... }`

#### Step 3 — Store long-term memory (separate from session history)
Store these in a durable DB (often Postgres) and/or vector store.

#### Step 4 — Retrieve + inject at the start of each run
At run start:
- Pull the top relevant long-term memories for the user/project
- Add them to the agent’s context as a **small, well-crafted summary**
- Use precedence rules (recent > old, verified > unverified, explicit user > inferred)

#### Step 5 — Consolidate and clean up
Periodically:
- dedupe overlapping memories,
- resolve contradictions,
- expire old low-value memories,
- mark stale procedures as “needs re-validation”.

This is the difference between “dump everything into history” vs “learning”.

---

## 6) What memory type should a self-learning agent use?

### Use **Sessions** for short-term continuity
Use a session type to maintain context within a conversation:
- `SQLAlchemySession` (prod) or `SQLiteSession` (dev)
- Add `OpenAIResponsesCompactionSession` if threads grow large

### Use a **separate long-term store** for learning
For “self-learning,” store structured state outside the session:
- A table for preferences, facts, and notes
- An event log of interactions and feedback
- A “memory summary” that is updated over time

The OpenAI cookbook pattern uses a state object + hooks to persist notes and inject them back each run (state-based personalization).

### Use a **vector DB** for semantic retrieval (optional but common)
If you need:
- “remember stuff like this” across large text corpora
- fuzzy recall (“something about refunds last month…”)

Then store memories/documents as embeddings in a vector store.

---

## 7) What databases should be used?

### Session storage (conversation history)
**Recommended for production:** PostgreSQL  
Why:
- concurrency, backups, HA, migrations, observability, access control

**OK for development:** SQLite file

### Long-term structured memory (preferences, notes, learned procedures)
**Recommended:** PostgreSQL (same DB as sessions, separate tables/schemas)

### Vector store (semantic memory)
Options:
- PostgreSQL + pgvector (simple stack, fewer moving parts)
- Dedicated vector DBs: Pinecone, Weaviate, Milvus, Qdrant
- Managed search: OpenSearch / Elasticsearch (hybrid setups)

### Fast cache (optional)
- Redis for caching retrieval results, rate-limiting, or short-lived “scratch” memory

---

## 8) Can we change from SQLite to another DB?

Yes.

### Option 1 — Use `SQLAlchemySession`
This is the official “switch the DB” path: use SQLAlchemy and point it at Postgres/MySQL/etc.

Example (conceptually):
- SQLite dev: `sqlite+aiosqlite:///conversations.db`
- Postgres prod: `postgresql+asyncpg://user:pass@host/db`

### Option 2 — Implement a custom session
If you want DynamoDB, MongoDB, Redis Streams, etc., you can implement the Session protocol (SessionABC) with:
- `get_items(...)`
- `add_items(...)`
- `pop_item()`
- `clear_session()`

That lets you plug in any storage technology, as long as you implement the interface.

---

## 9) Common “gotchas” and best practices

1. **Don’t rely on raw session history as long-term learning**  
   It becomes noisy, expensive, and can “poison” context with old mistakes.

2. **Use compaction / summarization for long threads**  
   This keeps token usage and failure rates down.

3. **Encrypt + TTL for sensitive workflows**  
   Especially for enterprise data, finance, HR, legal, etc.

4. **Prefer structured long-term memory over “verbatim chat logs”**  
   Store stable facts and preferences as structured records.

5. **Add governance**
   - Redact/avoid storing secrets
   - Keep audit trails for learned changes
   - Add a “forget me” / delete path per user/project

---

## 10) Suggested “starter blueprint”

If you’re building a serious agent app:

- **Session memory:** `SQLAlchemySession` (Postgres)
- **Security:** wrap with `EncryptedSession` + TTL
- **Context size:** add `OpenAIResponsesCompactionSession` for long threads
- **Self-learning:** separate Postgres tables for preferences/notes + optional vector store
- **Human-in-loop:** explicit feedback UI + review queue + memory consolidation job

This gives you a clean, understandable architecture that scales.

---
