import { ChevronRight } from "lucide-react";

export default function OperatorFormFooter({
  onCancel,
  submitLabel = "Jetzt erfassen",
  submitting = false,
  accent = "#1E4FD6",
}) {
  return (
    <footer className="sticky bottom-0 z-20 border-t border-slate-200 bg-white/95 px-4 py-3 backdrop-blur sm:px-6">
      <div className="mx-auto flex w-full max-w-[1600px] flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
        <button
          type="button"
          onClick={onCancel}
          className="inline-flex min-h-11 items-center justify-center rounded-xl border border-slate-300 bg-white px-5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
        >
          Abbrechen
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="inline-flex min-h-11 flex-1 items-center justify-center gap-2 rounded-xl px-6 text-sm font-semibold text-white shadow-sm transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60 sm:max-w-xl"
          style={{ backgroundColor: accent }}
        >
          {submitting ? "Wird gespeichert…" : submitLabel}
          {!submitting ? (
            <ChevronRight className="h-4 w-4" strokeWidth={2.5} />
          ) : null}
        </button>
      </div>
    </footer>
  );
}
