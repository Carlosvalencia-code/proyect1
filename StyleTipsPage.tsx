
import React from 'react';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../components/UI/PageHeader';
import Button from '../components/UI/Button';
import { useAnalysis } from '../contexts/AnalysisContext';
import { StyleTip as StyleTipType, RecomendacionItem, ColorRecomendacionItem } from '../types'; // Renamed to avoid conflict
import { facial_shapes_db, color_seasons_db } from '../constants'; // For fallback/more info

interface TipCardProps {
  title: string;
  description: string;
  imageUrl?: string;
  hexColor?: string; // For color swatches
  category: string;
}

const TipCard: React.FC<TipCardProps> = ({ title, description, imageUrl, hexColor, category }) => (
  <div className="bg-white rounded-xl shadow-lg overflow-hidden">
    <div className="flex flex-col sm:flex-row">
      {imageUrl && !hexColor && <img src={imageUrl} alt={title} className="w-full sm:w-1/3 h-40 sm:h-auto object-cover"/>}
      {hexColor && (
        <div className="w-full sm:w-1/3 h-40 sm:min-h-[150px] flex items-center justify-center" style={{backgroundColor: hexColor}}>
          <span className="text-white text-xs p-1 bg-black bg-opacity-30 rounded">{hexColor}</span>
        </div>
      )}
      <div className="p-4 sm:p-5 flex-grow">
        <p className="text-xs text-rose-500 font-semibold uppercase tracking-wide mb-1">{category}</p>
        <h3 className="text-lg font-semibold text-gray-800 mb-1.5">{title}</h3>
        <p className="text-sm text-gray-600 leading-relaxed">{description}</p>
      </div>
    </div>
  </div>
);


const StyleTipsPage: React.FC = () => {
  const navigate = useNavigate();
  const { analysis } = useAnalysis();
  const { facialData, geminiChromatic, localChromatic } = analysis;

  const generatedTips: TipCardProps[] = [];

  // Facial recommendations
  if (facialData?.recomendaciones) {
    facialData.recomendaciones.cortes_pelo.slice(0,1).forEach(item => generatedTips.push({ title: `Haircut: ${item.nombre}`, description: item.explicacion, imageUrl: `https://picsum.photos/seed/hairtip${item.nombre}/300/200`, category: "Hairstyle" }));
    facialData.recomendaciones.gafas.slice(0,1).forEach(item => generatedTips.push({ title: `Glasses: ${item.tipo}`, description: item.explicacion, imageUrl: `https://picsum.photos/seed/glatip${item.tipo}/300/200`, category: "Eyewear" }));
    facialData.recomendaciones.escotes.slice(0,1).forEach(item => generatedTips.push({ title: `Neckline: ${item.tipo}`, description: item.explicacion, imageUrl: `https://picsum.photos/seed/nectip${item.tipo}/300/200`, category: "Neckline" }));
  }

  // Chromatic recommendations
  if (geminiChromatic?.paleta_primaria) {
    geminiChromatic.paleta_primaria.slice(0, 2).forEach(item => generatedTips.push({ title: `Color: ${item.color}`, description: item.explicacion, hexColor: item.codigo_hex, category: `Your ${geminiChromatic.estacion} Palette`}));
  } else if (localChromatic?.season) {
    // Fallback to DB if Gemini palette not available
    const dbSeason = color_seasons_db[localChromatic.season.toLowerCase()];
    dbSeason?.paleta_primaria.slice(0,2).forEach(item => generatedTips.push({ title: `Color: ${item.color}`, description: item.explicacion, hexColor: item.codigo_hex, category: `Your ${localChromatic.season} Palette`}));
  }


  return (
    <>
      <PageHeader title="Personalized Style Insights" showBackButton />
      <div className="p-4 sm:p-6 max-w-3xl mx-auto">
        {generatedTips.length === 0 && (!facialData && !localChromatic) && (
           <div className="text-center py-12">
             <img src="https://picsum.photos/seed/stylenotfound/150/150" alt="Empty search" className="mx-auto mb-6 rounded-lg opacity-70" />
             <p className="text-gray-600 mb-4 text-lg">Complete your style analysis to unlock personalized tips!</p>
             <Button onClick={() => navigate('/style-consultation')} className="!bg-blue-500 hover:!bg-blue-600">Start My Analysis</Button>
           </div>
        )}

        {generatedTips.length > 0 && (
            <div className="space-y-5 sm:space-y-6 mt-4">
            {generatedTips.map((tip, index) => <TipCard key={index} {...tip} />)}
            </div>
        )}
        
        { (facialData || localChromatic) && generatedTips.length === 0 && (
             <div className="text-center py-12">
                <img src="https://picsum.photos/seed/styleloading/150/150" alt="Loading tips" className="mx-auto mb-6 rounded-lg opacity-70" />
                <p className="text-gray-600 mb-4 text-lg">Crafting your tips... If this persists, some analysis might be pending or couldn't generate specific tips.</p>
                {/* Maybe link to profile or re-analysis */}
             </div>
        )}

        <div className="mt-12 text-center">
          <h3 className="text-lg font-semibold text-gray-700 mb-3">Want to explore more?</h3>
          <div className="flex flex-col sm:flex-row justify-center gap-3">
            {facialData?.forma_rostro && (
                 <Button 
                    variant="outline" 
                    onClick={() => alert(`Explore more for ${facialData.forma_rostro} shape - coming soon!`)}
                    className="w-full sm:w-auto"
                >
                    More for {facialData.forma_rostro} Shape
                </Button>
            )}
            {(geminiChromatic?.estacion || localChromatic?.season) && (
                 <Button 
                    variant="outline" 
                    onClick={() => alert(`Explore more for ${geminiChromatic?.estacion || localChromatic?.season} season - coming soon!`)}
                    className="w-full sm:w-auto"
                >
                    More for {geminiChromatic?.estacion || localChromatic?.season} Colors
                </Button>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default StyleTipsPage;
