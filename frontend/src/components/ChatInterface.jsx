// src/components/ChatInterface.jsx

import React, { useState, useRef, useEffect } from 'react';
import { Send, MessageCircle, X } from 'lucide-react';
import { todoAPI } from '../services/api';

const ChatInterface = ({ userId, onTodoUpdate, isOpen, onToggle }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState(null);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [currentJobId, setCurrentJobId] = useState(null);
  const messagesEndRef = useRef(null);
  const streamCloseRef = useRef(null);
  const streamingMessageRef = useRef('');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  // Cleanup stream connection on unmount
  useEffect(() => {
    return () => {
      if (streamCloseRef.current) {
        streamCloseRef.current();
      }
    };
  }, []);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = { role: 'user', content: inputMessage };
    if(messages.length === 0) { 
      setMessages([userMessage]);
    } else {
      setMessages(prev => [...prev, userMessage]);
    }
    setInputMessage('');
    setIsLoading(true);
    setStreamingMessage('');

    try {
      // Send message and get job info
      const response = threadId 
        ? await todoAPI.continueChat(userId, threadId, inputMessage)
        : await todoAPI.startNewChat(userId, inputMessage);

      if (!threadId && response.thread_id) {
        setThreadId(response.thread_id);
      }

      setCurrentJobId(response.job_id);

      // Start streaming results
      const closeStream = todoAPI.streamJobResults(
        response.job_id,
        (data) => {
          switch (data.type) {
            case 'start':
              console.log('Stream started');
              //setStreamingMessage('🤔 Thinking...');
              break;
            case 'chunk':
              setStreamingMessage(prev => {
                const updated = (prev || "") + data.content;
                streamingMessageRef.current = updated;
                return updated;
              });
              console.log('Received chunk:', data.content);
              break;
            case 'end':
              // Use the ref to get the latest value
              const finalContent = streamingMessageRef.current + (data.content || "");
              setMessages(prev => [...prev, { role: 'assistant', content: finalContent }]);
              setStreamingMessage('');
              setIsLoading(false);
              console.log('Stream ended:', isLoading);
              setCurrentJobId(null);
              onTodoUpdate();
              streamingMessageRef.current = '';
              break;
          }
        },
        (error) => {
          console.error('Streaming error:', error);
          setMessages(prev => [...prev, { 
            role: 'assistant', 
            content: 'Sorry, I encountered an error. Please try again.' 
          }]);
          setStreamingMessage('');
          setIsLoading(false);
          setCurrentJobId(null);
        },
        (data) => {
          // Completion callback
          setIsLoading(false);
          setCurrentJobId(null);
        }
      );

      streamCloseRef.current = closeStream;

    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }]);
      setStreamingMessage('');
      setIsLoading(false);
      setCurrentJobId(null);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg transition-colors duration-200 z-50"
      >
        <MessageCircle className="h-6 w-6" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 h-[500px] bg-white rounded-lg shadow-xl border border-gray-200 flex flex-col z-50">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-gray-900">Todo mAIstro</h3>
          {currentJobId && (
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
              Job: {currentJobId.slice(0, 8)}...
            </span>
          )}
        </div>
        <button
          onClick={onToggle}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <MessageCircle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>Hi! I'm your AI assistant.</p>
            <p className="text-sm">Ask me to help manage your todos!</p>
            <p className="text-xs mt-2 text-blue-600">Now powered by Redis queues!</p>
          </div>
        )}
        
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] p-3 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            </div>
          </div>
        ))}

        {streamingMessage.length == 0 && isLoading && (
          <div className="flex justify-start">
            <div className="max-w-[80%] p-3 rounded-lg bg-gray-100 text-gray-900">
              <div className="flex items-center mt-2">
                <div className="animate-pulse text-blue-600">●</div>
                <div className="animate-pulse text-blue-600 ml-1">●</div>
                <div className="animate-pulse text-blue-600 ml-1">●</div>
              </div>
            </div>
          </div>
        )}

        {streamingMessage && (
          <div className="flex justify-start">
            <div className="max-w-[80%] p-3 rounded-lg bg-gray-100 text-gray-900">
              <p className="text-sm whitespace-pre-wrap">{streamingMessage}</p>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me to add, update, or organize your todos..."
            className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows="2"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !inputMessage.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white p-2 rounded-lg transition-colors duration-200"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
        {streamingMessage.length == 0 && isLoading && (
          <div className="mt-2 text-xs text-blue-600">
            Job queued and processing...
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;
