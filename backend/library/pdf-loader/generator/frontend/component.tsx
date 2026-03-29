import React, { useState } from "react";
// The Generator will create this API client file.
// We assume it exports a function 'uploadPdf' mapped to the route above.
import { api } from "../../client/api";
import { useAppStore } from "../../store";

export default function PdfLoaderWidget() {
  const [status, setStatus] = useState<string>("");

  // The generator named this specific variable based on the key + output name
  const { set_pdfloader_file_text } = useAppStore();

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setStatus("Uploading & Extracting...");

    try {
      const response = await (api as any)["pdf-loader"].upload(file);
      setStatus(` Success`);

      // Save the result to the Global Store so other components can use it
      if (set_pdfloader_file_text && response.preview) {
        set_pdfloader_file_text(response.preview);
      }
    } catch (err) {
      setStatus(" Upload failed");
      console.error(err);
    }
  };

  return (
    <div className="p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">
        Upload Document
      </h3>

      <div className="border-2 border-dashed border-blue-200 rounded-lg p-6 bg-blue-50 text-center hover:bg-blue-100 transition-colors">
        <input
          type="file"
          accept=".pdf"
          onChange={handleUpload}
          className="block w-full text-sm text-gray-500
            file:mr-4 file:py-2 file:px-4
            file:rounded-full file:border-0
            file:text-sm file:font-semibold
            file:bg-blue-600 file:text-white
            hover:file:bg-blue-700"
        />
      </div>

      {status && (
        <p className="mt-3 text-sm font-medium text-gray-600 animate-pulse">
          {status}
        </p>
      )}
    </div>
  );
}
