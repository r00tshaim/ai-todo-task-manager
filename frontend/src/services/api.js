// src/services/api.js

import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const todoAPI = {
  // Get user todos (unchanged)
  getUserTodos: async (userId) => {
    const response = await api.post('/todos/get', { user_id: userId });
    return response.data;
  },

  // Start new chat (now returns job_id)
  startNewChat: async (userId, message) => {
    const response = await api.post('/chat/new', {
      user_id: userId,
      message: message
    });
    return response.data;
  },

  // Continue existing chat (now returns job_id)
  continueChat: async (userId, threadId, message) => {
    const response = await api.post('/chat/continue', {
      user_id: userId,
      thread_id: threadId,
      message: message
    });
    return response.data;
  },

  // Get job status
  getJobStatus: async (jobId) => {
    const response = await api.get(`/jobs/${jobId}/status`);
    return response.data;
  },

  // Stream job results using SSE
  streamJobResults: async (jobId, onMessage, onError, onComplete) => {
    const eventSource = new EventSource(`${API_BASE_URL}/stream/${jobId}`);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'start':
            onMessage(data);
            break;
          case 'chunk':
            onMessage(data);
            break;
          case 'end':
            onMessage(data);
            eventSource.close();
            if (onComplete) onComplete(data);
            break;
          case 'error':
            if (onError) onError(data.error);
            eventSource.close();
            break;
          case 'keepalive':
            // Handle keepalive
            break;
        }
      } catch (error) {
        console.error('Error parsing SSE data:', error);
        if (onError) onError(error.message);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      if (onError) onError('Connection error');
      eventSource.close();
    };

    // Return function to close the connection
    return () => eventSource.close();
  }
};

export default api;
