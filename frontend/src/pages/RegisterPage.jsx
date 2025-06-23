import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import apiClient from '../services/api';

export default function RegisterPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        if (password.length < 8) {
            setError('La contraseña debe tener al menos 8 caracteres.');
            setIsLoading(false);
            return;
        }

        try {
            const payload = { email, password };
            if (name.trim()) { // Only include name if it's not just whitespace
                payload.name = name.trim();
            }

            await apiClient.post('/auth/register', payload);
            // On success, navigate to login page and pass a state to show success message
            navigate('/login', { state: { registrationSuccess: true, userEmail: email } });
        } catch (err) {
            if (err.response && err.response.data && err.response.data.detail) {
                setError(err.response.data.detail);
            } else {
                setError('Fallo en el registro. Por favor, inténtalo de nuevo más tarde.');
            }
            console.error('Registration error:', err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-seentia-white-bone px-4 py-8">
            <div className="p-8 bg-white rounded-xl shadow-2xl w-full max-w-md space-y-6">
                <div className="text-center">
                    {/* Placeholder for logo image */}
                    {/* <img src="/path/to/logo_draft_S_negra.png" alt="SEENTIA Logo" className="mx-auto h-16 w-auto mb-4" /> */}
                    <h1 className="text-3xl sm:text-4xl font-bold font-display text-seentia-golden-amber">SEENTIA</h1>
                    <h2 className="mt-2 text-xl sm:text-2xl font-semibold text-seentia-graphite-gray">Crear Nueva Cuenta</h2>
                </div>

                {error && (
                    <div className="p-3 bg-red-100 border border-red-300 text-red-700 text-sm rounded-md text-center">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label htmlFor="name" className="block text-sm font-medium text-seentia-graphite-gray mb-1">
                            Nombre (Opcional)
                        </label>
                        <input
                            id="name"
                            name="name"
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            className="w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-seentia-golden-amber focus:border-seentia-golden-amber transition-all"
                            placeholder="Tu Nombre Completo"
                        />
                    </div>
                    <div>
                        <label htmlFor="emailReg" className="block text-sm font-medium text-seentia-graphite-gray mb-1">
                            Correo Electrónico
                        </label>
                        <input
                            id="emailReg"
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
                        <label htmlFor="passwordReg" className="block text-sm font-medium text-seentia-graphite-gray mb-1">
                            Contraseña
                        </label>
                        <input
                            id="passwordReg"
                            name="password"
                            type="password"
                            autoComplete="new-password"
                            required
                            minLength="8"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-seentia-golden-amber focus:border-seentia-golden-amber transition-all"
                            placeholder="Mínimo 8 caracteres"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full bg-seentia-golden-amber text-white p-3 rounded-lg font-semibold hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-seentia-golden-amber focus:ring-offset-2 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                        {isLoading ? 'Registrando...' : 'Crear Cuenta'}
                    </button>
                </form>
                <p className="text-sm text-center text-seentia-graphite-gray pt-4">
                    ¿Ya tienes una cuenta?{' '}
                    <Link to="/login" className="font-medium text-seentia-golden-amber hover:underline">
                        Inicia Sesión Aquí
                    </Link>
                </p>
            </div>
        </div>
    );
}
