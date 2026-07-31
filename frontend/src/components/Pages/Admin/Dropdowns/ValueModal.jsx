import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import safeApi, { ENDPOINTS } from "../../../../api/safeApi";
import { getApiErrorMessage } from "../../../../utils/apiError";
import { ActionButton, inputClass, ModalShell } from "../adminUi";

const EMPTY_FORM = {
  value: "",
  display_order: "1",
  active: true,
};

export default function ValueModal({ valueItem, categoryId, nextOrder, onClose, onSaved }) {
  const { t } = useTranslation();
  const isEdit = Boolean(valueItem?.id);
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!valueItem) {
      setForm({
        ...EMPTY_FORM,
        display_order: String(nextOrder || 1),
      });
      return;
    }

    setForm({
      value: valueItem.value || "",
      display_order: String(valueItem.display_order ?? 1),
      active: valueItem.active !== false,
    });
  }, [valueItem, nextOrder]);

  const onChange = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();

    if (!form.value.trim()) {
      toast.error(t("admin.dropdowns.validation.valueRequired"));
      return;
    }

    setSubmitting(true);

    try {
      const payload = {
        category_id: categoryId,
        value: form.value.trim(),
        display_order: Number(form.display_order) || 1,
        active: Boolean(form.active),
      };

      const response = isEdit
        ? await safeApi.put(`${ENDPOINTS.dropdownValues}/${valueItem.id}`, payload)
        : await safeApi.post(ENDPOINTS.dropdownValues, payload);

      toast.success(
        isEdit ? t("admin.dropdowns.value.updated") : t("admin.dropdowns.value.created")
      );
      onSaved(response.data);
      onClose();
    } catch (error) {
      toast.error(getApiErrorMessage(error, t("admin.dropdowns.value.saveFailed")));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ModalShell
      title={
        isEdit ? t("admin.dropdowns.value.editTitle") : t("admin.dropdowns.value.createTitle")
      }
      onClose={onClose}
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <label className="block space-y-1">
          <span className="text-sm font-medium text-slate-700">
            {t("admin.dropdowns.value.label")}
          </span>
          <input
            name="value"
            value={form.value}
            onChange={onChange}
            className={inputClass}
            placeholder={t("admin.dropdowns.value.placeholder")}
            required
          />
        </label>

        <label className="block space-y-1">
          <span className="text-sm font-medium text-slate-700">
            {t("admin.dropdowns.value.displayOrder")}
          </span>
          <input
            type="number"
            min="1"
            name="display_order"
            value={form.display_order}
            onChange={onChange}
            className={inputClass}
            required
          />
        </label>

        <label className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
          <input
            type="checkbox"
            name="active"
            checked={form.active}
            onChange={onChange}
            className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm font-medium text-slate-700">
            {t("admin.dropdowns.value.active")}
          </span>
        </label>

        <div className="flex flex-wrap justify-end gap-2 pt-2">
          <ActionButton variant="secondary" type="button" onClick={onClose}>
            {t("common.cancel")}
          </ActionButton>
          <ActionButton type="submit" disabled={submitting}>
            {submitting
              ? t("common.saving")
              : isEdit
                ? t("common.saveChanges")
                : t("common.create")}
          </ActionButton>
        </div>
      </form>
    </ModalShell>
  );
}
