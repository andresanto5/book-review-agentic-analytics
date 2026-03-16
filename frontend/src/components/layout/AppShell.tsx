import type { ReactNode } from "react";

interface AppShellProps {
  topBar: ReactNode;
  sidebar: ReactNode;
  main: ReactNode;
  rightPanels: ReactNode;
  bottomArea: ReactNode;
}

export function AppShell({
  topBar,
  sidebar,
  main,
  rightPanels,
  bottomArea
}: AppShellProps) {
  return (
    <div className="flex h-screen flex-col bg-background">
      {topBar}
      <div className="flex flex-1 flex-col gap-2 px-3 pb-2 pt-2">
        <div className="flex min-h-0 flex-1 gap-2">
          {sidebar}
          <main className="flex min-h-0 flex-1 flex-col gap-3">
            {main}
          </main>
          <section className="flex w-80 min-w-[18rem] flex-col gap-3 overflow-y-auto">
            {rightPanels}
            {bottomArea}
          </section>
        </div>
      </div>
    </div>
  );
}

