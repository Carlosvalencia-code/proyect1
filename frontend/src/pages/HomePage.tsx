import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const HomePage: React.FC = () => {
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="text-center">
      <h1 className="text-4xl font-bold text-seentia-golden-amber mb-6">
        Bienvenido a SEENTIA
      </h1>
      <p className="text-lg text-seentia-graphite-gray mb-8">
        Tu asesor de estilo personal impulsado por IA.
      </p>
      {isAuthenticated ? (
        <div>
          <p className="text-xl mb-4">Hola, {user?.name || user?.email || 'Usuario'}!</p>
          <p className="mb-4">Estás listo para descubrir tu estilo único.</p>
          <Link
            to="/facial-analysis" // Assuming this will be the route for facial analysis
            className="bg-seentia-golden-amber hover:opacity-90 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition duration-300 text-lg"
          >
            Analizar mi Estilo
          </Link>
        </div>
      ) : (
        <div>
          <p className="text-xl mb-4">
            Inicia sesión o regístrate para comenzar tu viaje de estilo.
          </p>
          <div className="space-x-4">
            <Link
              to="/login"
              className="bg-seentia-golden-amber hover:opacity-90 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition duration-300"
            >
              Iniciar Sesión
            </Link>
            <Link
              to="/register"
              className="bg-gray-200 hover:bg-gray-300 text-seentia-graphite-gray font-bold py-3 px-6 rounded-lg shadow-lg transition duration-300"
            >
              Registrarse
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;
