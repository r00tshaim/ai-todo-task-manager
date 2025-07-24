# server.py

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Generator
import uuid
import json
import redis
from rq import Queue
import asyncio
import redis.asyncio as aioredis
import uvicorn

app = FastAPI(title="ToDo mAIstro API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
job_queue = Queue('chat_jobs', connection=redis_client)

# Pydantic models
class NewChatRequest(BaseModel):
    user_id: str
    message: str

class ContinueChatRequest(BaseModel):
    user_id: str
    thread_id: str
    message: str

class GetTodosRequest(BaseModel):
    user_id: str

class ChatResponse(BaseModel):
    thread_id: str
    response: str
    job_id: Optional[str] = None

class TodosResponse(BaseModel):
    user_id: str
    todos: List[Dict[str, Any]]

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    thread_id: Optional[str] = None

@app.post("/chat/new", response_model=ChatResponse)
async def start_new_chat(request: NewChatRequest):
    """
    Start a new chat session - enqueue job and return immediately
    """
    try:
        # Generate new thread_id and job_id
        thread_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        
        # Prepare job payload
        job_payload = {
            "job_id": job_id,
            "thread_id": thread_id,
            "user_id": request.user_id,
            "message": request.message,
            "job_type": "new_chat"
        }
        
        # Enqueue job
        job = job_queue.enqueue(
            'worker.process_chat_job',
            job_payload,
            job_id=job_id,
            job_timeout='5m'
        )
        
        # Store job metadata in Redis
        redis_client.hset(f"job:{job_id}:meta", mapping={
            "user_id": request.user_id,
            "thread_id": thread_id,
            "status": "queued",
            "job_type": "new_chat"
        })
        redis_client.expire(f"job:{job_id}:meta", 3600)  # 1 hour TTL
        
        return ChatResponse(
            thread_id=thread_id,
            response="Job queued successfully. Use /stream endpoint to get real-time updates.",
            job_id=job_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting new chat: {str(e)}")

@app.post("/chat/continue", response_model=ChatResponse)
async def continue_existing_chat(request: ContinueChatRequest):
    """
    Continue an existing chat session - enqueue job and return immediately
    """
    try:
        # Generate job_id
        job_id = str(uuid.uuid4())
        
        # Prepare job payload
        job_payload = {
            "job_id": job_id,
            "thread_id": request.thread_id,
            "user_id": request.user_id,
            "message": request.message,
            "job_type": "continue_chat"
        }
        
        # Enqueue job
        job = job_queue.enqueue(
            'worker.process_chat_job',
            job_payload,
            job_id=job_id,
            job_timeout='5m'
        )
        
        # Store job metadata in Redis
        redis_client.hset(f"job:{job_id}:meta", mapping={
            "user_id": request.user_id,
            "thread_id": request.thread_id,
            "status": "queued",
            "job_type": "continue_chat"
        })
        redis_client.expire(f"job:{job_id}:meta", 3600)  # 1 hour TTL
        
        return ChatResponse(
            thread_id=request.thread_id,
            response="Job queued successfully. Use /stream endpoint to get real-time updates.",
            job_id=job_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error continuing chat: {str(e)}")

@app.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status of a specific job
    """
    try:
        job_meta = redis_client.hgetall(f"job:{job_id}:meta")
        if not job_meta:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatusResponse(
            job_id=job_id,
            status=job_meta.get("status", "unknown"),
            thread_id=job_meta.get("thread_id")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting job status: {str(e)}")

@app.get("/stream/{job_id}")
async def stream_job_results(job_id: str):
    """
    Stream job results using Server-Sent Events from Redis Streams
    """
    async def generate_stream():
        try:
            # Connect to Redis for streaming
            redis_stream = aioredis.from_url("redis://localhost:6379", decode_responses=True)
            
            # Check if job exists
            job_meta = await redis_stream.hgetall(f"job:{job_id}:meta")
            if not job_meta:
                yield f"data: {json.dumps({'type': 'error', 'error': 'Job not found'})}\n\n"
                return
            
            stream_key = f"job:{job_id}:stream"
            last_id = "0"  # Start from beginning
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'start', 'job_id': job_id, 'status': 'streaming'})}\n\n"
            
            while True:
                try:
                    # Read from Redis Stream
                    messages = await redis_stream.xread({stream_key: last_id}, count=1, block=1000)
                    
                    if messages:
                        for stream, msgs in messages:
                            for msg_id, fields in msgs:
                                last_id = msg_id
                                
                                # Parse the message
                                event_data = json.loads(fields.get('data', '{}'))
                                yield f"data: {json.dumps(event_data)}\n\n"
                                
                                # If job is complete, break
                                if event_data.get('type') in ['end', 'error']:
                                    return
                    
                    # Check if job still exists (timeout handling)
                    job_exists = await redis_stream.exists(f"job:{job_id}:meta")
                    if not job_exists:
                        yield f"data: {json.dumps({'type': 'error', 'error': 'Job expired'})}\n\n"
                        return
                        
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
                    continue
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
                    return
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.post("/todos/get", response_model=TodosResponse)
async def get_user_todos(request: GetTodosRequest):
    """
    Get all todo tasks for a specific user (direct access to store)
    """
    try:
        # Import here to avoid circular imports
        from agent import across_thread_memory     #Only accesses the server’s (not worker’s) memory objects,
        
        # Define the namespace for todo items
        namespace = ("todo", request.user_id)
        
        # Retrieve all todo memories from the store
        memories = across_thread_memory.search(namespace)
        
        # Format the todos
        todos = []
        for memory in memories:
            todo_data = memory.value
            todo_item = {
                "id": memory.key,
                "task": todo_data.get("task", ""),
                "time_to_complete": todo_data.get("time_to_complete"),
                "deadline": todo_data.get("deadline"),
                "solutions": todo_data.get("solutions", []),
                "status": todo_data.get("status", "not started")
            }
            todos.append(todo_item)
        
        return TodosResponse(
            user_id=request.user_id,
            todos=todos
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving todos: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        redis_client.ping()
        queue_length = len(job_queue)
        
        return {
            "status": "healthy",
            "message": "ToDo mAIstro API is running",
            "redis_connected": True,
            "queue_length": queue_length
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Error: {str(e)}",
            "redis_connected": False
        }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to ToDo mAIstro API (Decoupled)",
        "version": "2.0.0",
        "endpoints": {
            "POST /chat/new": "Start a new chat session (queued)",
            "POST /chat/continue": "Continue an existing chat session (queued)",
            "GET /stream/{job_id}": "Stream job results in real-time",
            "GET /jobs/{job_id}/status": "Get job status",
            "POST /todos/get": "Get user's todo tasks",
            "GET /health": "Health check",
            "GET /docs": "API documentation"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
