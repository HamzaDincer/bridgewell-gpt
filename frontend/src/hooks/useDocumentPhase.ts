import { useEffect, useState, useRef } from "react";

export function useDocumentPhase(docId: string | undefined) {
  const [phase, setPhase] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!docId) return;

    const fetchPhase = async () => {
      try {
        const res = await fetch(`/api/v1/ingest/status/${docId}`);
        if (res.ok) {
          const data = await res.json();
          setPhase(data.phase || null);
        }
      } catch {
        // ignore errors
      }
    };

    fetchPhase(); // initial fetch

    // Start polling
    intervalRef.current = setInterval(fetchPhase, 2000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [docId]);

  // Stop polling when phase is "completed"
  useEffect(() => {
    if (phase === "completed" && intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, [phase]);

  return phase;
}
