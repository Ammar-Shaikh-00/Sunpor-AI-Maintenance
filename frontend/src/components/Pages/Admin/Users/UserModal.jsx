import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import safeApi, { ENDPOINTS } from "../../../../api/safeApi";
import { getApiErrorMessage } from "../../../../utils/apiError";
import { ActionButton, inputClass, ModalShell } from "../adminUi";

const EMPTY_FORM = {
  first_name: "",
  last_name: "",
  email: "",
  password: "",
  is_active: true,
  email_notifications_enabled: true,
  role_ids: [],
};

export default function UserModal({ user, roles, onClose, onSaved }) {
  const { t } = useTranslation();
  const isEdit = Boolean(user?.id);
  const [form, setForm] = useState(EMPTY_FORM);
  const [resetPassword, setResetPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!user) {
      setForm(EMPTY_FORM);
      return;
    }

    setForm({
      first_name: user.first_name || "",
      last_name: user.last_name || "",
      email: user.email || "",
      password: "",
      is_active: user.is_active ?? true,
      email_notifications_enabled: user.email_notifications_enabled ?? true,
      role_ids: (user.roles || []).map((role) => role.id),
    });
  }, [user]);

  const onChange = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const toggleRole = (roleId) => {
    setForm((prev) => ({
      ...prev,
      role_ids: prev.role_ids.includes(roleId)
        ? prev.role_ids.filter((id) => id !== roleId)
        : [...prev.role_ids, roleId],
    }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);

    try {
      let savedUser = user;

      if (isEdit) {
        const payload = {
          first_name: form.first_name,
          last_name: form.last_name,
          email: form.email,
          is_active: form.is_active,
          email_notifications_enabled: form.email_notifications_enabled,
        };

        if (form.password) {
          payload.password = form.password;
        }

        const response = await safeApi.put(`${ENDPOINTS.users}/${user.id}`, payload);
        savedUser = response.data;
      } else {
        const response = await safeApi.post(ENDPOINTS.users, {
          first_name: form.first_name,
          last_name: form.last_name,
          email: form.email,
          password: form.password,
          is_active: form.is_active,
          email_notifications_enabled: form.email_notifications_enabled,
        });
        savedUser = response.data;
      }

      const rolesResponse = await safeApi.put(
        `${ENDPOINTS.users}/${savedUser.id}/roles`,
        { role_ids: form.role_ids }
      );

      if (isEdit && resetPassword.trim()) {
        await safeApi.post(ENDPOINTS.resetPassword, {
          email: form.email,
          new_password: resetPassword,
        });
      }

      toast.success(isEdit ? t("admin.users.updated") : t("admin.users.created"));
      onSaved({
        ...savedUser,
        roles: rolesResponse.data,
      });
      onClose();
    } catch (error) {
      toast.error(getApiErrorMessage(error, t("admin.users.saveFailed")));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ModalShell
      title={isEdit ? t("admin.users.edit") : t("admin.users.createTitle")}
      onClose={onClose}
    >
      <form onSubmit={onSubmit} className="space-y-5">
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-2 block font-medium text-slate-700">
              {t("admin.users.fields.firstName")}
            </span>
            <input
              name="first_name"
              value={form.first_name}
              onChange={onChange}
              required
              className={inputClass}
            />
          </label>

          <label className="block text-sm">
            <span className="mb-2 block font-medium text-slate-700">
              {t("admin.users.fields.lastName")}
            </span>
            <input
              name="last_name"
              value={form.last_name}
              onChange={onChange}
              required
              className={inputClass}
            />
          </label>

          <label className="block text-sm md:col-span-2">
            <span className="mb-2 block font-medium text-slate-700">{t("common.email")}</span>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={onChange}
              required
              className={inputClass}
            />
          </label>

          <label className="block text-sm md:col-span-2">
            <span className="mb-2 block font-medium text-slate-700">
              {isEdit ? t("admin.users.fields.newPasswordOptional") : t("common.password")}
            </span>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={onChange}
              required={!isEdit}
              className={inputClass}
            />
          </label>

          {isEdit ? (
            <label className="block text-sm md:col-span-2">
              <span className="mb-2 block font-medium text-slate-700">
                {t("admin.users.fields.adminResetPassword")}
              </span>
              <input
                type="password"
                value={resetPassword}
                onChange={(event) => setResetPassword(event.target.value)}
                className={inputClass}
                placeholder={t("admin.users.fields.adminResetPlaceholder")}
              />
            </label>
          ) : null}
        </div>

        <div className="flex flex-wrap gap-6">
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              name="is_active"
              checked={form.is_active}
              onChange={onChange}
            />
            {t("admin.users.fields.activeAccount")}
          </label>

          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              name="email_notifications_enabled"
              checked={form.email_notifications_enabled}
              onChange={onChange}
            />
            {t("admin.users.fields.emailNotifications")}
          </label>
        </div>

        <div>
          <div className="mb-3 text-sm font-medium text-slate-700">
            {t("admin.users.columns.roles")}
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            {roles.map((role) => (
              <label
                key={role.id}
                className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm"
              >
                <input
                  type="checkbox"
                  checked={form.role_ids.includes(role.id)}
                  onChange={() => toggleRole(role.id)}
                />
                <span>{role.name}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <ActionButton variant="secondary" onClick={onClose}>
            {t("common.cancel")}
          </ActionButton>
          <ActionButton type="submit" disabled={submitting}>
            {submitting
              ? t("common.saving")
              : isEdit
                ? t("admin.users.saveChanges")
                : t("admin.users.createUser")}
          </ActionButton>
        </div>
      </form>
    </ModalShell>
  );
}
