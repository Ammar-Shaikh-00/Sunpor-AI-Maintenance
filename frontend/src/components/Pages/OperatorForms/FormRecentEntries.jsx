import { useTranslation } from "react-i18next";
import { isProductionRunEditable } from "../../../constants/productionRun";
import { formatEntryDateTime } from "../../../utils/formEntryUtils";
import { useAuth } from "../../../context/authContext";
import { isSuperAdminUser } from "../../../utils/permissions";

function resolveRun(entry, runsById, getRunForEntry) {
  if (getRunForEntry) {
    return getRunForEntry(entry, runsById);
  }
  if (entry?.production_run_id) {
    return runsById[entry.production_run_id];
  }
  return entry;
}

function defaultCanEdit(entry, runsById, getRunForEntry) {
  const run = resolveRun(entry, runsById, getRunForEntry);
  return isProductionRunEditable(run);
}

function renderCell(entry, column, context) {
  if (column.render) {
    return column.render(entry, context);
  }

  if (column.type === "datetime") {
    return formatEntryDateTime(entry[column.key]);
  }

  const value = entry[column.key];
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  if (typeof value === "boolean") {
    return value ? context.t("common.yes") : context.t("common.no");
  }
  return String(value);
}

function EntryActions({
  entry,
  editable,
  canComplete,
  completing,
  showDelete,
  deletable,
  deleting,
  onEdit,
  onComplete,
  onDelete,
  t,
}) {
  return (
    <div className="flex flex-wrap gap-2">
      <button
        type="button"
        disabled={!editable}
        onClick={() => onEdit(entry)}
        title={editable ? undefined : t("forms.common.cannotEditCompleted")}
        className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {t("forms.common.edit")}
      </button>
      {onComplete ? (
        <button
          type="button"
          disabled={!canComplete || completing}
          onClick={() => onComplete(entry)}
          title={
            canComplete ? undefined : t("forms.common.cannotCompleteInactive")
          }
          className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-800 hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {completing ? t("forms.common.completing") : t("forms.common.complete")}
        </button>
      ) : null}
      {showDelete && onDelete ? (
        <button
          type="button"
          disabled={!deletable || deleting}
          onClick={() => onDelete(entry)}
          title={deletable ? undefined : t("forms.common.cannotDeleteCompleted")}
          className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {deleting ? t("forms.common.deleting") : t("forms.common.delete")}
        </button>
      ) : null}
    </div>
  );
}

export default function FormRecentEntries({
  entries,
  columns,
  runsById,
  loading,
  onEdit,
  onComplete,
  completingId = null,
  onDelete,
  deletingId = null,
  getRunForEntry,
  canEdit = defaultCanEdit,
  canComplete = defaultCanEdit,
  canDelete = defaultCanEdit,
  hideHeader = false,
}) {
  const { t } = useTranslation();
  const { user } = useAuth();
  const showDelete = Boolean(onDelete) && isSuperAdminUser(user);
  const showInitialLoading = loading && entries.length === 0;

  return (
    <section className={hideHeader ? "" : "mt-8 border-t border-slate-100 pt-6"}>
      {hideHeader ? null : (
        <>
          <h3 className="text-base font-semibold text-slate-900">
            {t("forms.common.recentEntries")}
          </h3>
          <p className="mt-1 text-sm text-slate-500">{t("forms.common.recentEntriesHint")}</p>
        </>
      )}

      {showInitialLoading ? (
        <p className="mt-4 text-sm text-slate-500">{t("forms.common.loadingRecent")}</p>
      ) : !entries.length ? (
        <p className="mt-4 text-sm text-slate-500">{t("forms.common.noRecentEntries")}</p>
      ) : (
        <>
          <div className="mt-4 hidden overflow-hidden rounded-2xl border border-slate-200 bg-white md:block">
            <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">
                <tr>
                  {columns.map((column) => (
                    <th key={column.key} className="px-4 py-3 font-semibold">
                      {column.label}
                    </th>
                  ))}
                  <th className="px-4 py-3 text-right font-semibold">
                    {t("forms.common.actions")}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {entries.map((entry) => {
                  const editable = canEdit(entry, runsById, getRunForEntry);
                  const completable = Boolean(onComplete) &&
                    canComplete(entry, runsById, getRunForEntry);
                  const deletable = canDelete(entry, runsById, getRunForEntry);
                  const context = { t, runsById };

                  return (
                    <tr
                      key={entry.id}
                      className="transition hover:bg-slate-50/70"
                    >
                      {columns.map((column) => (
                        <td key={column.key} className="px-4 py-3 align-top text-slate-800">
                          {renderCell(entry, column, context)}
                        </td>
                      ))}
                      <td className="px-4 py-3 align-top">
                        <div className="flex justify-end">
                        <EntryActions
                          entry={entry}
                          editable={editable}
                          canComplete={completable}
                          completing={completingId === entry.id}
                          showDelete={showDelete}
                          deletable={deletable}
                          deleting={deletingId === entry.id}
                          onEdit={onEdit}
                          onComplete={onComplete}
                          onDelete={onDelete}
                          t={t}
                        />
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            </div>
          </div>

          <div className="mt-4 space-y-3 md:hidden">
            {entries.map((entry) => {
              const editable = canEdit(entry, runsById, getRunForEntry);
              const completable = Boolean(onComplete) &&
                canComplete(entry, runsById, getRunForEntry);
              const deletable = canDelete(entry, runsById, getRunForEntry);
              const context = { t, runsById };

              return (
                <article
                  key={entry.id}
                  className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
                >
                  <dl className="space-y-2 text-sm">
                    {columns.map((column) => (
                      <div key={column.key} className="flex flex-col gap-0.5 sm:flex-row sm:gap-3">
                        <dt className="shrink-0 text-xs font-medium uppercase tracking-wide text-slate-500 sm:min-w-28 sm:text-sm sm:normal-case sm:tracking-normal">
                          {column.label}
                        </dt>
                        <dd className="min-w-0 break-words text-slate-800">{renderCell(entry, column, context)}</dd>
                      </div>
                    ))}
                  </dl>
                  <div className="mt-3">
                    <EntryActions
                      entry={entry}
                      editable={editable}
                      canComplete={completable}
                      completing={completingId === entry.id}
                      showDelete={showDelete}
                      deletable={deletable}
                      deleting={deletingId === entry.id}
                      onEdit={onEdit}
                      onComplete={onComplete}
                      onDelete={onDelete}
                      t={t}
                    />
                  </div>
                </article>
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}
