import type { ReactNode } from "react";

interface BadgeProps {
  variant?:
    | "default"
    | "primary"
    | "success"
    | "warning"
    | "danger"
    | "muted"
    | "outline";
  children: ReactNode;
}

export function Badge({ variant = "default", children }: BadgeProps) {
  const base =
    "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium";

  const variants: Record<string, string> = {
    default: "bg-slate-100 text-slate-800",
    primary: "bg-primary/10 text-primary",
    success: "bg-success/10 text-success",
    warning: "bg-warning/10 text-warning",
    danger: "bg-danger/10 text-danger",
    muted: "bg-slate-50 text-slate-500",
    outline: "border border-slate-200 text-slate-700"
  };

  return <span className={`${base} ${variants[variant]}`}>{children}</span>;
}

