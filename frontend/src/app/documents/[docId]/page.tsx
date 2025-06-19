"use client";
import React, { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/esm/Page/AnnotationLayer.css";
import "react-pdf/dist/esm/Page/TextLayer.css";
import { BENEFIT_FIELDS } from "@/constants/benefitFields";
import { toast } from "sonner";
import { useDocumentPhase } from "@/hooks/useDocumentPhase";

// Configure PDF.js worker (recommended way for Next.js App Router)
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

// Import types from @/types
import type {
  Annotation,
  AnnotationsByPage,
  ExtractionResult,
  ExtractionField,
} from "@/types";

// Custom display names for benefit sections
const SECTION_LABELS: Record<string, string> = {
  life_insurance_ad_d: "LIFE INSURANCE and AD&D",
};

function toLabel(str: string) {
  return str.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

// Utility to get bounding box from either coordinates or bbox
function getBoundingBox(field: ExtractionField | null) {
  if (field?.coordinates && typeof field.coordinates === "object") {
    const { x, y, width, height } = field.coordinates;
    if (
      typeof x === "number" &&
      typeof y === "number" &&
      typeof width === "number" &&
      typeof height === "number"
    ) {
      return { x, y, width, height };
    }
  }
  // Handle bbox as array
  if (field?.bbox && Array.isArray(field.bbox) && field.bbox.length > 0) {
    const { l, t, r, b } = field.bbox[0] as {
      l: number;
      t: number;
      r: number;
      b: number;
    };
    if (
      typeof l === "number" &&
      typeof t === "number" &&
      typeof r === "number" &&
      typeof b === "number"
    ) {
      return { x: l, y: t, width: r - l, height: b - t };
    }
  }
  // Handle bbox as single object
  if (
    field?.bbox &&
    typeof field.bbox === "object" &&
    !Array.isArray(field.bbox) &&
    field.bbox !== null
  ) {
    const { l, t, r, b } = field.bbox as {
      l: number;
      t: number;
      r: number;
      b: number;
    };
    if (
      typeof l === "number" &&
      typeof t === "number" &&
      typeof r === "number" &&
      typeof b === "number"
    ) {
      return { x: l, y: t, width: r - l, height: b - t };
    }
  }
  return null;
}

// Function to transform extraction result to annotations
function transformExtractionToAnnotations(
  extractionResult: ExtractionResult | null,
): AnnotationsByPage {
  const annotationsByPage: AnnotationsByPage = {};
  const annotationMap = new Map();

  if (!extractionResult?.result) {
    return annotationsByPage;
  }

  Object.entries(extractionResult.result).forEach(([sectionName, section]) => {
    if (!section) {
      return;
    }

    Object.entries(section).forEach(([fieldName, field]) => {
      if (!field || typeof field.page !== "number") {
        return;
      }
      const bbox = getBoundingBox(field);
      if (!bbox) {
        return;
      }
      const { x, y, width, height } = bbox;
      if (x === null || y === null || width === null || height === null) {
        return;
      }
      const pageNumber = field.page + 1;
      const annotationId = `${pageNumber}-${x}-${y}-${width}-${height}`;
      let existingAnnotation = annotationMap.get(annotationId);
      const newContent = `${toLabel(sectionName)} - ${toLabel(fieldName)}: ${
        field.value
      }\n\nSource: ${field.source_snippet || "N/A"}`;
      if (existingAnnotation) {
        existingAnnotation.content += "\n---\n" + newContent;
      } else {
        existingAnnotation = {
          id: annotationId, // Use annotationId as stable ID
          content: newContent,
          position: { x, y },
          type: "bounding_box",
          color: "#f59e0b",
          pageNumber,
          width,
          height,
        };
        annotationMap.set(annotationId, existingAnnotation);
      }
    });
  });

  // Convert map to required format
  annotationMap.forEach((annotation) => {
    const pageStr = annotation.pageNumber.toString();
    if (!annotationsByPage[pageStr]) {
      annotationsByPage[pageStr] = [];
    }
    annotationsByPage[pageStr].push(annotation);
  });

  return annotationsByPage;
}

// Add a type for active field
type ActiveField = {
  fieldRect: DOMRect;
  annotationId: string;
} | null;

// Add SourceRef type for chat sources
export type SourceRef = {
  text: string;
  page: number;
  bbox: { x: number; y: number; width: number; height: number };
};

function ExtractionPanel({
  extraction,
  loading,
  error,
  onFieldClick,
  onBack,
  sidebarRef,
  handleExport,
  exporting,
  exportError,
  lastClickedFieldRef,
  docId,
  onExtractionUpdate,
}: {
  extraction: ExtractionResult | null;
  loading: boolean;
  error: string | null;
  onFieldClick: (field: ActiveField) => void;
  onBack: () => void;
  sidebarRef: React.RefObject<HTMLDivElement | null>;
  handleExport: () => void;
  exporting: boolean;
  exportError: string | null;
  lastClickedFieldRef: React.RefObject<HTMLElement | null>;
  docId: string;
  onExtractionUpdate: (result: ExtractionResult) => void;
}) {
  const [editingField, setEditingField] = useState<{
    section: string;
    field: string;
  } | null>(null);
  const [editValue, setEditValue] = useState("");
  const [saving, setSaving] = useState(false);
  const editBoxRef = useRef<HTMLTextAreaElement | null>(null);

  const handleDoubleClick = (
    section: string,
    fieldName: string,
    value: string,
  ) => {
    setEditingField({ section, field: fieldName });
    setEditValue(value || "");
  };

  const handleEditChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    setEditValue(e.target.value);
  };

  const handleEditSave = async () => {
    if (!editingField || !extraction) return;
    const { section, field: fieldName } = editingField;
    // Deep clone extraction result
    const updatedExtraction: ExtractionResult = JSON.parse(
      JSON.stringify(extraction),
    );
    // Ensure the field object has all required properties
    const sectionFields = updatedExtraction.result[
      section
    ] as unknown as Record<string, ExtractionField | null>;
    const prevField = sectionFields?.[fieldName];
    // Convert coordinates to bbox if present
    let bbox = undefined;
    if (prevField?.coordinates && typeof prevField.coordinates === "object") {
      const { x, y, width, height } = prevField.coordinates;
      if (
        typeof x === "number" &&
        typeof y === "number" &&
        typeof width === "number" &&
        typeof height === "number"
      ) {
        bbox = { l: x, t: y, r: x + width, b: y + height };
      }
    } else if (
      prevField?.bbox &&
      typeof prevField.bbox === "object" &&
      !Array.isArray(prevField.bbox)
    ) {
      // If bbox is a single object, use it directly
      bbox = prevField.bbox;
    } else if (
      prevField?.bbox &&
      Array.isArray(prevField.bbox) &&
      prevField.bbox.length > 0
    ) {
      bbox = prevField.bbox[0];
    }
    sectionFields[fieldName] = {
      value: editValue,
      page: prevField?.page ?? 0,
      bbox: bbox ? bbox : undefined,
      source_snippet: prevField?.source_snippet ?? "",
    } as ExtractionField;
    // Remove coordinates property if present
    if (sectionFields[fieldName] && "coordinates" in sectionFields[fieldName]) {
      delete (sectionFields[fieldName] as Partial<ExtractionField>).coordinates;
    }
    onExtractionUpdate(updatedExtraction);
    try {
      setSaving(true);
      await fetch(`/api/v1/documents/${docId}/extraction`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedExtraction),
      });
    } catch (e) {
      console.error("Failed to update extraction field", e);
    } finally {
      setSaving(false);
      setEditingField(null);
    }
  };

  const handleEditKeyDown = (
    e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleEditSave();
    } else if (e.key === "Escape") {
      setEditingField(null);
    }
  };

  const autoResize = () => {
    const el = editBoxRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = el.scrollHeight + "px";
    }
  };

  useEffect(() => {
    if (editingField) {
      autoResize();
    }
  }, [editValue, editingField]);

  return (
    <div
      ref={sidebarRef}
      style={{
        width: 420,
        background: "#f8f9fa",
        padding: 24,
        overflowY: "auto",
        height: "100vh",
        borderRight: "1px solid #e5e7eb",
      }}
    >
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <button
          onClick={onBack}
          style={{
            padding: "8px 16px",
            background: "#e5e7eb",
            border: "none",
            borderRadius: 4,
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          ← Back
        </button>
        <button
          onClick={handleExport}
          disabled={exporting}
          style={{
            padding: "8px 16px",
            background: exporting ? "#e5e7eb" : "#6366f1",
            color: exporting ? "#888" : "#fff",
            border: "none",
            borderRadius: 4,
            fontWeight: 600,
            cursor: exporting ? "not-allowed" : "pointer",
          }}
        >
          {exporting ? "Exporting..." : "Export to Excel"}
        </button>
      </div>
      {exportError && (
        <div style={{ color: "red", fontSize: 13, marginBottom: 8 }}>
          {exportError}
        </div>
      )}
      {loading && <div>Loading...</div>}
      {error && <div style={{ color: "red" }}>{error}</div>}
      {extraction && (
        <div>
          {Object.entries(BENEFIT_FIELDS).map(([section, fields]) => {
            const sectionRaw = extraction.result[section];
            // Only treat as Record<string, ExtractionField | null> if at least one value is an object with a 'value' property and sectionRaw is not an ExtractionField itself
            const sectionFields:
              | Record<string, ExtractionField | null>
              | undefined =
              sectionRaw &&
              typeof sectionRaw === "object" &&
              !Array.isArray(sectionRaw) &&
              !("value" in sectionRaw) &&
              Object.values(sectionRaw).some(
                (v) => v && typeof v === "object" && "value" in v,
              )
                ? (sectionRaw as Record<string, ExtractionField | null>)
                : undefined;
            return (
              <div key={section} style={{ marginBottom: 32 }}>
                <h3
                  style={{
                    fontWeight: 600,
                    fontSize: 16,
                    marginBottom: 16,
                    padding: "8px 12px",
                    backgroundColor: "#e5e7eb",
                    borderRadius: "4px",
                  }}
                >
                  {SECTION_LABELS[section] ||
                    section.replace(/_/g, " ").toUpperCase()}
                </h3>
                <div
                  style={{
                    display: "table",
                    width: "100%",
                    borderCollapse: "collapse",
                  }}
                >
                  {fields.map((fieldName: string) => {
                    if (!sectionFields) return null;
                    const fieldObj: ExtractionField | null | undefined =
                      sectionFields[fieldName];
                    const isEditing =
                      editingField &&
                      editingField.section === section &&
                      editingField.field === fieldName;
                    return (
                      <div
                        key={fieldName}
                        onClick={function (event) {
                          if (fieldObj?.page !== undefined) {
                            const bbox = getBoundingBox(fieldObj);
                            if (bbox) {
                              const { x, y, width, height } = bbox;
                              const pageNumber = (fieldObj.page ?? 0) + 1;
                              const annotationId = `${pageNumber}-${x}-${y}-${width}-${height}`;
                              const fieldRect = (
                                event.currentTarget as HTMLElement
                              ).getBoundingClientRect();
                              lastClickedFieldRef.current =
                                event.currentTarget as HTMLElement;
                              onFieldClick({ fieldRect, annotationId });
                            }
                          }
                        }}
                        onDoubleClick={() =>
                          handleDoubleClick(
                            section,
                            fieldName,
                            fieldObj?.value || "",
                          )
                        }
                        className={fieldObj?.coordinates ? "clickable-row" : ""}
                        data-field-id={
                          fieldObj?.page !== undefined && fieldObj?.coordinates
                            ? `${(fieldObj.page ?? 0) + 1}-${
                                fieldObj.coordinates.x
                              }-${fieldObj.coordinates.y}-${
                                fieldObj.coordinates.width
                              }-${fieldObj.coordinates.height}`
                            : undefined
                        }
                        style={{
                          display: "table-row",
                          borderBottom: "1px solid #e5e7eb",
                          backgroundColor: fieldObj?.value
                            ? "transparent"
                            : "#fafafa",
                          cursor: fieldObj?.coordinates ? "pointer" : "default",
                          transition: "background-color 0.2s ease",
                        }}
                      >
                        <div
                          style={{
                            display: "table-cell",
                            padding: "8px 12px",
                            fontWeight: 500,
                            color: fieldObj?.value ? "#4b5563" : "#9ca3af",
                          }}
                        >
                          {fieldName.replace(/_/g, " ")}
                        </div>
                        <div
                          style={{
                            display: "table-cell",
                            padding: "8px 12px",
                            verticalAlign: "top",
                            color: fieldObj?.value ? "#000" : "#9ca3af",
                            fontStyle: fieldObj?.value ? "normal" : "italic",
                          }}
                        >
                          {isEditing ? (
                            <textarea
                              ref={editBoxRef}
                              value={editValue}
                              autoFocus
                              onChange={handleEditChange}
                              onBlur={handleEditSave}
                              onKeyDown={handleEditKeyDown}
                              disabled={saving}
                              style={{
                                width: "100%",
                                fontSize: 15,
                                padding: "4px 8px",
                                border: "1px solid #6366f1",
                                borderRadius: 4,
                                resize: "none",
                                lineHeight: 1.5,
                                minHeight: 32,
                                maxHeight: 300,
                                overflow: "auto",
                              }}
                            />
                          ) : (
                            fieldObj?.value || "(Not found)"
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function ConnectorLine({
  activeField,
  annotations,
}: {
  activeField: ActiveField;
  annotations: Annotation[];
}) {
  if (!activeField) return null;

  const annotation = annotations.find((a) => a.id === activeField.annotationId);
  if (!annotation) return null;

  // Get the page element that contains the annotation
  const pageElement = document.querySelector(
    `[data-page-number="${annotation.pageNumber}"]`,
  );
  if (!pageElement) return null;

  const pageRect = pageElement.getBoundingClientRect();
  const fieldRect = activeField.fieldRect;

  // Calculate connector line points
  const startX = fieldRect.right;
  const startY = fieldRect.top + fieldRect.height / 2;
  const endX = pageRect.left + annotation.position.x * pageRect.width;
  const endY =
    pageRect.top +
    annotation.position.y * pageRect.height +
    (annotation.height * pageRect.height) / 2;

  return (
    <svg
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        zIndex: 9999,
      }}
    >
      <line
        x1={startX}
        y1={startY}
        x2={endX}
        y2={endY}
        stroke="#f59e0b"
        strokeWidth="2"
        strokeDasharray="4 2"
      />
    </svg>
  );
}

function AnnotationLayer({
  annotations,
  pageNumber,
}: {
  annotations: Annotation[];
  pageNumber: number;
}) {
  const pageAnnotations = annotations.filter(
    (ann) => ann.pageNumber === pageNumber,
  );

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        pointerEvents: "none",
      }}
    >
      {pageAnnotations.map((annotation) => (
        <div key={annotation.id}>
          <div
            data-annotation-id={annotation.id}
            style={{
              position: "absolute",
              left: `${annotation.position.x * 100}%`,
              top: `${annotation.position.y * 100}%`,
              width: `${annotation.width * 100}%`,
              height: `${annotation.height * 100}%`,
              border: `2px solid ${annotation.color}`,
              backgroundColor: `${annotation.color}20`,
              pointerEvents: "auto",
              cursor: "pointer",
              zIndex: 1000,
              transition: "all 0.3s ease",
            }}
            title={annotation.content}
          />
        </div>
      ))}
    </div>
  );
}

function StyleManager() {
  useEffect(() => {
    const style = document.createElement("style");
    style.textContent = `
      .annotation-highlight {
        border: 2px solid #2563eb !important;
        background-color: rgba(37, 99, 235, 0.2) !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.4);
        transition: background-color 0.2s, border 0.2s;
      }
      .clickable-row:hover {
        background-color: #f3f4f6 !important;
      }
    `;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, []);

  return null;
}

// Simple ChatBox component for sidebar chat
function ChatBox({
  docId,
  onSourceClick,
}: {
  docId: string;
  onSourceClick: (
    page: number,
    bbox: { x: number; y: number; width: number; height: number },
  ) => void;
}) {
  const [messages, setMessages] = useState<
    { role: string; content: string; sources?: SourceRef[] }[]
  >([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;
    setMessages((msgs) => [...msgs, { role: "user", content: input }]);
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/documents/${docId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [{ role: "user", content: input }],
          use_context: true,
          include_sources: true,
          context_filter: { docs_ids: [docId] },
        }),
      });
      const data = await res.json();
      const answer =
        data.choices?.[0]?.message?.content ||
        data.choices?.[0]?.delta?.content ||
        data.response ||
        "(No response)";
      // Parse sources
      const sources: SourceRef[] =
        data.choices?.[0]?.sources
          ?.map((src: unknown): SourceRef | null => {
            // src is expected to be { text: string, document: { doc_metadata: { page: number, bbox: [...] } } }
            if (!src || typeof src !== "object") return null;
            const s = src as {
              text: string;
              document?: {
                doc_metadata?: {
                  page?: number;
                  bbox?: {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                  }[];
                };
              };
            };
            const meta = s.document?.doc_metadata || {};
            const bbox =
              Array.isArray(meta.bbox) && meta.bbox.length > 0
                ? (meta.bbox[0] as {
                    x: number;
                    y: number;
                    width: number;
                    height: number;
                  })
                : null;
            return bbox && typeof meta.page === "number"
              ? {
                  text: s.text,
                  page: meta.page,
                  bbox,
                }
              : null;
          })
          .filter((v: SourceRef | null): v is SourceRef => Boolean(v)) || [];
      // Filter sources: remove duplicates, boilerplate, and very short text
      const seenTexts = new Set<string>();
      const filteredSources = sources.filter((src) => {
        const text = src.text.trim();
        if (
          seenTexts.has(text) ||
          text.length < 20 ||
          /^northern labs inc\.?/i.test(text) ||
          /^policy:/i.test(text) ||
          /^benefit summary/i.test(text) ||
          /^all employees/i.test(text) ||
          /^page \d+/i.test(text)
        ) {
          return false;
        }
        seenTexts.add(text);
        return true;
      });
      // Only include the first reference
      const limitedSources =
        filteredSources.length > 0 ? [filteredSources[0]] : [];
      setMessages((msgs) => [
        ...msgs,
        { role: "assistant", content: answer, sources: limitedSources },
      ]);
    } catch (e: unknown) {
      console.error("Error sending message:", e);
      setMessages((msgs) => [
        ...msgs,
        { role: "assistant", content: "Error: Could not get response." },
      ]);
    } finally {
      setLoading(false);
      setInput("");
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          marginBottom: 12,
          background: "#f3f4f6",
          borderRadius: 4,
          padding: 12,
        }}
      >
        {messages.length === 0 && (
          <div style={{ color: "#888" }}>
            Ask a question about this document.
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              marginBottom: 8,
              textAlign: msg.role === "user" ? "right" : "left",
            }}
          >
            <span
              style={{
                display: "inline-block",
                background: msg.role === "user" ? "#6366f1" : "#e5e7eb",
                color: msg.role === "user" ? "#fff" : "#111",
                borderRadius: 8,
                padding: "6px 12px",
                maxWidth: "80%",
                wordBreak: "break-word",
              }}
            >
              {msg.content}
            </span>
            {/* Show sources for assistant messages */}
            {msg.role === "assistant" &&
              msg.sources &&
              msg.sources.length > 0 && (
                <div style={{ marginTop: 8, textAlign: "left" }}>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "flex-start",
                      gap: 4,
                    }}
                  >
                    {msg.sources.map((src, j) => (
                      <button
                        key={j}
                        style={{
                          background: "#f8fafc",
                          border: "1px solid #e5e7eb",
                          borderRadius: 6,
                          padding: "3px 10px",
                          color: "#22c55e",
                          fontWeight: 500,
                          cursor: "pointer",
                          fontSize: 13,
                          display: "flex",
                          alignItems: "center",
                          gap: 4,
                          marginLeft: 0,
                          boxShadow: "none",
                        }}
                        onClick={() => onSourceClick(src.page, src.bbox)}
                      >
                        {j + 1}.{" "}
                        <span style={{ textDecoration: "underline" }}>
                          text
                        </span>{" "}
                        <span style={{ fontSize: 15 }}>&rarr;</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
          </div>
        ))}
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") sendMessage();
          }}
          placeholder="Type your question..."
          style={{
            flex: 1,
            padding: 8,
            borderRadius: 4,
            border: "1px solid #e5e7eb",
          }}
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          style={{
            padding: "8px 16px",
            borderRadius: 4,
            background: "#6366f1",
            color: "#fff",
            border: "none",
            fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}

// Utility to convert {b, l, r, t} to {x, y, width, height}
function convertBbox(bbox: unknown) {
  function isLTRB(
    obj: unknown,
  ): obj is { b: number; l: number; r: number; t: number } {
    return (
      typeof obj === "object" &&
      obj !== null &&
      "b" in obj &&
      typeof (obj as Record<string, unknown>).b === "number" &&
      "l" in obj &&
      typeof (obj as Record<string, unknown>).l === "number" &&
      "r" in obj &&
      typeof (obj as Record<string, unknown>).r === "number" &&
      "t" in obj &&
      typeof (obj as Record<string, unknown>).t === "number"
    );
  }
  if (isLTRB(bbox)) {
    const { b, l, r, t } = bbox;
    return {
      x: l,
      y: t,
      width: r - l,
      height: b - t,
    };
  }
  return bbox as { x: number; y: number; width: number; height: number };
}

export default function DocumentReviewPage() {
  const router = useRouter();
  const sidebarRef = useRef<HTMLDivElement | null>(null);
  const params = useParams();
  const [numPages, setNumPages] = useState<number>(0);
  const [pdfUrl, setPdfUrl] = useState<string>("");
  const [extractionResult, setExtractionResult] =
    useState<ExtractionResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeField, setActiveField] = useState<ActiveField>(null);
  const [sidebarTab, setSidebarTab] = useState<"fields" | "chat">("fields");
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const lastClickedFieldRef = useRef<HTMLElement | null>(null);
  const [chatHighlight, setChatHighlight] = useState<{
    page: number;
    rect: { x: number; y: number; width: number; height: number };
  } | null>(null);
  const [prevExtraction, setPrevExtraction] = useState<ExtractionResult | null>(
    null,
  );
  const phase = useDocumentPhase(params.docId as string | undefined);

  // Move fetchData to component scope so it can be reused
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log("Fetching data for document:", params.docId);

      // Fetch document data including PDF URL and extraction
      const docResponse = await fetch(`/api/v1/documents/${params.docId}`);
      if (!docResponse.ok) {
        throw new Error("Failed to fetch document data");
      }
      const docData = await docResponse.json();
      console.log("Document data received:", docData);
      setPdfUrl(docData.url);

      // Fetch extraction results
      const extractionResponse = await fetch(
        `/api/v1/documents/${params.docId}/extraction`,
      );
      if (!extractionResponse.ok) {
        throw new Error("Failed to fetch extraction data");
      }
      const extractionData = await extractionResponse.json();
      console.log("Extraction data received:", extractionData);
      setExtractionResult(extractionData);
    } catch (err) {
      console.error("Error fetching data:", err);
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (params.docId) {
      fetchData();
    }
  }, [params.docId]);

  // Remove scroll event logic and use setInterval for connector line updates
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (activeField) {
      interval = setInterval(() => {
        setActiveField((prev) => (prev ? { ...prev } : null));
      }, 100); // update every 100ms
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [activeField]);

  // Enhanced onFieldClick: scroll to annotation and highlight
  const handleFieldClick = (field: ActiveField) => {
    setActiveField(field);
    // Remove previous highlight
    document
      .querySelectorAll(".annotation-highlight")
      .forEach((el) => el.classList.remove("annotation-highlight"));
    if (field?.annotationId) {
      // Find the annotation element
      const annotation = document.querySelector(
        `[data-annotation-id="${field.annotationId}"]`,
      );
      if (annotation) {
        annotation.classList.add("annotation-highlight");
        annotation.scrollIntoView({ behavior: "smooth", block: "center" });
      } else {
        // Fallback: scroll to the page
        const pageNum = field.annotationId.split("-")[0];
        const pageElement = document.querySelector(
          `[data-page-number="${pageNum}"]`,
        );
        if (pageElement) {
          pageElement.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }
    }
  };

  // Update connector line on sidebar scroll by updating fieldRect using the ref
  useEffect(() => {
    const sidebar = sidebarRef.current;
    if (!sidebar || !activeField) return;

    const handleSidebarScroll = () => {
      if (lastClickedFieldRef.current) {
        const rect = lastClickedFieldRef.current.getBoundingClientRect();
        setActiveField((prev) => (prev ? { ...prev, fieldRect: rect } : null));
      }
    };
    sidebar.addEventListener("scroll", handleSidebarScroll);
    return () => {
      sidebar.removeEventListener("scroll", handleSidebarScroll);
    };
  }, [sidebarRef, activeField]);

  useEffect(() => {
    if (prevExtraction && extractionResult) {
      if (
        JSON.stringify(prevExtraction.result) !==
        JSON.stringify(extractionResult.result)
      ) {
        toast.success("New extraction results have been added!");
        // Re-fetch extraction data
        fetchData();
      }
    }
    setPrevExtraction(extractionResult);
  }, [extractionResult]);

  const handleDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
  };

  const annotationsByPage = transformExtractionToAnnotations(extractionResult);
  const allAnnotations = Object.values(annotationsByPage).flat();

  // Transform extractionResult?.result to Record<string, Record<string, string>>
  const extractionDisplay: Record<string, Record<string, string>> = {};
  if (extractionResult?.result) {
    for (const [section, fields] of Object.entries(BENEFIT_FIELDS)) {
      extractionDisplay[section] = {};
      const sectionRaw = extractionResult.result[section];
      // Only treat as Record<string, ExtractionField | null> if at least one value is an object with a 'value' property and sectionRaw is not an ExtractionField itself
      const sectionFields: Record<string, ExtractionField | null> | undefined =
        sectionRaw &&
        typeof sectionRaw === "object" &&
        !Array.isArray(sectionRaw) &&
        !("value" in sectionRaw) &&
        Object.values(sectionRaw).some(
          (v) => v && typeof v === "object" && "value" in v,
        )
          ? (sectionRaw as Record<string, ExtractionField | null>)
          : undefined;
      for (const fieldName of fields as readonly string[]) {
        if (!sectionFields) continue;
        const fieldObj: ExtractionField | null | undefined =
          sectionFields[fieldName];
        extractionDisplay[section][fieldName] =
          fieldObj && typeof fieldObj.value === "string" ? fieldObj.value : "";
      }
    }
  }

  // Export handler
  const handleExport = async () => {
    setExporting(true);
    setExportError(null);
    try {
      const res = await fetch(`/api/v1/documents/${params.docId}/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(extractionResult?.result),
      });
      if (!res.ok) {
        setExportError("Export failed");
        setExporting(false);
        return;
      }
      // Download the file
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "benefit_comparison.xlsx";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e: unknown) {
      setExportError(e instanceof Error ? e.message : "Export failed");
    } finally {
      setExporting(false);
    }
  };

  // In DocumentReviewPage, add the handler and pass it to ChatBox
  const handleChatSourceClick = (
    page: number,
    bbox:
      | { x: number; y: number; width: number; height: number }
      | { b: number; l: number; r: number; t: number },
  ) => {
    const rect = convertBbox(bbox);
    setChatHighlight({ page: page + 1, rect }); // +1 if PDF pages are 1-indexed
    // Scroll to the page container first
    const pageElement = document.querySelector(
      `[data-page-number='${page + 1}']`,
    );
    if (pageElement) {
      pageElement.scrollIntoView({ behavior: "smooth", block: "nearest" });
      // Wait for the highlight to render, then scroll to the highlight box
      setTimeout(() => {
        const highlight = pageElement.querySelector(
          "[data-annotation-id='chat-highlight']",
        );
        if (highlight) {
          highlight.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }, 300); // Adjust delay if needed for rendering
    }
  };

  // Auto-clear chat highlight after 4 seconds
  useEffect(() => {
    if (chatHighlight) {
      const timeout = setTimeout(() => setChatHighlight(null), 4000);
      return () => clearTimeout(timeout);
    }
  }, [chatHighlight]);

  // Remove the old polling useEffect for phase
  // Instead, useEffect to re-fetch extraction result when phase changes to 'completed'
  useEffect(() => {
    if (phase === "completed") {
      fetchData();
    }
  }, [phase]);

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <StyleManager />
      <div
        style={{
          width: 420,
          background: "#f8f9fa",
          borderRight: "1px solid #e5e7eb",
          display: "flex",
          flexDirection: "column",
          height: "100vh",
        }}
      >
        {/* Tab bar */}
        <div
          style={{
            display: "flex",
            borderBottom: "1px solid #e5e7eb",
            marginBottom: 8,
          }}
        >
          <button
            onClick={() => setSidebarTab("fields")}
            style={{
              flex: 1,
              padding: 12,
              background: sidebarTab === "fields" ? "#fff" : "transparent",
              border: "none",
              borderBottom:
                sidebarTab === "fields" ? "2px solid #6366f1" : "none",
              fontWeight: 600,
              cursor: "pointer",
              color: sidebarTab === "fields" ? "#6366f1" : "#222",
              transition: "background 0.2s",
            }}
          >
            Fields
          </button>
          <button
            onClick={() => setSidebarTab("chat")}
            style={{
              flex: 1,
              padding: 12,
              background: sidebarTab === "chat" ? "#fff" : "transparent",
              border: "none",
              borderBottom:
                sidebarTab === "chat" ? "2px solid #6366f1" : "none",
              fontWeight: 600,
              cursor: "pointer",
              color: sidebarTab === "chat" ? "#6366f1" : "#222",
              transition: "background 0.2s",
            }}
          >
            Chat
          </button>
        </div>
        {/* Tab content */}
        <div style={{ flex: 1, overflow: "hidden" }}>
          {sidebarTab === "fields" ? (
            <ExtractionPanel
              extraction={extractionResult}
              loading={loading}
              error={error}
              onFieldClick={handleFieldClick}
              onBack={() => router.back()}
              sidebarRef={sidebarRef}
              handleExport={handleExport}
              exporting={exporting}
              exportError={exportError}
              lastClickedFieldRef={lastClickedFieldRef}
              docId={params.docId as string}
              onExtractionUpdate={setExtractionResult}
            />
          ) : (
            <ChatBox
              docId={params.docId as string}
              onSourceClick={handleChatSourceClick}
            />
          )}
        </div>
      </div>
      <div
        style={{
          flex: 1,
          padding: 24,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          backgroundColor: "#f3f4f6",
        }}
      >
        {pdfUrl && (
          <Document
            file={pdfUrl}
            onLoadSuccess={handleDocumentLoadSuccess}
            loading={<div>Loading PDF...</div>}
          >
            {Array.from(new Array(numPages), (_, index) => {
              const pageNum = index + 1;
              return (
                <div
                  key={pageNum}
                  data-page-number={pageNum}
                  style={{
                    marginBottom: 24,
                    position: "relative",
                    backgroundColor: "white",
                    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                    borderRadius: "4px",
                  }}
                >
                  <Page
                    key={`page_${pageNum}`}
                    pageNumber={pageNum}
                    renderAnnotationLayer={false}
                    renderTextLayer={false}
                    width={800}
                  >
                    <AnnotationLayer
                      annotations={[
                        ...(annotationsByPage[pageNum] || []),
                        ...(chatHighlight && chatHighlight.page === pageNum
                          ? [
                              {
                                id: "chat-highlight",
                                content: "Chat Reference",
                                position: {
                                  x: chatHighlight.rect.x,
                                  y: chatHighlight.rect.y,
                                },
                                type: "bounding_box",
                                color: "#22c55e", // green
                                pageNumber: pageNum,
                                width: chatHighlight.rect.width,
                                height: chatHighlight.rect.height,
                              },
                            ]
                          : []),
                      ]}
                      pageNumber={pageNum}
                    />
                  </Page>
                </div>
              );
            })}
          </Document>
        )}
      </div>
      <ConnectorLine activeField={activeField} annotations={allAnnotations} />
    </div>
  );
}
