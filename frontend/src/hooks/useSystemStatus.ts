import { useEffect, useState } from "react";
import { getHealth } from "../api/client";

export type ApiStatus = "unknown" | "online" | "offline";

interface SystemStatus {
  apiStatus: ApiStatus;
  lastCheckedAt?: string;
}

export function useSystemStatus(): SystemStatus {
  const [status, setStatus] = useState<SystemStatus>({
    apiStatus: "unknown"
  });

  useEffect(() => {
    let cancelled = false;

    async function check() {
      try {
        const res = await getHealth();
        if (cancelled) return;

        setStatus({
          apiStatus: res.status === "ok" ? "online" : "offline",
          lastCheckedAt: new Date().toISOString()
        });
      } catch {
        if (cancelled) return;
        setStatus({
          apiStatus: "offline",
          lastCheckedAt: new Date().toISOString()
        });
      }
    }

    check();
    const interval = setInterval(check, 30000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return status;
}

