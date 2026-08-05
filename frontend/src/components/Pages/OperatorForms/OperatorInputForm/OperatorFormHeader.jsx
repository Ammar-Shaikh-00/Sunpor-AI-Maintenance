import { ArrowLeft, X } from "lucide-react";
import { Link } from "react-router-dom";

export default function OperatorFormHeader({
  title,
  description,
  accent = "#1E3A8A",
  backTo = "/operator",
  onClose,
}) {
  return (
    <header
      className="sticky top-0 z-20 flex items-start gap-3 px-4 py-3.5 text-white shadow-md sm:gap-4 sm:px-6 sm:py-4"
      style={{ backgroundColor: accent }}
    >
      <Link
        to={backTo}
        className="mt-0.5 inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-white/95 transition hover:bg-white/15"
        aria-label="Zurück"
      >
        <ArrowLeft className="h-5 w-5" strokeWidth={2.2} />
      </Link>

      <div className="min-w-0 flex-1">
        <h1 className="text-lg font-bold uppercase tracking-wide sm:text-xl">
          {title}
        </h1>
        {description ? (
          <p className="mt-1 max-w-4xl text-sm leading-relaxed text-white/90">
            {description}
          </p>
        ) : null}
      </div>

      {onClose ? (
        <button
          type="button"
          onClick={onClose}
          className="mt-0.5 inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-white/95 transition hover:bg-white/15"
          aria-label="Schließen"
        >
          <X className="h-5 w-5" strokeWidth={2.2} />
        </button>
      ) : (
        <Link
          to={backTo}
          className="mt-0.5 inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-white/95 transition hover:bg-white/15"
          aria-label="Schließen"
        >
          <X className="h-5 w-5" strokeWidth={2.2} />
        </Link>
      )}
    </header>
  );
}
