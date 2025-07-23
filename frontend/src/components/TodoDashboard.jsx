import React, { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, RefreshCw, User } from 'lucide-react';
import TodoCard from './TodoCard';
import ChatInterface from './ChatInterface';
import { todoAPI } from '../services/api';

const TodoDashboard = () => {
  const [userId, setUserId] = useState('demo_user');
  const [isChatOpen, setIsChatOpen] = useState(false);
  const queryClient = useQueryClient();

  // Fetch todos
  const { data: todosData, isLoading, error, refetch } = useQuery({
    queryKey: ['todos', userId],
    queryFn: () => todoAPI.getUserTodos(userId),
    enabled: !!userId,
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  const todos = todosData?.todos || [];

  // Group todos by status
  const todosByStatus = {
    'not started': todos.filter(todo => todo.status === 'not started'),
    'in progress': todos.filter(todo => todo.status === 'in progress'),
    'done': todos.filter(todo => todo.status === 'done')
  };

  const handleTodoUpdate = () => {
    // Force refresh of todos
    refetch();
    queryClient.invalidateQueries({ queryKey: ['todos', userId] });
  };

  const handleStatusChange = async (todoId, newStatus) => {
    // This would typically make an API call to update the todo status
    // For now, we'll just refresh the data
    console.log(`Changing todo ${todoId} status to ${newStatus}`);
    // You can implement a PUT/PATCH endpoint in your backend for this
    setTimeout(() => {
      refetch();
    }, 1000);
  };

  const getColumnColor = (status) => {
    switch (status) {
      case 'not started':
        return 'bg-red-50 border-red-200';
      case 'in progress':
        return 'bg-yellow-50 border-yellow-200';
      case 'done':
        return 'bg-green-50 border-green-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getColumnTitle = (status) => {
    switch (status) {
      case 'not started':
        return 'To Do';
      case 'in progress':
        return 'In Progress';
      case 'done':
        return 'Done';
      default:
        return status;
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 mb-4">
            <svg className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Todos</h2>
          <p className="text-gray-600 mb-4">{error.message}</p>
          <button
            onClick={() => refetch()}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors duration-200"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Todo mAIstro</h1>
              <span className="ml-3 text-sm text-gray-500">AI-Powered Task Management</span>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-gray-500" />
                <input
                  type="text"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="Enter User ID"
                  className="border border-gray-300 rounded px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <button
                onClick={() => refetch()}
                disabled={isLoading}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg transition-colors duration-200"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <Plus className="h-5 w-5 text-blue-600" />
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Total Tasks</p>
                    <p className="text-2xl font-semibold text-gray-900">{todos.length}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">To Do</p>
                    <p className="text-2xl font-semibold text-gray-900">{todosByStatus['not started'].length}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                      <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">In Progress</p>
                    <p className="text-2xl font-semibold text-gray-900">{todosByStatus['in progress'].length}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Done</p>
                    <p className="text-2xl font-semibold text-gray-900">{todosByStatus['done'].length}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Kanban Board */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {Object.entries(todosByStatus).map(([status, statusTodos]) => (
                <div key={status} className={`rounded-lg border-2 ${getColumnColor(status)} p-4`}>
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-gray-900 capitalize">
                      {getColumnTitle(status)}
                    </h2>
                    <span className="bg-gray-200 text-gray-700 text-sm px-2 py-1 rounded-full">
                      {statusTodos.length}
                    </span>
                  </div>
                  
                  <div className="space-y-4">
                    {statusTodos.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        <p className="text-sm">No tasks in this column</p>
                        {status === 'not started' && (
                          <p className="text-xs mt-2">Ask the AI to add some tasks!</p>
                        )}
                      </div>
                    ) : (
                      statusTodos.map((todo) => (
                        <TodoCard
                          key={todo.id}
                          todo={todo}
                          onStatusChange={handleStatusChange}
                        />
                      ))
                    )}
                  </div>
                </div>
              ))}
            </div>

            {todos.length === 0 && (
              <div className="text-center py-12">
                <div className="text-gray-400 mb-4">
                  <svg className="h-24 w-24 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </div>
                <h3 className="text-xl font-medium text-gray-900 mb-2">No todos yet</h3>
                <p className="text-gray-600 mb-6">Start by chatting with your AI assistant to add some tasks!</p>
                <button
                  onClick={() => setIsChatOpen(true)}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition-colors duration-200 inline-flex items-center gap-2"
                >
                  <Plus className="h-5 w-5" />
                  Start Chatting
                </button>
              </div>
            )}
          </>
        )}
      </main>

      {/* Chat Interface */}
      <ChatInterface
        userId={userId}
        onTodoUpdate={handleTodoUpdate}
        isOpen={isChatOpen}
        onToggle={() => setIsChatOpen(!isChatOpen)}
      />
    </div>
  );
};

export default TodoDashboard;
