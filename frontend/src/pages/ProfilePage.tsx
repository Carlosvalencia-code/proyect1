import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';

const ProfilePage: React.FC = () => {
  const { isAuthenticated, user, isLoading } = useAuth();

  if (isLoading) {
    return <div className="text-center p-8">Cargando perfil...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-xl">
      <h1 className="text-3xl font-bold text-seentia-golden-amber mb-6">Mi Perfil</h1>
      {user ? (
        <div className="space-y-4">
          <div>
            <p className="text-sm font-medium text-gray-500">Nombre</p>
            <p className="text-lg text-seentia-graphite-gray">{user.name || 'No especificado'}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Correo Electrónico</p>
            <p className="text-lg text-seentia-graphite-gray">{user.email}</p>
          </div>
          {/* Add more user details here as they become available */}
          {/* For example, subscription status, analysis history link, etc. */}
        </div>
      ) : (
        <p className="text-seentia-graphite-gray">No se pudo cargar la información del usuario.</p>
      )}
    </div>
  );
};

export default ProfilePage;
