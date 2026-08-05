import React, { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import Sidebar from "../SiderBar/sideBar";
import { menuData } from "../../assets/Data/ConstantData";
import Header from "../Header/header";
import HomeRedirect from "../auth/HomeRedirect";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "../../context/authContext";
import { useAppBranding } from "../../store/backendStore";
import { filterMenuByPermissions, isOperatorOnlyUser } from "../../utils/permissions";
import { Toaster } from "react-hot-toast";
import ProductionStartForm from "../Pages/OperatorForms/ProductionStartForm";
import ExtruderEventsForm, {
  GranulatorEventsForm,
  CleaningEventsForm,
  FaultsForm,
} from "../Pages/OperatorForms/ExtruderEventsForm";
import MaterialBehaviorForm from "../Pages/OperatorForms/MaterialBehaviorForm";
import MaterialBlockingForm from "../Pages/OperatorForms/MaterialBlockingForm";
import DailyQualityForm from "../Pages/OperatorForms/DailyQualityForm";
import AllFormsPage from "../Pages/OperatorForms/AllFormsPage";
import OperatorInputFormPage from "../Pages/OperatorForms/OperatorInputForm/OperatorInputFormPage";
import RecentEntriesPage from "../Pages/OperatorForms/RecentEntries/RecentEntriesPage";
import OperatorHomePage from "../Pages/OperatorAssist/OperatorHomePage";
import OperatorNavStrip from "../Pages/OperatorAssist/OperatorNavStrip";
import ProductionRunsPage from "../Pages/ProductionRuns/ProductionRunsPage";
import UsersPage from "../Pages/Admin/Users/UsersPage";
import RolesPage from "../Pages/Admin/Roles/RolesPage";
import DropdownsPage from "../Pages/Admin/Dropdowns/DropdownsPage";
import DataExportPage from "../Pages/DataExport/DataExportPage";
import SignalsChartsPage from "../Pages/SignalsCharts/SignalsChartsPage";
import PermissionGate, { OperatorRoute } from "../auth/AdminRoute";

const OPERATOR_THEME_STORAGE_KEY = "operator-interface-theme";

const MainLayout = ({ backendStatus }) => {
  const { t } = useTranslation();
  const [mobileSideBar, setMobileSideBar] = useState(false);
  const [operatorTheme, setOperatorTheme] = useState(() => {
    if (typeof window === "undefined") {
      return "dark";
    }
    const savedTheme = window.localStorage.getItem(OPERATOR_THEME_STORAGE_KEY);
    return savedTheme === "light" ? "light" : "dark";
  });
  const { user, logout, hasPermission, hasAnyPermission, roleLabel, isLoading: authLoading } = useAuth();
  const { appName, tagline, companyName } = useAppBranding();
  const operatorShell = isOperatorOnlyUser(user);
  const showProductionRuns = hasPermission("signal.view");
  const toggleOperatorTheme = () => {
    setOperatorTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    window.localStorage.setItem(OPERATOR_THEME_STORAGE_KEY, operatorTheme);
  }, [operatorTheme]);

  const visibleMenu = useMemo(() => {
    if (authLoading) {
      return menuData
        .map((section) => ({
          ...section,
          items: section.items.filter((item) => !item.permission && !item.anyOf?.length),
        }))
        .filter((section) => section.items.length > 0);
    }
    return filterMenuByPermissions(menuData, hasPermission, hasAnyPermission, user);
  }, [hasPermission, hasAnyPermission, authLoading, user]);

  if (backendStatus === "offline") {
    logout();
    return null;
  }

  const operatorRoutes = (
    <Routes>
      <Route path="/" element={<HomeRedirect backendStatus={backendStatus} />} />
      <Route
        path="production-runs"
        element={
          <PermissionGate
            permission="signal.view"
            fallback={<Navigate to={operatorShell ? "/operator" : "/"} replace />}
          >
            <ProductionRunsPage />
          </PermissionGate>
        }
      />
      <Route
        path="data-export"
        element={
          <PermissionGate
            permission="signal.view"
            fallback={<Navigate to={operatorShell ? "/operator" : "/"} replace />}
          >
            <DataExportPage />
          </PermissionGate>
        }
      />
      <Route
        path="signals-charts"
        element={
          <PermissionGate
            permission="signal.view"
            fallback={<Navigate to={operatorShell ? "/operator" : "/"} replace />}
          >
            <SignalsChartsPage />
          </PermissionGate>
        }
      />
      <Route
        path="operator"
        element={
          <OperatorRoute>
            <OperatorHomePage
              operatorTheme={operatorTheme}
              onToggleOperatorTheme={toggleOperatorTheme}
            />
          </OperatorRoute>
        }
      />
      <Route path="forms/all" element={<AllFormsPage />} />
      <Route path="forms/production-start" element={<ProductionStartForm />} />
      <Route
        path="forms/dosing-material"
        element={<OperatorInputFormPage categoryId="dosing_material" />}
      />
      <Route
        path="forms/extruder"
        element={<OperatorInputFormPage categoryId="extruder" />}
      />
      <Route
        path="forms/screen-changer"
        element={<OperatorInputFormPage categoryId="screen_changer" />}
      />
      <Route
        path="forms/die"
        element={<OperatorInputFormPage categoryId="die" />}
      />
      <Route
        path="forms/water-box"
        element={<OperatorInputFormPage categoryId="water_box" />}
      />
      <Route
        path="forms/granulator"
        element={<OperatorInputFormPage categoryId="granulator" />}
      />
      <Route
        path="forms/quality"
        element={<OperatorInputFormPage categoryId="quality" />}
      />
      <Route
        path="forms/general-event"
        element={<OperatorInputFormPage categoryId="general_event" />}
      />
      <Route path="forms/recent-entries" element={<RecentEntriesPage />} />
      {/* Legacy form routes kept for existing bookmarks */}
      <Route path="forms/extruder-events" element={<ExtruderEventsForm />} />
      <Route path="forms/granulator-events" element={<GranulatorEventsForm />} />
      <Route path="forms/cleaning" element={<CleaningEventsForm />} />
      <Route path="forms/faults" element={<FaultsForm />} />
      <Route path="forms/material-behavior" element={<MaterialBehaviorForm />} />
      <Route path="forms/material-blocking" element={<MaterialBlockingForm />} />
      <Route path="forms/daily-quality" element={<DailyQualityForm />} />
      <Route path="admin/users" element={<UsersPage />} />
      <Route path="admin/roles" element={<RolesPage />} />
      <Route path="admin/dropdowns" element={<DropdownsPage />} />
    </Routes>
  );

  return (
    <div
      data-operator-theme={operatorShell ? operatorTheme : undefined}
      className={`relative flex min-h-screen ${
        operatorShell ? "operator-theme-shell" : "bg-[#B1B8C2]"
      }`}
    >
      {!operatorShell ? (
        <Sidebar
          menuData={visibleMenu}
          mobileSideBar={mobileSideBar}
          setMobileSideBar={setMobileSideBar}
          showProductionRuns={showProductionRuns}
        />
      ) : null}

      {!operatorShell && mobileSideBar ? (
        <div
          className="fixed inset-0 z-30 bg-black/30 lg:hidden"
          onClick={() => setMobileSideBar(false)}
        />
      ) : null}

      <div className="ml-0 w-full min-w-0 flex-1 transition-all duration-300 ease-in-out">
        {!operatorShell ? (
          <Header
            appName={companyName ? `${companyName} AI` : appName}
            tagline={tagline || t("dashboard.taglineFallback")}
            user={user}
            role={roleLabel}
            aiStatus="planned"
            aiLoading={false}
            onLogout={logout}
            onMenuClick={() => setMobileSideBar((prev) => !prev)}
            backendStatus={backendStatus}
          />
        ) : null}

        <main
          className={
            operatorShell
              ? "overflow-x-hidden py-4 sm:py-6"
              : "py-4 sm:p-6"
          }
        >
          {operatorShell ? (
            <div className="mx-auto w-full max-w-7xl px-3 sm:px-4 lg:px-6">
              <OperatorNavStrip
                operatorTheme={operatorTheme}
                onToggleOperatorTheme={toggleOperatorTheme}
              />
              {operatorRoutes}
            </div>
          ) : (
            operatorRoutes
          )}
        </main>
        <Toaster />
      </div>
    </div>
  );
};

export default MainLayout;
