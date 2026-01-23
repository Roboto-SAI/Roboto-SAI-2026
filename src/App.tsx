/**
 * Roboto SAI - Main Application
 * Created by Roberto Villarreal Martinez for Roboto SAI (powered by Grok)
 * © 2025 Roberto Villarreal Martinez - All rights reserved
 */

import { useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, HashRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import Chat from "./pages/Chat";
import Legacy from "./pages/Legacy";
import NotFound from "./pages/NotFound";
import Login from "./pages/Login";
import Register from "./pages/Register";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { useAuthStore } from "@/stores/authStore";

const queryClient = new QueryClient();

const isGitHubPagesHost = () => {
  if (globalThis.window === undefined) return false;
  return globalThis.window.location.hostname.endsWith("github.io");
};

const Router = isGitHubPagesHost() ? HashRouter : BrowserRouter;

const App = () => {
  const refreshSession = useAuthStore((state) => state.refreshSession);

  useEffect(() => {
    void refreshSession();
  }, [refreshSession]);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <Router>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/chat" element={
              <RequireAuth>
                <Chat />
              </RequireAuth>
            } />
            <Route path="/legacy" element={
              <RequireAuth>
                <Legacy />
              </RequireAuth>
            } />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Router>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
