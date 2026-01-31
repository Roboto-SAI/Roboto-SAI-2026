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
import { HashRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import Chat from "./pages/Chat";
import Legacy from "./pages/Legacy";
import NotFound from "./pages/NotFound";
import Login from "./pages/Login";
import Register from "./pages/Register";
import MCPPage from "./pages/MCP";
import Settings from "./pages/Settings";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { useAuthStore } from "@/stores/authStore";
import { useMemoryStore } from "@/stores/memoryStore";

const queryClient = new QueryClient();

const Router = HashRouter;

const App = () => {
  const refreshSession = useAuthStore((state) => state.refreshSession);
  const userId = useAuthStore((state) => state.userId);
  const isLoggedIn = useAuthStore((state) => state.isLoggedIn);
  const loadUserMemories = useMemoryStore((state) => state.loadUserMemories);

  useEffect(() => {
    void refreshSession();
  }, [refreshSession]);

  // Load user memories when logged in
  useEffect(() => {
    if (isLoggedIn && userId) {
      void loadUserMemories(userId);
    }
  }, [isLoggedIn, userId, loadUserMemories]);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
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
            <Route path="/mcp" element={
              <RequireAuth>
                <MCPPage />
              </RequireAuth>
            } />
            <Route path="/settings" element={
              <RequireAuth>
                <Settings />
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
