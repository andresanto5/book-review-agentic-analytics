import { Copy, User, Bot } from "lucide-react";
import type { ChatMessage } from "../../types/ui";
import { Badge } from "../common/Badge";

interface MessageCardProps {
  message: ChatMessage;
}

export function MessageCard({ message }: MessageCardProps) {
  const isUser = message.role === "user";

  return (
    <article
      className={`flex gap-3 rounded-xl border px-4 py-3 text-base shadow-sm ${
        isUser
          ? "border-slate-200 bg-white"
          : "border-primary/15 bg-primary/5 backdrop-blur"
      }`}
    >
      <div
        className={`mt-1 flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${
          isUser
            ? "bg-slate-100 text-slate-700"
            : "bg-primary text-white shadow-md"
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <div className="flex-1">
        <div className="mb-1 flex items-center justify-between">
          <span className="text-xs font-medium text-slate-500">
            {isUser ? "Você" : "Agentic Analytics"}
          </span>
          <div className="flex items-center gap-2">
            {!isUser && message.responseMeta && (
              <div className="flex items-center gap-1.5">
                <Badge variant="primary">{message.responseMeta.strategy}</Badge>
                {message.responseMeta.targetEntity && (
                  <Badge variant="muted">{message.responseMeta.targetEntity}</Badge>
                )}
                {message.responseMeta.metricIntent && (
                  <Badge variant="outline">{message.responseMeta.metricIntent}</Badge>
                )}
              </div>
            )}
            <button
              type="button"
              onClick={() => navigator.clipboard.writeText(message.content)}
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-500 hover:bg-slate-50"
            >
              <Copy className="h-3 w-3" />
              Copiar
            </button>
          </div>
        </div>
        <p className="whitespace-pre-wrap text-[15px] leading-relaxed text-slate-800">
          {message.content}
        </p>
        {!isUser && message.responseMeta && (
          <p className="mt-1 text-xs text-slate-500">
            {message.responseMeta.totalTimeMs &&
              `Tempo: ${message.responseMeta.totalTimeMs.toFixed(1)} ms · `}
            {typeof message.responseMeta.structuredRows === "number" &&
              `Rows estruturado: ${message.responseMeta.structuredRows} · `}
            {typeof message.responseMeta.semanticRows === "number" &&
              `Rows semântico: ${message.responseMeta.semanticRows}`}
          </p>
        )}
      </div>
    </article>
  );
}

