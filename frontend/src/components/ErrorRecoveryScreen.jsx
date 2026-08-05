// components/ErrorRecoveryScreen.jsx

import { useEffect, useState } from "react";

export default function ErrorRecoveryScreen({ error }) {
  const [countdown, setCountdown] = useState(10);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          window.location.href = "/";
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const message = error?.message || String(error || "Unknown error");

  return (
    <div className="fixed inset-0 z-[99999] flex items-center justify-center bg-slate-900">
      <div className="max-w-md rounded-2xl bg-[#C5C8CF] p-8 text-center shadow-2xl">
        <h1 className="mb-4 text-2xl font-bold text-blue-500">
          Entschuldigen Sie die Unannehmlichkeiten
        </h1>

        <p className="mb-3 text-slate-600">
          Bei der Anwendung traten unerwartete Ergebnisse auf.
        </p>

        <p className="text-slate-500">Lösung...</p>

        <div className="mt-4 text-4xl font-bold">{countdown}</div>

        {import.meta.env.DEV ? (
          <pre className="mt-4 max-h-40 overflow-auto rounded bg-slate-100 p-2 text-left text-xs text-slate-700">
            {message}
          </pre>
        ) : null}
      </div>
    </div>
  );
}
