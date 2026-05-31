import React from 'react';

interface MetricItem {
  label: string;
  value: string;
  unit: string;
  percentage?: number;
  status?: 'nominal' | 'warning' | 'critical';
}

interface MetricGridProps {
  metrics: MetricItem[];
}

const statusColor = {
  nominal: 'bg-data-pos',
  warning: 'bg-phosphor-amber',
  critical: 'bg-data-neg',
};

const statusGlow = {
  nominal: 'bg-data-pos',
  warning: 'bg-phosphor-amber',
  critical: 'bg-data-neg',
};

export default function MetricGrid({ metrics }: MetricGridProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 border-b border-phosphor-dim/30 bg-phosphor-deep">
      {metrics.map((metric, idx) => (
        <div
          key={idx}
          className={`p-4 ${idx < metrics.length - 1 ? 'border-r border-phosphor-dim/20' : ''}`}
        >
          <span className="text-[10px] text-phosphor-dim tracking-wider uppercase block">
            {metric.label}
          </span>
          <div className="text-xl font-bold text-white tracking-tight mt-1 font-data">
            {metric.value}{' '}
            <span className="text-xs text-phosphor-amber">{metric.unit}</span>
          </div>
          {metric.percentage !== undefined && (
            <div className="w-full bg-phosphor-elevated h-1 mt-2 overflow-hidden relative">
              <div
                className={`${statusColor[metric.status || 'nominal']} h-full ${
                  metric.status === 'nominal' ? 'animate-pulse' : ''
                }`}
                style={{ width: `${metric.percentage}%` }}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
