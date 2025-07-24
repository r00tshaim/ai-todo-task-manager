# worker.py

import redis
import json
from datetime import datetime
from langchain_core.messages import HumanMessage
from agent import graph
from dotenv import load_dotenv
import os

load_dotenv()


# Redis connection
redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"), decode_responses=True)

def publish_to_stream(job_id: str, event_type: str, content: str = None, error: str = None, **kwargs):
    """
    Publish events to Redis Stream for the job
    """
    stream_key = f"job:{job_id}:stream"
    
    event_data = {
        "type": event_type,
        "timestamp": datetime.now().isoformat(),
        "job_id": job_id,
        **kwargs
    }
    
    if content:
        event_data["content"] = content
    if error:
        event_data["error"] = error
    
    # Add to Redis Stream
    redis_client.xadd(stream_key, {"data": json.dumps(event_data)})
    
    # Set TTL on stream (1 hour)
    redis_client.expire(stream_key, 3600)

def process_chat_job(job_payload):
    """
    Process a chat job - this runs in the worker process
    """
    job_id = job_payload["job_id"]
    thread_id = job_payload["thread_id"]
    user_id = job_payload["user_id"]
    message = job_payload["message"]
    job_type = job_payload["job_type"]
    
    try:
        # Update job status to running
        redis_client.hset(f"job:{job_id}:meta", "status", "running")
        
        # Publish start event
        publish_to_stream(
            job_id, 
            "start", 
            content="Processing your message...",
            thread_id=thread_id
        )
        
        # Create config for the graph
        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id
            }
        }
        
        # Create input message
        input_messages = [HumanMessage(content=message)]
        
        # Process through the graph
        full_response = ""
        chunk_count = 0

        for chunk in graph.stream({"messages": input_messages}, config, stream_mode="messages"):
            print(f"Processing chunk {chunk_count}: {chunk}\n")
            # Each chunk is a tuple: (AIMessageChunk, metadata_dict)
            if isinstance(chunk, tuple) and hasattr(chunk[0], "content"):
                #print(f"Chunk {chunk_count}: {chunk[0]}\n")
                msg_obj = chunk[0]
                content = msg_obj.content
                metadata = getattr(msg_obj, "response_metadata", {})
                is_tool_call = bool(getattr(msg_obj, "tool_calls", None))
                is_end = False
                print(f"metadata: {metadata}, is_tool_call: {is_tool_call}\n")
                if metadata.get("model_name") and metadata.get("model_name").find("ollama") != -1:
                    #print("llm provider is ollama\n\n")
                    is_end = metadata.get("done_reason") == "stop" and not is_tool_call
                elif metadata.get("model_name") and metadata.get("model_name").find("gemini") != -1:
                    # For Gemini, finish_reason is used
                    #print("llm provider is google_genai\n\n")
                    is_end = metadata.get("finish_reason") == "STOP" and not is_tool_call
                

                print(f"Chunk {chunk_count}: {content} | End: {is_end}")

                # Only publish if content changed
                if content != full_response:
                    publish_to_stream(
                        job_id,
                        "end" if is_end else "chunk",
                        content=content,
                        thread_id=thread_id,
                        chunk_id=chunk_count,
                        final=is_end
                    )
                    full_response = content
                    chunk_count += 1
            else:
                print(f"Chunk {chunk_count}: (no content found)")

        # Publish completion event if not already published as end
        # final_content = full_response or "I received your message and I'm ready to help with your tasks!"
        # publish_to_stream(
        #     job_id,
        #     "end",
        #     content=final_content,
        #     thread_id=thread_id,
        #     final=True
        # )
        
        # Update job status to completed
        redis_client.hset(f"job:{job_id}:meta", mapping={
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "result": full_response
        })
        
        return {"status": "success", "result": full_response}
        
    except Exception as e:
        error_msg = str(e)
        
        # Publish error event
        publish_to_stream(
            job_id,
            "error",
            error=error_msg,
            thread_id=thread_id
        )
        
        # Update job status to failed
        redis_client.hset(f"job:{job_id}:meta", mapping={
            "status": "failed",
            "failed_at": datetime.now().isoformat(),
            "error": error_msg
        })
        
        raise Exception(f"Job {job_id} failed: {error_msg}")

if __name__ == "__main__":
    print("Worker module loaded. Use 'rq worker' command to start the worker.")
