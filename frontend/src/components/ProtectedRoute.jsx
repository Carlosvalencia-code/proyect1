import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';

export default function ProtectedRoute() {
    const { token, isLoading: authIsLoading } = useAuth();
    const location = useLocation();

    if (authIsLoading) {
        // You might want to render a global loading spinner here
        // or a minimal layout to prevent layout shifts.
        return (
            <div className="flex justify-center items-center min-h-screen bg-seentia-white-bone">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-seentia-golden-amber"></div>
                {/* <p className="ml-3 text-seentia-graphite-gray">Cargando...</p> */}
            </div>
        );
    }

    if (!token) {
        // User is not authenticated, redirect to login page.
        // Pass the current location in state so we can redirect back after login.
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    // User is authenticated, render the child routes.
    // <Outlet /> is used by react-router-dom to render the matched child route component.
    return <Outlet />;
}
