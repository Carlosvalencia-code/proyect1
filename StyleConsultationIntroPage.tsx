
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/UI/Button';
import PageHeader from '../components/UI/PageHeader';
import { ShieldCheckIcon } from '../components/icons';
import { useAnalysis } from '../contexts/AnalysisContext';

const StyleConsultationIntroPage: React.FC = () => {
  const [agreedToAnalysis, setAgreedToAnalysis] = useState(false);
  const navigate = useNavigate();
  const { resetAnalysis } = useAnalysis();

  const handleStartConsultation = () => {
    if (agreedToAnalysis) {
      resetAnalysis(); // Reset previous analysis before starting a new one
      navigate('/face-analysis');
    } else {
      alert("Please agree to the terms to start the consultation.");
    }
  };

  return (
    <>
      <PageHeader title="Style Consultation" showBackButton />
      <div className="p-6 max-w-2xl mx-auto text-center">
        <h1 className="text-3xl sm:text-4xl font-bold text-gray-800 mt-4 mb-6">Discover Your Perfect Style</h1>
        <p className="text-gray-600 mb-8 text-lg leading-relaxed">
          Our AI-powered tool analyzes your facial features to suggest hairstyles, glasses, and makeup that enhance your natural beauty. Your privacy is our priority.
        </p>
        
        <div className="bg-rose-50 p-8 rounded-xl shadow-lg mb-10 flex flex-col items-center">
            <ShieldCheckIcon className="h-24 w-24 text-rose-400 mb-6" />
            <p className="text-gray-700 text-sm">
              We use your photo temporarily for analysis and do not share it. For details, see our <a href="#" className="text-blue-600 hover:underline">privacy policy</a>.
            </p>
        </div>

        <div className="flex items-start space-x-3 mb-10 p-4 bg-gray-100 rounded-lg">
          <input
            id="agreeAnalysis"
            name="agreeAnalysis"
            type="checkbox"
            checked={agreedToAnalysis}
            onChange={(e) => setAgreedToAnalysis(e.target.checked)}
            className="focus:ring-blue-500 h-5 w-5 text-blue-600 border-gray-300 rounded mt-1"
          />
          <label htmlFor="agreeAnalysis" className="text-sm text-gray-700 text-left">
            I agree to allow the app to analyze my facial data for style recommendations.
          </label>
        </div>

        <div className="space-y-4 sm:space-y-0 sm:flex sm:space-x-4 justify-center">
          <Button variant="secondary" size="lg" onClick={() => navigate(-1)} className="w-full sm:w-auto">
            Decline
          </Button>
          <Button 
            variant="primary" 
            size="lg" 
            onClick={handleStartConsultation} 
            disabled={!agreedToAnalysis}
            className="w-full sm:w-auto"
          >
            Start Consultation
          </Button>
        </div>
      </div>
    </>
  );
};

export default StyleConsultationIntroPage;
