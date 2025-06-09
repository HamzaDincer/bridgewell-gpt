"use client";

import React, { createContext, useContext, useReducer, ReactNode } from "react";
import { UploadInfo } from "@/components/UploadProgress";

interface UploadState {
  uploads: UploadInfo[];
}

type UploadAction =
  | { type: "ADD_UPLOAD"; payload: UploadInfo }
  | {
      type: "UPDATE_UPLOAD";
      payload: { id: string; updates: Partial<UploadInfo> };
    }
  | { type: "REMOVE_UPLOAD"; payload: string };

const initialState: UploadState = {
  uploads: [],
};

const UploadContext = createContext<{
  state: UploadState;
  addUpload: (upload: Omit<UploadInfo, "id">) => string;
  updateUpload: (id: string, updates: Partial<UploadInfo>) => void;
  removeUpload: (id: string) => void;
} | null>(null);

function uploadReducer(state: UploadState, action: UploadAction): UploadState {
  switch (action.type) {
    case "ADD_UPLOAD":
      return {
        ...state,
        uploads: [...state.uploads, action.payload],
      };
    case "UPDATE_UPLOAD":
      return {
        ...state,
        uploads: state.uploads.map((upload) =>
          upload.id === action.payload.id
            ? { ...upload, ...action.payload.updates }
            : upload,
        ),
      };
    case "REMOVE_UPLOAD":
      return {
        ...state,
        uploads: state.uploads.filter((upload) => upload.id !== action.payload),
      };
    default:
      return state;
  }
}

export function UploadProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(uploadReducer, initialState);

  const addUpload = (upload: Omit<UploadInfo, "id">) => {
    const id = Math.random().toString(36).substring(7);
    dispatch({
      type: "ADD_UPLOAD",
      payload: { ...upload, id },
    });
    return id;
  };

  const updateUpload = (id: string, updates: Partial<UploadInfo>) => {
    dispatch({
      type: "UPDATE_UPLOAD",
      payload: { id, updates },
    });
  };

  const removeUpload = (id: string) => {
    dispatch({
      type: "REMOVE_UPLOAD",
      payload: id,
    });
  };

  return (
    <UploadContext.Provider
      value={{
        state,
        addUpload,
        updateUpload,
        removeUpload,
      }}
    >
      {children}
    </UploadContext.Provider>
  );
}

export function useUpload() {
  const context = useContext(UploadContext);
  if (!context) {
    throw new Error("useUpload must be used within an UploadProvider");
  }
  return context;
}
