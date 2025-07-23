import React from 'react';
import { Clock, Calendar, CheckCircle, Circle, AlertCircle } from 'lucide-react';

const TodoCard = ({ todo, onStatusChange }) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'done':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'in progress':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      default:
        return <Circle className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'done':
        return 'border-green-200 bg-green-50';
      case 'in progress':
        return 'border-yellow-200 bg-yellow-50';
      default:
        return 'border-gray-200 bg-white';
    }
  };

  const formatDeadline = (deadline) => {
    if (!deadline) return null;
    try {
      const date = new Date(deadline);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return deadline;
    }
  };

  return (
    <div className={`p-4 rounded-lg border-2 shadow-sm hover:shadow-md transition-shadow duration-200 ${getStatusColor(todo.status)}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          {getStatusIcon(todo.status)}
          <span className="text-sm font-medium text-gray-600 capitalize">
            {todo.status}
          </span>
        </div>
        <select
          value={todo.status}
          onChange={(e) => onStatusChange && onStatusChange(todo.id, e.target.value)}
          className="text-xs bg-transparent border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="not started">Not Started</option>
          <option value="in progress">In Progress</option>
          <option value="done">Done</option>
          <option value="archived">Archived</option>
        </select>
      </div>

      <h3 className="font-semibold text-gray-900 mb-3 leading-tight">
        {todo.task}
      </h3>

      <div className="space-y-2 mb-3">
        {todo.time_to_complete && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Clock className="h-4 w-4" />
            <span>{todo.time_to_complete} minutes</span>
          </div>
        )}

        {todo.deadline && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Calendar className="h-4 w-4" />
            <span>{formatDeadline(todo.deadline)}</span>
          </div>
        )}
      </div>

      {todo.solutions && todo.solutions.length > 0 && (
        <div className="mt-3">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Solutions:</h4>
          <ul className="space-y-1">
            {todo.solutions.slice(0, 3).map((solution, index) => (
              <li key={index} className="text-sm text-gray-600 flex items-start gap-2">
                <span className="text-blue-500 mt-1">•</span>
                <span className="flex-1">{solution}</span>
              </li>
            ))}
            {todo.solutions.length > 3 && (
              <li className="text-sm text-gray-500 italic">
                +{todo.solutions.length - 3} more solutions...
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
};

export default TodoCard;
