/**
 * ImageUpload Component
 *
 * This component handles file uploads via click to select.
 *
 * KEY CONCEPTS:
 *
 * 1. USEREF
 *    useRef creates a "reference" to a DOM element.
 *    It's like document.getElementById() but the React way.
 *    We use it here to programmatically click the hidden file input.
 *
 * 2. TERNARY OPERATOR
 *    condition ? valueIfTrue : valueIfFalse
 *    Used for conditional rendering in JSX
 */

"use client";

import { useRef, useState, ChangeEvent } from "react";

interface ImageUploadProps {
  onUpload: (file: File) => void; // Callback when a file is selected
}

export default function ImageUpload({ onUpload }: ImageUploadProps) {
  // State to show a preview of the selected image
  const [preview, setPreview] = useState<string | null>(null);

  // Reference to the hidden file input element
  const fileInputRef = useRef<HTMLInputElement>(null);

  /**
   * Handle when user selects a file via the file picker
   */
  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  /**
   * Process the selected file
   */
  const handleFile = (file: File) => {
    // Validate it's an image
    if (!file.type.startsWith("image/")) {
      alert("Please select an image file");
      return;
    }

    // Create a preview URL for the image
    // URL.createObjectURL creates a temporary URL for the file
    const previewUrl = URL.createObjectURL(file);
    setPreview(previewUrl);
  };

  /**
   * Submit the selected file
   */
  const handleSubmit = () => {
    if (fileInputRef.current?.files?.[0]) {
      onUpload(fileInputRef.current.files[0]);
    }
  };

  /**
   * Clear the selection
   */
  const handleClear = () => {
    setPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="max-w-xl mx-auto">
      {/* 
        Hidden file input - we hide it and trigger it programmatically 
        because native file inputs are hard to style
      */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept="image/*"
        className="hidden"
      />

      {/* Upload area */}
      <div
        onClick={() => !preview && fileInputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
          transition-all duration-200 ease-in-out
          ${
            preview
              ? "border-green-400 bg-green-50"
              : "border-gray-300 hover:border-blue-400 hover:bg-blue-50"
          }
        `}
      >
        {preview ? (
          // Show preview if we have one
          <div className="space-y-4">
            <img
              src={preview}
              alt="Preview"
              className="max-h-64 mx-auto rounded-lg shadow-md"
            />
          </div>
        ) : (
          // Show upload prompt
          <div className="space-y-4">
            {/* Upload icon - using SVG */}
            <div className="flex justify-center">
              <svg
                className="w-16 h-16 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>
            <div>
              <p className="text-lg font-medium text-gray-700">
                Upload your flowchart image here
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Action buttons - only show when we have a preview */}
      {preview && (
        <div className="flex gap-4 mt-6 justify-center">
          <button
            onClick={handleClear}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 
                       hover:bg-gray-50 transition-colors font-medium"
          >
            Clear
          </button>
          <button
            onClick={handleSubmit}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg 
                       hover:bg-blue-700 transition-colors font-medium"
          >
            Analyze Flowchart
          </button>
        </div>
      )}
    </div>
  );
}
