import React, { useState } from 'react';
import apiClient from '../services/api';
import ClothingItemCard from '../components/ClothingItemCard.jsx'; // To display outfit items

// Define available options for occasion - could be constants or fetched
const OCCASION_OPTIONS = ["Casual", "Work", "Office", "Business", "Evening", "Party", "Sport", "Gym", "Errands", "Weekend", "Date Night"];

const OutfitGeneratorPage = () => {
  const [occasion, setOccasion] = useState(OCCASION_OPTIONS[0]);
  const [temperature, setTemperature] = useState(''); // Optional temperature
  const [suggestedOutfit, setSuggestedOutfit] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSuggestOutfit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSuggestedOutfit(null);

    if (!occasion) {
        setError("Por favor, selecciona una ocasión.");
        setIsLoading(false);
        return;
    }

    try {
      const params = new URLSearchParams();
      params.append('occasion', occasion);
      if (temperature && !isNaN(parseInt(temperature, 10))) {
        params.append('current_temp_celsius', parseInt(temperature, 10));
      }

      const response = await apiClient.post(`/outfits/suggest?${params.toString()}`);
      setSuggestedOutfit(response.data);
    } catch (err) {
      console.error('Error suggesting outfit:', err.response || err);
      setError(err.response?.data?.detail || 'No se pudo generar una sugerencia de outfit. Verifica tu guardarropa o inténtalo más tarde.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8">
      <h1 className="text-2xl sm:text-3xl font-bold font-display text-seentia-graphite-gray mb-8 text-center">
        Generador de Outfits SEENTIA
      </h1>

      <section className="max-w-xl mx-auto bg-white p-6 sm:p-8 rounded-xl shadow-lg mb-10">
        <form onSubmit={handleSuggestOutfit} className="space-y-5">
          <div>
            <label htmlFor="occasion" className="block text-sm font-medium text-seentia-graphite-gray mb-1">
              Selecciona la Ocasión:
            </label>
            <select
              id="occasion"
              value={occasion}
              onChange={(e) => setOccasion(e.target.value)}
              required
              className="w-full p-3 border-gray-300 rounded-md shadow-sm focus:ring-seentia-golden-amber focus:border-seentia-golden-amber transition-all"
            >
              {OCCASION_OPTIONS.map(opt => <option key={opt} value={opt}>{opt}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="temperature" className="block text-sm font-medium text-seentia-graphite-gray mb-1">
              Temperatura Actual (°C) (Opcional):
            </label>
            <input
              type="number"
              id="temperature"
              value={temperature}
              onChange={(e) => setTemperature(e.target.value)}
              placeholder="Ej: 22"
              className="w-full p-3 border-gray-300 rounded-md shadow-sm focus:ring-seentia-golden-amber focus:border-seentia-golden-amber transition-all"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-seentia-golden-amber text-white p-3 rounded-lg font-semibold hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-seentia-golden-amber focus:ring-offset-2 transition-all disabled:opacity-70"
          >
            {isLoading ? 'Generando...' : 'Sugerir Outfit'}
          </button>
        </form>
      </section>

      {isLoading && (
        <div className="text-center py-10">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-seentia-golden-amber mx-auto"></div>
          <p className="mt-3 text-seentia-graphite-gray">Buscando el outfit perfecto...</p>
        </div>
      )}

      {error && !isLoading && (
        <div className="max-w-xl mx-auto mt-6 p-4 text-sm text-center text-red-700 bg-red-100 rounded-lg shadow" role="alert">
          <span className="font-medium">Error:</span> {error}
        </div>
      )}

      {suggestedOutfit && !isLoading && !error && (
        <section className="mt-10">
          <h2 className="text-xl sm:text-2xl font-semibold font-display text-seentia-graphite-gray mb-6 text-center">
            Tu Outfit Sugerido para <span className="text-seentia-golden-amber">{suggestedOutfit.occasion}</span>
          </h2>
          {suggestedOutfit.temperature_consideration !== "Not specified" && (
            <p className="text-sm text-center text-gray-600 mb-1">
              Considerando: {suggestedOutfit.temperature_consideration}
            </p>
          )}
          <p className="text-sm text-center italic text-seentia-graphite-gray/80 mb-6">
            "{suggestedOutfit.notes}"
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 items-start">
            {/* Render each item in the outfit. The keys 'top', 'bottom', etc. come from backend service. */}
            {Object.entries(suggestedOutfit.items).map(([itemCategory, itemDetails]) => {
              if (!itemDetails) return null; // Skip if an item category is not filled
              return (
                <div key={itemCategory} className="flex flex-col items-center">
                   <p className="text-xs font-semibold uppercase text-seentia-golden-amber mb-1">{itemCategory}</p>
                   <ClothingItemCard item={itemDetails} onDelete={() => {}} onEdit={() => {}} />
                   {/* onDelete and onEdit might not be relevant here, or could link back to wardrobe */}
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
};

export default OutfitGeneratorPage;
