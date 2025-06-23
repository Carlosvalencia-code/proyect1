import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage('');
    // TODO: Implement actual API call to backend for password reset
    console.log('Password reset requested for:', email);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    setIsLoading(false);
    setMessage('Si existe una cuenta con este correo, recibirás un enlace para restablecer tu contraseña.');
    setEmail(''); // Clear email field
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-seentia-white-bone p-4">
      <div className="w-full max-w-md bg-white p-8 rounded-lg shadow-xl">
        <h2 className="text-3xl font-bold text-center text-seentia-graphite-gray mb-8">
          Restablecer Contraseña
        </h2>
        <p className="text-sm text-seentia-graphite-gray mb-6 text-center">
          Ingresa tu correo electrónico y te enviaremos instrucciones para restablecer tu contraseña.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-seentia-graphite-gray">
              Correo Electrónico
            </label>
            <input
              type="email"
              name="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-seentia-golden-amber focus:border-seentia-golden-amber sm:text-sm"
            />
          </div>

          {message && <p className="text-sm text-green-600 text-center">{message}</p>}

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-seentia-golden-amber hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-seentia-golden-amber disabled:opacity-50"
            >
              {isLoading ? 'Enviando...' : 'Enviar Instrucciones'}
            </button>
          </div>
        </form>

        <p className="mt-8 text-sm text-center text-seentia-graphite-gray">
          ¿Recordaste tu contraseña?{' '}
          <Link to="/login" className="font-medium text-seentia-golden-amber hover:underline">
            Inicia Sesión
          </Link>
        </p>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
