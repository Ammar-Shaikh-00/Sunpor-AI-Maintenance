import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export default function FormHubCard({ path, image, titleKey, descriptionKey }) {
  const { t } = useTranslation();

  return (
    <Link
      to={path}
      className="group flex h-full min-w-0 flex-col rounded-2xl border border-slate-400/30 bg-[#C5C8CF] p-4 text-center transition hover:-translate-y-0.5 hover:border-blue-300 hover:brightness-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-300 sm:p-6"
    >
      <div className="mx-auto flex h-16 w-full items-center justify-center sm:h-20 lg:h-24">
        <img
          src={image}
          alt=""
          aria-hidden="true"
          loading="lazy"
          draggable="false"
          className="h-full w-auto max-w-full object-contain"
        />
      </div>

      <h3 className="mt-4 text-base font-semibold text-slate-900 sm:mt-5 sm:text-[1.125rem]">
        {t(titleKey)}
      </h3>
      <p className="mt-2 flex-1 text-sm leading-relaxed text-slate-500">{t(descriptionKey)}</p>

      <span className="mx-auto mt-4 inline-flex h-9 w-9 items-center justify-center rounded-full bg-blue-600 text-white transition group-hover:bg-blue-700 group-hover:shadow-md sm:mt-5">
        <ArrowRight
          className="h-4 w-4 group-hover:animate-[hub-arrow-nudge_0.85s_ease-in-out_infinite]"
          aria-hidden="true"
        />
      </span>
    </Link>
  );
}
