import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import safeApi, { ENDPOINTS } from "../../../../api/safeApi";
import { getApiErrorMessage } from "../../../../utils/apiError";
import { useAuth } from "../../../../context/authContext";
import { AdminRoute } from "../../../auth/AdminRoute";
import {
  ActionButton,
  AdminCard,
  StatusBadge,
} from "../adminUi";
import UserModal from "./UserModal";

export default function UsersPage() {
  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const loadData = async () => {
    setLoading(true);

    try {
      const [usersRes, rolesRes] = await Promise.all([
        safeApi.get(ENDPOINTS.users),
        hasPermission("role.view") || hasPermission("role.assign")
          ? safeApi.get(ENDPOINTS.roles)
          : Promise.resolve({ data: [] }),
      ]);

      if (!usersRes.fallback) {
        setUsers(usersRes.data || []);
      }

      if (!rolesRes.fallback) {
        setRoles(rolesRes.data || []);
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, t("admin.users.loadFailed")));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openCreate = () => {
    setSelectedUser(null);
    setShowModal(true);
  };

  const openEdit = (user) => {
    setSelectedUser(user);
    setShowModal(true);
  };

  const handleSaved = (savedUser) => {
    setUsers((prev) => {
      const exists = prev.some((item) => item.id === savedUser.id);
      if (exists) {
        return prev.map((item) => (item.id === savedUser.id ? savedUser : item));
      }
      return [...prev, savedUser];
    });
  };

  const toggleActive = async (user) => {
    try {
      const endpoint = user.is_active
        ? `${ENDPOINTS.users}/${user.id}/deactivate`
        : `${ENDPOINTS.users}/${user.id}/activate`;
      const response = await safeApi.patch(endpoint);
      setUsers((prev) =>
        prev.map((item) => (item.id === user.id ? response.data : item))
      );
      toast.success(user.is_active ? t("admin.users.deactivated") : t("admin.users.activated"));
    } catch (error) {
      toast.error(getApiErrorMessage(error, t("admin.users.statusFailed")));
    }
  };

  const deleteUser = async (user) => {
    if (!window.confirm(t("admin.users.deleteConfirm", { email: user.email }))) {
      return;
    }

    try {
      await safeApi.delete(`${ENDPOINTS.users}/${user.id}`);
      setUsers((prev) => prev.filter((item) => item.id !== user.id));
      toast.success(t("admin.users.deleted"));
    } catch (error) {
      toast.error(getApiErrorMessage(error, t("errors.requestFailed")));
    }
  };

  return (
    <AdminRoute permission="user.view">
      <AdminCard
        title={t("admin.users.title")}
        description={t("admin.users.description")}
        actions={
          hasPermission("user.create") ? (
            <ActionButton onClick={openCreate}>{t("admin.users.create")}</ActionButton>
          ) : null
        }
      >
        {loading ? (
          <div className="text-slate-500">{t("admin.users.loading")}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b text-slate-500">
                <tr>
                  <th className="px-3 py-2">{t("common.name")}</th>
                  <th className="px-3 py-2">{t("common.email")}</th>
                  <th className="px-3 py-2">{t("admin.users.columns.roles")}</th>
                  <th className="px-3 py-2">{t("common.status")}</th>
                  <th className="px-3 py-2">{t("admin.users.columns.emailAlerts")}</th>
                  <th className="px-3 py-2">{t("common.actions")}</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b border-slate-100">
                    <td className="px-3 py-3 font-medium">
                      {user.first_name} {user.last_name}
                    </td>
                    <td className="px-3 py-3">{user.email}</td>
                    <td className="px-3 py-3">
                      {(user.roles || []).map((role) => role.name).join(", ") || t("common.none")}
                    </td>
                    <td className="px-3 py-3">
                      <StatusBadge
                        active={user.is_active}
                        activeLabel={t("common.active")}
                        inactiveLabel={t("common.inactive")}
                      />
                    </td>
                    <td className="px-3 py-3">
                      <StatusBadge
                        active={user.email_notifications_enabled}
                        activeLabel={t("common.allowed")}
                        inactiveLabel={t("common.blocked")}
                      />
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex flex-wrap gap-2">
                        {hasPermission("user.update") ? (
                          <ActionButton variant="secondary" onClick={() => openEdit(user)}>
                            {t("common.edit")}
                          </ActionButton>
                        ) : null}
                        {hasPermission("user.update") ? (
                          <ActionButton
                            variant="secondary"
                            onClick={() => toggleActive(user)}
                          >
                            {user.is_active
                              ? t("admin.users.actions.deactivate")
                              : t("admin.users.actions.activate")}
                          </ActionButton>
                        ) : null}
                        {hasPermission("user.delete") ? (
                          <ActionButton
                            variant="danger"
                            onClick={() => deleteUser(user)}
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
        <UserModal
          user={selectedUser}
          roles={roles}
          onClose={() => setShowModal(false)}
          onSaved={handleSaved}
        />
      ) : null}
    </AdminRoute>
  );
}
