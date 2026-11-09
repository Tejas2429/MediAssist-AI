import React from 'react';
import { AlertOctagon, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

interface TriageBadgeProps {
  level: 'EMERGENCY' | 'URGENT' | 'ROUTINE' | 'SELF_CARE' | string;
  score?: number;
  size?: 'sm' | 'md' | 'lg';
}

export const TriageBadge: React.FC<TriageBadgeProps> = ({ level, score, size = 'md' }) => {
  const normLevel = level.toUpperCase();

  let bg = 'bg-slate-100 text-slate-800 border-slate-300';
  let icon = <Clock className="w-3.5 h-3.5 mr-1" />;
  let label = level;

  if (normLevel === 'EMERGENCY') {
    bg = 'bg-red-50 text-red-700 border-red-300 ring-1 ring-red-400 emergency-pulse';
    icon = <AlertOctagon className="w-3.5 h-3.5 mr-1 text-red-600" />;
    label = `EMERGENCY ${score ? `(ESI ${score})` : ''}`;
  } else if (normLevel === 'URGENT') {
    bg = 'bg-amber-50 text-amber-800 border-amber-300 ring-1 ring-amber-300';
    icon = <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-600" />;
    label = `URGENT ${score ? `(ESI ${score})` : ''}`;
  } else if (normLevel === 'ROUTINE') {
    bg = 'bg-emerald-50 text-emerald-700 border-emerald-300';
    icon = <CheckCircle className="w-3.5 h-3.5 mr-1 text-emerald-600" />;
    label = `ROUTINE ${score ? `(ESI ${score})` : ''}`;
  } else if (normLevel === 'SELF_CARE') {
    bg = 'bg-blue-50 text-blue-700 border-blue-300';
    icon = <CheckCircle className="w-3.5 h-3.5 mr-1 text-blue-600" />;
    label = 'SELF-CARE';
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3.5 py-1.5 font-semibold',
  }[size];

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border shadow-sm ${bg} ${sizeClasses}`}
    >
      {icon}
      <span>{label}</span>
    </span>
  );
};

