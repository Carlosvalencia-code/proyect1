import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx'; // Ensure path is correct

const MainLayout = () => {
  const { isAuthenticated, logout, user } = useAuth();
  const logoTextPlaceholder = "SEENTIA"; // Placeholder for actual logo image

  return (
    <div className="min-h-screen flex flex-col bg-seentia-white-bone">
      <header className="bg-white shadow-md sticky top-0 z-50">
        <nav className="container mx-auto px-4 sm:px-6 lg:px-8 py-3 flex justify-between items-center">
          <Link to={isAuthenticated ? "/dashboard" : "/"} className="flex items-center space-x-2">
            {/* Placeholder for logo image - replace with <img/> tag when available */}
            {/* <img src="/path/to/logo_draft_S_negra.png" alt="SEENTIA Logo" className="h-8 w-auto" /> */}
            <span className="text-2xl font-bold font-display text-seentia-golden-amber">{logoTextPlaceholder}</span>
          </Link>

          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <Link to="/dashboard" className="text-sm font-medium text-seentia-graphite-gray hover:text-seentia-golden-amber transition-colors">Análisis Facial</Link>
                <Link to="/wardrobe" className="text-sm font-medium text-seentia-graphite-gray hover:text-seentia-golden-amber transition-colors">Mi Guardarropa</Link>
                <Link to="/outfit-generator" className="text-sm font-medium text-seentia-graphite-gray hover:text-seentia-golden-amber transition-colors">Generar Outfit</Link>
                {/* Optional: Display user email or name */}
                {/* {user && user.email && <span className="text-sm text-seentia-graphite-gray">{user.email}</span>} */}
                {/* <Link to="/profile" className="text-seentia-graphite-gray hover:text-seentia-golden-amber transition-colors">Perfil</Link> */}
                <button
                  onClick={logout}
                  className="px-4 py-2 text-sm font-medium text-white bg-seentia-golden-amber rounded-md hover:opacity-90 transition-opacity focus:outline-none focus:ring-2 focus:ring-seentia-golden-amber focus:ring-offset-2"
                >
                  Cerrar Sesión
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-sm font-medium text-seentia-graphite-gray hover:text-seentia-golden-amber transition-colors">
                  Iniciar Sesión
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 text-sm font-medium text-white bg-seentia-golden-amber rounded-md hover:opacity-90 transition-opacity focus:outline-none focus:ring-2 focus:ring-seentia-golden-amber focus:ring-offset-2"
                >
                  Registrarse
                </Link>
              </>
            )}
          </div>
        </nav>
      </header>

      <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet /> {/* Child routes will render here */}
      </main>

      <footer className="bg-gray-100 border-t border-gray-200 py-6 text-center">
        <p className="text-xs text-seentia-graphite-gray/70">
          &copy; {new Date().getFullYear()} SEENTIA. Todos los derechos reservados.
        </p>
        {/* You can add more footer links or information here */}
      </footer>
    </div>
  );
};

export default MainLayout;
