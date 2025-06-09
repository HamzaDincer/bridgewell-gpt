"use client";

import { useUpload } from "@/contexts/UploadContext";
import { UploadProgress } from "./UploadProgress";

export function UploadProgressContainer() {
  const { state, removeUpload } = useUpload();
  return <UploadProgress uploads={state.uploads} onDismiss={removeUpload} />;
}
