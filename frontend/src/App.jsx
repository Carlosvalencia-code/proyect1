import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import RegisterPage from './pages/RegisterPage.jsx';
import LoginPage from './pages/LoginPage.jsx';
import DashboardPage from './pages/DashboardPage.jsx'; // Main page after login
import WardrobePage from './pages/WardrobePage.jsx';
import AddEditItemPage from './pages/AddEditItemPage.jsx';
import OutfitGeneratorPage from './pages/OutfitGeneratorPage.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import MainLayout from './components/MainLayout.jsx'; // Import MainLayout

function App() {
  return (
    <Routes>
      {/* Public routes that don't use MainLayout (or could have a different layout) */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Routes that use MainLayout */}
      <Route element={<MainLayout />}>
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Navigate to="/dashboard" replace />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/wardrobe"
          element={
            <ProtectedRoute>
              <WardrobePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/wardrobe/add-item"
          element={
            <ProtectedRoute>
              <AddEditItemPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/wardrobe/edit-item" // Assumes item data is passed via state for editing
          element={
            <ProtectedRoute>
              <AddEditItemPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/outfit-generator"
          element={
            <ProtectedRoute>
              <OutfitGeneratorPage />
            </ProtectedRoute>
          }
        />
        {/* Add other protected routes within MainLayout here, e.g., /profile */}
        {/* <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} /> */}
      </Route>

      {/* Fallback for any other unmatched routes */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
