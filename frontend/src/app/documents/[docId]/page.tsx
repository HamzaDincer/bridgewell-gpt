"use client";
import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/esm/Page/AnnotationLayer.css";
import "react-pdf/dist/esm/Page/TextLayer.css";

// Configure PDF.js worker (recommended way for Next.js App Router)
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

// Import types from @/types
import type { Annotation, AnnotationsByPage, ExtractionResult } from "@/types";

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

function scrollToPage(pageNumber: number) {
  const pageElement = document.querySelector(
    `[data-page-number="${pageNumber}"]`,
  );
  if (pageElement) {
    pageElement.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

function highlightAnnotation(annotationId: string) {
  // Remove previous highlight
  const previousHighlight = document.querySelector(".annotation-highlight");
  if (previousHighlight) {
    previousHighlight.classList.remove("annotation-highlight");
  }

  // Add highlight to new annotation
  const annotation = document.querySelector(
    `[data-annotation-id="${annotationId}"]`,
  );
  if (annotation) {
    annotation.classList.add("annotation-highlight");
  }
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
}: {
  extraction: ExtractionResult | null;
  loading: boolean;
  error: string | null;
  onFieldClick: (field: ActiveField) => void;
}) {
  return (
    <div
      style={{
        width: 420,
        background: "#f8f9fa",
        padding: 24,
        overflowY: "auto",
        height: "100vh",
        borderRight: "1px solid #e5e7eb",
      }}
    >
      {loading && <div>Loading...</div>}
      {error && <div style={{ color: "red" }}>{error}</div>}
      {extraction && (
        <div>
          {Object.entries(extraction.result).map(
            ([sectionName, section]) =>
              section && (
                <div key={sectionName} style={{ marginBottom: 32 }}>
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
                    {toLabel(sectionName)}
                  </h3>
                  <div
                    style={{
                      display: "table",
                      width: "100%",
                      borderCollapse: "collapse",
                    }}
                  >
                    {Object.entries(section).map(([fieldName, field]) => {
                      return (
                        <div
                          key={fieldName}
                          onClick={(e) => {
                            if (
                              field?.page !== undefined &&
                              field?.coordinates
                            ) {
                              const pageNumber = field.page + 1;
                              const { x, y, width, height } = field.coordinates;
                              const annotationId = `${pageNumber}-${x}-${y}-${width}-${height}`;
                              const fieldRect =
                                e.currentTarget.getBoundingClientRect();
                              onFieldClick({ fieldRect, annotationId });
                              scrollToPage(pageNumber);
                              highlightAnnotation(annotationId);
                            }
                          }}
                          className={field?.coordinates ? "clickable-row" : ""}
                          style={{
                            display: "table-row",
                            borderBottom: "1px solid #e5e7eb",
                            backgroundColor: field?.value
                              ? "transparent"
                              : "#fafafa",
                            cursor: field?.coordinates ? "pointer" : "default",
                            transition: "background-color 0.2s ease",
                          }}
                        >
                          <div
                            style={{
                              display: "table-cell",
                              padding: "8px 12px",
                              fontWeight: 500,
                              color: field?.value ? "#4b5563" : "#9ca3af",
                              width: "40%",
                              verticalAlign: "top",
                            }}
                          >
                            {toLabel(fieldName)}
                          </div>
                          <div
                            style={{
                              display: "table-cell",
                              padding: "8px 12px",
                              verticalAlign: "top",
                              color: field?.value ? "#000" : "#9ca3af",
                              fontStyle: field?.value ? "normal" : "italic",
                            }}
                          >
                            {field?.value || "(Not found)"}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ),
          )}
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

export default function DocumentReviewPage() {
  const params = useParams();
  const [numPages, setNumPages] = useState<number>(0);
  const [pdfUrl, setPdfUrl] = useState<string>("");
  const [extractionResult, setExtractionResult] =
    useState<ExtractionResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeField, setActiveField] = useState<ActiveField>(null);

  // Add click handler to clear active field
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      // Check if click is outside the extraction panel and annotation boxes
      const target = e.target as HTMLElement;
      const isClickable =
        target.closest(".clickable-row") ||
        target.closest("[data-annotation-id]");
      if (!isClickable) {
        setActiveField(null);
        // Also remove any existing highlight
        const previousHighlight = document.querySelector(
          ".annotation-highlight",
        );
        if (previousHighlight) {
          previousHighlight.classList.remove("annotation-highlight");
        }
      }
    };

    document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, []);

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

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <StyleManager />
      <ExtractionPanel
        extraction={extractionResult}
        loading={loading}
        error={error}
        onFieldClick={setActiveField}
      />
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
