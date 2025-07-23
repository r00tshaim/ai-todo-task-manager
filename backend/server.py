# server.py

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Generator
import uuid
import json
from langchain_core.messages import HumanMessage
import uvicorn
from fastapi.middleware.cors import CORSMiddleware  # Add this import

# Import the graph from agent.py
from agent import graph, across_thread_memory

app = FastAPI(title="ToDo mAIstro API", version="1.0.0")

# Add CORS middleware - ADD THIS SECTION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:*", "http://127.0.0.1:*"],  # React dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Include OPTIONS
    allow_headers=["*"],
)

# Pydantic models for request/response
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
    message_id: Optional[str] = None

class StreamChunk(BaseModel):
    type: str  # "start", "chunk", "end", "error"
    thread_id: Optional[str] = None
    content: Optional[str] = None
    error: Optional[str] = None

class TodoItem(BaseModel):
    task: str
    time_to_complete: Optional[int] = None
    deadline: Optional[str] = None
    solutions: List[str] = []
    status: str = "not started"

class TodosResponse(BaseModel):
    user_id: str
    todos: List[Dict[str, Any]]

def format_sse_data(data: StreamChunk) -> str:
    """Format data for Server-Sent Events"""
    return f"data: {json.dumps(data)}\n\n"

def generate_chat_stream(messages: list, config: dict, thread_id: str) -> Generator[str, None, None]:
    """Generator function for streaming chat responses"""
    try:
        # Send start event
        yield format_sse_data({
            "type": "start",
            "thread_id": thread_id,
            "content": "Processing your message..."
        })
        
        full_response = ""
        chunk_count = 0
        
        # Stream the graph execution
        for chunk in graph.stream({"messages": messages}, config, stream_mode="values"):
            if chunk["messages"]:
                last_message = chunk["messages"][-1]
                if hasattr(last_message, 'content') and last_message.content:
                    # Send incremental content
                    content = last_message.content
                    if content != full_response:  # Only send if content changed
                        yield format_sse_data({
                            "type": "chunk",
                            "thread_id": thread_id,
                            "content": content,
                            "chunk_id": chunk_count
                        })
                        full_response = content
                        chunk_count += 1
        
        # Send completion event
        yield format_sse_data({
            "type": "end",
            "thread_id": thread_id,
            "content": full_response or "I received your message and I'm ready to help with your tasks!",
            "final": True
        })
        
    except Exception as e:
        # Send error event
        yield format_sse_data({
            "type": "error",
            "thread_id": thread_id,
            "error": str(e)
        })

@app.post("/chat/new/stream")
async def start_new_chat_stream(request: NewChatRequest):
    """
    Start a new chat session with streaming response
    """
    try:
        # Generate new thread_id
        thread_id = str(uuid.uuid4())
        
        # Create config with thread_id and user_id
        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": request.user_id
            }
        }
        
        # Create input message
        input_messages = [HumanMessage(content=request.message)]
        
        # Return streaming response
        return StreamingResponse(
            generate_chat_stream(input_messages, config, thread_id),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting new chat: {str(e)}")

@app.post("/chat/continue/stream")
async def continue_existing_chat_stream(request: ContinueChatRequest):
    """
    Continue an existing chat session with streaming response
    """
    try:
        # Create config with existing thread_id and user_id
        config = {
            "configurable": {
                "thread_id": request.thread_id,
                "user_id": request.user_id
            }
        }
        
        # Create input message
        input_messages = [HumanMessage(content=request.message)]
        
        # Return streaming response
        return StreamingResponse(
            generate_chat_stream(input_messages, config, request.thread_id),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error continuing chat: {str(e)}")

# Keep the original non-streaming endpoints as well
@app.post("/chat/new", response_model=ChatResponse)
async def start_new_chat(request: NewChatRequest):
    """
    Start a new chat session with a generated thread_id (non-streaming)
    """
    try:
        # Generate new thread_id
        thread_id = str(uuid.uuid4())
        
        # Create config with thread_id and user_id
        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": request.user_id
            }
        }
        
        # Create input message
        input_messages = [HumanMessage(content=request.message)]
        
        # Run the graph and collect the response
        response_content = ""
        for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
            if chunk["messages"]:
                last_message = chunk["messages"][-1]
                if hasattr(last_message, 'content') and last_message.content:
                    response_content = last_message.content
        
        return ChatResponse(
            thread_id=thread_id,
            response=response_content or "I received your message and I'm ready to help with your tasks!"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting new chat: {str(e)}")

@app.post("/chat/continue", response_model=ChatResponse)
async def continue_existing_chat(request: ContinueChatRequest):
    """
    Continue an existing chat session using thread_id (non-streaming)
    """
    try:
        # Create config with existing thread_id and user_id
        config = {
            "configurable": {
                "thread_id": request.thread_id,
                "user_id": request.user_id
            }
        }
        
        # Create input message
        input_messages = [HumanMessage(content=request.message)]
        
        # Run the graph and collect the response
        response_content = ""
        for chunk in graph.stream({"messages": input_messages}, config, stream_mode="values"):
            if chunk["messages"]:
                last_message = chunk["messages"][-1]
                if hasattr(last_message, 'content') and last_message.content:
                    response_content = last_message.content
        
        return ChatResponse(
            thread_id=request.thread_id,
            response=response_content or "I received your message and processed it!"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error continuing chat: {str(e)}")

@app.post("/todos/get", response_model=TodosResponse)
async def get_user_todos(request: GetTodosRequest):
    """
    Get all todo tasks for a specific user
    """
    try:
        # Define the namespace for todo items
        namespace = ("todo", request.user_id)
        
        # Retrieve all todo memories from the store
        memories = across_thread_memory.search(namespace)
        
        # Format the todos
        todos = []
        for memory in memories:
            todo_data = memory.value
            # Add the memory key as an ID for reference
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
    return {"status": "healthy", "message": "ToDo mAIstro API is running"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to ToDo mAIstro API",
        "version": "1.0.0",
        "endpoints": {
            "POST /chat/new": "Start a new chat session (non-streaming)",
            "POST /chat/new/stream": "Start a new chat session (streaming)",
            "POST /chat/continue": "Continue an existing chat session (non-streaming)",
            "POST /chat/continue/stream": "Continue an existing chat session (streaming)",
            "POST /todos/get": "Get user's todo tasks",
            "GET /health": "Health check",
            "GET /docs": "API documentation"
        }
    }

# Additional utility endpoint to get user profile (optional)
@app.post("/profile/get")
async def get_user_profile(request: GetTodosRequest):
    """
    Get user profile information
    """
    try:
        # Define the namespace for profile
        namespace = ("profile", request.user_id)
        
        # Retrieve profile memories from the store
        memories = across_thread_memory.search(namespace)
        
        if memories:
            profile_data = memories[0].value
            return {
                "user_id": request.user_id,
                "profile": profile_data
            }
        else:
            return {
                "user_id": request.user_id,
                "profile": None,
                "message": "No profile found for this user"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving profile: {str(e)}")

# Run the server
if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
