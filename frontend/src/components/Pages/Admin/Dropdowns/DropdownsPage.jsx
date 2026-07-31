import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import safeApi, { ENDPOINTS } from "../../../../api/safeApi";
import { getApiErrorMessage } from "../../../../utils/apiError";
import { useAuth } from "../../../../context/authContext";
import { AdminRoute } from "../../../auth/AdminRoute";
import { ActionButton, AdminCard, StatusBadge } from "../adminUi";
import CategoryModal from "./CategoryModal";
import ValueModal from "./ValueModal";

function StatCard({ label, value, accent = "violet" }) {
  const accentClasses =
    accent === "emerald"
      ? "from-emerald-500/10 to-emerald-500/5 text-emerald-700"
      : accent === "amber"
        ? "from-amber-500/10 to-amber-500/5 text-amber-700"
        : "from-blue-500/10 to-blue-500/5 text-blue-700";

  return (
    <div className={`rounded-2xl border border-slate-200 bg-gradient-to-br ${accentClasses} p-4`}>
      <p className="text-xs font-medium uppercase tracking-wide opacity-80">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

export default function DropdownsPage() {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const [categories, setCategories] = useState([]);
  const [values, setValues] = useState([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState(null);
  const [loadingCategories, setLoadingCategories] = useState(true);
  const [loadingValues, setLoadingValues] = useState(false);
  const [categorySearch, setCategorySearch] = useState("");
  const [valueSearch, setValueSearch] = useState("");
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [showValueModal, setShowValueModal] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedValue, setSelectedValue] = useState(null);

  const selectedCategoryData = useMemo(
    () => categories.find((item) => item.id === selectedCategoryId) || null,
    [categories, selectedCategoryId]
  );

  const filteredCategories = useMemo(() => {
    const query = categorySearch.trim().toLowerCase();
    if (!query) {
      return categories;
    }

    return categories.filter(
      (item) =>
        item.name.toLowerCase().includes(query) || item.code.toLowerCase().includes(query)
    );
  }, [categories, categorySearch]);

  const filteredValues = useMemo(() => {
    const query = valueSearch.trim().toLowerCase();
    if (!query) {
      return values;
    }

    return values.filter((item) => item.value.toLowerCase().includes(query));
  }, [values, valueSearch]);

  const activeValueCount = useMemo(
    () => values.filter((item) => item.active).length,
    [values]
  );

  const nextDisplayOrder = useMemo(() => {
    if (!values.length) {
      return 1;
    }
    return Math.max(...values.map((item) => item.display_order || 0)) + 1;
  }, [values]);

  const loadCategories = async () => {
    setLoadingCategories(true);

    try {
      const response = await safeApi.get(`${ENDPOINTS.dropdownCategories}?limit=500`);
      if (!response.fallback) {
        const items = response.data || [];
        setCategories(items);
        setSelectedCategoryId((current) => {
          if (current && items.some((item) => item.id === current)) {
            return current;
          }
          return items[0]?.id || null;
        });
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, t("admin.dropdowns.loadFailed")));
    } finally {
      setLoadingCategories(false);
    }
  };

  const loadValues = async (categoryId) => {
    if (!categoryId) {
      setValues([]);
      return;
    }

    setLoadingValues(true);

    try {
      const response = await safeApi.get(
        `${ENDPOINTS.dropdownValues}?category_id=${categoryId}&limit=500`
      );
      if (!response.fallback) {
        setValues(response.data || []);
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, t("admin.dropdowns.valuesLoadFailed")));
    } finally {
      setLoadingValues(false);
    }
  };

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    loadValues(selectedCategoryId);
  }, [selectedCategoryId]);

  const openCreateCategory = () => {
    setSelectedCategory(null);
    setShowCategoryModal(true);
  };

  const openEditCategory = (category) => {
    setSelectedCategory(category);
    setShowCategoryModal(true);
  };

  const openCreateValue = () => {
    setSelectedValue(null);
    setShowValueModal(true);
  };

  const openEditValue = (valueItem) => {
    setSelectedValue(valueItem);
    setShowValueModal(true);
  };

  const handleCategorySaved = (savedCategory) => {
    setCategories((prev) => {
      const exists = prev.some((item) => item.id === savedCategory.id);
      if (exists) {
        return prev.map((item) => (item.id === savedCategory.id ? savedCategory : item));
      }
      return [...prev, savedCategory].sort((left, right) => left.name.localeCompare(right.name));
    });
    setSelectedCategoryId(savedCategory.id);
  };

  const handleValueSaved = (savedValue) => {
    setValues((prev) => {
      const exists = prev.some((item) => item.id === savedValue.id);
      const next = exists
        ? prev.map((item) => (item.id === savedValue.id ? savedValue : item))
        : [...prev, savedValue];
      return next.sort((left, right) => left.display_order - right.display_order);
    });
  };

  const deleteCategory = async (category) => {
    if (!window.confirm(t("admin.dropdowns.category.deleteConfirm", { name: category.name }))) {
      return;
    }

    try {
      await safeApi.delete(`${ENDPOINTS.dropdownCategories}/${category.id}`);
      setCategories((prev) => prev.filter((item) => item.id !== category.id));
      if (selectedCategoryId === category.id) {
        setSelectedCategoryId(null);
        setValues([]);
      }
      toast.success(t("admin.dropdowns.category.deleted"));
    } catch (error) {
      toast.error(getApiErrorMessage(error, t("errors.requestFailed")));
    }
  };

  const deleteValue = async (valueItem) => {
    if (!window.confirm(t("admin.dropdowns.value.deleteConfirm", { value: valueItem.value }))) {
      return;
    }

    try {
      await safeApi.delete(`${ENDPOINTS.dropdownValues}/${valueItem.id}`);
      setValues((prev) => prev.filter((item) => item.id !== valueItem.id));
      toast.success(t("admin.dropdowns.value.deleted"));
    } catch (error) {
      toast.error(getApiErrorMessage(error, t("errors.requestFailed")));
    }
  };

  const toggleValueActive = async (valueItem) => {
    try {
      const response = await safeApi.put(`${ENDPOINTS.dropdownValues}/${valueItem.id}`, {
        active: !valueItem.active,
      });
      setValues((prev) =>
        prev.map((item) => (item.id === valueItem.id ? response.data : item))
      );
      toast.success(
        valueItem.active
          ? t("admin.dropdowns.value.deactivated")
          : t("admin.dropdowns.value.activated")
      );
    } catch (error) {
      toast.error(getApiErrorMessage(error, t("admin.dropdowns.value.statusFailed")));
    }
  };

  return (
    <AdminRoute permission="dropdown.view">
      <div className="space-y-6">
        <AdminCard
          title={t("admin.dropdowns.title")}
          description={t("admin.dropdowns.description")}
          actions={
            hasPermission("dropdown.create") ? (
              <ActionButton onClick={openCreateCategory}>
                {t("admin.dropdowns.category.create")}
              </ActionButton>
            ) : null
          }
        >
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard
              label={t("admin.dropdowns.stats.categories")}
              value={categories.length}
              accent="violet"
            />
            <StatCard
              label={t("admin.dropdowns.stats.values")}
              value={selectedCategoryData ? values.length : "—"}
              accent="emerald"
            />
            <StatCard
              label={t("admin.dropdowns.stats.activeValues")}
              value={selectedCategoryData ? activeValueCount : "—"}
              accent="amber"
            />
          </div>
        </AdminCard>

        <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
          <section className="rounded-2xl border border-slate-200 bg-[#C5C8CF] p-4 shadow-sm">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-slate-900">
                {t("admin.dropdowns.category.listTitle")}
              </h2>
              <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700">
                {filteredCategories.length}
              </span>
            </div>

            <input
              value={categorySearch}
              onChange={(event) => setCategorySearch(event.target.value)}
              placeholder={t("admin.dropdowns.category.search")}
              className="mb-4 w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            />

            {loadingCategories ? (
              <p className="text-sm text-slate-500">{t("admin.dropdowns.loadingCategories")}</p>
            ) : !filteredCategories.length ? (
              <p className="text-sm text-slate-500">{t("admin.dropdowns.category.empty")}</p>
            ) : (
              <div className="max-h-[520px] space-y-2 overflow-y-auto pr-1">
                {filteredCategories.map((category) => {
                  const isSelected = category.id === selectedCategoryId;

                  return (
                    <button
                      key={category.id}
                      type="button"
                      onClick={() => setSelectedCategoryId(category.id)}
                      className={`w-full rounded-xl border px-4 py-3 text-left transition ${
                        isSelected
                          ? "border-blue-300 bg-blue-50 shadow-sm"
                          : "border-slate-200 bg-[#C5C8CF] hover:border-blue-200 hover:bg-blue-50/40"
                      }`}
                    >
                      <p className="font-medium text-slate-900">{category.name}</p>
                      <p className="mt-1 font-mono text-xs text-slate-500">{category.code}</p>
                    </button>
                  );
                })}
              </div>
            )}
          </section>

          <section className="rounded-2xl border border-slate-200 bg-[#C5C8CF] p-4 shadow-sm sm:p-6">
            {!selectedCategoryData ? (
              <div className="flex min-h-[320px] items-center justify-center text-center">
                <div>
                  <p className="text-lg font-medium text-slate-900">
                    {t("admin.dropdowns.value.selectCategory")}
                  </p>
                  <p className="mt-1 text-sm text-slate-500">
                    {t("admin.dropdowns.value.selectCategoryHint")}
                  </p>
                </div>
              </div>
            ) : (
              <>
                <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-slate-900">
                      {selectedCategoryData.name}
                    </h2>
                    <p className="mt-1 font-mono text-sm text-slate-500">
                      {selectedCategoryData.code}
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {hasPermission("dropdown.update") ? (
                      <ActionButton
                        variant="secondary"
                        onClick={() => openEditCategory(selectedCategoryData)}
                      >
                        {t("admin.dropdowns.category.edit")}
                      </ActionButton>
                    ) : null}
                    {hasPermission("dropdown.delete") ? (
                      <ActionButton
                        variant="danger"
                        onClick={() => deleteCategory(selectedCategoryData)}
                      >
                        {t("admin.dropdowns.category.delete")}
                      </ActionButton>
                    ) : null}
                    {hasPermission("dropdown.create") ? (
                      <ActionButton onClick={openCreateValue}>
                        {t("admin.dropdowns.value.create")}
                      </ActionButton>
                    ) : null}
                  </div>
                </div>

                <input
                  value={valueSearch}
                  onChange={(event) => setValueSearch(event.target.value)}
                  placeholder={t("admin.dropdowns.value.search")}
                  className="mb-4 w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                />

                {loadingValues ? (
                  <p className="text-sm text-slate-500">{t("admin.dropdowns.loadingValues")}</p>
                ) : !filteredValues.length ? (
                  <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center">
                    <p className="font-medium text-slate-800">{t("admin.dropdowns.value.empty")}</p>
                    <p className="mt-1 text-sm text-slate-500">
                      {t("admin.dropdowns.value.emptyHint")}
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="hidden overflow-x-auto md:block">
                      <table className="min-w-full text-left text-sm">
                        <thead className="border-b text-slate-500">
                          <tr>
                            <th className="px-3 py-2">{t("admin.dropdowns.value.order")}</th>
                            <th className="px-3 py-2">{t("admin.dropdowns.value.label")}</th>
                            <th className="px-3 py-2">{t("common.status")}</th>
                            <th className="px-3 py-2">{t("common.actions")}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredValues.map((valueItem) => (
                            <tr key={valueItem.id} className="border-b border-slate-100">
                              <td className="px-3 py-3 font-mono text-slate-600">
                                {valueItem.display_order}
                              </td>
                              <td className="px-3 py-3 font-medium text-slate-900">
                                {valueItem.value}
                              </td>
                              <td className="px-3 py-3">
                                <StatusBadge
                                  active={valueItem.active}
                                  activeLabel={t("common.active")}
                                  inactiveLabel={t("common.inactive")}
                                />
                              </td>
                              <td className="px-3 py-3">
                                <div className="flex flex-wrap gap-2">
                                  {hasPermission("dropdown.update") ? (
                                    <ActionButton
                                      variant="secondary"
                                      onClick={() => openEditValue(valueItem)}
                                    >
                                      {t("common.edit")}
                                    </ActionButton>
                                  ) : null}
                                  {hasPermission("dropdown.update") ? (
                                    <ActionButton
                                      variant="secondary"
                                      onClick={() => toggleValueActive(valueItem)}
                                    >
                                      {valueItem.active
                                        ? t("admin.dropdowns.value.deactivate")
                                        : t("admin.dropdowns.value.activate")}
                                    </ActionButton>
                                  ) : null}
                                  {hasPermission("dropdown.delete") ? (
                                    <ActionButton
                                      variant="danger"
                                      onClick={() => deleteValue(valueItem)}
                                    >
                                      {t("common.delete")}
                                    </ActionButton>
                                  ) : null}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <div className="space-y-3 md:hidden">
                      {filteredValues.map((valueItem) => (
                        <article
                          key={valueItem.id}
                          className="rounded-xl border border-slate-200 bg-slate-50/70 p-4"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="font-medium text-slate-900">{valueItem.value}</p>
                              <p className="mt-1 text-xs text-slate-500">
                                {t("admin.dropdowns.value.order")}: {valueItem.display_order}
                              </p>
                            </div>
                            <StatusBadge
                              active={valueItem.active}
                              activeLabel={t("common.active")}
                              inactiveLabel={t("common.inactive")}
                            />
                          </div>
                          <div className="mt-3 flex flex-wrap gap-2">
                            {hasPermission("dropdown.update") ? (
                              <ActionButton
                                variant="secondary"
                                onClick={() => openEditValue(valueItem)}
                              >
                                {t("common.edit")}
                              </ActionButton>
                            ) : null}
                            {hasPermission("dropdown.delete") ? (
                              <ActionButton
                                variant="danger"
                                onClick={() => deleteValue(valueItem)}
                              >
                                {t("common.delete")}
                              </ActionButton>
                            ) : null}
                          </div>
                        </article>
                      ))}
                    </div>
                  </>
                )}
              </>
            )}
          </section>
        </div>
      </div>

      {showCategoryModal ? (
        <CategoryModal
          category={selectedCategory}
          onClose={() => setShowCategoryModal(false)}
          onSaved={handleCategorySaved}
        />
      ) : null}

      {showValueModal && selectedCategoryId ? (
        <ValueModal
          valueItem={selectedValue}
          categoryId={selectedCategoryId}
          nextOrder={nextDisplayOrder}
          onClose={() => setShowValueModal(false)}
          onSaved={handleValueSaved}
        />
      ) : null}
    </AdminRoute>
  );
}
