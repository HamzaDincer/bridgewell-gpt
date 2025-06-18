import { useEffect, useState } from "react";

export function useDocumentPhase(docId: string | undefined) {
  const [phase, setPhase] = useState<string | null>(null);

  useEffect(() => {
    if (!docId) return;
    let interval: NodeJS.Timeout | null = null;
    const fetchPhase = async () => {
      try {
        const res = await fetch(`/api/v1/documents/${docId}`);
        if (res.ok) {
          const data = await res.json();
          setPhase(data.phase || null);
        }
      } catch {
        // ignore errors
      }
    };
    fetchPhase(); // initial fetch
    interval = setInterval(fetchPhase, 2000);
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [docId]);

  return phase;
}
