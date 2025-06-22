
import React, { useEffect, useState } from 'react';
import { useNavigate }
from 'react-router-dom';
import Button from '../components/UI/Button';
import PageHeader from '../components/UI/PageHeader';
import { useAnalysis } from '../contexts/AnalysisContext';
import { ColorSeason, SkinUndertone, ChromaticAnalysisDataAPI, ColorRecomendacionItem } from '../types';
import { SEASON_PALETTE_IMAGES, getSeasonDescription, color_seasons_db } from '../constants';
import { getColorAnalysisFromGemini } from '../services/geminiService';
import LoadingSpinner from '../components/UI/LoadingSpinner';
import { SunIcon, SparklesIcon } from '../components/icons';

const ColorSwatch: React.FC<{ colorItem: ColorRecomendacionItem, isPrimary: boolean }> = ({ colorItem, isPrimary }) => (
    <div className={`p-3 rounded-lg shadow-sm flex flex-col items-center text-center ${isPrimary ? 'bg-white' : 'bg-gray-100'}`}>
        <div 
            className="w-16 h-16 rounded-full border-2 border-gray-200 mb-2 shadow-inner" 
            style={{ backgroundColor: colorItem.codigo_hex }}
            aria-label={`Color swatch for ${colorItem.color}`}
        ></div>
        <p className="text-sm font-medium text-gray-700">{colorItem.color}</p>
        <p className="text-xs text-gray-500 mb-1">{colorItem.codigo_hex}</p>
        <p className={`text-xs ${isPrimary ? 'text-gray-600' : 'text-gray-500'} leading-tight`}>{colorItem.explicacion}</p>
    </div>
);

