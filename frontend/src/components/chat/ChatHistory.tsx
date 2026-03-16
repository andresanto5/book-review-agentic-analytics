import { useEffect, useRef } from "react";
import type { ChatMessage } from "../../types/ui";
import { EmptyState } from "../common/EmptyState";
import { MessageCard } from "./MessageCard";

interface ChatHistoryProps {
  messages: ChatMessage[];
}

export function ChatHistory({ messages }: ChatHistoryProps) {
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Sempre que o histórico mudar, rola o container para o final (estilo ChatGPT),
  // mantendo a pergunta atual e a última resposta visíveis sem precisar rolar manualmente.
  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages]);

  if (!messages.length) {
    return (
      <div className="mt-6 flex justify-center">
        <div className="max-w-md flex-1">
          <EmptyState
            title="Comece fazendo uma pergunta ao agente."
            description="Use os exemplos na barra lateral para explorar os diferentes caminhos (structured, semantic, out_of_scope, composite)."
          />
        </div>
      </div>
    );
  }

  return (
    <div
      ref={scrollRef}
      className="flex flex-col gap-3"
    >
      {messages.map((m) => (
        <MessageCard key={m.id} message={m} />
      ))}
    </div>
  );
}

