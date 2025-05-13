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

interface Annotation {
  id: string;
  content: string;
  position: { x: number; y: number };
  type: "bounding_box";
  color: string;
  pageNumber: number;
  width: number;
  height: number;
}

type AnnotationsByPage = {
  [key: string]: Annotation[];
};

// Dummy annotations data with bounding boxes
// We will replace the usage of this with our new hardcoded data
// const dummyAnnotations: AnnotationsByPage = {
//  "8": [
//    {
//      id: "1",
//      content: "Bounding box annotation",
//      position: { x: 0.08875, y: 0.2798529411764706 },
//      type: "bounding_box",
//      color: "#2196f3",
//      pageNumber: 1, // This was pageNumber: 1, but dummy data was for "8", let's assume it was a typo
//      width: 0.37999999999999995,
//      height: 0.0558088235294117,
//    },
//  ],
// };

// User provided hardcoded extraction data
const hardcodedExtractionData = {
  schedule: {
    value: "$25,000",
    page: "1",
    coordinates: {
      x: 0.08875,
      y: 0.2798529411764706,
      width: 0.37999999999999995,
      height: 0.0558088235294117,
    },
    source_snippet: "$25,000 Reducing by 50% at age 65.",
  },
  reduction: {
    value: "Reducing by 50% at age 65",
    page: "1",
    coordinates: {
      x: 0.08875,
      y: 0.2798529411764706,
      width: 0.37999999999999995,
      height: 0.0558088235294117,
    },
    source_snippet: "$25,000 Reducing by 50% at age 65.",
  },
  non_evidence_maximum: {
    value: "$5,850",
    page: "1",
    coordinates: {
      x: 0.08875,
      y: 0.6171323529411764,
      width: 0.82125,
      height: 0.2119117647058825,
    },
    source_snippet:
      "Any amount of LTD Insurance over $5,850 is subject to approval of evidence of insurability.",
  },
  termination_age: {
    value: "65",
    page: "1",
    coordinates: {
      x: 0.08875,
      y: 0.6171323529411764,
      width: 0.82125,
      height: 0.2119117647058825,
    },
    source_snippet: "Benefit period: to age 65",
  },
};

// Function to transform hardcodedExtractionData to AnnotationsByPage format
function transformExtractionToAnnotations(
  extractionData: typeof hardcodedExtractionData,
): AnnotationsByPage {
  const annotationsByPage: AnnotationsByPage = {};

  Object.entries(extractionData).forEach(([key, data]) => {
    const pageStr = data.page;
    if (!annotationsByPage[pageStr]) {
      annotationsByPage[pageStr] = [];
    }
    annotationsByPage[pageStr].push({
      id: key, // Use the field key as id
      content: data.value, // Use the extracted value as content for title tooltip
      position: { x: data.coordinates.x, y: data.coordinates.y },
      type: "bounding_box",
      color: "#f59e0b", // Default color, can be customized
      pageNumber: parseInt(pageStr, 10),
      width: data.coordinates.width,
      height: data.coordinates.height,
    });
  });

  return annotationsByPage;
}

