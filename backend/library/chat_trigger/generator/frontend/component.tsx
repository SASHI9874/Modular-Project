import React from "react";
import { MessageCircle } from "lucide-react";

export default function ChatTriggerWidget() {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl">
      <MessageCircle className="w-16 h-16 text-blue-600 mb-4" />
      <h3 className="text-xl font-bold text-blue-900 mb-2">Chat Input</h3>
      <p className="text-sm text-blue-700 text-center max-w-xs">
        This is the entry point for your conversational flow. User messages will
        start here.
      </p>
    </div>
  );
}
