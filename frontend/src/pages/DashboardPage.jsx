import React, { useState } from 'react';
import FileUpload from '../components/FileUpload.jsx';
import ResultsDisplay from '../components/ResultsDisplay.jsx';
import apiClient from '../services/api.js';
// import { useAuth } from '../contexts/AuthContext.jsx'; // Uncomment if user context is needed

export default function DashboardPage() {
    const [analysisResult, setAnalysisResult] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [uploadedImagePreview, setUploadedImagePreview] = useState(null);

    const handleFileAnalyze = async (file) => {
        setIsLoading(true);
        setError('');
        setAnalysisResult(null); // Clear previous results
        if (file) {
            setUploadedImagePreview(URL.createObjectURL(file)); // Create and set preview URL for the new image
        } else {
            setUploadedImagePreview(null); // Clear preview if no file
        }

        const formData = new FormData();
        // The key 'file' must match the parameter name in the backend endpoint definition
        // In backend/app/analysis/routes.py, it's `file: UploadFile = File(...)`
        formData.append('file', file);

        try {
            const response = await apiClient.post('/api/analysis/facial', formData, {
                // Axios typically sets 'Content-Type': 'multipart/form-data' automatically for FormData
            });
            setAnalysisResult(response.data);
        } catch (err) {
            let errorMessage = 'Fallo el análisis. Por favor, inténtalo de nuevo.';
            if (err.response && err.response.data && err.response.data.detail) {
                 errorMessage = err.response.data.detail;
            } else if (err.message) {
                errorMessage = err.message;
            }
            setError(errorMessage);
            console.error('Analysis API error:', err.response || err);
            // Do not clear uploadedImagePreview here, user might want to see what they uploaded
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="space-y-8">
            {/* Optional: Welcome message or user info */}
            {/* <h1 className="text-3xl font-bold font-display text-seentia-graphite-gray mb-6">Hola, [User Name]!</h1> */}

            <section className="bg-white p-6 sm:p-8 rounded-xl shadow-lg">
                <h2 className="text-2xl font-semibold font-display text-seentia-graphite-gray mb-3 text-center sm:text-left">
                    Análisis de Estilo Facial SEENTIA
                </h2>
                <p className="text-sm text-seentia-graphite-gray/80 mb-6 text-center sm:text-left">
                    Sube una foto clara y frontal de tu rostro para recibir un análisis detallado
                    y recomendaciones de estilo personalizadas por nuestra IA.
                </p>
                <FileUpload onFileAnalyze={handleFileAnalyze} isLoading={isLoading} />

                {isLoading && (
                    <div className="mt-6 text-center">
                        <div className="inline-block animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-seentia-golden-amber"></div>
                        <p className="mt-3 text-seentia-graphite-gray text-sm">
                            Analizando tu imagen... Esto puede tardar unos segundos.
                        </p>
                    </div>
                )}

                {error && !isLoading && ( // Show error only if not loading
                    <div className="mt-6 p-4 text-sm text-red-700 bg-red-100 rounded-lg shadow text-center" role="alert">
                        <span className="font-medium">Error en el Análisis:</span> {error}
                    </div>
                )}
            </section>

            {/* Display area for the image that was analyzed and its results */}
            {uploadedImagePreview && !isLoading && ( // Show preview and results if not loading
                <section className="mt-8">
                    <div className="mb-6 p-4 bg-gray-50 rounded-lg shadow text-center">
                        <h3 className="text-lg font-semibold text-seentia-graphite-gray mb-2">Imagen Enviada para Análisis:</h3>
                        <img
                            src={uploadedImagePreview}
                            alt="Uploaded for analysis"
                            className="max-w-xs mx-auto rounded-md shadow-md max-h-72"
                        />
                    </div>
                    {analysisResult && <ResultsDisplay data={analysisResult} />}
                    {!analysisResult && !error && ( // If analysis is complete but no result (should not happen if error is caught)
                         <p className="text-center text-gray-500 mt-6">Esperando resultados del análisis...</p>
                    )}
                </section>
            )}
        </div>
    );
}
