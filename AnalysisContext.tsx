
import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { 
    UserAnalysis, 
    FacialAnalysisDataAPI, 
    LocalChromaticAnalysis,
    ChromaticAnalysisDataAPI,
    StyleTip,
    FaceShape, // For default initialization
    SkinUndertone,
    ColorSeason
} from '../types';
import { MOCK_STYLE_TIPS, determine_color_season, facial_shapes_db, color_seasons_db } from '../constants';

interface AnalysisContextType {
  analysis: UserAnalysis;
  setFacialAnalysisData: (data: FacialAnalysisDataAPI, imageUsed?: string) => void;
  setQuizAnswersAndDetermineLocalSeason: (answers: Record<string, string>) => LocalChromaticAnalysis | null;
  setGeminiChromaticData: (data: ChromaticAnalysisDataAPI) => void;
  getStyleTips: () => StyleTip[]; // This will need significant update
  resetAnalysis: () => void;
  loadingAnalysis: boolean;
  setLoadingAnalysis: (loading: boolean) => void;
}

const initialAnalysis: UserAnalysis = {
  facialData: null,
  localChromatic: null,
  geminiChromatic: null,
  quizAnswers: {},
  faceImageForAnalysis: undefined,
};

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined);

export const AnalysisProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [analysis, setAnalysisState] = useState<UserAnalysis>(initialAnalysis);
  const [loadingAnalysis, setLoadingAnalysis] = useState<boolean>(false);

  useEffect(() => {
    const storedAnalysis = localStorage.getItem('synthiaAnalysis');
    if (storedAnalysis) {
      try {
        const parsed = JSON.parse(storedAnalysis);
        // Basic validation to ensure structure is somewhat as expected
        if (parsed && typeof parsed.quizAnswers === 'object') {
            setAnalysisState(parsed);
        } else {
            setAnalysisState(initialAnalysis);
        }
      } catch (e) {
        console.error("Failed to parse stored analysis:", e);
        setAnalysisState(initialAnalysis);
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('synthiaAnalysis', JSON.stringify(analysis));
  }, [analysis]);

  const setFacialAnalysisData = (data: FacialAnalysisDataAPI, imageUsed?: string) => {
    setAnalysisState(prev => ({ 
        ...prev, 
        facialData: data,
        faceImageForAnalysis: imageUsed || prev.faceImageForAnalysis
    }));
  };

  const setQuizAnswersAndDetermineLocalSeason = (answers: Record<string, string>): LocalChromaticAnalysis | null => {
    const localResult = determine_color_season(answers);
    setAnalysisState(prev => ({
      ...prev,
      quizAnswers: answers,
      localChromatic: localResult,
      geminiChromatic: null, // Reset Gemini chromatic data when quiz is retaken
    }));
    return localResult;
  };

  const setGeminiChromaticData = (data: ChromaticAnalysisDataAPI) => {
     setAnalysisState(prev => ({ ...prev, geminiChromatic: data }));
  };
  
  const getStyleTips = (): StyleTip[] => {
    const tips: StyleTip[] = [];
    
    // Add AI-generated facial recommendations as tips
    if (analysis.facialData?.recomendaciones) {
        const { cortes_pelo, gafas, escotes } = analysis.facialData.recomendaciones;
        cortes_pelo.forEach((item, i) => tips.push({
            id: `fhr-${i}`, title: `Haircut: ${item.nombre}`, description: item.explicacion, 
            imageUrl: `https://picsum.photos/seed/hair${i}/200/200`, category: 'faceShape'
        }));
        gafas.forEach((item, i) => tips.push({
            id: `fgl-${i}`, title: `Glasses: ${item.tipo}`, description: item.explicacion,
            imageUrl: `https://picsum.photos/seed/glass${i}/200/200`, category: 'faceShape'
        }));
        escotes.forEach((item, i) => tips.push({
            id: `fne-${i}`, title: `Neckline: ${item.tipo}`, description: item.explicacion,
            imageUrl: `https://picsum.photos/seed/neck${i}/200/200`, category: 'faceShape'
        }));
    }

    // Add AI-generated color palette recommendations as tips
    if (analysis.geminiChromatic?.paleta_primaria) {
        analysis.geminiChromatic.paleta_primaria.slice(0,2).forEach((item, i) => tips.push({ // Show first 2 palette colors as tips
            id: `cpa-${i}`, title: `Color Idea: ${item.color}`, description: item.explicacion,
            imageUrl: `https://via.placeholder.com/200x200/${item.codigo_hex.substring(1)}/${item.codigo_hex.substring(1)}?text=${item.color.replace(' ','+')}`, 
            category: 'colorSeason'
        }));
    }
    
    // Fallback or additional general tips from MOCK_STYLE_TIPS if AI tips are few
    if (tips.length < 3) {
        MOCK_STYLE_TIPS.forEach(tip => {
            if (tips.length < 5 && !tips.find(t => t.title === tip.title)) { // Avoid duplicates
                 if (tip.category === 'colorSeason' && analysis.localChromatic?.season && tip.appliesTo === analysis.localChromatic.season) {
                    tips.push(tip);
                } else if (tip.category === 'faceShape' && analysis.facialData?.forma_rostro && tip.appliesTo === analysis.facialData.forma_rostro) {
                    tips.push(tip);
                } else if (tip.category === 'general') {
                   // tips.push(tip);
                }
            }
        });
    }
    return tips.slice(0, 5); // Max 5 tips
  };
  
  const resetAnalysis = () => {
    setAnalysisState(initialAnalysis);
    localStorage.removeItem('synthiaAnalysis');
  };

  return (
    <AnalysisContext.Provider value={{ 
        analysis, 
        setFacialAnalysisData, 
        setQuizAnswersAndDetermineLocalSeason,
        setGeminiChromaticData,
        getStyleTips, 
        resetAnalysis, 
        loadingAnalysis, 
        setLoadingAnalysis 
    }}>
      {children}
    </AnalysisContext.Provider>
  );
};

export const useAnalysis = (): AnalysisContextType => {
  const context = useContext(AnalysisContext);
  if (context === undefined) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
};
