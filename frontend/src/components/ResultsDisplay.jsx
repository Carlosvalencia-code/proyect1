import React from 'react';

// Reusable card component for displaying various recommendations
const RecommendationCard = ({ title, items, primaryKey, secondaryKey, explanationKey }) => {
    if (!items || items.length === 0) {
        return (
            <div className="mb-6 p-4 border border-gray-200 rounded-lg bg-white shadow-sm">
                <h4 className="text-lg font-semibold font-display text-seentia-graphite-gray mb-2">{title}</h4>
                <p className="text-sm text-gray-500">No hay recomendaciones específicas disponibles en esta categoría.</p>
            </div>
        );
    }

    return (
        <div className="mb-6 p-4 border border-gray-200 rounded-lg bg-white shadow-sm">
            <h4 className="text-lg font-semibold font-display text-seentia-graphite-gray mb-3">{title}</h4>
            <div className="space-y-3">
                {items.map((item, index) => (
                    <div key={index} className="pb-3 last:pb-0 border-b border-gray-100 last:border-b-0">
                        <h5 className="font-semibold text-seentia-golden-amber">{item[primaryKey] || "Sugerencia"}</h5>
                        {secondaryKey && item[secondaryKey] && (
                            <p className="text-xs text-gray-500 my-1">{item[secondaryKey]}</p>
                        )}
                        {explanationKey && item[explanationKey] && (
                            <p className="text-sm text-seentia-graphite-gray/90 mt-1">{item[explanationKey]}</p>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

// Component for displaying a list of features
const FeatureList = ({ title, features }) => {
    if (!features || features.length === 0) {
        return (
             <div className="mb-6 p-4 border border-gray-200 rounded-lg bg-white shadow-sm">
                <h4 className="text-lg font-semibold font-display text-seentia-graphite-gray mb-2">{title}</h4>
                <p className="text-sm text-gray-500">No se especificaron características.</p>
            </div>
        );
    }
    return (
        <div className="mb-6 p-4 border border-gray-200 rounded-lg bg-white shadow-sm">
            <h4 className="text-lg font-semibold font-display text-seentia-graphite-gray mb-2">{title}</h4>
            <ul className="list-disc list-inside space-y-1 text-seentia-graphite-gray/90 pl-4">
                {features.map((feature, i) => <li key={i} className="text-sm">{feature}</li>)}
            </ul>
        </div>
    );
};

export default function ResultsDisplay({ data }) {
    if (!data) {
        return (
            <div className="text-center p-6 bg-white rounded-lg shadow-md mt-8">
                <p className="text-seentia-graphite-gray">Esperando resultados del análisis...</p>
            </div>
        );
    }

    // Destructure data based on the JSON structure from Gemini prompt in backend/app/services/gemini_service.py
    const {
        forma_rostro,
        caracteristicas_destacadas,
        confianza_analisis_facial,
        recomendaciones_estilo_facial
    } = data;

    // Further destructure recommendations if they exist
    const {
        cortes_pelo,
        gafas_monturas,
        escotes_prendas
    } = recomendaciones_estilo_facial || {};

    return (
        <div className="max-w-3xl mx-auto bg-seentia-white-bone/50 p-4 sm:p-6 rounded-xl shadow-xl animate-fade-in mt-8">
            <h3 className="text-2xl sm:text-3xl font-bold font-display text-seentia-golden-amber mb-6 text-center">
                Resultados de Tu Análisis Facial
            </h3>

            <div className="text-center mb-8 p-4 bg-white rounded-lg shadow-md">
                <p className="text-md sm:text-lg">
                    Forma del Rostro Identificada:
                    <span className="font-bold text-seentia-golden-amber ml-2">{forma_rostro || "No determinada"}</span>
                </p>
                {typeof confianza_analisis_facial === 'number' && ( // Check if it's a number
                    <p className="text-xs text-seentia-graphite-gray/70 mt-1">
                        Confianza del Análisis: {confianza_analisis_facial}%
                    </p>
                )}
            </div>

            <FeatureList title="Características Destacadas" features={caracteristicas_destacadas} />

            <hr className="my-6 border-gray-300"/>

            <div className="space-y-6">
                <RecommendationCard
                    title="Cortes de Pelo Sugeridos"
                    items={cortes_pelo}
                    primaryKey="nombre_corte"
                    secondaryKey="descripcion_corte"
                    explanationKey="explicacion_corte"
                />
                <RecommendationCard
                    title="Monturas de Gafas Ideales"
                    items={gafas_monturas}
                    primaryKey="tipo_montura"
                    // secondaryKey={null} // No secondary key in this structure
                    explanationKey="explicacion_montura"
                />
                <RecommendationCard
                    title="Escotes que te Favorecen"
                    items={escotes_prendas}
                    primaryKey="tipo_escote"
                    // secondaryKey={null} // No secondary key
                    explanationKey="explicacion_escote"
                />
            </div>

            {(!cortes_pelo || cortes_pelo.length === 0) &&
             (!gafas_monturas || gafas_monturas.length === 0) &&
             (!escotes_prendas || escotes_prendas.length === 0) &&
                <p className="text-center text-gray-500 mt-6 p-4 bg-white rounded-lg shadow">
                    No hay recomendaciones de estilo detalladas disponibles en este momento.
                </p>
            }
        </div>
    );
}
