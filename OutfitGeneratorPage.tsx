import React, { useState, useEffect } from 'react';
import { PageHeader } from '../components/UI/PageHeader';
import { Button } from '../components/UI/Button';
import { LoadingSpinner } from '../components/UI/LoadingSpinner';
import { 
  Sparkles, Refresh, Heart, Save, Share, Calendar,
  Sun, Cloud, CloudRain, Snowflake, ThermometerSun
} from '../components/icons';
import { useWardrobe } from '../contexts/WardrobeContext';
import { apiService } from '../services/apiService';
import {
  WardrobeItem,
  OutfitSuggestion,
  OutfitGenerationRequest,
  OutfitGenerationResponse
} from '../types';

export const OutfitGeneratorPage: React.FC = () => {
  const {
    state,
    setSuggestionsLoading,
    setSuggestions,
    setSuggestionsError,
    clearSuggestions,
    addOutfit
  } = useWardrobe();

  const [selectedSuggestion, setSelectedSuggestion] = useState<number>(0);

  // Extract values from context state
  const {
    suggestions,
    suggestionsLoading: loading,
    suggestionsError: error
  } = state;

  // Form state
  const [occasion, setOccasion] = useState('CASUAL');
  const [season, setSeason] = useState('');
  const [weather, setWeather] = useState('');
  const [temperature, setTemperature] = useState<number | null>(null);
  const [preferredStyles, setPreferredStyles] = useState<string[]>([]);
  const [colorPreferences, setColorPreferences] = useState<string[]>([]);

  const occasions = [
    { value: 'WORK', label: 'Trabajo', icon: '💼' },
    { value: 'CASUAL', label: 'Casual', icon: '👕' },
    { value: 'FORMAL', label: 'Formal', icon: '🤵' },
    { value: 'PARTY', label: 'Fiesta', icon: '🎉' },
    { value: 'DATE', label: 'Cita', icon: '💕' },
    { value: 'VACATION', label: 'Vacaciones', icon: '🏖️' },
    { value: 'EXERCISE', label: 'Ejercicio', icon: '🏃' },
    { value: 'HOME', label: 'Casa', icon: '🏠' },
  ];

  const seasons = [
    { value: 'SPRING', label: 'Primavera', icon: '🌸' },
    { value: 'SUMMER', label: 'Verano', icon: '☀️' },
    { value: 'FALL', label: 'Otoño', icon: '🍂' },
    { value: 'WINTER', label: 'Invierno', icon: '❄️' },
  ];

  const weatherOptions = [
    { value: 'sunny', label: 'Soleado', icon: Sun },
    { value: 'cloudy', label: 'Nublado', icon: Cloud },
    { value: 'rainy', label: 'Lluvioso', icon: CloudRain },
    { value: 'snowy', label: 'Nevado', icon: Snowflake },
  ];

  const styles = [
    'CASUAL', 'FORMAL', 'BUSINESS', 'ELEGANT', 'SPORTY',
    'BOHEMIAN', 'MINIMALIST', 'VINTAGE', 'TRENDY', 'CLASSIC'
  ];

  const colors = [
    'negro', 'blanco', 'gris', 'azul marino', 'azul',
    'rojo', 'verde', 'amarillo', 'rosa', 'morado', 'beige', 'marrón'
  ];

  const generateOutfits = async () => {
    try {
      setSuggestionsLoading(true);
      setSuggestionsError(null);

      const request: OutfitGenerationRequest = {
        occasion,
        season: season || undefined,
        weather: weather || undefined,
        temperature: temperature || undefined,
        preferred_styles: preferredStyles,
        color_preferences: colorPreferences,
        must_include_items: [],
        exclude_items: [],
        max_suggestions: 5
      };

      const response = await apiService.generateOutfits(request);
      setSuggestions(response.suggestions || []);
      setSelectedSuggestion(0);

    } catch (err) {
      setSuggestionsError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setSuggestionsLoading(false);
    }
  };

  const saveOutfit = async (suggestion: OutfitSuggestion) => {
    try {
      const outfitData = {
        name: `Outfit ${occasion.toLowerCase()}`,
        description: suggestion.reasoning,
        style: preferredStyles,
        occasion: [occasion],
        season: season || 'ALL_SEASON',
        item_ids: suggestion.items.map(item => item.id),
        tags: ['generado', 'ai']
      };

      const savedOutfit = await apiService.createOutfit(outfitData);
      addOutfit(savedOutfit);
      alert('Outfit guardado exitosamente!');
    } catch (error) {
      console.error('Error saving outfit:', error);
      alert('Error al guardar el outfit. Inténtalo de nuevo.');
    }
  };

  const getCurrentSuggestion = () => {
    return suggestions[selectedSuggestion];
  };

  useEffect(() => {
    // Generate initial suggestions with default values
    generateOutfits();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <PageHeader 
        title="Generador de Outfits" 
        subtitle="Deja que la IA cree el look perfecto para ti"
      />

      <div className="px-4 py-6 space-y-6">
        {/* Configuration Panel */}
        <div className="bg-white rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-600" />
            Personaliza tu outfit
          </h3>

          <div className="space-y-6">
            {/* Occasion Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                ¿Para qué ocasión?
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {occasions.map((occ) => (
                  <button
                    key={occ.value}
                    onClick={() => setOccasion(occ.value)}
                    className={`p-3 rounded-lg border text-center transition-colors ${
                      occasion === occ.value
                        ? 'border-purple-500 bg-purple-50 text-purple-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="text-2xl mb-1">{occ.icon}</div>
                    <div className="text-sm font-medium">{occ.label}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Season and Weather */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Temporada (opcional)
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {seasons.map((s) => (
                    <button
                      key={s.value}
                      onClick={() => setSeason(season === s.value ? '' : s.value)}
                      className={`p-2 rounded-lg border text-center transition-colors ${
                        season === s.value
                          ? 'border-purple-500 bg-purple-50 text-purple-700'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="text-lg mb-1">{s.icon}</div>
                      <div className="text-xs">{s.label}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Clima (opcional)
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {weatherOptions.map((w) => {
                    const IconComponent = w.icon;
                    return (
                      <button
                        key={w.value}
                        onClick={() => setWeather(weather === w.value ? '' : w.value)}
                        className={`p-2 rounded-lg border text-center transition-colors ${
                          weather === w.value
                            ? 'border-purple-500 bg-purple-50 text-purple-700'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <IconComponent className="w-5 h-5 mx-auto mb-1" />
                        <div className="text-xs">{w.label}</div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Temperature */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Temperatura (°C) - opcional
              </label>
              <div className="flex items-center gap-3">
                <ThermometerSun className="w-5 h-5 text-orange-500" />
                <input
                  type="number"
                  value={temperature || ''}
                  onChange={(e) => setTemperature(e.target.value ? parseInt(e.target.value) : null)}
                  placeholder="ej: 25"
                  className="w-24 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <span className="text-sm text-gray-500">
                  Ayuda a elegir prendas apropiadas para el clima
                </span>
              </div>
            </div>

            {/* Preferred Styles */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Estilos preferidos (opcional)
              </label>
              <div className="flex flex-wrap gap-2">
                {styles.map((style) => (
                  <button
                    key={style}
                    onClick={() => {
                      setPreferredStyles(prev => 
                        prev.includes(style)
                          ? prev.filter(s => s !== style)
                          : [...prev, style]
                      );
                    }}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                      preferredStyles.includes(style)
                        ? 'bg-purple-100 text-purple-700 border border-purple-300'
                        : 'bg-gray-100 text-gray-700 border border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {style.toLowerCase()}
                  </button>
                ))}
              </div>
            </div>

            {/* Color Preferences */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Colores preferidos (opcional)
              </label>
              <div className="flex flex-wrap gap-2">
                {colors.map((color) => (
                  <button
                    key={color}
                    onClick={() => {
                      setColorPreferences(prev => 
                        prev.includes(color)
                          ? prev.filter(c => c !== color)
                          : [...prev, color]
                      );
                    }}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                      colorPreferences.includes(color)
                        ? 'bg-purple-100 text-purple-700 border border-purple-300'
                        : 'bg-gray-100 text-gray-700 border border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {color}
                  </button>
                ))}
              </div>
            </div>

            {/* Generate Button */}
            <div className="flex justify-center pt-4">
              <Button
                onClick={generateOutfits}
                disabled={loading}
                className="flex items-center gap-2 px-8"
                size="lg"
              >
                {loading ? (
                  <LoadingSpinner size="small" />
                ) : (
                  <Sparkles className="w-5 h-5" />
                )}
                {loading ? 'Generando...' : 'Generar Outfits'}
              </Button>
            </div>
          </div>
        </div>

        {/* Results */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {suggestions.length > 0 && (
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">
                Outfits sugeridos ({suggestions.length})
              </h3>
              <div className="flex items-center gap-2">
                {suggestions.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setSelectedSuggestion(index)}
                    className={`w-3 h-3 rounded-full transition-colors ${
                      index === selectedSuggestion
                        ? 'bg-purple-600'
                        : 'bg-gray-300'
                    }`}
                  />
                ))}
              </div>
            </div>

            {getCurrentSuggestion() && (
              <div className="space-y-6">
                {/* Outfit Items */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {getCurrentSuggestion().items.map((item, index) => (
                    <div key={item.id} className="text-center">
                      <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden mb-3">
                        {item.thumbnail_url || item.image_url[0] ? (
                          <img
                            src={item.thumbnail_url || item.image_url[0]}
                            alt={item.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <span className="text-gray-400">Sin imagen</span>
                          </div>
                        )}
                      </div>
                      <h4 className="font-medium text-gray-900 text-sm truncate">
                        {item.name}
                      </h4>
                      {item.brand && (
                        <p className="text-xs text-gray-500 truncate">{item.brand}</p>
                      )}
                    </div>
                  ))}
                </div>

                {/* Outfit Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">
                      {Math.round(getCurrentSuggestion().confidence)}%
                    </div>
                    <div className="text-xs text-gray-600">Confianza</div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {Math.round(getCurrentSuggestion().style_coherence)}%
                    </div>
                    <div className="text-xs text-gray-600">Coherencia</div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {Math.round(getCurrentSuggestion().color_harmony.harmony_score)}%
                    </div>
                    <div className="text-xs text-gray-600">Armonía</div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-orange-600">
                      {Math.round(getCurrentSuggestion().appropriateness)}%
                    </div>
                    <div className="text-xs text-gray-600">Apropiado</div>
                  </div>
                </div>

                {/* Reasoning */}
                <div className="bg-purple-50 rounded-lg p-4">
                  <h4 className="font-medium text-purple-900 mb-2">
                    ¿Por qué este outfit?
                  </h4>
                  <p className="text-purple-800 text-sm">
                    {getCurrentSuggestion().reasoning}
                  </p>
                </div>

                {/* Tips */}
                {getCurrentSuggestion().tips.length > 0 && (
                  <div className="bg-blue-50 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900 mb-2">
                      Consejos de styling
                    </h4>
                    <ul className="space-y-1">
                      {getCurrentSuggestion().tips.map((tip, index) => (
                        <li key={index} className="text-blue-800 text-sm flex items-start gap-2">
                          <span className="text-blue-600 mt-1">•</span>
                          {tip}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex flex-wrap gap-3 justify-center">
                  <Button
                    variant="outline"
                    onClick={generateOutfits}
                    className="flex items-center gap-2"
                  >
                    <Refresh className="w-4 h-4" />
                    Generar Nuevos
                  </Button>

                  <Button
                    variant="outline"
                    onClick={() => saveOutfit(getCurrentSuggestion())}
                    className="flex items-center gap-2"
                  >
                    <Save className="w-4 h-4" />
                    Guardar Outfit
                  </Button>

                  <Button
                    variant="outline"
                    className="flex items-center gap-2"
                  >
                    <Heart className="w-4 h-4" />
                    Favorito
                  </Button>

                  <Button
                    variant="outline"
                    className="flex items-center gap-2"
                  >
                    <Calendar className="w-4 h-4" />
                    Programar
                  </Button>

                  <Button
                    variant="outline"
                    className="flex items-center gap-2"
                  >
                    <Share className="w-4 h-4" />
                    Compartir
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}

        {!loading && suggestions.length === 0 && !error && (
          <div className="text-center py-12">
            <Sparkles className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Configura tus preferencias
            </h3>
            <p className="text-gray-500 mb-4">
              Selecciona una ocasión y haz clic en "Generar Outfits" para comenzar
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
