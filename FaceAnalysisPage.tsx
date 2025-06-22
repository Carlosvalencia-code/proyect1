
import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/UI/Button';
import PageHeader from '../components/UI/PageHeader';
import { CameraIcon, PhotoIcon, XMarkIcon } from '../components/icons';
import { getFacialAnalysisFromGemini, fileToBase64 } from '../services/geminiService';
import { useAnalysis } from '../contexts/AnalysisContext';
import LoadingSpinner from '../components/UI/LoadingSpinner';

const FaceAnalysisPage: React.FC = () => {
  const [selectedImagePreview, setSelectedImagePreview] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const navigate = useNavigate();
  const { setFacialAnalysisData, setLoadingAnalysis, loadingAnalysis } = useAnalysis();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.size > 4 * 1024 * 1024) { // 4MB limit
        setError("Image size should be less than 4MB.");
        setSelectedImagePreview(null);
        setImageFile(null);
        return;
      }
      setError(null);
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setSelectedImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const triggerFileUpload = () => fileInputRef.current?.click();
  const triggerCameraUpload = () => cameraInputRef.current?.click();

  const handleSubmit = async () => {
    if (!imageFile) {
      setError("Please select an image first.");
      return;
    }
    setError(null);
    setLoadingAnalysis(true);
    try {
      const base64Data = await fileToBase64(imageFile);
      const facialAnalysisResult = await getFacialAnalysisFromGemini(base64Data);
      
      if (facialAnalysisResult) {
        setFacialAnalysisData(facialAnalysisResult, base64Data); // Store base64 image with results
        navigate('/face-analysis-results');
      } else {
        // Error already handled by alert in service, but set local error too.
        setError("Facial analysis failed. The AI could not process your image.");
      }
    } catch (err) {
      console.error("Analysis submission failed:", err);
      setError("Analysis failed. Please try again. Ensure your API Key is configured if this persists.");
    } finally {
      setLoadingAnalysis(false);
    }
  };

  if (loadingAnalysis) {
    return (
      <>
        <PageHeader title="Analyzing..." showBackButton />
        <div className="flex flex-col items-center justify-center h-[calc(100vh-10rem)]">
          <LoadingSpinner text="Analyzing your features..." size="lg" />
          <p className="text-gray-500 mt-4">This might take a moment. The AI is determining your face shape and best features.</p>
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeader title="Face Analysis" showBackButton />
      <div className="p-6 max-w-lg mx-auto text-center">
        <h2 className="text-2xl font-semibold text-gray-800 mt-4 mb-2">Upload a photo of your face</h2>
        <p className="text-gray-600 mb-8">
          For best results: face forward, good lighting (no strong shadows), hair pulled back, no glasses if possible.
        </p>

        <div className="mb-8 w-full aspect-[3/4] bg-rose-100 rounded-lg flex items-center justify-center overflow-hidden relative border-2 border-dashed border-rose-300">
          {selectedImagePreview ? (
            <>
              <img src={selectedImagePreview} alt="Selected face" className="object-contain h-full w-full" />
              <button 
                onClick={() => { setSelectedImagePreview(null); setImageFile(null); if(fileInputRef.current) fileInputRef.current.value = ""; if(cameraInputRef.current) cameraInputRef.current.value = ""; }}
                className="absolute top-2 right-2 bg-black/50 text-white p-1.5 rounded-full hover:bg-black/70"
                aria-label="Remove image"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </>
          ) : (
            <div className="text-center text-rose-400 p-4">
                <CameraIcon className="h-16 w-16 mx-auto mb-2 opacity-70" />
                <p className="text-sm">Image preview will appear here</p>
            </div>
          )}
           <input type="file" accept="image/*" ref={fileInputRef} onChange={handleFileChange} className="hidden" />
           <input type="file" accept="image/*" capture="user" ref={cameraInputRef} onChange={handleFileChange} className="hidden" />
        </div>

        {error && <p className="text-red-500 text-sm mb-4 bg-red-50 p-3 rounded-md">{error}</p>}

        <div className="space-y-4 mb-8">
          <Button variant="primary" fullWidth size="lg" onClick={triggerCameraUpload} className="!bg-blue-500 hover:!bg-blue-600">
            <CameraIcon className="h-5 w-5 mr-2" /> Take Photo
          </Button>
          <Button variant="secondary" fullWidth size="lg" onClick={triggerFileUpload}>
            <PhotoIcon className="h-5 w-5 mr-2" /> Upload Photo
          </Button>
        </div>
        
        {selectedImagePreview && (
          <Button variant="primary" fullWidth size="lg" onClick={handleSubmit} isLoading={loadingAnalysis} className="!bg-green-500 hover:!bg-green-600">
            Analyze My Face
          </Button>
        )}
      </div>
    </>
  );
};

export default FaceAnalysisPage;
