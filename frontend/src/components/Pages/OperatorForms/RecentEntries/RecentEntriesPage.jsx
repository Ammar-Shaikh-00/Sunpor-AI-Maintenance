import {
  Check,
  ChevronLeft,
  ChevronRight,
  ClipboardCopy,
  Download,
  FileText,
  Filter,
  FlaskConical,
  Pencil,
  Plus,
  Search,
  Trash2,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate } from "react-router-dom";
import api from "../../../../api";
import { ENDPOINTS } from "../../../../api/sunpor";
import { useAuth } from "../../../../context/authContext";
import { useFormOptions } from "../../../../hooks/useSunporData";
import { isSuperAdminUser } from "../../../../utils/permissions";
import { FORM_CATEGORIES, getCategory } from "../spec";

const STATUS_LABELS = {
  open: "Offen",
  resolved: "Behoben",
  released: "Freigegeben",
  hold: "Gesperrt",
  scrap: "Ausschuss",
};

const WEEKDAYS = [
  "Sonntag",
  "Montag",
  "Dienstag",
  "Mittwoch",
  "Donnerstag",
  "Freitag",
  "Samstag",
];

function formatDateTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${day}.${month}.${year}, ${hours}:${minutes}, ${WEEKDAYS[date.getDay()]}`;
}

function operatorName(operator) {
  if (!operator) return "—";
  const name = [operator.first_name, operator.last_name]
    .filter(Boolean)
    .join(" ")
    .trim();
  return name || operator.email || `Benutzer #${operator.id}`;
}

function formatMaterialLabel(item, materials = []) {
  if (!item) return "—";

  const raw =
    item.material_label ||
    item.payload?.affected_material?.other ||
    item.payload?.affected_material?.value ||
    item.payload?.affected_material ||
    item.payload?.material ||
    null;

  if (raw == null || raw === "") return "—";

  const text = String(raw);
  if (!/^\d+$/.test(text)) {
    return text;
  }

  const match = materials.find((material) => String(material.id) === text);
  if (!match) {
    return text;
  }

  if (
    match.code &&
    match.description &&
    match.description !== match.code
  ) {
    return `${match.code} — ${match.description}`;
  }

  return match.code || match.description || text;
}

function StatusBadge({ status }) {
  const key = typeof status === "string" ? status : "";
  const label = STATUS_LABELS[key] || key || "—";
  const isPositive =
    key === "resolved" || key === "released" || key === "fully_resolved";

  return (
    <span
      className={
        isPositive
          ? "inline-flex items-center gap-1 rounded-full border border-emerald-500/40 bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700"
          : "inline-flex items-center gap-1 rounded-full border border-amber-500/40 bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700"
      }
    >
      {isPositive ? (
        <Check className="h-3 w-3 shrink-0" aria-hidden="true" strokeWidth={3} />
      ) : null}
      <span>{label}</span>
    </span>
  );
}

function CategoryIcon({ categoryId, accent }) {
  const Icon = categoryId === "quality" ? FlaskConical : FileText;
  return (
    <span
      className="inline-flex h-9 w-9 items-center justify-center rounded-full text-white"
      style={{ backgroundColor: accent || "#64748b" }}
    >
      <Icon className="h-4 w-4" />
    </span>
  );
}

function createEmptyFilters() {
  return {
    search: "",
    dateFrom: "",
    dateTo: "",
    productionRunId: "",
    categories: FORM_CATEGORIES.filter((c) => c.hasForm).map((c) => c.id),
    statuses: ["open", "resolved", "released", "hold", "scrap"],
    sort: "newest",
  };
}

