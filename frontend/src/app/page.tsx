"use client";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import Dashboard from "@/components/Dashboard";

export default function HomePage() {
  useRequireAuth();
  return <Dashboard />;
}
