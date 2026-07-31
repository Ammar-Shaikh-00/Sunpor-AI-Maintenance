import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import safeApi, { ENDPOINTS } from "../../../../api/safeApi";
import { getApiErrorMessage } from "../../../../utils/apiError";
import { ActionButton, inputClass, ModalShell } from "../adminUi";

const EMPTY_FORM = {
  code: "",
  name: "",
};

function slugifyCode(value) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 100);
}

export default function CategoryModal({ category, onClose, onSaved }) {
  const { t } = useTranslation();
  const isEdit = Boolean(category?.id);
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [codeTouched, setCodeTouched] = useState(false);

  useEffect(() => {
    if (!category) {
      setForm(EMPTY_FORM);
      setCodeTouched(false);
      return;
    }

    setForm({
      code: category.code || "",
      name: category.name || "",
    });
    setCodeTouched(true);
  }, [category]);

  const onChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => {
      const next = { ...prev, [name]: value };
      if (name === "name" && !isEdit && !codeTouched) {
        next.code = slugifyCode(value);
      }
      return next;
    });
  };

  const onCodeChange = (event) => {
    setCodeTouched(true);
    setForm((prev) => ({ ...prev, code: slugifyCode(event.target.value) }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();

    if (!form.code.trim() || !form.name.trim()) {
      toast.error(t("admin.dropdowns.validation.requiredFields"));
      return;
    }

    setSubmitting(true);

    try {
      const payload = {
        code: form.code.trim(),
        name: form.name.trim(),
      };

      const response = isEdit
        ? await safeApi.put(`${ENDPOINTS.dropdownCategories}/${category.id}`, payload)
        : await safeApi.post(ENDPOINTS.dropdownCategories, payload);

      toast.success(
        isEdit ? t("admin.dropdowns.category.updated") : t("admin.dropdowns.category.created")
      );
      onSaved(response.data);
      onClose();
    } catch (error) {
      toast.error(getApiErrorMessage(error, t("admin.dropdowns.category.saveFailed")));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ModalShell
      title={
        isEdit
          ? t("admin.dropdowns.category.editTitle")
          : t("admin.dropdowns.category.createTitle")
      }
      onClose={onClose}
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <label className="block space-y-1">
          <span className="text-sm font-medium text-slate-700">
            {t("admin.dropdowns.category.name")}
          </span>
          <input
            name="name"
            value={form.name}
            onChange={onChange}
            className={inputClass}
            placeholder={t("admin.dropdowns.category.namePlaceholder")}
            required
          />
        </label>

        <label className="block space-y-1">
          <span className="text-sm font-medium text-slate-700">
            {t("admin.dropdowns.category.code")}
          </span>
          <input
            name="code"
            value={form.code}
            onChange={onCodeChange}
            className={`${inputClass} font-mono`}
            placeholder={t("admin.dropdowns.category.codePlaceholder")}
            required
          />
          <p className="text-xs text-slate-500">{t("admin.dropdowns.category.codeHint")}</p>
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