const SeasonResultsPage: React.FC = () => {
  const navigate = useNavigate();
  const { analysis, setGeminiChromaticData, setLoadingAnalysis: setContextLoading } = useAnalysis();
  const { localChromatic, quizAnswers, geminiChromatic } = analysis;
  
  const [isLoadingGemini, setIsLoadingGemini] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!localChromatic || Object.keys(quizAnswers).length === 0) {
      console.warn("No local chromatic analysis or quiz answers, redirecting to quiz.");
      navigate('/chromatic-quiz');
      return;
    }

    // Fetch Gemini results if not already present
    if (localChromatic && Object.keys(quizAnswers).length > 0 && !geminiChromatic) {
      const fetchGeminiData = async () => {
        setIsLoadingGemini(true);
        setContextLoading(true);
        setError(null);
        try {
          const geminiResult = await getColorAnalysisFromGemini(quizAnswers);
          if (geminiResult) {
            setGeminiChromaticData(geminiResult);
          } else {
            setError("Could not fetch detailed palette from AI. Showing general recommendations.");
          }
        } catch (e) {
          console.error("Error fetching Gemini color data:", e);
          setError("An error occurred while fetching your detailed color palette.");
        } finally {
          setIsLoadingGemini(false);
          setContextLoading(false);
        }
      };
      fetchGeminiData();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [localChromatic, quizAnswers, geminiChromatic]); // Run only when these key dependencies change

  if (!localChromatic) { // Should be caught by useEffect, but as a fallback
    return (
        <>
         <PageHeader title="Your Season" showBackButton onBack={() => navigate('/chromatic-quiz')}/>
         <LoadingSpinner text="Loading analysis results..." />
        </>
    );
  }

  const displaySeason = geminiChromatic?.estacion || localChromatic.season;
  const displayUndertone = geminiChromatic?.subtono || localChromatic.undertone;
  const displayConfidence = geminiChromatic?.confianza_analisis ?? localChromatic.confidence; // Prioritize Gemini confidence
  const displayDescription = geminiChromatic?.descripcion || getSeasonDescription(displaySeason);
  
  const primaryPalette = geminiChromatic?.paleta_primaria || color_seasons_db[displaySeason.toLowerCase()]?.paleta_primaria || [];
  const colorsToAvoid = geminiChromatic?.colores_evitar || color_seasons_db[displaySeason.toLowerCase()]?.colores_evitar || [];
  const placeholderImages = SEASON_PALETTE_IMAGES[displaySeason] || SEASON_PALETTE_IMAGES[ColorSeason.Unknown];


  return (
    <>
      <PageHeader title="Your Color Season" showBackButton onBack={() => navigate('/chromatic-quiz')} />
      <div className="p-4 sm:p-6 max-w-3xl mx-auto">
        <div className="text-center mb-8 mt-2">
            <SunIcon className={`h-20 w-20 mx-auto mb-3 ${
                displaySeason === ColorSeason.Invierno ? 'text-blue-500' :
                displaySeason === ColorSeason.Primavera ? 'text-yellow-400' :
                displaySeason === ColorSeason.Verano ? 'text-pink-400' :
                displaySeason === ColorSeason.Otono ? 'text-orange-500' : 'text-gray-400'
            }`} />
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-800">
            You are a <span className="text-rose-500">{displaySeason}</span>
          </h1>
          <p className="text-md text-gray-600 mt-1">Undertone: {displayUndertone} | Confidence: {Math.round(displayConfidence)}%</p>
        </div>

        <div className="bg-white p-4 sm:p-6 rounded-xl shadow-lg mb-8">
          <h2 className="text-xl font-semibold text-gray-700 mb-2 flex items-center">
            <SparklesIcon className="h-5 w-5 mr-2 text-rose-400" />
            About Your Season
          </h2>
          <p className="text-gray-600 text-sm leading-relaxed">{displayDescription}</p>
        </div>
        
        {isLoadingGemini && <LoadingSpinner text="Loading your personalized AI palette..." />}
        {error && <p className="text-center text-red-500 bg-red-50 p-3 rounded-md my-4">{error}</p>}

        {!isLoadingGemini && primaryPalette.length > 0 && (
          <div className="mb-10">
            <h2 className="text-xl font-semibold text-gray-700 mb-3 text-center sm:text-left">Your Primary Palette</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 sm:gap-4">
              {primaryPalette.map((colorItem) => (
                <ColorSwatch key={colorItem.codigo_hex} colorItem={colorItem} isPrimary={true} />
              ))}
            </div>
          </div>
        )}

        {!isLoadingGemini && colorsToAvoid.length > 0 && (
          <div className="mb-10">
            <h2 className="text-xl font-semibold text-gray-700 mb-3 text-center sm:text-left">Colors to Approach with Caution</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4">
              {colorsToAvoid.map((colorItem) => (
                <ColorSwatch key={colorItem.codigo_hex} colorItem={colorItem} isPrimary={false} />
              ))}
            </div>
          </div>
        )}
        
        {/* Placeholder if AI palette fails or not loaded and no DB fallback */}
        {!isLoadingGemini && primaryPalette.length === 0 && colorsToAvoid.length === 0 && (
             <div className="grid grid-cols-2 gap-4 mb-12">
                {placeholderImages.slice(0,4).map((src, index) => (
                    <div key={index} className="aspect-square bg-gray-200 rounded-lg overflow-hidden shadow-md">
                    <img src={src} alt={`${displaySeason} placeholder palette ${index + 1}`} className="w-full h-full object-cover" />
                    </div>
                ))}
            </div>
        )}


        <div className="mt-10 space-y-3 text-center">
            <Button 
                variant="primary" 
                size="lg" 
                onClick={() => navigate('/style-tips')}
                className="w-full sm:w-auto"
            >
                See My Style Recommendations
            </Button>
            <Button 
                variant="outline" 
                size="md" 
                onClick={() => navigate('/chromatic-quiz')}
                className="w-full sm:w-auto"
            >
                Retake Color Quiz
            </Button>
        </div>
      </div>
    </>
  );
};

export default SeasonResultsPage;
