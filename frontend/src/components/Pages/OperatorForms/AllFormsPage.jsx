import { Hand } from "lucide-react";
import { useTranslation } from "react-i18next";
import CurrentProductionRunBanner from "./CurrentProductionRunBanner";
import FormHubCard from "./FormHubCard";
import { OPERATOR_FORM_HUB_ITEMS } from "./operatorFormHub";

export default function AllFormsPage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-4 sm:space-y-6">
      <CurrentProductionRunBanner />

      <section className="rounded-2xl border border-slate-400/30 bg-[#C5C8CF] px-4 py-4 sm:px-8 sm:py-6">
        <div className="flex items-start gap-3 sm:gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-600 text-white shadow-sm sm:h-12 sm:w-12">
            <Hand className="h-5 w-5 sm:h-6 sm:w-6" aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <h1 className="text-lg font-semibold text-slate-900 sm:text-2xl">
              {t("allForms.greeting")}
            </h1>
            <p className="mt-1 text-sm text-slate-600 sm:text-base">{t("allForms.subtitle")}</p>
          </div>
        </div>
      </section>

      <section
        className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 xl:grid-cols-4"
        aria-label={t("allForms.title")}
      >
        {OPERATOR_FORM_HUB_ITEMS.map((item) => (
          <FormHubCard
            key={item.id}
            path={item.path}
            image={item.image}
            titleKey={item.titleKey}
            descriptionKey={item.descriptionKey}
          />
        ))}
      </section>
    </div>
  );
}
