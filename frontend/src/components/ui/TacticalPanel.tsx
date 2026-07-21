import React from 'react';

interface TacticalPanelProps {
  title?: string;
  subtitle?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  bordered?: boolean;
}

export default function TacticalPanel({
  title,
  subtitle,
  icon,
  children,
  className = '',
  bordered = true,
}: TacticalPanelProps) {
  return (
    <div className={`flex flex-col ${bordered ? 'border border-phosphor-dim/30' : ''} bg-phosphor-surface ${className}`}>
      {(title || subtitle || icon) && (
        <div className="border-b border-phosphor-dim/20 p-4 bg-phosphor-deep/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {icon && <div className="text-phosphor-amber">{icon}</div>}
              <div>
                {title && (
                  <h3 className="text-xs font-display uppercase tracking-widest text-white">
                    {title}
                  </h3>
                )}
                {subtitle && (
                  <p className="text-[10px] text-phosphor-dim tracking-wider mt-0.5">
                    {subtitle}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
      <div className="flex-1">{children}</div>
    </div>
  );
}
