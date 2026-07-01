import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import Sidebar from "../SiderBar/sideBar";
import { menuData } from "../../assets/Data/ConstantData";
import Header from "../Header/header";
import Dashboard from "../Pages/Dashboard/dashboard";
import { Route, Routes } from "react-router-dom";
import { useAuth } from "../../context/authContext";
import { useAppBranding } from "../../store/backendStore";
import { filterMenuByPermissions } from "../../utils/permissions";
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
import ProductionRunsPage from "../Pages/ProductionRuns/ProductionRunsPage";
import UsersPage from "../Pages/Admin/Users/UsersPage";
import RolesPage from "../Pages/Admin/Roles/RolesPage";
import DataExportPage from "../Pages/DataExport/DataExportPage";

const MainLayout = ({ backendStatus }) => {
  const { t } = useTranslation();
  const [mobileSideBar, setMobileSideBar] = useState(false);
  const { user, logout, hasPermission, roleLabel } = useAuth();
  const { appName, tagline, companyName } = useAppBranding();
  const visibleMenu = useMemo(
    () => filterMenuByPermissions(menuData, hasPermission),
    [hasPermission]
  );

  if (backendStatus === "offline") {
    logout();
    return null;
  }

  return (
    <div className="relative flex min-h-screen bg-[#FAFAFF]">
      <Sidebar
        menuData={visibleMenu}
        mobileSideBar={mobileSideBar}
        setMobileSideBar={setMobileSideBar}
      />

      {mobileSideBar ? (
        <div
          className="fixed inset-0 z-30 bg-black/30 lg:hidden"
          onClick={() => setMobileSideBar(false)}
        />
      ) : null}

      <div className="ml-0 w-full min-w-0 flex-1 transition-all duration-300 ease-in-out">
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

        <main className="py-4 sm:p-6">
          <Routes>
            <Route path="/" element={<Dashboard backendStatus={backendStatus} />} />
            <Route path="production-runs" element={<ProductionRunsPage />} />
            <Route path="data-export" element={<DataExportPage />} />
            <Route path="forms/production-start" element={<ProductionStartForm />} />
            <Route path="forms/extruder-events" element={<ExtruderEventsForm />} />
            <Route path="forms/granulator-events" element={<GranulatorEventsForm />} />
            <Route path="forms/cleaning" element={<CleaningEventsForm />} />
            <Route path="forms/faults" element={<FaultsForm />} />
            <Route path="forms/material-behavior" element={<MaterialBehaviorForm />} />
            <Route path="forms/material-blocking" element={<MaterialBlockingForm />} />
            <Route path="forms/daily-quality" element={<DailyQualityForm />} />
            <Route path="admin/users" element={<UsersPage />} />
            <Route path="admin/roles" element={<RolesPage />} />
          </Routes>
        </main>
        <Toaster />
      </div>
    </div>
  );
};

export default MainLayout;