export default function RecentEntriesPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isSuperAdmin = isSuperAdminUser(user);
  const { options: formOptions } = useFormOptions();
  const materials = formOptions?.material_types || formOptions?.materials || [];

  const [draft, setDraft] = useState(createEmptyFilters);
  const [filters, setFilters] = useState(createEmptyFilters);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);

  const selected = useMemo(
    () => items.find((item) => item.id === selectedId) || null,
    [items, selectedId]
  );

  const loadEntries = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("skip", String((page - 1) * pageSize));
      params.set("limit", String(pageSize));
      params.set("sort", filters.sort);
      if (filters.search.trim()) params.set("search", filters.search.trim());
      if (filters.dateFrom) {
        params.set("date_from", new Date(filters.dateFrom).toISOString());
      }
      if (filters.dateTo) {
        params.set("date_to", new Date(filters.dateTo).toISOString());
      }
      if (filters.productionRunId) {
        params.set("production_run_id", filters.productionRunId);
      }
      filters.categories.forEach((category) =>
        params.append("category", category)
      );
      filters.statuses.forEach((status) => params.append("status", status));

      const { data } = await api.get(
        `${ENDPOINTS.operatorEntries}?${params.toString()}`
      );
      setItems(data.items || []);
      setTotal(data.total || 0);
      if (data.items?.length) {
        setSelectedId((prev) =>
          prev && data.items.some((item) => item.id === prev)
            ? prev
            : data.items[0].id
        );
      } else {
        setSelectedId(null);
      }
    } catch (error) {
      const detail = error?.response?.data?.detail;
      toast.error(
        typeof detail === "string"
          ? detail
          : "Einträge konnten nicht geladen werden."
      );
      setItems([]);
      setTotal(0);
      setSelectedId(null);
    } finally {
      setLoading(false);
    }
  }, [filters, page, pageSize]);

  useEffect(() => {
    loadEntries();
  }, [loadEntries]);

  const pageCount = Math.max(1, Math.ceil(total / pageSize));

  const applyFilters = () => {
    setPage(1);
    setFilters({
      ...draft,
      categories: [...draft.categories],
      statuses: [...draft.statuses],
    });
  };

  const resetFilters = () => {
    const empty = createEmptyFilters();
    setDraft(empty);
    setFilters(createEmptyFilters());
    setPage(1);
  };

  const handleDuplicate = async () => {
    if (!selected) return;
    try {
      await api.post(`${ENDPOINTS.operatorEntries}/${selected.id}/duplicate`);
      toast.success("Eintrag dupliziert.");
      loadEntries();
    } catch {
      toast.error("Duplizieren fehlgeschlagen.");
    }
  };

  const handleDelete = async () => {
    if (!selected || !isSuperAdmin) return;
    if (!window.confirm("Eintrag wirklich löschen?")) return;
    try {
      await api.delete(`${ENDPOINTS.operatorEntries}/${selected.id}`);
      toast.success("Eintrag gelöscht.");
      loadEntries();
    } catch {
      toast.error("Löschen fehlgeschlagen.");
    }
  };

  const handleEdit = () => {
    if (!selected) return;
    const category = getCategory(selected.category);
    if (!category?.path) return;
    navigate(`${category.path}?edit=${selected.id}`);
  };

  const handleExport = () => {
    if (!selected) return;
    const blob = new Blob([JSON.stringify(selected, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `eintrag-${selected.id}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex w-full flex-col gap-4 text-slate-800">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold uppercase tracking-wide text-[#003399]">
            Letzte Einträge
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Alle Produktionsereignisse und Qualitätsprüfungen in chronologischer
            Reihenfolge.
          </p>
        </div>
        <Link
          to="/operator"
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-[#1E4FD6] px-4 text-sm font-semibold text-white shadow-sm"
        >
          <Plus className="h-4 w-4" />
          Neuen Eintrag erfassen
        </Link>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
          <div className="lg:col-span-4">
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Suche nach
            </label>
            <div className="relative mt-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                className="w-full rounded-lg border border-slate-300 py-2.5 pl-10 pr-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                placeholder="Produktionslauf, Charge, Material, Kommentar…"
                value={draft.search}
                onChange={(event) =>
                  setDraft((prev) => ({ ...prev, search: event.target.value }))
                }
              />
            </div>
            <div className="mt-2 rounded-lg bg-slate-100 px-3 py-2 text-xs text-slate-600">
              Durchsucht: Produktionslauf, Charge, Material, Rezept, Operator,
              Maschine, Ereignis, Kommentar
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:col-span-4">
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Zeitraum von
              <input
                type="datetime-local"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                value={draft.dateFrom}
                onChange={(event) =>
                  setDraft((prev) => ({
                    ...prev,
                    dateFrom: event.target.value,
                  }))
                }
              />
            </label>
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Bis
              <input
                type="datetime-local"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                value={draft.dateTo}
                onChange={(event) =>
                  setDraft((prev) => ({ ...prev, dateTo: event.target.value }))
                }
              />
            </label>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:col-span-4">
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Produktionslauf
              <input
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                placeholder="z. B. 145"
                value={draft.productionRunId}
                onChange={(event) =>
                  setDraft((prev) => ({
                    ...prev,
                    productionRunId: event.target.value,
                  }))
                }
              />
            </label>
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Sortierung
              <select
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                value={draft.sort}
                onChange={(event) =>
                  setDraft((prev) => ({ ...prev, sort: event.target.value }))
                }
              >
                <option value="newest">Neueste zuerst</option>
                <option value="oldest">Älteste zuerst</option>
                <option value="run">Nach Produktionslauf</option>
                <option value="machine">Nach Maschine</option>
              </select>
            </label>
          </div>
        </div>

        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={resetFilters}
            className="inline-flex min-h-11 items-center justify-center rounded-xl border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700"
          >
            Filter zurücksetzen
          </button>
          <button
            type="button"
            onClick={applyFilters}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-[#1E4FD6] px-4 text-sm font-semibold text-white"
          >
            <Filter className="h-4 w-4" />
            Filter anwenden
          </button>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm xl:col-span-7">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-3">Zeitpunkt</th>
                  <th className="px-3 py-3">Kategorie</th>
                  <th className="px-3 py-3">Ereignis</th>
                  <th className="px-3 py-3">Operator</th>
                  <th className="px-3 py-3">Lauf / Charge</th>
                  <th className="px-3 py-3">Status</th>
                  <th className="px-3 py-3" />
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-3 py-8 text-center text-slate-500">
                      Laden…
                    </td>
                  </tr>
                ) : items.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-3 py-8 text-center text-slate-500">
                      Keine Einträge gefunden.
                    </td>
                  </tr>
                ) : (
                  items.map((item) => {
                    const category = getCategory(item.category);
                    const active = item.id === selectedId;
                    return (
                      <tr
                        key={item.id}
                        onClick={() => setSelectedId(item.id)}
                        className={`cursor-pointer border-t border-slate-100 transition ${
                          active ? "bg-blue-50" : "hover:bg-slate-50"
                        }`}
                      >
                        <td className="whitespace-nowrap px-3 py-3 text-slate-700">
                          {formatDateTime(item.event_time)}
                        </td>
                        <td className="px-3 py-3">
                          <div className="flex items-center gap-2">
                            <CategoryIcon
                              categoryId={item.category}
                              accent={category?.accent}
                            />
                            <span className="font-medium text-slate-800">
                              {category?.title || item.category}
                            </span>
                          </div>
                        </td>
                        <td className="px-3 py-3">
                          <div className="font-semibold text-slate-900">
                            {item.title}
                          </div>
                          {item.comment ? (
                            <div className="mt-0.5 line-clamp-1 text-xs text-slate-500">
                              {item.comment}
                            </div>
                          ) : null}
                        </td>
                        <td className="px-3 py-3 text-slate-700">
                          {operatorName(item.operator)}
                        </td>
                        <td className="px-3 py-3 text-slate-700">
                          <div>
                            {item.production_run_id
                              ? `Lauf #${item.production_run_id}`
                              : "—"}
                          </div>
                          <div className="text-xs text-slate-500">
                            {item.batch_label || "—"}
                          </div>
                        </td>
                        <td className="px-3 py-3">
                          <StatusBadge status={item.status} />
                        </td>
                        <td className="px-3 py-3 text-slate-400">
                          <ChevronRight className="h-4 w-4" />
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <div className="flex flex-col gap-3 border-t border-slate-200 px-3 py-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-xs text-slate-500">
              {total
                ? `${(page - 1) * pageSize + 1}–${Math.min(page * pageSize, total)} von ${total} Einträgen`
                : "0 Einträge"}
            </div>
            <div className="flex items-center gap-2">
              <select
                className="rounded-lg border border-slate-300 px-2 py-1.5 text-xs"
                value={pageSize}
                onChange={(event) => {
                  setPageSize(Number(event.target.value));
                  setPage(1);
                }}
              >
                {[10, 20, 50].map((size) => (
                  <option key={size} value={size}>
                    {size} / Seite
                  </option>
                ))}
              </select>
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                className="rounded-lg border border-slate-300 p-1.5 disabled:opacity-40"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="text-xs text-slate-600">
                {page} / {pageCount}
              </span>
              <button
                type="button"
                disabled={page >= pageCount}
                onClick={() => setPage((prev) => Math.min(pageCount, prev + 1))}
                className="rounded-lg border border-slate-300 p-1.5 disabled:opacity-40"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </section>

        <aside className="rounded-2xl border border-slate-200 bg-white shadow-sm xl:col-span-5">
          {!selected ? (
            <div className="flex h-full min-h-[320px] items-center justify-center p-6 text-sm text-slate-500">
              Wählen Sie einen Eintrag aus der Liste.
            </div>
          ) : (
            <div className="flex h-full flex-col">
              <div className="flex items-start justify-between gap-3 border-b border-slate-200 px-4 py-4">
                <div className="flex items-start gap-3">
                  <CategoryIcon
                    categoryId={selected.category}
                    accent={getCategory(selected.category)?.accent}
                  />
                  <div>
                    <h2 className="text-base font-bold text-slate-900">
                      {selected.title}
                    </h2>
                    <p className="text-sm text-slate-500">
                      {getCategory(selected.category)?.title || selected.category}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedId(null)}
                  className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100"
                  aria-label="Schließen"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="flex-1 space-y-5 overflow-y-auto px-4 py-4">
                <DetailSection title="Allgemeine Informationen">
                  <DetailGrid
                    rows={[
                      ["Produktionslauf", selected.production_run_id ? `#${selected.production_run_id}` : "—"],
                      ["Charge", selected.batch_label || "—"],
                      ["Material", formatMaterialLabel(selected, materials)],
                      ["Rezept", selected.recipe_label || selected.production_run?.recipe_number || "—"],
                      ["Maschine", selected.machine_label || "—"],
                      ["Operator", operatorName(selected.operator)],
                    ]}
                  />
                </DetailSection>

                <DetailSection title="Zeitpunkt">
                  <DetailGrid
                    rows={[
                      ["Ereignisdatum", formatDateTime(selected.event_time)],
                      ["Erfasst am", formatDateTime(selected.created_at)],
                      ["Erfasst von", operatorName(selected.operator)],
                    ]}
                  />
                </DetailSection>

                <DetailSection title="Ergebnis">
                  <StatusBadge status={selected.status} />
                </DetailSection>

                {selected.comment ? (
                  <DetailSection title="Kommentar">
                    <p className="whitespace-pre-wrap text-sm text-slate-700">
                      {selected.comment}
                    </p>
                  </DetailSection>
                ) : null}
              </div>

              <div className="grid grid-cols-2 gap-2 border-t border-slate-200 p-3 sm:grid-cols-4">
                <button
                  type="button"
                  onClick={handleEdit}
                  className="inline-flex min-h-10 items-center justify-center gap-1.5 rounded-lg bg-[#1E4FD6] px-2 text-xs font-semibold text-white"
                >
                  <Pencil className="h-3.5 w-3.5" />
                  Bearbeiten
                </button>
                <button
                  type="button"
                  onClick={handleExport}
                  className="inline-flex min-h-10 items-center justify-center gap-1.5 rounded-lg border border-slate-300 px-2 text-xs font-semibold text-slate-700"
                >
                  <Download className="h-3.5 w-3.5" />
                  Exportieren
                </button>
                <button
                  type="button"
                  onClick={handleDuplicate}
                  className="inline-flex min-h-10 items-center justify-center gap-1.5 rounded-lg border border-slate-300 px-2 text-xs font-semibold text-slate-700"
                >
                  <ClipboardCopy className="h-3.5 w-3.5" />
                  Duplizieren
                </button>
                <button
                  type="button"
                  onClick={handleDelete}
                  disabled={!isSuperAdmin}
                  className="inline-flex min-h-10 items-center justify-center gap-1.5 rounded-lg border border-red-300 px-2 text-xs font-semibold text-red-600 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Löschen
                </button>
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function DetailSection({ title, children }) {
  return (
    <section>
      <h3 className="mb-2 text-sm font-bold text-[#1E4FD6]">{title}</h3>
      {children}
    </section>
  );
}

function DetailGrid({ rows }) {
  return (
    <dl className="grid grid-cols-1 gap-2 sm:grid-cols-2">
      {rows.map(([label, value]) => (
        <div key={label} className="rounded-lg border border-slate-200 px-3 py-2">
          <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            {label}
          </dt>
          <dd className="mt-0.5 text-sm font-medium text-slate-800">{value}</dd>
        </div>
      ))}
    </dl>
  );
}
