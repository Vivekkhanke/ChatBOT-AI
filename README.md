<img width="953" height="437" alt="bot0" src="https://github.com/user-attachments/assets/24ceb820-5c67-4c24-9060-3fb26b3b6bea" />

<img width="955" height="468" alt="Bot1" src="https://github.com/user-attachments/assets/988e291e-504a-41f1-8ef6-935b0c42cec0" />

<img width="958" height="463" alt="bot2" src="https://github.com/user-attachments/assets/ab493448-9b1d-4d10-b7d3-38f265c738ed" />

# Banking AI Assistant

A conversational AI assistant for private banking that answers customer questions by combining structured account data with unstructured policy documents. It routes each question to the right data source, retrieves grounded context, and generates a response with an LLM — rather than answering from memory alone.

## What it does

A customer can ask things like:

- "What's my savings balance?" — a structured, account-specific question
- "What's the deposit policy for large cheques?" — a general, policy-based question
- "Can I close my account and what happens to pending transactions?" — a question that may need both

The assistant classifies the question, pulls the right context, and returns a single grounded answer — without exposing raw database access or requiring the customer to know which system holds the answer.

## Architecture overview

```
User → Frontend (chat UI) → Flask API → Orchestrator
                                            │
                        ┌───────────────────┴───────────────────┐
                        ▼                                       ▼
                RAG pipeline                              SQL agent
        (policy & general questions)              (account & customer questions)
                        │                                       │
                        └───────────────────┬───────────────────┘
                                            ▼
                                Context aggregation
                                            │
                                            ▼
                                      Gemini LLM
                                            │
                                            ▼
                            Response → Flask → Frontend → User
```

### 1. Frontend

A lightweight chat interface built with plain HTML, CSS, and JavaScript. It sends the user's question along with a session ID to the backend and renders the streamed response. No framework dependency keeps it easy to embed or restyle.

### 2. Backend API (Flask)

A Flask application exposes the endpoints the frontend calls:

- `POST /chat` — receives a question and session ID, returns the assistant's response
- `GET /health` — basic health check for deployment monitoring
- `POST /rebuild-index` — rebuilds the RAG vector index when source documents change

Flask's only job here is transport: it validates the request, hands it to the orchestrator, and returns whatever the orchestrator produces.

### 3. Orchestrator

The core decision-making layer. For each incoming question it:

- **Classifies the question** — does it need account data (SQL), policy/general knowledge (RAG), or both?
- **Routes to the right pipeline(s)** and waits for their context
- **Tracks conversation history** per session, so follow-up questions ("and what about my checking account?") resolve correctly
- **Assembles the final context** and calls the LLM to generate the answer

### 4. RAG pipeline — policy & general questions

Used when the question is about bank policy, product terms, or general information rather than a specific customer's data.

1. **Ingestion** — banking policy PDFs (deposit policy, credit card policy, etc.) are loaded and split into overlapping text chunks.
2. **Embedding** — each chunk is embedded using Gemini's embedding model.
3. **Storage** — embeddings are stored in **ChromaDB**, a local vector database.
4. **Retrieval** — at query time, the user's question is embedded with the same model, and ChromaDB performs a similarity search to return the top-K most relevant chunks.

The retrieved chunks become the "RAG context" passed to the final LLM call.

### 5. SQL agent — account & customer questions

Used when the question requires live data from the bank's systems, such as balances or transaction history.

1. **SQL generation** — Gemini is prompted to translate the natural-language question into a SQL query, using the known schema.
2. **Validation** — before execution, the generated query passes through a security layer that only allows read-only statements (`SELECT`, `WITH`) and blocks anything that could mutate or damage data (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `GRANT`, etc.).
3. **Execution** — the validated query runs against **Oracle Database**, and the results are formatted into "Oracle context."

This separation means the LLM never talks to the database directly — it only ever proposes a query, which is checked before anything runs.

### 6. Context aggregation

Before generating a response, the orchestrator assembles a single context containing:

- A system prompt establishing the assistant's role and constraints
- The user's original question
- Recent conversation history for the session
- RAG context, if the question needed it
- Oracle context, if the question needed it

### 7. Response generation (Gemini)

Gemini receives the aggregated context and generates a grounded, conversational answer — using only the retrieved policy text and/or query results as its factual basis, rather than relying on general knowledge about banking.

### 8. Response delivery

The generated answer flows back through Flask to the frontend and is displayed to the user, completing the request.

## Technology stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | HTML, CSS, JavaScript | Chat UI, session handling, calls to the Flask API |
| Backend / API | Python, Flask | Request handling, routing, orchestration entry point |
| Orchestration | Python | Question classification, routing, context assembly, conversation memory |
| LLM & embeddings | Google Gemini | SQL generation, response generation, text embeddings |
| Vector store | ChromaDB | Stores and searches document embeddings for RAG |
| Document processing | PDF loader + text splitter (e.g. LangChain-style chunking) | Converts source policy PDFs into retrievable chunks |
| Structured data | Oracle Database | Source of truth for customer and account data |
| SQL safety | Custom query validation layer | Restricts the SQL agent to read-only, allow-listed statements |

## Key design principles

- **Hybrid retrieval** — combines unstructured knowledge (RAG over policy PDFs) with structured data (SQL over Oracle) so the assistant can answer both "what's the policy" and "what's my balance" questions accurately.
- **Security by construction** — the SQL agent can only generate queries; a separate validation step, not the LLM, decides what's allowed to execute.
- **Context-aware** — per-session conversation history lets the assistant handle natural follow-up questions.
- **Separation of concerns** — retrieval, data access, and generation are independent components, making each one easier to test, swap, or scale on its own.
