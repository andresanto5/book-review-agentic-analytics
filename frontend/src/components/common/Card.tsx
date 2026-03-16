import type { ReactNode } from "react";

interface CardProps {
  title?: string;
  description?: string;
  children?: ReactNode;
  className?: string;
  headerRight?: ReactNode;
}

export function Card({
  title,
  description,
  children,
  className = "",
  headerRight
}: CardProps) {
  return (
    <div
      className={`rounded-xl bg-white shadow-card border border-slate-100 ${className}`}
    >
      {(title || description) && (
        <div className="flex items-start justify-between border-b border-slate-100 px-4 py-3">
          <div>
            {title && (
              <h3 className="text-base font-semibold text-slate-900">{title}</h3>
            )}
            {description && (
              <p className="mt-0.5 text-sm text-slate-500">{description}</p>
            )}
          </div>
          {headerRight && <div className="ml-3">{headerRight}</div>}
        </div>
      )}
      <div className="px-4 py-3 text-sm text-slate-700">{children}</div>
    </div>
  );
}

