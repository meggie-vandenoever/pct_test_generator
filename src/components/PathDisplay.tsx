/**
 * PathDisplay Component
 *
 * Shows the edge coverage test paths and the colored graph visualization.
 * Each path is color-coded to match the graph.
 *
 * KEY CONCEPTS:
 *
 * 1. MAPPING ARRAYS
 *    In React, we use .map() to render lists:
 *    items.map((item, index) => <div key={index}>{item}</div>)
 *    Each item MUST have a unique "key" prop for React to track changes.
 *
 * 2. CONDITIONAL STYLING
 *    We can dynamically set styles using template literals:
 *    className={`base-styles ${condition ? 'style-a' : 'style-b'}`}
 *
 * 3. INLINE STYLES
 *    For dynamic values (like colors), we can use inline styles:
 *    style={{ backgroundColor: colors[index] }}
 *    Note: CSS properties use camelCase (backgroundColor not background-color)
 */

"use client";

interface Path {
  path_number: number;
  steps: string[];
  raw_path: [string, string, string][];
}

interface PathDisplayProps {
  paths: Path[];
  coloredGraph: string; // Base64 encoded
  numPaths: number;
  onReset: () => void;
  onBackToCompare: () => void;
}

// Same colors used in the Python get_colored_graph function
const PATH_COLORS = [
  "#ef4444", // red
  "#3b82f6", // blue
  "#22c55e", // green
  "#f97316", // orange
  "#a855f7", // purple
  "#78350f", // brown
  "#06b6d4", // cyan
  "#ec4899", // magenta (pink used as approximation)
  "#eab308", // gold (yellow used as approximation)
  "#f472b6", // pink
];

export default function PathDisplay({
  paths,
  coloredGraph,
  numPaths,
  onReset,
  onBackToCompare,
}: PathDisplayProps) {
  return (
    <div className="space-y-8">
      {/* Summary card */}
      <div className="bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl p-6 text-white shadow-lg">
        <div className="flex items-center gap-4">
          {/* Checkmark icon */}
          <div className="bg-white/20 rounded-full p-3">
            <svg
              className="w-8 h-8"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <div>
            <h2 className="text-2xl font-bold">Complete!</h2>
            <p className="text-green-100">
              {numPaths} test path{numPaths !== 1 ? "s" : ""} needed for test
              depth level-1
            </p>
          </div>
        </div>
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Colored graph */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="bg-purple-50 px-4 py-3 border-b border-purple-100">
            <h3 className="font-medium text-purple-800">
              Color-Coded Test Paths
            </h3>
          </div>
          <div className="p-4">
            <img
              src={`data:image/png;base64,${coloredGraph}`}
              alt="Colored graph showing test paths"
              className="w-full h-auto rounded-lg"
            />
            <p className="text-xs text-gray-500 mt-3 text-center">
              Each color represents a different test path
            </p>
          </div>
        </div>

        {/* Path list */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="bg-blue-50 px-4 py-3 border-b border-blue-100">
            <h3 className="font-medium text-blue-800">Test Paths to Execute</h3>
          </div>
          <div className="p-4 space-y-4 max-h-[600px] overflow-y-auto">
            {paths.map((path, pathIndex) => (
              <div
                key={path.path_number}
                className="border rounded-lg overflow-hidden"
                style={{
                  borderColor: PATH_COLORS[pathIndex % PATH_COLORS.length],
                }}
              >
                {/* Path header */}
                <div
                  className="px-4 py-2 flex items-center gap-2"
                  style={{
                    backgroundColor: `${PATH_COLORS[pathIndex % PATH_COLORS.length]}15`,
                  }}
                >
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{
                      backgroundColor:
                        PATH_COLORS[pathIndex % PATH_COLORS.length],
                    }}
                  />
                  <span className="font-medium text-gray-800">
                    Path {path.path_number}
                  </span>
                  <span className="text-sm text-gray-500 ml-auto">
                    {path.steps.length} steps
                  </span>
                </div>

                {/* Path steps */}
                <div className="px-4 py-3 bg-white">
                  <ol className="space-y-2">
                    {path.steps.map((step, stepIndex) => (
                      <li
                        key={stepIndex}
                        className="flex items-start gap-2 text-sm"
                      >
                        <span
                          className="flex-shrink-0 w-5 h-5 rounded-full bg-gray-200 
                                       flex items-center justify-center text-xs text-gray-600"
                        >
                          {stepIndex + 1}
                        </span>
                        <span className="text-gray-700 font-mono text-xs">
                          {step}
                        </span>
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="font-medium text-gray-800 mb-4">Path Color Legend</h3>
        <div className="flex flex-wrap gap-4">
          {paths.map((path, index) => (
            <div key={path.path_number} className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded-full"
                style={{
                  backgroundColor: PATH_COLORS[index % PATH_COLORS.length],
                }}
              />
              <span className="text-sm text-gray-600">
                Path {path.path_number}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex justify-center gap-4">
        <button
          onClick={onBackToCompare}
          className="px-6 py-3 border border-blue-600 text-blue-600 rounded-lg 
                     hover:bg-blue-50 transition-colors font-medium"
        >
          Change Test Depth Level
        </button>
        <button
          onClick={onReset}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg 
                     hover:bg-blue-700 transition-colors font-medium"
        >
          Analyze Another Flowchart
        </button>
      </div>
    </div>
  );
}
