
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/UI/Button';
import PageHeader from '../components/UI/PageHeader';
import { QUIZ_QUESTIONS } from '../constants';
import { useAnalysis } from '../contexts/AnalysisContext';

const ChromaticQuizPage: React.FC = () => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const navigate = useNavigate();
  const { setQuizAnswersAndDetermineLocalSeason } = useAnalysis();

  const currentQuestion = QUIZ_QUESTIONS[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / QUIZ_QUESTIONS.length) * 100;

  const handleAnswerSelection = (questionId: string, value: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }));
  };

  const handleNext = () => {
    if (!answers[currentQuestion.id]) {
      alert("Please select an option.");
      return;
    }
    if (currentQuestionIndex < QUIZ_QUESTIONS.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      // Quiz finished
      setQuizAnswersAndDetermineLocalSeason(answers);
      navigate('/season-results');
    }
  };
  
  const handleBack = () => {
    if (currentQuestionIndex > 0) {
        setCurrentQuestionIndex(currentQuestionIndex - 1);
    } else {
        navigate(-1); // Or to style consultation intro
    }
  };

  return (
    <>
      <PageHeader title="Color Analysis Quiz" showBackButton onBack={handleBack} />
      <div className="p-4 sm:p-6 max-w-xl mx-auto">
        <div className="mb-6">
          <div className="flex justify-between items-center mb-1">
            <p className="text-sm text-gray-500">Question {currentQuestionIndex + 1} of {QUIZ_QUESTIONS.length}</p>
            {currentQuestion.image && 
                <a href={currentQuestion.image} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-500 hover:underline">View Example</a>
            }
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div className="bg-rose-500 h-2.5 rounded-full transition-all duration-300 ease-out" style={{ width: `${progress}%` }}></div>
          </div>
        </div>

        <h2 className="text-xl sm:text-2xl font-semibold text-gray-800 mb-6 min-h-[3em]">{currentQuestion.text}</h2>

        <div className="space-y-3">
          {currentQuestion.options.map((option) => (
            <button
              key={option.value}
              onClick={() => handleAnswerSelection(currentQuestion.id, option.value)}
              aria-pressed={answers[currentQuestion.id] === option.value}
              className={`w-full text-left p-3 sm:p-4 rounded-lg border-2 transition-all duration-150 text-sm sm:text-base
                ${answers[currentQuestion.id] === option.value 
                  ? 'bg-rose-500 border-rose-500 text-white shadow-lg transform scale-102' 
                  : 'bg-white border-gray-300 hover:border-rose-400 hover:bg-rose-50 text-gray-700'}`}
            >
              {option.text}
            </button>
          ))}
        </div>
        
        <div className="mt-10 text-center">
            <Button 
                variant="primary" 
                size="lg" 
                onClick={handleNext}
                disabled={!answers[currentQuestion.id]}
                className="w-full sm:w-auto min-w-[150px] !bg-blue-500 hover:!bg-blue-600"
            >
                {currentQuestionIndex < QUIZ_QUESTIONS.length - 1 ? 'Next Question' : 'View My Color Results'}
            </Button>
        </div>
      </div>
    </>
  );
};

export default ChromaticQuizPage;
