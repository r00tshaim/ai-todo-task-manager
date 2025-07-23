import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const todoAPI = {
  // Get user todos
  getUserTodos: async (userId) => {
    const response = await api.post('/todos/get', { user_id: userId });
    return response.data;
  },

  // Start new chat
  startNewChat: async (userId, message) => {
    const response = await api.post('/chat/new', {
      user_id: userId,
      message: message
    });
    return response.data;
  },

  // Continue existing chat
  continueChat: async (userId, threadId, message) => {
    const response = await api.post('/chat/continue', {
      user_id: userId,
      thread_id: threadId,
      message: message
    });
    return response.data;
  },

  // Streaming chat
  streamChat: async (endpoint, payload, onMessage) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            onMessage(data);
          } catch (error) {
            console.error('Error parsing SSE data:', error);
          }
        }
      }
    }
  }
};

export default api;
