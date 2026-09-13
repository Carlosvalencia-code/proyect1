
import React from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/UI/Button';
import PageHeader from '../components/UI/PageHeader';
import { useAnalysis } from '../contexts/AnalysisContext';
import { FaceShape, RecomendacionItem } from '../types';
import { XMarkIcon, FaceSmileIcon } from '../components/icons';
import { getFaceShapeDescription, FACE_SHAPE_IMAGE_URL, facial_shapes_db } from '../constants';
import LoadingSpinner from '../components/UI/LoadingSpinner';

const ResultCard: React.FC<{title: string; value: string | number; icon?: React.ElementType; className?: string}> = ({title, value, icon: Icon, className=""}) => (
    <div className={`bg-white p-4 rounded-lg shadow-md flex items-center ${className}`}>
        {Icon && <Icon className="h-8 w-8 text-blue-500 mr-3 flex-shrink-0" />}
        <div>
            <p className="text-sm text-gray-500">{title}</p>
            <p className="text-lg font-semibold text-gray-800">{String(value)}</p>
        </div>
    </div>
);

const RecommendationSection: React.FC<{ title: string; items: RecomendacionItem[]; categoryImageUrlSeed: string }> = ({ title, items, categoryImageUrlSeed }) => {
    if (!items || items.length === 0) return null;
    return (
        <div className="mb-8">
            <h3 className="text-xl font-semibold text-gray-700 mb-3">{title}</h3>
            <div className="space-y-4">
                {items.map((item, index) => (
                    <div key={index} className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-start space-x-4">
                            <img 
                                src={`https://picsum.photos/seed/${categoryImageUrlSeed}${index}/${item.nombre ? '100' : '80'}/${item.nombre ? '100' : '80'}`} 
                                alt={item.nombre || item.tipo} 
                                className="w-16 h-16 sm:w-20 sm:h-20 object-cover rounded-md flex-shrink-0 bg-gray-100" 
                            />
                            <div>
                                <h4 className="font-semibold text-blue-600">{item.nombre || item.tipo}</h4>
                                {item.descripcion && <p className="text-xs text-gray-500 mt-0.5 mb-1">{item.descripcion}</p>}
                                <p className="text-sm text-gray-600">{item.explicacion}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};


const FaceAnalysisResultsPage: React.FC = () => {
  const navigate = useNavigate();
  const { analysis, loadingAnalysis } = useAnalysis();
  const { facialData, faceImageForAnalysis } = analysis;

  React.useEffect(() => {
    if (!loadingAnalysis && !facialData) {
        console.warn("No facial data found, redirecting to analysis page.");
        navigate('/face-analysis');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [facialData, loadingAnalysis, navigate]);

  if (loadingAnalysis || !facialData) {
     return (
      <>
        <PageHeader title="Face Analysis Results" showBackButton onBack={() => navigate('/face-analysis')} />
        <div className="flex items-center justify-center h-[calc(100vh-10rem)]">
          <LoadingSpinner text={loadingAnalysis ? "Finalizing results..." : "Loading data..."} />
        </div>
      </>
    );
  }
  
  const { forma_rostro, caracteristicas_destacadas, confianza_analisis, recomendaciones } = facialData;
  const dbFaceInfo = facial_shapes_db[(forma_rostro as string)?.toLowerCase()];


  return (
    <>
      <PageHeader 
        title="Your Face Analysis" 
        showBackButton 
        onBack={() => navigate('/face-analysis')}
        rightAction={
            <button onClick={() => navigate('/')} className="p-2 text-gray-500 hover:text-gray-700" aria-label="Close">
                <XMarkIcon className="h-6 w-6"/>
            </button>
        }
      />
      <div className="p-4 sm:p-6 max-w-2xl mx-auto">
        {faceImageForAnalysis && (
            <div className="mb-6 rounded-lg overflow-hidden shadow-lg aspect-video max-h-64 mx-auto">
                <img src={`data:image/jpeg;base64,${faceImageForAnalysis}`} alt="Analyzed face" className="w-full h-full object-contain bg-gray-100" />
            </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
            <ResultCard title="Detected Face Shape" value={forma_rostro as string || "N/A"} icon={FaceSmileIcon} />
            <ResultCard title="Analysis Confidence" value={`${confianza_analisis || 0}%`} />
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-sm mb-8">
            <h3 className="text-md font-semibold text-gray-700 mb-1">Key Features Identified:</h3>
            {caracteristicas_destacadas && caracteristicas_destacadas.length > 0 ? (
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-0.5">
                    {caracteristicas_destacadas.map((feature, i) => <li key={i}>{feature}</li>)}
                </ul>
            ) : <p className="text-sm text-gray-500">No specific dominant features highlighted by AI.</p>}
        </div>

        <div className="bg-amber-50 p-4 rounded-lg shadow-inner mb-8">
             <h3 className="text-md font-semibold text-amber-800 mb-1">About Your {forma_rostro} Face:</h3>
            <p className="text-sm text-amber-700 leading-relaxed">{getFaceShapeDescription(forma_rostro) || dbFaceInfo?.descripcion || "General information about this face shape."}</p>
        </div>

        <h2 className="text-2xl font-bold text-gray-800 mb-4 mt-10 text-center">AI Personalized Recommendations</h2>
        
        <RecommendationSection title="Suggested Hairstyles" items={recomendaciones?.cortes_pelo} categoryImageUrlSeed="hairstyle" />
        <RecommendationSection title="Flattering Glasses" items={recomendaciones?.gafas} categoryImageUrlSeed="glasses" />
        <RecommendationSection title="Complementary Necklines" items={recomendaciones?.escotes} categoryImageUrlSeed="neckline" />
        
        <div className="mt-12 text-center">
          <p className="text-gray-600 mb-4">Next, let's find your perfect color palette!</p>
          <Button 
            variant="primary" 
            size="lg" 
            onClick={() => navigate('/chromatic-quiz')}
            className="w-full sm:w-auto"
          >
            Discover Your Colors
          </Button>
           <Button 
            variant="outline" 
            size="md" 
            onClick={() => navigate('/face-analysis')}
            className="w-full sm:w-auto mt-3"
          >
            Re-analyze Face
          </Button>
        </div>
      </div>
    </>
  );
};

export default FaceAnalysisResultsPage;
