export const PERMISSION_GROUPS = [
  {
    labelKey: "admin.permissions.groups.userManagement",
    permissions: ["user.create", "user.view", "user.update", "user.delete"],
  },
  {
    labelKey: "admin.permissions.groups.roles",
    permissions: [
      "role.create",
      "role.view",
      "role.update",
      "role.delete",
      "role.assign",
    ],
  },
  {
    labelKey: "admin.permissions.groups.production",
    permissions: [
      "production.create",
      "production.view",
      "production.update",
      "production.delete",
    ],
  },
  {
    labelKey: "admin.permissions.groups.events",
    permissions: ["event.create", "event.view", "event.update"],
  },
  {
    labelKey: "admin.permissions.groups.quality",
    permissions: ["quality.create", "quality.view", "quality.update"],
  },
  {
    labelKey: "admin.permissions.groups.materialBlocks",
    permissions: ["material_block.create", "material_block.view"],
  },
  {
    labelKey: "admin.permissions.groups.signals",
    permissions: ["signal.view"],
  },
  {
    labelKey: "admin.permissions.groups.ml",
    permissions: ["ml.view"],
  },
  {
    labelKey: "admin.permissions.groups.system",
    permissions: ["system.admin"],
  },
];

export function groupPermissions(allPermissions = [], t = (key) => key) {
  const permissionMap = new Map(allPermissions.map((item) => [item.code, item]));
  const used = new Set();

  const grouped = PERMISSION_GROUPS.map((group) => {
    const items = group.permissions
      .map((code) => permissionMap.get(code))
      .filter(Boolean);

    items.forEach((item) => used.add(item.code));

    return {
      label: t(group.labelKey),
      permissions: items,
    };
  }).filter((group) => group.permissions.length > 0);

  const other = allPermissions.filter((item) => !used.has(item.code));
  if (other.length) {
    grouped.push({
      label: t("admin.permissions.groups.other"),
      permissions: other,
    });
  }

  return grouped;
}

export function filterMenuByPermissions(menuData, hasPermission) {
  return menuData
    .map((section) => ({
      ...section,
      items: section.items.filter(
        (item) => !item.permission || hasPermission(item.permission)
      ),
    }))
    .filter((section) => section.items.length > 0);
}
