import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import { useDataExportCatalog, useDataExportQuery } from "../../../hooks/useDataExport";
import { downloadCsv } from "../../../utils/csvExport";

const PAGE_SIZE = 100;
const EXPORT_LIMIT = 10000;

function toIsoDateStart(value) {
  if (!value) return undefined;
  return new Date(`${value}T00:00:00`).toISOString();
}

function toIsoDateEnd(value) {
  if (!value) return undefined;
  return new Date(`${value}T23:59:59.999`).toISOString();
}

function formatCell(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  return String(value);
}

function getColumnGroups(dataset) {
  if (!dataset) {
    return [];
  }
  if (dataset.column_groups?.length) {
    return dataset.column_groups;
  }
  return [
    {
      key: "base",
      label: dataset.label,
      columns: dataset.columns || [],
    },
  ];
}

function findColumnMeta(dataset, key) {
  if (!dataset) {
    return null;
  }
  const flat = dataset.columns?.find((column) => column.key === key);
  if (flat) {
    return flat;
  }
  for (const group of getColumnGroups(dataset)) {
    const match = group.columns.find((column) => column.key === key);
    if (match) {
      return match;
    }
  }
  return null;
}

export default function DataExportPage() {
  const { t } = useTranslation();
  const { catalog, loading: catalogLoading, error: catalogError } = useDataExportCatalog();
  const { data, loading, error, fetchData } = useDataExportQuery();

  const [datasetKey, setDatasetKey] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [offset, setOffset] = useState(0);

  const activeDataset = useMemo(
    () => catalog.find((item) => item.key === datasetKey) || null,
    [catalog, datasetKey]
  );

  const columnGroups = useMemo(
    () => getColumnGroups(activeDataset),
    [activeDataset]
  );

  useEffect(() => {
    if (!catalog.length) {
      return;
    }
    if (!datasetKey || !catalog.some((item) => item.key === datasetKey)) {
      setDatasetKey(catalog[0].key);
    }
  }, [catalog, datasetKey]);

  useEffect(() => {
    if (!activeDataset) {
      setSelectedColumns([]);
      return;
    }
    setSelectedColumns(activeDataset.columns.map((column) => column.key));
    setOffset(0);
  }, [activeDataset?.key]);

  const columnLabels = useMemo(() => {
    if (!activeDataset) {
      return [];
    }

    return selectedColumns.map((key) => {
      const meta = findColumnMeta(activeDataset, key);
      return t(`dataExport.columns.${key}`, {
        defaultValue: meta?.label || key,
      });
    });
  }, [activeDataset, selectedColumns, t]);

  const datasetLabel = (key, fallback) =>
    t(`dataExport.datasets.${key}`, { defaultValue: fallback });

  const buildQueryParams = (limit, nextOffset = offset) => ({
    dataset: datasetKey,
    from_date: toIsoDateStart(fromDate),
    to_date: toIsoDateEnd(toDate),
    columns: selectedColumns.join(","),
    limit,
    offset: nextOffset,
  });

  const validateFilters = () => {
    if (!datasetKey) {
      toast.error(t("dataExport.errors.datasetRequired"));
      return false;
    }
    if (!selectedColumns.length) {
      toast.error(t("dataExport.errors.columnsRequired"));
      return false;
    }
    if (fromDate && toDate && fromDate > toDate) {
      toast.error(t("dataExport.errors.invalidDateRange"));
      return false;
    }
    return true;
  };

  const handlePreview = async (nextOffset = 0) => {
    if (!validateFilters()) {
      return;
    }

    setOffset(nextOffset);
    await fetchData(buildQueryParams(PAGE_SIZE, nextOffset));
  };

  const handleExport = async () => {
    if (!validateFilters()) {
      return;
    }

    const total = data?.total ?? EXPORT_LIMIT;
    const exportLimit = Math.min(total || EXPORT_LIMIT, EXPORT_LIMIT);

    toast.loading(t("dataExport.exporting"), { id: "export-csv" });

    const exportData = await fetchData(buildQueryParams(exportLimit, 0));

    toast.dismiss("export-csv");

    if (!exportData?.rows?.length) {
      toast.error(t("dataExport.errors.noData"));
      return;
    }

    const timestamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
    downloadCsv({
      filename: `sunpor-${datasetKey}-${timestamp}.csv`,
      columns: exportData.columns,
      columnLabels: exportData.column_labels,
      rows: exportData.rows,
    });

    toast.success(t("dataExport.exportSuccess", { count: exportData.rows.length }));
  };

  const toggleColumn = (key) => {
    setSelectedColumns((prev) =>
      prev.includes(key) ? prev.filter((item) => item !== key) : [...prev, key]
    );
  };

  const selectAllColumns = () => {
    if (!activeDataset) return;
    setSelectedColumns(activeDataset.columns.map((column) => column.key));
  };

  const clearColumns = () => {
    setSelectedColumns([]);
  };

  const groupLabel = (group) =>
    t(`dataExport.columnGroups.${group.key}`, { defaultValue: group.label });

  const columnLabel = (column) =>
    t(`dataExport.columns.${column.key}`, { defaultValue: column.label });

  const isGroupFullySelected = (group) =>
    group.columns.every((column) => selectedColumns.includes(column.key));

  const toggleGroupColumns = (group, checked) => {
    const keys = group.columns.map((column) => column.key);
    setSelectedColumns((prev) => {
      if (checked) {
        return [...new Set([...prev, ...keys])];
      }
      return prev.filter((key) => !keys.includes(key));
    });
  };

  if (catalogLoading) {
    return <div className="text-slate-500">{t("dataExport.loadingCatalog")}</div>;
  }

  if (catalogError) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-rose-700">
        {catalogError}
      </div>
    );
  }

  if (!catalog.length) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-800">
        {t("dataExport.noDatasets")}
      </div>
    );
  }

  const total = data?.total ?? 0;
  const canGoPrev = offset > 0;
  const canGoNext = data ? offset + data.rows.length < total : false;

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{t("dataExport.title")}</h1>
        <p className="mt-1 text-sm text-slate-500">{t("dataExport.description")}</p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-slate-700">{t("dataExport.dataset")}</span>
            <select
              value={datasetKey}
              onChange={(event) => setDatasetKey(event.target.value)}
              className="rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
            >
              {catalog.map((item) => (
                <option key={item.key} value={item.key}>
                  {datasetLabel(item.key, item.label)}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-slate-700">{t("dataExport.fromDate")}</span>
            <input
              type="date"
              value={fromDate}
              onChange={(event) => setFromDate(event.target.value)}
              className="rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
            />
          </label>

          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-slate-700">{t("dataExport.toDate")}</span>
            <input
              type="date"
              value={toDate}
              onChange={(event) => setToDate(event.target.value)}
              className="rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
            />
          </label>

          <div className="flex items-end gap-2">
            <button
              type="button"
              onClick={() => handlePreview(0)}
              disabled={loading}
              className="flex-1 rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-violet-700 disabled:opacity-60"
            >
              {loading ? t("dataExport.loading") : t("dataExport.preview")}
            </button>
            <button
              type="button"
              onClick={handleExport}
              disabled={loading}
              className="flex-1 rounded-xl border border-violet-200 bg-violet-50 px-4 py-2.5 text-sm font-semibold text-violet-700 hover:bg-violet-100 disabled:opacity-60"
            >
              {t("dataExport.exportCsv")}
            </button>
          </div>
        </div>

        <div className="mt-6 border-t border-slate-100 pt-5">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-semibold text-slate-800">{t("dataExport.columns")}</h2>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={selectAllColumns}
                className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
              >
                {t("dataExport.selectAll")}
              </button>
              <button
                type="button"
                onClick={clearColumns}
                className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
              >
                {t("dataExport.clearAll")}
              </button>
            </div>
          </div>

          <div className="space-y-5">
            {columnGroups.map((group) => (
              <div key={group.key} className="rounded-xl border border-slate-100 bg-slate-50/60 p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <h3 className="text-sm font-semibold text-slate-800">{groupLabel(group)}</h3>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => toggleGroupColumns(group, true)}
                      className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
                    >
                      {t("dataExport.selectGroup")}
                    </button>
                    <button
                      type="button"
                      onClick={() => toggleGroupColumns(group, false)}
                      className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
                    >
                      {t("dataExport.clearGroup")}
                    </button>
                  </div>
                </div>

                <label className="mb-3 flex items-center gap-2 text-xs font-medium text-slate-500">
                  <input
                    type="checkbox"
                    checked={isGroupFullySelected(group)}
                    onChange={(event) => toggleGroupColumns(group, event.target.checked)}
                  />
                  <span>{t("dataExport.selectWholeGroup")}</span>
                </label>

                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                  {group.columns.map((column) => (
                    <label
                      key={column.key}
                      className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
                    >
                      <input
                        type="checkbox"
                        checked={selectedColumns.includes(column.key)}
                        onChange={() => toggleColumn(column.key)}
                      />
                      <span>{columnLabel(column)}</span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          {error}
        </div>
      ) : null}

      <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-2 border-b border-slate-100 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div className="text-sm text-slate-600">
            {data
              ? t("dataExport.resultSummary", {
                  shown: data.rows.length,
                  total,
                })
              : t("dataExport.noPreview")}
          </div>

          {data ? (
            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={!canGoPrev || loading}
                onClick={() => handlePreview(Math.max(0, offset - PAGE_SIZE))}
                className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 disabled:opacity-50"
              >
                {t("dataExport.previous")}
              </button>
              <button
                type="button"
                disabled={!canGoNext || loading}
                onClick={() => handlePreview(offset + PAGE_SIZE)}
                className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 disabled:opacity-50"
              >
                {t("dataExport.next")}
              </button>
            </div>
          ) : null}
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                {selectedColumns.map((column, index) => (
                  <th key={column} className="whitespace-nowrap px-4 py-3 font-medium">
                    {columnLabels[index]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td
                    colSpan={Math.max(selectedColumns.length, 1)}
                    className="px-4 py-8 text-center text-slate-500"
                  >
                    {t("dataExport.loading")}
                  </td>
                </tr>
              ) : data?.rows?.length ? (
                data.rows.map((row, rowIndex) => (
                  <tr key={rowIndex} className="border-t border-slate-100 hover:bg-slate-50/70">
                    {selectedColumns.map((column) => (
                      <td key={column} className="whitespace-nowrap px-4 py-3 text-slate-800">
                        {formatCell(row[column])}
                      </td>
                    ))}
                  </tr>
                ))
              ) : (
                <tr>
                  <td
                    colSpan={Math.max(selectedColumns.length, 1)}
                    className="px-4 py-8 text-center text-slate-500"
                  >
                    {t("dataExport.emptyTable")}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
