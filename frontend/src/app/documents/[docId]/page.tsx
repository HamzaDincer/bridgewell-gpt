"use client";
import React, { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/esm/Page/AnnotationLayer.css";
import "react-pdf/dist/esm/Page/TextLayer.css";
import { BENEFIT_FIELDS } from "@/constants/benefitFields";

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

function toLabel(str: string) {
  return str.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
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
      if (!field || typeof field.page !== "number" || !field.coordinates) {
        return;
      }

      const { x, y, width, height } = field.coordinates;
      if (x === null || y === null || width === null || height === null) {
        return;
      }

      const pageNumber = field.page + 1;
      const coordKey = `${pageNumber}-${x}-${y}-${width}-${height}`;

      let existingAnnotation = annotationMap.get(coordKey);
      const newContent = `${toLabel(sectionName)} - ${toLabel(fieldName)}: ${
        field.value
      }\n\nSource: ${field.source_snippet || "N/A"}`;

      if (existingAnnotation) {
        existingAnnotation.content += "\n---\n" + newContent;
      } else {
        existingAnnotation = {
          id: coordKey, // Use coordKey as stable ID instead of random
          content: newContent,
          position: { x, y },
          type: "bounding_box",
          color: "#f59e0b",
          pageNumber,
          width,
          height,
        };
        annotationMap.set(coordKey, existingAnnotation);
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
}) {
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
            const sectionObj =
              sectionRaw &&
              typeof sectionRaw === "object" &&
              !Array.isArray(sectionRaw)
                ? (sectionRaw as unknown as Record<string, ExtractionField>)
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
                  {section.replace(/_/g, " ").toUpperCase()}
                </h3>
                <div
                  style={{
                    display: "table",
                    width: "100%",
                    borderCollapse: "collapse",
                  }}
                >
                  {fields.map((field) => {
                    const fieldObj = sectionObj?.[field];
                    return (
                      <div
                        key={field}
                        onClick={function (event) {
                          if (
                            fieldObj?.page !== undefined &&
                            fieldObj?.coordinates
                          ) {
                            const pageNumber = (fieldObj.page ?? 0) + 1;
                            const { x, y, width, height } =
                              fieldObj.coordinates;
                            const annotationId = `${pageNumber}-${x}-${y}-${width}-${height}`;
                            const fieldRect = (
                              event.currentTarget as HTMLElement
                            ).getBoundingClientRect();
                            lastClickedFieldRef.current =
                              event.currentTarget as HTMLElement;
                            onFieldClick({ fieldRect, annotationId });
                          }
                        }}
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
                          {field.replace(/_/g, " ")}
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
                          {fieldObj?.value || "(Not found)"}
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
function ChatBox({ docId }: { docId: string }) {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>(
    [],
  );
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;
    setMessages((msgs) => [...msgs, { role: "user", content: input }]);
    setLoading(true);
    try {
      // Replace with your backend chat endpoint
      const res = await fetch(`/api/v1/documents/${docId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      const data = await res.json();
      setMessages((msgs) => [
        ...msgs,
        { role: "assistant", content: data.response || "(No response)" },
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

    if (params.docId) {
      fetchData();
    }
  }, [params.docId]);

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
      const sectionObj =
        sectionRaw &&
        typeof sectionRaw === "object" &&
        !Array.isArray(sectionRaw)
          ? (sectionRaw as unknown as Record<string, ExtractionField>)
          : undefined;
      for (const field of fields) {
        const fieldObj = sectionObj?.[field];
        extractionDisplay[section][field] =
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
            />
          ) : (
            <ChatBox docId={params.docId as string} />
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
                      annotations={annotationsByPage[pageNum] || []}
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
