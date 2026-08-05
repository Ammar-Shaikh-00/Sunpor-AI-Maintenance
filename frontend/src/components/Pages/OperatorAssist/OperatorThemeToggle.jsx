import { Moon, Sun } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function OperatorThemeToggle({ theme = "dark", onToggle }) {
  const { t } = useTranslation();
  const isDark = theme !== "light";

  return (
    <button
      type="button"
      onClick={onToggle}
      className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-400/30 bg-[#C5C8CF] px-3 text-xs font-semibold text-slate-800 transition hover:bg-white"
      aria-label={t("operatorAssist.shell.themeToggle", {
        defaultValue: "Ansicht umschalten",
      })}
      title={t(
        isDark
          ? "operatorAssist.shell.lightMode"
          : "operatorAssist.shell.darkMode",
        {
          defaultValue: isDark ? "Hellmodus" : "Dunkelmodus",
        }
      )}
    >
      {isDark ? (
        <Sun className="h-4 w-4 text-amber-500" aria-hidden="true" />
      ) : (
        <Moon className="h-4 w-4 text-slate-700" aria-hidden="true" />
      )}
      <span className="uppercase tracking-wide">
        {isDark
          ? t("operatorAssist.shell.light", { defaultValue: "Hell" })
          : t("operatorAssist.shell.dark", { defaultValue: "Dunkel" })}
      </span>
    </button>
  );
}
