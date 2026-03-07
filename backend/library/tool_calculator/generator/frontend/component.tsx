import React, { useState } from "react";
import { Calculator } from "lucide-react";

export default function CalculatorWidget() {
  const [expression, setExpression] = useState("");
  const [result, setResult] = useState<number | null>(null);
  const [error, setError] = useState("");

  const handleCalculate = async () => {
    if (!expression) return;

    try {
      const response = await fetch("/api/tool-calculator/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ expression }),
      });

      const data = await response.json();

      if (data.success) {
        setResult(data.result);
        setError("");
      } else {
        setError(data.error);
        setResult(null);
      }
    } catch (err: any) {
      setError(err.message);
      setResult(null);
    }
  };

  return (
    <div className="flex flex-col h-full w-full bg-white rounded-xl shadow-lg border border-purple-200 overflow-hidden">
      <div className="bg-gradient-to-r from-purple-500 to-purple-600 p-4 text-white">
        <div className="flex items-center gap-2">
          <Calculator className="w-5 h-5" />
          <h3 className="font-bold">Calculator</h3>
        </div>
      </div>

      <div className="flex-1 p-4 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Expression
          </label>
          <input
            type="text"
            value={expression}
            onChange={(e) => setExpression(e.target.value)}
            placeholder="e.g., 5 + 3 * 2"
            className="w-full p-3 border border-gray-300 rounded-lg"
            onKeyPress={(e) => e.key === "Enter" && handleCalculate()}
          />
        </div>

        <button
          onClick={handleCalculate}
          className="w-full bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700"
        >
          Calculate
        </button>

        {result !== null && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <p className="text-sm text-purple-700">Result:</p>
            <p className="text-2xl font-bold text-purple-900">{result}</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
