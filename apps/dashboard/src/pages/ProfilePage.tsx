
import React from 'react';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../components/UI/PageHeader';
import Button from '../components/UI/Button';
import { useAuth } from '../contexts/AuthContext';
import { useAnalysis } from '../contexts/AnalysisContext';
import { DEFAULT_USER_AVATAR } from '../constants';
import { FaceSmileIcon, SunIcon, Cog6ToothIcon, HeartIcon, ArrowLeftIcon, SparklesIcon } from '../components/icons'; // Added SparklesIcon

interface InfoRowProps {
  icon: React.ElementType;
  label: string;
  value: string | number | null | undefined;
  action?: () => void;
  actionLabel?: string;
}

const InfoRow: React.FC<InfoRowProps> = ({ icon: Icon, label, value, action, actionLabel }) => (
  <div className="flex items-center bg-white p-3 sm:p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow">
    <Icon className="h-6 w-6 sm:h-7 sm:w-7 text-blue-500 mr-3 sm:mr-4 flex-shrink-0" />
    <div className="flex-grow">
      <p className="text-xs sm:text-sm text-gray-500">{label}</p>
      <p className="text-sm sm:text-md font-semibold text-gray-700">{value || 'Not analyzed'}</p>
    </div>
    {action && actionLabel && (
        <Button variant="ghost" size="sm" onClick={action} className="ml-2 !text-blue-600">
            {actionLabel}
        </Button>
    )}
  </div>
);

const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const { analysis, resetAnalysis } = useAnalysis();

  const handleSignOut = () => {
    signOut();
    resetAnalysis();
    navigate('/welcome');
  };

  const facialResult = analysis.facialData;
  const chromaticResult = analysis.geminiChromatic || analysis.localChromatic;


  return (
    <>
      <PageHeader
        title="My Profile"
        showBackButton
        onBack={() => navigate('/')}
      />
      <div className="p-4 sm:p-6 max-w-2xl mx-auto">
        <div className="flex flex-col items-center mt-2 mb-6 sm:mb-8">
          <img
            src={user?.email === "demo@example.com" ? "https://picsum.photos/seed/demouser/150/150" : DEFAULT_USER_AVATAR}
            alt="User avatar"
            className="w-24 h-24 sm:w-28 sm:h-28 rounded-full object-cover border-4 border-white shadow-lg mb-2 sm:mb-3"
          />
          <h2 className="text-xl sm:text-2xl font-bold text-gray-800">{user?.fullName || 'User'}</h2>
          <p className="text-xs sm:text-sm text-gray-500">{user?.email}</p>
          {user?.joinedDate && <p className="text-xs text-gray-400 mt-0.5">{user.joinedDate}</p>}
        </div>

        <section className="mb-8">
          <h3 className="text-lg sm:text-xl font-semibold text-gray-700 mb-3 px-1 flex items-center">
            <SparklesIcon className="h-5 w-5 mr-2 text-rose-500" /> My Style DNA
          </h3>
          <div className="space-y-2.5 sm:space-y-3">
            <InfoRow
                icon={FaceSmileIcon}
                label="Face Shape Analysis"
                value={facialResult?.forma_rostro ? `${facialResult.forma_rostro} (Confidence: ${facialResult.confianza_analisis}%)` : undefined}
                action={facialResult ? () => navigate('/face-analysis-results') : () => navigate('/face-analysis')}
                actionLabel={facialResult ? "View Details" : "Analyze"}
            />
            <InfoRow
                icon={SunIcon}
                label="Color Season Analysis"
                value={
                  analysis.geminiChromatic
                    ? `${analysis.geminiChromatic.estacion} (${analysis.geminiChromatic.subtono})`
                    : analysis.localChromatic
                    ? `${analysis.localChromatic.season} (${analysis.localChromatic.undertone})`
                    : undefined
                }
                action={chromaticResult ? () => navigate('/season-results') : () => navigate('/chromatic-quiz')}
                actionLabel={chromaticResult ? "View Palette" : "Take Quiz"}
            />
          </div>
            {(!facialResult && !chromaticResult) && (
                <Button
                    variant="outline"
                    fullWidth
                    onClick={() => navigate('/style-consultation')}
                    className="mt-4 !border-blue-500 !text-blue-600 hover:!bg-blue-50"
                >
                    Start Full Style Analysis
                </Button>
            )}
        </section>

        <section className="mb-8">
          <h3 className="text-lg sm:text-xl font-semibold text-gray-700 mb-3 px-1">Account & Preferences</h3>
          <div className="space-y-2.5 sm:space-y-3">
            <button className="w-full text-left flex items-center bg-white p-3 sm:p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow" onClick={() => alert("Settings page coming soon!")}>
              <Cog6ToothIcon className="h-6 w-6 sm:h-7 sm:w-7 text-gray-500 mr-3 sm:mr-4" />
              <div>
                <p className="text-sm sm:text-md font-semibold text-gray-700">Settings</p>
                <p className="text-xs sm:text-sm text-gray-500">Manage account & app preferences</p>
              </div>
            </button>
            <button className="w-full text-left flex items-center bg-white p-3 sm:p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow" onClick={() => alert("Favorites page coming soon!")}>
              <HeartIcon className="h-6 w-6 sm:h-7 sm:w-7 text-red-400 mr-3 sm:mr-4" />
              <div>
                <p className="text-sm sm:text-md font-semibold text-gray-700">My Favorites</p>
                <p className="text-xs sm:text-sm text-gray-500">Saved items, outfits, and inspirations</p>
              </div>
            </button>
          </div>
        </section>

        <Button
            variant="secondary" // Changed from danger for softer look
            fullWidth
            onClick={handleSignOut}
            className="!bg-gray-100 !text-red-500 hover:!bg-red-50 border border-gray-200 hover:!border-red-200"
        >
          Sign Out
        </Button>
         <p className="text-center text-xs text-gray-400 mt-6">App Version 1.0.0 (MVP)</p>
      </div>
    </>
  );
};

export default ProfilePage;
