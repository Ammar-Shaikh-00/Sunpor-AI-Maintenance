import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import safeApi, { ENDPOINTS } from "../../../../api/safeApi";
import { getApiErrorMessage } from "../../../../utils/apiError";
import { useAuth } from "../../../../context/authContext";
import { AdminRoute } from "../../../auth/AdminRoute";
import { ActionButton, AdminCard } from "../adminUi";
import RoleModal from "./RoleModal";

export default function RolesPage() {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRole, setSelectedRole] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const loadData = async () => {
    setLoading(true);

    try {
      const [rolesRes, permissionsRes] = await Promise.all([
        safeApi.get(ENDPOINTS.roles),
        safeApi.get(ENDPOINTS.permissionsCatalog),
      ]);

      if (!rolesRes.fallback) {
        setRoles(rolesRes.data || []);
      }

      if (!permissionsRes.fallback) {
        setPermissions(permissionsRes.data || []);
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, t("admin.roles.loadFailed")));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openCreate = () => {
    setSelectedRole(null);
    setShowModal(true);
  };

  const openEdit = async (role) => {
    try {
      const response = await safeApi.get(`${ENDPOINTS.roles}/${role.id}/permissions`);
      setSelectedRole({
        ...role,
        permissions: response.data || [],
      });
      setShowModal(true);
    } catch (error) {
      toast.error(getApiErrorMessage(error, t("admin.roles.detailsFailed")));
    }
  };

  const handleSaved = (savedRole) => {
    setRoles((prev) => {
      const exists = prev.some((item) => item.id === savedRole.id);
      if (exists) {
        return prev.map((item) => (item.id === savedRole.id ? savedRole : item));
      }
      return [...prev, savedRole];
    });
  };

  const deleteRole = async (role) => {
    if (!window.confirm(t("admin.roles.deleteConfirm", { name: role.name }))) {
      return;
    }

    try {
      await safeApi.delete(`${ENDPOINTS.roles}/${role.id}`);
      setRoles((prev) => prev.filter((item) => item.id !== role.id));
      toast.success(t("admin.roles.deleted"));
    } catch (error) {
      toast.error(getApiErrorMessage(error, t("errors.requestFailed")));
    }
  };

  return (
    <AdminRoute permission="role.view">
      <AdminCard
        title={t("admin.roles.title")}
        description={t("admin.roles.description")}
        actions={
          hasPermission("role.create") ? (
            <ActionButton onClick={openCreate}>{t("admin.roles.create")}</ActionButton>
          ) : null
        }
      >
        {loading ? (
          <div className="text-slate-500">{t("admin.roles.loading")}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b text-slate-500">
                <tr>
                  <th className="px-3 py-2">{t("admin.roles.role")}</th>
                  <th className="px-3 py-2">{t("common.description")}</th>
                  <th className="px-3 py-2">{t("common.actions")}</th>
                </tr>
              </thead>
              <tbody>
                {roles.map((role) => (
                  <tr key={role.id} className="border-b border-slate-100">
                    <td className="px-3 py-3 font-medium">{role.name}</td>
                    <td className="px-3 py-3">{role.description || t("common.none")}</td>
                    <td className="px-3 py-3">
                      <div className="flex flex-wrap gap-2">
                        {hasPermission("role.update") ? (
                          <ActionButton variant="secondary" onClick={() => openEdit(role)}>
                            {t("common.edit")}
                          </ActionButton>
                        ) : null}
                        {hasPermission("role.delete") && role.name !== "SuperAdmin" ? (
                          <ActionButton
                            variant="danger"
                            onClick={() => deleteRole(role)}
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
        )}
      </AdminCard>

      {showModal ? (
        <RoleModal
          role={selectedRole}
          permissions={permissions}
          onClose={() => setShowModal(false)}
          onSaved={handleSaved}
        />
      ) : null}
    </AdminRoute>
  );
}
