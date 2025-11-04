import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import LiveFeed from "./pages/LiveFeed";
import { Auth } from "./pages/Auth";
import Footfall from "./pages/Footfall";
import AIIntelligence from "./pages/AIIntelligence";
import PeopleCount from "./pages/PeopleCount";
import Assets from "./pages/Assets";
import Settings from "./pages/Settings";
import ActivityLog from "./pages/ActivityLog";
import NotFound from "./pages/NotFound";
import { DashboardLayout } from "./components/layout/DashboardLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { NotificationProvider } from "./contexts/NotificationContext";
import NotificationPopup from "./components/NotificationPopup";
import { useDetectionNotifications } from "./hooks/useDetectionNotifications";

const queryClient = new QueryClient();

// Component to handle detection notifications
const DetectionNotificationHandler = () => {
  useDetectionNotifications();
  return null;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <NotificationProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <NotificationPopup />
        <DetectionNotificationHandler />
        <BrowserRouter>
          <Routes>
            <Route path="/auth" element={<Auth />} />
            <Route path="/" element={
              <ProtectedRoute>
                <DashboardLayout>
                  <Dashboard />
                </DashboardLayout>
              </ProtectedRoute>
            } />
            <Route path="/live-feed" element={
            <ProtectedRoute>
              <DashboardLayout>
                <LiveFeed />
              </DashboardLayout>
            </ProtectedRoute>
          } />
            <Route path="/footfall" element={
              <ProtectedRoute>
                <DashboardLayout>
                  <Footfall />
                </DashboardLayout>
              </ProtectedRoute>
            } />
            <Route path="/ai-intelligence" element={
              <ProtectedRoute>
                <DashboardLayout>
                  <AIIntelligence />
                </DashboardLayout>
              </ProtectedRoute>
            } />
            <Route path="/people-count" element={
              <ProtectedRoute>
                <DashboardLayout>
                  <PeopleCount />
                </DashboardLayout>
              </ProtectedRoute>
            } />
            <Route path="/assets" element={
              <ProtectedRoute>
                <DashboardLayout>
                  <Assets />
                </DashboardLayout>
              </ProtectedRoute>
            } />
            <Route path="/assets/:tab" element={
              <ProtectedRoute>
                <DashboardLayout>
                  <Assets />
                </DashboardLayout>
              </ProtectedRoute>
            } />
            <Route path="/settings" element={
              <ProtectedRoute>
                <DashboardLayout>
                  <Settings />
                </DashboardLayout>
              </ProtectedRoute>
            } />
            <Route path="/activity-log" element={
              <ProtectedRoute>
                <DashboardLayout>
                  <ActivityLog />
                </DashboardLayout>
              </ProtectedRoute>
            } />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </NotificationProvider>
  </QueryClientProvider>
);

export default App;
