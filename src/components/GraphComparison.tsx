/**
 * GraphComparison Component
 *
 * Shows the original flowchart image side-by-side with the generated graph,
 * plus a list of extracted edges. User can accept or reject the translation.
 *
 * KEY CONCEPTS:
 *
 * 1. CSS GRID vs FLEXBOX
 *    - Flexbox: One-dimensional layout (row OR column)
 *    - Grid: Two-dimensional layout (rows AND columns)
 *    We use grid here to create a two-column layout
 *
 * 2. RESPONSIVE DESIGN
 *    Tailwind uses breakpoint prefixes:
 *    - sm: (min-width: 640px)  - small screens
 *    - md: (min-width: 768px)  - medium screens
 *    - lg: (min-width: 1024px) - large screens
 *    Example: "grid-cols-1 lg:grid-cols-2" means:
 *    1 column by default, 2 columns on large screens
 *
 * 3. MODALS
 *    A modal is a popup that appears over the main content.
 *    We use state (isModalOpen) to show/hide it.
 */

"use client";

import { useState } from "react";

interface GraphComparisonProps {
  originalImage: string; // Base64 encoded
  graphImage: string; // Base64 encoded
  edges: [string, string, string][]; // Array of [source, label, target]
  onAccept: () => void;
  onReject: (feedback: string) => void;
  onReset: () => void;
}

export default function GraphComparison({
  originalImage,
  graphImage,
  edges,
  onAccept,
  onReject,
  onReset,
}: GraphComparisonProps) {
  // State for the feedback modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [feedback, setFeedback] = useState("");

  const handleRejectSubmit = () => {
    if (feedback.trim()) {
      onReject(feedback);
      setIsModalOpen(false);
      setFeedback("");
    }
  };

  return (
    <div className="space-y-8">
      {/* Image comparison grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Original image */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="bg-gray-100 px-4 py-3 border-b border-gray-200">
            <h3 className="font-medium text-gray-800">Original Flowchart</h3>
          </div>
          <div className="p-4">
            <img
              src={`data:image/png;base64,${originalImage}`}
              alt="Original flowchart"
              className="w-full h-auto rounded-lg"
            />
          </div>
        </div>

        {/* Generated graph */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="bg-blue-50 px-4 py-3 border-b border-blue-100">
            <h3 className="font-medium text-blue-800">Generated Graph</h3>
          </div>
          <div className="p-4">
            <img
              src={`data:image/png;base64,${graphImage}`}
              alt="Generated graph"
              className="w-full h-auto rounded-lg"
            />
          </div>
        </div>
      </div>

      {/* Extracted edges table */}
      <div className="bg-white rounded-xl shadow-md overflow-hidden">
        <div className="bg-gray-100 px-4 py-3 border-b border-gray-200">
          <h3 className="font-medium text-gray-800">
            Extracted Edges ({edges.length} total)
          </h3>
        </div>
        <div className="overflow-x-auto">
          {/* 
            Table styling with Tailwind:
            - w-full: full width
            - divide-y: adds borders between rows
          */}
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">
                  #
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">
                  Source
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">
                  Label
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">
                  Target
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {edges.map((edge, index) => (
                // Each row needs a unique "key" for React to track it
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {index + 1}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-800">{edge[0]}</td>
                  <td className="px-4 py-3 text-sm">
                    {edge[1] ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                        {edge[1]}
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-800">{edge[2]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <button
          onClick={onReset}
          className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 
                     hover:bg-gray-50 transition-colors font-medium"
        >
          Start Over
        </button>
        <button
          onClick={() => setIsModalOpen(true)}
          className="px-6 py-3 border border-red-300 rounded-lg text-red-700 
                     hover:bg-red-50 transition-colors font-medium"
        >
          Not Correct - Regenerate
        </button>
        <button
          onClick={onAccept}
          className="px-6 py-3 bg-green-600 text-white rounded-lg 
                     hover:bg-green-700 transition-colors font-medium"
        >
          Accept & Generate Test Paths
        </button>
      </div>

      {/* Feedback Modal */}
      {isModalOpen && (
        // Modal overlay - fixed position covers entire screen
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          {/* Modal content */}
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              What&apos;s Wrong?
            </h3>
            <p className="text-gray-600 text-sm mb-4">
              Please describe what&apos;s incorrect about the generated graph.
              This feedback will be used to regenerate a better translation.
            </p>

            {/* Textarea for feedback */}
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="E.g., The 'Yes' and 'No' labels are swapped on the second decision point..."
              className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg 
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         resize-none text-sm"
            />

            <div className="flex gap-3 justify-end mt-4">
              <button
                onClick={() => {
                  setIsModalOpen(false);
                  setFeedback("");
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 
                           hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleRejectSubmit}
                disabled={!feedback.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg 
                           hover:bg-blue-700 transition-colors
                           disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                Regenerate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
