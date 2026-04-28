/**
 * Main page component for the Flowchart Analyzer
 *
 * WHAT IS React.js?
 * React is a JavaScript library for building user interfaces.
 * It breaks the UI into reusable "components" (like building blocks).
 *
 * WHAT IS Next.js?
 * Next.js is a framework built on top of React that adds:
 * - File-based routing (each file in /app becomes a page)
 * - Server-side rendering (faster initial page load)
 * - API routes (backend code in the same project)
 *
 * WHAT IS TypeScript?
 * TypeScript is JavaScript with TYPE ANNOTATIONS.
 * Instead of: function add(a, b) { return a + b }
 * You write:  function add(a: number, b: number): number { return a + b }
 * This catches errors before runtime!
 */

"use client"; // This tells Next.js this component runs in the browser (client-side)

import { useState } from "react";
import ImageUpload from "@/components/ImageUpload";
import GraphComparison from "@/components/GraphComparison";
import PathDisplay from "@/components/PathDisplay";

/**
 * WHAT IS useState?
 * useState is a React "hook" that lets you store data that can CHANGE.
 * When the data changes, React automatically re-renders the component.
 *
 * const [value, setValue] = useState(initialValue);
 * - value: the current value
 * - setValue: function to update the value
 * - initialValue: what value starts as
 */

// TypeScript interface - defines the shape of our data
interface AnalysisResult {
  edges: [string, string, string][]; // Array of [source, label, target] tuples
  originalImage: string; // Base64 encoded image
  graphImage: string; // Base64 encoded image
  sessionId: string;
}

interface PathResult {
  numPaths: number;
  paths: {
    path_number: number;
    steps: string[];
    raw_path: [string, string, string][];
  }[];
  coloredGraph: string;
}

// STEP enum to track which stage we're at
type Step = "upload" | "compare" | "paths";

export default function Home() {
  // State variables - these control what the app displays
  const [currentStep, setCurrentStep] = useState<Step>("upload");
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(
    null,
  );
  const [pathResult, setPathResult] = useState<PathResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  /**
   * Handle file upload - called when user selects an image
   *
   * WHAT IS async/await?
   * async/await is syntax for handling asynchronous operations (things that take time).
   * - async: marks a function as asynchronous
   * - await: pauses execution until a Promise resolves
   *
   * Example: await fetch() waits for the HTTP request to complete
   */
  const handleUpload = async (file: File) => {
    setUploadedFile(file);
    setIsLoading(true);
    setError(null);

    try {
      // FormData is used to send files over HTTP
      const formData = new FormData();
      formData.append("file", file);

      // fetch() makes an HTTP request to our Flask API
      const response = await fetch("http://localhost:5000/api/translate", {
        method: "POST", // POST because we're sending data
        body: formData,
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || "Translation failed");
      }

      // Update state with the results
      setAnalysisResult({
        edges: data.edges,
        originalImage: data.original_image,
        graphImage: data.graph_image,
        sessionId: data.session_id,
      });
      setCurrentStep("compare");
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle acceptance of the translation
   *
   * When the user accepts the graph, we calculate the edge coverage paths
   */
  const handleAccept = async () => {
    if (!analysisResult) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:5000/api/generate-paths", {
        method: "POST",
        headers: {
          "Content-Type": "application/json", // Tell the server we're sending JSON
        },
        body: JSON.stringify({
          edges: analysisResult.edges,
          session_id: analysisResult.sessionId,
        }),
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || "Path generation failed");
      }

      setPathResult({
        numPaths: data.num_paths,
        paths: data.paths,
        coloredGraph: data.colored_graph,
      });
      setCurrentStep("paths");
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle rejection - regenerate with feedback
   */
  const handleReject = async (feedback: string) => {
    if (!uploadedFile || !analysisResult) return;

    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", uploadedFile);
      formData.append("feedback", feedback);
      formData.append("previous_edges", JSON.stringify(analysisResult.edges));

      const response = await fetch("http://localhost:5000/api/regenerate", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || "Regeneration failed");
      }

      setAnalysisResult({
        edges: data.edges,
        originalImage: data.original_image,
        graphImage: data.graph_image,
        sessionId: data.session_id,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Reset to start over
   */
  const handleReset = () => {
    setCurrentStep("upload");
    setAnalysisResult(null);
    setPathResult(null);
    setError(null);
    setUploadedFile(null);
  };

  /**
   * WHAT IS JSX?
   * JSX is a syntax extension that lets you write HTML-like code in JavaScript.
   * It looks like HTML but gets transformed into JavaScript function calls.
   *
   * Example: <div className="foo">Hello</div>
   * Becomes: React.createElement('div', {className: 'foo'}, 'Hello')
   */
  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 py-12 px-4">
      {/* Container for content */}
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            Process Cycle Test Generator
          </h1>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Upload a flowchart image to automatically extract decision points
            and generate test paths
          </p>
        </header>

        {/* Progress indicator */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center space-x-4">
            <StepIndicator
              number={1}
              label="Upload"
              active={currentStep === "upload"}
              completed={currentStep !== "upload"}
            />
            <div className="w-12 h-0.5 bg-gray-300" />
            <StepIndicator
              number={2}
              label="Compare"
              active={currentStep === "compare"}
              completed={currentStep === "paths"}
            />
            <div className="w-12 h-0.5 bg-gray-300" />
            <StepIndicator
              number={3}
              label="Paths"
              active={currentStep === "paths"}
              completed={false}
            />
          </div>
        </div>

        {/* Error display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-6 max-w-xl mx-auto">
            <p className="font-medium">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Loading overlay */}
        {isLoading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-8 flex flex-col items-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
              <p className="text-gray-700">Processing...</p>
            </div>
          </div>
        )}

        {/* Step content - conditional rendering based on currentStep */}
        {currentStep === "upload" && <ImageUpload onUpload={handleUpload} />}

        {currentStep === "compare" && analysisResult && (
          <GraphComparison
            originalImage={analysisResult.originalImage}
            graphImage={analysisResult.graphImage}
            edges={analysisResult.edges}
            onAccept={handleAccept}
            onReject={handleReject}
            onReset={handleReset}
          />
        )}

        {currentStep === "paths" && pathResult && (
          <PathDisplay
            paths={pathResult.paths}
            coloredGraph={pathResult.coloredGraph}
            numPaths={pathResult.numPaths}
            onReset={handleReset}
          />
        )}
      </div>
    </main>
  );
}

/**
 * Step indicator component - a small circle showing progress
 *
 * WHAT ARE PROPS?
 * Props are inputs to a component, passed from the parent.
 * They're read-only - you can't change them inside the component.
 */
interface StepIndicatorProps {
  number: number;
  label: string;
  active: boolean;
  completed: boolean;
}

function StepIndicator({
  number,
  label,
  active,
  completed,
}: StepIndicatorProps) {
  return (
    <div className="flex flex-col items-center">
      <div
        className={`
          w-10 h-10 rounded-full flex items-center justify-center font-medium
          ${
            active
              ? "bg-blue-600 text-white"
              : completed
                ? "bg-green-500 text-white"
                : "bg-gray-200 text-gray-500"
          }
        `}
      >
        {completed ? "✓" : number}
      </div>
      <span
        className={`text-sm mt-2 ${active ? "text-blue-600 font-medium" : "text-gray-500"}`}
      >
        {label}
      </span>
    </div>
  );
}