// Hardcoded insurance extraction schema
const insuranceExtractionSchema: Record<string, Record<string, string>> = {
  life_insurance_ad_d: {
    schedule: "",
    reduction: "",
    non_evidence_maximum: "",
    termination_age: "",
  },
  dependent_life: {
    schedule: "",
    termination_age: "",
  },
  critical_illness: {
    schedule: "",
    impairments: "",
    termination_age: "",
  },
  long_term_disability: {
    schedule: "",
    monthly_maximum: "",
    tax_status: "",
    elimination_period: "",
    benefit_period: "",
    definition: "",
    offsets: "",
    cost_of_living_adjustment: "",
    pre_existing: "",
    survivor_benefit: "",
    non_evidence_maximum: "",
    termination_age: "",
  },
  short_term_disability: {
    schedule: "",
    weekly_maximum: "",
    tax_status: "",
    elimination_period: "",
    benefit_period: "",
    non_evidence_maximum: "",
    termination_age: "",
  },
  health_care: {
    prescription_drugs: "",
    pay_direct_drug_card: "",
    maximum: "",
    fertility_drugs: "",
    smoking_cessations: "",
    vaccines: "",
    major_medical: "",
    annual_deductible: "",
    hospitalization: "",
    orthotic_shoes: "",
    orthotic_inserts: "",
    hearing_aids: "",
    vision_care: "",
    eye_exams: "",
    paramedical_practitioners: "",
    included_specialists: "",
    out_of_country: "",
    maximum_duration: "",
    trip_cancellation: "",
    private_duty_nursing: "",
    survivor_benefit: "",
    termination_age: "",
  },
  dental_care: {
    annual_deductible: "",
    basic_and_preventative: "",
    periodontic_and_endodontic: "",
    annual_maximum: "",
    major_restorative_services: "",
    orthodontic_services: "",
    lifetime_maximum: "",
    recall_frequency: "",
    scaling_and_rooting_units: "",
    white_filings: "",
    fee_guide: "",
    survivor_benefit: "",
    termination_age: "",
  },
  notes_and_definitions: {
    dependent_child_definition: "",
    benefit_year: "",
    second_medical_opinion: "",
    eap: "",
    digital_wellness_program: "",
    virtual_healthcare_services: "",
  },
};

type ExtractionSection = Record<string, string>;

type ExtractionData = Record<string, ExtractionSection>;

function mergeExtractionWithSchema(
  schema: ExtractionData,
  extraction: ExtractionData,
): ExtractionData {
  const result: ExtractionData = {};
  for (const key in schema) {
    result[key] = { ...schema[key], ...(extraction?.[key] || {}) };
  }
  return result;
}

function toLabel(str: string) {
  return str.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function AnnotationLayer({
  annotations,
  pageNumber,
}: {
  annotations: Annotation[];
  pageNumber: number;
}) {
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
      {annotations
        .filter((ann) => ann.pageNumber === pageNumber)
        .map((annotation) => (
          <div
            key={annotation.id}
            style={{
              position: "absolute",
              left: `${annotation.position.x * 100}%`,
              top: `${annotation.position.y * 96}%`,
              width: `${annotation.width * 100}%`,
              height: `${annotation.height * 150}%`,
              border: `2px solid ${annotation.color}`,
              backgroundColor: `${annotation.color}20`,
              pointerEvents: "auto",
              cursor: "pointer",
              zIndex: 1000,
            }}
            title={annotation.content}
          />
        ))}
    </div>
  );
}

