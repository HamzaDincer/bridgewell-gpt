"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export function useRequireAuth() {
  const router = useRouter();

  useEffect(() => {
    if (typeof window !== "undefined") {
      const isAuthed = localStorage.getItem("bridgewell-auth") === "1";
      if (!isAuthed) {
        router.replace("/login");
      }
    }
  }, [router]);
}
