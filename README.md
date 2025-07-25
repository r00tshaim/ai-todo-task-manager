# ai-todo-task-manager

                             ┌───────────────────────────────────────────────┐
                             │                  Frontend                     │
                             │       (React App, Browser)                    │
                             └───────────────────────────────────────────────┘
                                              │       ▲
                                   1. HTTP API│       │ 6. SSE (Streaming)
                           (POST /chat/new,   │       │ (GET /stream/{job})  
                            /chat/continue)   │       │
                                              ▼       │
                           ┌──────────────────────────────────────────────┐
                           │  API Server (FastAPI)                        │
                           │   - Handles chat requests                    │
                           │   - Enqueues jobs in RQ Queue                │
                           │   - Streams AI results from Redis Stream     │
                           │   - Handles /todos/get (reads psql memory)   │
                           └─────────────┬────────────────────────────────┘
                                         │
                                         │2. Enqueue job
                                         ▼
                           ┌───────────────────────────────────┐
                           │    Redis (RQ Job Queue)           │
                           │ - rq:queue:chat_jobs (list)       │
                           │ - job metadata keys, stream keys  │
                           └────────────────┬──────────────────┘
                                            │3. Worker pulls job
                                            ▼
                ┌─────────────────────────────────────────────────────┐
                │            RQ Worker Process (worker.py)            │
                │  - Fetches job from RQ queue                        │
                │  - Triggers LangGraph LLM on task                   │
                │  - Reads/writes long-term memory in Postgres        │
                │  - Publishes streaming AI output to Redis Streams   │
                └────────────┬────────────────────────────────────────┘
                             │ 4. Reads/writes memory in PSQL
                             ▼
                   ┌───────────────────────────────┐
                   │  PostgreSQL (Persistent DB)   │
                   │ - Long-term memory store      │
                   │   ("store" table, tasks, ... )│
                   └───────────────────────────────┘
                             │
                             │ 5. Streams result chunks/status
                             ▼
                   ┌───────────────────────────────┐
                   │     Redis Stream              │
                   │ (job:{id}:stream, per job)    │
                   └───────────────────────────────┘
                             │
                             │6. Server reads stream chunks
                             ▼
                  (Back to API Server ➔ Frontend via SSE as above)


Details and Explanations
1. Frontend App sends HTTP POST to FastAPI (/chat/new or /chat/continue)

2. FastAPI Server enqueues a job in Redis RQ queue

Also creates job metadata keys in Redis for tracking

3. RQ Worker pulls job from Redis

Runs LangGraph workflow, triggers LLM/agent

Reads/writes persistent todos, profile, etc. in PostgreSQL

As soon as it gets chunks from LLM, publishes each to Redis Stream (job:{job_id}:stream)

4. FastAPI reads Redis Stream for that job and streams the output via SSE (Server-Sent Events) to the frontend

The frontend UI displays the bot’s message “chunk-by-chunk” as streamed events

5. All to-dos/metadata are stored persistently in PostgreSQL using LangGraph’s PostgresStore

6. /todos/get and similar endpoints read directly from PostgreSQL