function ExtractionPanel({
  extraction,
  loading,
  error,
}: {
  extraction: ExtractionData;
  loading: boolean;
  error: string | null;
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
      <h2 style={{ fontWeight: 600, fontSize: 22, marginBottom: 20 }}>
        Extraction
      </h2>
      {loading ? (
        <div>Loading extraction...</div>
      ) : error ? (
        <div style={{ color: "red" }}>{error}</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {Object.entries(extraction).map(([section, fields]) => (
            <div
              key={section}
              style={{
                background: "#fff",
                borderRadius: 8,
                boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
                padding: 16,
                border: "1px solid #e5e7eb",
              }}
            >
              <div
                style={{
                  fontWeight: 600,
                  fontSize: 16,
                  marginBottom: 10,
                  color: "#6366f1",
                  letterSpacing: 0.5,
                }}
              >
                {toLabel(section)}
              </div>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <tbody>
                  {Object.entries(fields).map(([key, value]) => (
                    <tr key={key}>
                      <td
                        style={{
                          fontWeight: 500,
                          padding: "4px 8px 4px 0",
                          color: "#374151",
                          width: 180,
                          verticalAlign: "top",
                        }}
                      >
                        {toLabel(key)}
                      </td>
                      <td
                        style={{
                          padding: "4px 0",
                          color: value ? "#111" : "#aaa",
                          fontStyle: value ? "normal" : "italic",
                        }}
                      >
                        {value || "(empty)"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function DocumentReviewPage() {
  const params = useParams();
  const docId = Array.isArray(params?.docId) ? params.docId[0] : params?.docId;
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [extraction, setExtraction] = useState<ExtractionData>({});
  const [numPages, setNumPages] = useState<number>(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clickPosition, setClickPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const [selectedPage, setSelectedPage] = useState<number | null>(null);

  // Transform the hardcoded data for the AnnotationLayer
  const transformedAnnotations = transformExtractionToAnnotations(
    hardcodedExtractionData,
  );

  useEffect(() => {
    if (!docId) return;
    setLoading(true);
    setError(null);
    fetch(`/api/v1/documents/${docId}`)
      .then(async (res) => {
        if (!res.ok) throw new Error("Failed to fetch document data");
        return res.json();
      })
      .then((data) => {
        setPdfUrl(data.url);
        setExtraction(data.extraction || {});
      })
      .catch((err) => {
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }, [docId]);

  const mergedExtraction = mergeExtractionWithSchema(
    insuranceExtractionSchema,
    extraction as ExtractionData,
  );

  const handlePageClick = (
    e: React.MouseEvent<HTMLDivElement>,
    pageNumber: number,
  ) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setClickPosition({ x, y });
    setSelectedPage(pageNumber);

    // Log the coordinates for easy copying
    console.log(`Page ${pageNumber} coordinates:`, { x, y });
  };

  return (
    <div style={{ display: "flex", height: "100vh", background: "#f3f4f6" }}>
      <ExtractionPanel
        extraction={mergedExtraction}
        loading={loading}
        error={error}
      />
      {/* PDF Viewer Panel */}
      <div
        style={{
          flex: 1,
          background: "#fff",
          display: "flex",
          flexDirection: "column",
          minWidth: 0,
        }}
      >
        {loading ? (
          <div style={{ padding: 20 }}>Loading PDF...</div>
        ) : error ? (
          <div style={{ padding: 20, color: "red" }}>{error}</div>
        ) : pdfUrl ? (
          <div
            style={{
              flex: 1,
              background: "#f3f4f6",
              display: "flex",
              flexDirection: "column",
              overflow: "auto",
              padding: "20px 0",
            }}
          >
            <Document
              file={pdfUrl}
              onLoadSuccess={({ numPages }) => setNumPages(numPages)}
              onLoadError={(err) => setError(err.message)}
              loading={<div style={{ padding: 20 }}>Loading PDF...</div>}
            >
              {Array.from(new Array(numPages), (el, index) => (
                <div
                  key={`page_${index + 1}`}
                  style={{
                    margin: "0 auto 20px",
                    background: "#fff",
                    padding: "20px",
                    borderRadius: "8px",
                    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
                    position: "relative",
                    cursor: "crosshair",
                  }}
                  onClick={(e) => handlePageClick(e, index + 1)}
                >
                  <Page
                    pageNumber={index + 1}
                    width={Math.min(900, window.innerWidth - 500)}
                    renderTextLayer={true}
                    renderAnnotationLayer={true}
                  />
                  <AnnotationLayer
                    annotations={transformedAnnotations[index + 1] || []}
                    pageNumber={index + 1}
                  />
                  {clickPosition && selectedPage === index + 1 && (
                    <div
                      style={{
                        position: "absolute",
                        left: clickPosition.x,
                        top: clickPosition.y,
                        width: "10px",
                        height: "10px",
                        backgroundColor: "red",
                        borderRadius: "50%",
                        transform: "translate(-50%, -50%)",
                        pointerEvents: "none",
                      }}
                    />
                  )}
                </div>
              ))}
            </Document>
            {clickPosition && selectedPage && (
              <div
                style={{
                  position: "fixed",
                  bottom: 20,
                  right: 20,
                  background: "white",
                  padding: "10px 20px",
                  borderRadius: "8px",
                  boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                  zIndex: 1000,
                }}
              >
                <div>Page: {selectedPage}</div>
                <div>X: {Math.round(clickPosition.x)}</div>
                <div>Y: {Math.round(clickPosition.y)}</div>
              </div>
            )}
          </div>
        ) : (
          <div style={{ padding: 20 }}>No PDF found.</div>
        )}
      </div>
    </div>
  );
}
