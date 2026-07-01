import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import safeApi, { ENDPOINTS } from "../../../../api/safeApi";
import { getApiErrorMessage } from "../../../../utils/apiError";
import { groupPermissions } from "../../../../utils/permissions";
import { ActionButton, inputClass, ModalShell } from "../adminUi";

const EMPTY_FORM = {
  name: "",
  description: "",
  permission_ids: [],
};

export default function RoleModal({ role, permissions, onClose, onSaved }) {
  const { t } = useTranslation();
  const isEdit = Boolean(role?.id);
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!role) {
      setForm(EMPTY_FORM);
      return;
    }

    setForm({
      name: role.name || "",
      description: role.description || "",
      permission_ids: (role.permissions || []).map((item) => item.id),
    });
  }, [role]);

  useEffect(() => {
    if (!role?.id || role.permissions?.length) {
      return;
    }

    const loadPermissions = async () => {
      try {
        const response = await safeApi.get(`${ENDPOINTS.roles}/${role.id}/permissions`);
        setForm((prev) => ({
          ...prev,
          permission_ids: (response.data || []).map((item) => item.id),
        }));
      } catch (error) {
        toast.error(getApiErrorMessage(error, t("admin.roles.permissionsFailed")));
      }
    };

    loadPermissions();
  }, [role, t]);

  const onChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const togglePermission = (permissionId) => {
    setForm((prev) => ({
      ...prev,
      permission_ids: prev.permission_ids.includes(permissionId)
        ? prev.permission_ids.filter((id) => id !== permissionId)
        : [...prev.permission_ids, permissionId],
    }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);

    try {
      let savedRole = role;

      if (isEdit) {
        const response = await safeApi.put(`${ENDPOINTS.roles}/${role.id}`, {
          name: form.name,
          description: form.description || null,
        });
        savedRole = response.data;
      } else {
        const response = await safeApi.post(ENDPOINTS.roles, {
          name: form.name,
          description: form.description || null,
        });
        savedRole = response.data;
      }

      const permissionsResponse = await safeApi.put(
        `${ENDPOINTS.roles}/${savedRole.id}/permissions`,
        { permission_ids: form.permission_ids }
      );

      toast.success(isEdit ? t("admin.roles.updated") : t("admin.roles.created"));
      onSaved({
        ...savedRole,
        permissions: permissionsResponse.data,
      });
      onClose();
    } catch (error) {
      toast.error(getApiErrorMessage(error, t("admin.roles.saveFailed")));
    } finally {
      setSubmitting(false);
    }
  };

  const groupedPermissions = groupPermissions(permissions, t);

  return (
    <ModalShell
      title={isEdit ? t("admin.roles.edit") : t("admin.roles.createTitle")}
      onClose={onClose}
    >
      <form onSubmit={onSubmit} className="space-y-5">
        <label className="block text-sm">
          <span className="mb-2 block font-medium text-slate-700">
            {t("admin.roles.roleName")}
          </span>
          <input
            name="name"
            value={form.name}
            onChange={onChange}
            required
            className={inputClass}
          />
        </label>

        <label className="block text-sm">
          <span className="mb-2 block font-medium text-slate-700">
            {t("common.description")}
          </span>
          <textarea
            name="description"
            value={form.description}
            onChange={onChange}
            rows={3}
            className={inputClass}
          />
        </label>

        <div className="space-y-4">
          <div className="text-sm font-medium text-slate-700">
            {t("admin.roles.permissions")}
          </div>
          {groupedPermissions.map((group) => (
            <div key={group.label} className="rounded-xl border border-slate-200 p-4">
              <div className="mb-3 text-sm font-semibold text-slate-800">
                {group.label}
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                {group.permissions.map((permission) => (
                  <label
                    key={permission.id}
                    className="flex items-start gap-2 rounded-lg px-2 py-1 text-sm"
                  >
                    <input
                      type="checkbox"
                      checked={form.permission_ids.includes(permission.id)}
                      onChange={() => togglePermission(permission.id)}
                      className="mt-1"
                    />
                    <span>
                      <span className="font-medium text-slate-800">
                        {permission.code}
                      </span>
                      {permission.description ? (
                        <span className="block text-xs text-slate-500">
                          {permission.description}
                        </span>
                      ) : null}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-end gap-3">
          <ActionButton variant="secondary" onClick={onClose}>
            {t("common.cancel")}
          </ActionButton>
          <ActionButton type="submit" disabled={submitting}>
            {submitting
              ? t("common.saving")
              : isEdit
                ? t("admin.roles.saveChanges")
                : t("admin.roles.createRole")}
          </ActionButton>
        </div>
      </form>
    </ModalShell>
  );
}
