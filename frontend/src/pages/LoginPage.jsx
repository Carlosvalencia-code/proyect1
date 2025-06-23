import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');
    const { login, isAuthenticated, isLoading: authIsLoading } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [isSubmitting, setIsSubmitting] = useState(false); // Local loading state for submit button

    useEffect(() => {
        // Check for registration success message from navigation state
        if (location.state?.registrationSuccess) {
            setSuccessMessage(`¡Registro exitoso para ${location.state.userEmail || 'tu cuenta'}! Por favor, inicia sesión.`);
            // Clear the state to prevent message from showing again on refresh/navigation
            navigate(location.pathname, { replace: true, state: {} });
        }
    }, [location, navigate]);

    useEffect(() => {
        // Redirect if already authenticated and auth context is not loading
        if (isAuthenticated && !authIsLoading) {
            const from = location.state?.from?.pathname || '/dashboard'; // Default to dashboard
            navigate(from, { replace: true });
        }
    }, [isAuthenticated, authIsLoading, navigate, location.state]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccessMessage(''); // Clear any previous success message on new login attempt
        setIsSubmitting(true);
        try {
            await login(email, password);
            // Successful login will trigger isAuthenticated change, and useEffect above will handle redirect.
        } catch (err) {
            if (err.response && err.response.data && err.response.data.detail) {
                setError(err.response.data.detail);
            } else {
                setError('Fallo en el inicio de sesión. Por favor, verifica tus credenciales.');
            }
            console.error('Login error:', err);
        } finally {
            setIsSubmitting(false);
        }
    };

    // If auth context is loading (e.g., verifying an existing token), show a loading indicator.
    // This prevents flashing the login form if the user is already authenticated.
    if (authIsLoading && !isAuthenticated) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-seentia-white-bone">
                <p className="text-seentia-graphite-gray">Verificando sesión...</p>
                {/* You could add a spinner here */}
            </div>
        );
    }

    return (
        <div className="flex items-center justify-center min-h-screen bg-seentia-white-bone px-4 py-8">
            <div className="p-8 bg-white rounded-xl shadow-2xl w-full max-w-md space-y-6">
                <div className="text-center">
                    {/* <img src="/path/to/logo_draft_S_negra.png" alt="SEENTIA Logo" className="mx-auto h-16 w-auto mb-4" /> */}
                    <h1 className="text-3xl sm:text-4xl font-bold font-display text-seentia-golden-amber">SEENTIA</h1>
                    <h2 className="mt-2 text-xl sm:text-2xl font-semibold text-seentia-graphite-gray">Bienvenido de Nuevo</h2>
                </div>

                {error && (
                    <div className="p-3 bg-red-100 border border-red-300 text-red-700 text-sm rounded-md text-center">
                        {error}
                    </div>
                )}
                {successMessage && (
                     <div className="p-3 bg-green-100 border border-green-300 text-green-700 text-sm rounded-md text-center">
                        {successMessage}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label htmlFor="emailLogin" className="block text-sm font-medium text-seentia-graphite-gray mb-1">
                            Correo Electrónico
                        </label>
                        <input
                            id="emailLogin"
                            name="email"
                            type="email"
                            autoComplete="email"
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-seentia-golden-amber focus:border-seentia-golden-amber transition-all"
                            placeholder="tu@email.com"
                        />
                    </div>
                    <div>
                        <label htmlFor="passwordLogin" className="block text-sm font-medium text-seentia-graphite-gray mb-1">
                            Contraseña
                        </label>
                        <input
                            id="passwordLogin"
                            name="password"
                            type="password"
                            autoComplete="current-password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-seentia-golden-amber focus:border-seentia-golden-amber transition-all"
                            placeholder="Tu Contraseña"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={isSubmitting || authIsLoading}
                        className="w-full bg-seentia-golden-amber text-white p-3 rounded-lg font-semibold hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-seentia-golden-amber focus:ring-offset-2 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                        {isSubmitting ? 'Iniciando Sesión...' : 'Iniciar Sesión'}
                    </button>
                </form>
                <p className="text-sm text-center text-seentia-graphite-gray pt-4">
                    ¿No tienes cuenta?{' '}
                    <Link to="/register" className="font-medium text-seentia-golden-amber hover:underline">
                        Regístrate Aquí
                    </Link>
                </p>
            </div>
        </div>
    );
}
