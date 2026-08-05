import {
  CircleDot,
  ClipboardCheck,
  ClipboardList,
  FileText,
} from "lucide-react";
import { Link } from "react-router-dom";
import { FORM_CATEGORIES } from "../OperatorForms/spec";
import {
  CAPTURE_HUB_CARD_ORDER,
  CAPTURE_HUB_DISPLAY,
} from "./captureHubDisplay";

const ICON_MAP = {
  "circle-dot": CircleDot,
  "clipboard-list": ClipboardList,
  "file-text": FileText,
};

const CATEGORY_MAP = Object.fromEntries(
  FORM_CATEGORIES.map((category) => [category.id, category]),
);

function CaptureCardIcon({ display }) {
  if (display?.image) {
    return (
      <img
        src={display.image}
        alt=""
        className="h-[4.5rem] w-[4.5rem] object-contain sm:h-20 sm:w-20"
        aria-hidden="true"
      />
    );
  }

  const Icon = ICON_MAP[display?.icon] || FileText;

  return (
    <Icon
      className="h-14 w-14 text-white/85 sm:h-16 sm:w-16"
      aria-hidden="true"
      strokeWidth={1.25}
    />
  );
}

function CaptureCard({ category, display }) {
  const prompt = category.hasForm
    ? "Was wird erfasst?"
    : "Was wird angezeigt?";
  const title = display?.title || category.title;
  const body =
    display?.body || category.examples || category.description;
  const cta = display?.ctaLabel || category.ctaLabel || "Jetzt erfassen";

  return (
    <Link
      to={category.path}
      className="operator-capture-card group flex h-full min-h-[19.5rem] flex-col rounded-xl border p-5 sm:min-h-[21rem] sm:p-6"
    >
      <div className="operator-capture-card__icon-wrap flex items-center justify-center pb-4 pt-1">
        <CaptureCardIcon display={display} />
      </div>

      <h3 className="operator-capture-card__title text-center text-base font-bold leading-snug sm:text-lg">
        {title}
      </h3>

      <p className="operator-capture-card__prompt mt-3 text-center text-sm font-medium">
        {prompt}
      </p>

      <p className="operator-capture-card__body mt-3 flex-1 text-sm leading-relaxed">
        {body}
      </p>

      <span className="operator-capture-card__cta mt-5 inline-flex min-h-11 w-full items-center justify-center rounded-lg px-4 text-sm font-semibold transition group-hover:brightness-110">
        {cta}
      </span>
    </Link>
  );
}

export default function OperatorCaptureHub() {
  const categories = CAPTURE_HUB_CARD_ORDER.map((id) => CATEGORY_MAP[id]).filter(
    Boolean,
  );

  return (
    <section className="operator-capture-hub relative overflow-hidden px-1 py-2 sm:px-2 sm:py-4 lg:px-0 lg:py-2">
      <div className="relative mb-6 flex items-start justify-between gap-4 sm:mb-8">
        <div className="min-w-0 max-w-3xl">
          <h2 className="operator-capture-hub__title text-2xl font-bold leading-tight sm:text-3xl lg:text-[2.15rem]">
            Was möchten Sie erfassen?
          </h2>
          <p className="operator-capture-hub__subtitle mt-2 text-sm sm:text-base">
            Bitte wählen Sie eine Kategorie aus, um ein neues Ereignis zu
            erfassen.
          </p>
        </div>
        <div
          className="operator-capture-hub__art hidden shrink-0 sm:block"
          aria-hidden="true"
        >
          <ClipboardCheck
            className="h-20 w-20 lg:h-24 lg:w-24"
            strokeWidth={1.1}
          />
        </div>
      </div>

      <div className="relative grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5 xl:grid-cols-4">
        {categories.map((category) => (
          <CaptureCard
            key={category.id}
            category={category}
            display={CAPTURE_HUB_DISPLAY[category.id]}
          />
        ))}
      </div>
    </section>
  );
}
