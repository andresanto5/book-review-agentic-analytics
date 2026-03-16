import { useState } from "react";
import { AppShell } from "./components/layout/AppShell";
import { TopBar } from "./components/layout/TopBar";
import { Sidebar } from "./components/layout/Sidebar";
import { ChatHistory } from "./components/chat/ChatHistory";
import { ChatInput } from "./components/chat/ChatInput";
import { LoadingState } from "./components/common/LoadingState";
import { ResponseSummaryPanel } from "./components/panels/ResponseSummaryPanel";
import { AgentFlowPanel } from "./components/panels/AgentFlowPanel";
import { ToolCallsPanel } from "./components/panels/ToolCallsPanel";
import { MetricsPanel } from "./components/panels/MetricsPanel";
import { SystemHealthPanel } from "./components/panels/SystemHealthPanel";
import { ArchitecturePanel } from "./components/panels/ArchitecturePanel";
import { useChat } from "./hooks/useChat";
import type { BedrockModelId } from "./types/ui";

export default function App() {
  const { state, sendMessage, clearConversation, modelId, setModelId } = useChat();
  const [draft, setDraft] = useState("");

  function handleExample(text: string, autoSend?: boolean) {
    setDraft(text);
    if (autoSend) {
      sendMessage(text);
      setDraft("");
    }
  }

  const topBar = (
    <TopBar
      modelId={modelId}
      onModelChange={(m: BedrockModelId) => setModelId(m)}
      onClearConversation={() => {
        clearConversation();
        setDraft("");
      }}
    />
  );

  const main = (
    <>
      {/* Área de histórico: ocupa quase toda a coluna central e rola internamente */}
      <section className="flex min-h-0 flex-1 flex-col rounded-xl border border-slate-200 bg-white/60 shadow-card">
        <div className="flex min-h-0 flex-1 flex-col gap-3 p-3 overflow-y-auto">
          <ChatHistory messages={state.messages} />
        </div>
      </section>
      {/* Input "suspenso" / sticky: sempre visível na parte inferior da coluna central */}
      <section className="sticky bottom-0 z-10 bg-background/90 pt-2 backdrop-blur">
        {state.isLoading && <LoadingState />}
        <ChatInput
          value={draft}
          onChange={setDraft}
          onSubmit={(value) => {
            sendMessage(value);
            setDraft("");
          }}
          disabled={state.isLoading}
        />
        {state.lastError && (
          <p className="mt-1 text-sm text-danger">
            Erro ao chamar a API: {state.lastError}
          </p>
        )}
      </section>
    </>
  );

  const rightPanels = (
    <>
      <ResponseSummaryPanel response={state.lastResponse} />
      <AgentFlowPanel response={state.lastResponse} />
      <ToolCallsPanel response={state.lastResponse} />
      <MetricsPanel metrics={state.metrics} />
      <SystemHealthPanel metrics={state.metrics} />
    </>
  );

  const bottomArea = (
    <ArchitecturePanel strategy={state.lastResponse?.strategy} />
  );

  return (
    <AppShell
      topBar={topBar}
      sidebar={
        <Sidebar
          onExampleClick={handleExample}
          modelId={modelId}
          setModelId={setModelId}
        />
      }
      main={main}
      rightPanels={rightPanels}
      bottomArea={bottomArea}
    />
  );
}

