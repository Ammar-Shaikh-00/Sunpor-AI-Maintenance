import { useEffect, useState } from "react";
import { ChevronLeft, Plus } from "lucide-react";
import { useTranslation } from "react-i18next";
import { NavIcon } from "../../assets/Data/ConstantData";
import { Link, useLocation } from "react-router-dom";
import safeApi, { ENDPOINTS } from "../../api/safeApi";

const formatRunTime = (value) => {
  if (!value) return "--:--";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--:--";

  return date.toLocaleTimeString("de-DE", {
    hour: "2-digit",
    minute: "2-digit",
  });
};

const getRunStatusClass = (status = "") => {
  const normalized = status.toLowerCase();

  if (normalized === "running") return "text-emerald-400";
  if (normalized === "completed") return "text-sky-400";
  if (normalized === "stopped") return "text-rose-400";

  return "text-slate-400";
};

export default function Sidebar({ menuData, mobileSideBar, setMobileSideBar}) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(true);
  const [openMenus, setOpenMenus] = useState({});
  const [menuState, setMenuState] = useState(menuData);
  const [productionRuns, setProductionRuns] = useState([]);
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const activeRunId = searchParams.get("runId");

  useEffect(() => {
    const fetchProductionRuns = async () => {
      const res = await safeApi.get(`${ENDPOINTS.productionRuns}?limit=5`);
      setProductionRuns(res.data || []);
    };

    fetchProductionRuns();

    const interval = setInterval(fetchProductionRuns, 5000);

    return () => clearInterval(interval);
  }, []);


    const handleSetActive = (clickedKey) => {
        const updatedMenu = menuState.map((section) => ({
            ...section,
            items: section.items.map((item) => ({
            ...item,
            active: item.labelKey === clickedKey,
            children: item.children
                ? item.children.map((child) => ({
                    ...child,
                    active: child.labelKey === clickedKey,
                }))
                : undefined,
            })),
    }));

    setMenuState(updatedMenu);
    };

  const toggleSubmenu = (key) => {
    setOpenMenus((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  return (
    <aside
        className={`fixed lg:sticky left-0 top-0 h-full z-40 py-6 bg-white
        transform transition-transform duration-300
        ${open ? "w-64" : "w-20"}
        ${mobileSideBar ? "translate-x-0" : "-translate-x-full"}
        lg:translate-x-0`}   
    >
        <div className="h-full overflow-y-auto">
        
            <div className="min-h-full rounded-[28px] bg-white/80 border border-purple-100 shadow-[0_12px_40px_rgba(139,92,246,0.12)] backdrop-blur px-4 py-5 flex flex-col">
                {/* Collapse Button for large Screen */}
                <div className="hidden lg:flex justify-center mb-4">
                <button
                    onClick={() => setOpen(!open)}
                    className="p-2 border rounded-lg hover:bg-purple-50"
                >
                    <ChevronLeft
                    className={`transition-transform ${!open && "rotate-180"}`}
                    />
                </button>
                </div>
                {/* Mobile Close Button */}
                <div className="lg:hidden flex justify-end mb-4 px-2">
                <button
                    onClick={() => setMobileSideBar(false)}
                    className="p-2 border rounded-lg"
                >
                    ✕
                </button>
                </div>

                {/* Menu */}
                <nav className="space-y-4">
                {menuState.map((section, i) => (
                    <div key={i}>

                    {/* Section Title */}
                    { open && section.titleKey && (
                        <div className="text-xs text-gray-400 px-3 mb-2">
                        {t(section.titleKey)}
                        </div>
                    )}

                    {/* Items */}
                    {section.items.map((item, idx) => (
                        <div key={idx}>

                        {/* Main Item */}
                        <Link to={item.path}>
                            <div
                                onClick={() =>{
                                        if (item.children) {
                                            toggleSubmenu(item.labelKey);
                                        }
                                            handleSetActive(item.labelKey);
                                    }
                                }
                                className={`flex items-center gap-3 px-4 py-2 rounded-xl cursor-pointer
                                hover:bg-purple-50 transition
                                ${item.active ? "bg-purple-100 text-purple-800" : ""}
                                `}
                            >
                                <NavIcon name={item.icon} active={item.active} />
                                {open && <span>{t(item.labelKey)}</span>}
                            </div>
                        </Link>

                        {/* Submenu */}
                        {item.children && openMenus[item.labelKey] && (
                            <div className="ml-8 mt-1 space-y-1">
                            {item.children.map((sub, subIdx) => (
                                <Link key={subIdx} to={sub.path}>
                                    <div
                                    className="flex px-3 py-1 rounded-lg hover:bg-purple-50 cursor-pointer text-sm"
                                    >
                                    <NavIcon name={sub.icon} active={sub.active} />
                                    { open && t(sub.labelKey)}
                                    </div>
                                </Link>
                            ))}
                            </div>
                        )}
                        </div>
                    ))}
                    </div>
                ))}
                </nav>

                <div className="mt-auto pt-6">
                    {open && (
                        <div className="px-3 pb-2 text-xs uppercase tracking-wide text-gray-400">
                            {t("sidebar.productionRuns")}
                        </div>
                    )}

                    <div className="space-y-2">
                        {productionRuns.map((run) => {
                            const isActive =
                                location.pathname.includes("/production-run") &&
                                activeRunId === String(run.id);

                            return (
                                <Link
                                    key={run.id}
                                    to={`/production-runs`}
                                    onClick={() => setMobileSideBar(false)}
                                >
                                    <div
                                        className={`rounded-xl border p-3 my-1 transition ${
                                            isActive
                                                ? "border-purple-500 bg-purple-600 text-white"
                                                : "border-slate-200 bg-slate-950 text-white hover:bg-slate-900"
                                        } ${open ? "" : "px-2"}`}
                                    >
                                        <div className="flex items-start justify-between gap-2">
                                            <div className="font-bold">
                                                {open ? `#${run.id}` : `#${run.id}`}
                                            </div>
                                            {open && (
                                                <span className={`text-[10px] font-bold uppercase ${isActive ? "text-white" : getRunStatusClass(run.status)}`}>
                                                    {run.status || "running"}
                                                </span>
                                            )}
                                        </div>

                                        {open && (
                                            <>
                                                <div className="mt-2 text-sm text-white/90">
                                                    {t("sidebar.runLine", {
                                                      id: run.id,
                                                      line: run.production_line_id || "—",
                                                    })}
                                                </div>
                                                <div className="mt-2 text-right text-xs text-white/70">
                                                    {formatRunTime(run.start_time)}
                                                </div>
                                            </>
                                        )}
                                    </div>
                                </Link>
                            );
                        })}

                        <Link
                            to="/forms/production-start"
                            onClick={() => setMobileSideBar(false)}
                        >
                            <div className={`flex items-center justify-center gap-2 rounded-lg border border-purple-500 px-3 py-2 text-sm font-semibold text-purple-600 transition hover:bg-purple-50 ${open ? "" : "px-2"}`}>
                                <Plus size={16} />
                                {open && <span>{t("sidebar.newProductionRun")}</span>}
                            </div>
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    </aside>
  );
}
