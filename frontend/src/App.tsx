import { Route, Routes } from "react-router-dom";

import { DashboardLayout } from "@/layouts/DashboardLayout";
import { ClauseViewerPage } from "@/pages/ClauseViewerPage";
import { ObligationViewerPage } from "@/pages/ObligationViewerPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { PoliciesPage } from "@/pages/PoliciesPage";
import { ReportsPage } from "@/pages/ReportsPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { UploadPage } from "@/pages/UploadPage";
import { ConflictDashboardPage } from "@/pages/ConflictDashboardPage";
import { RecommendationDashboardPage } from "@/pages/RecommendationDashboardPage";

export function App() {
  return (
    <Routes>
      <Route element={<DashboardLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="policies" element={<PoliciesPage />} />
        <Route path="upload" element={<UploadPage />} />
        <Route path="clauses" element={<ClauseViewerPage />} />
        <Route path="clauses/:policyId" element={<ClauseViewerPage />} />
        <Route path="obligations" element={<ObligationViewerPage />} />
        <Route path="obligations/:policyId" element={<ObligationViewerPage />} />
        <Route path="conflicts" element={<ConflictDashboardPage />} />
        <Route path="conflicts/:policyId" element={<ConflictDashboardPage />} />
        <Route path="recommendations" element={<RecommendationDashboardPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}

export default App;
