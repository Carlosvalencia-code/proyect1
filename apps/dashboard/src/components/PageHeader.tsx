
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeftIcon, Cog6ToothIcon } from '../icons'; // Assuming you have an icons file

interface PageHeaderProps {
  title: string;
  showBackButton?: boolean;
  onBack?: () => void;
  rightAction?: React.ReactNode;
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, showBackButton = false, onBack, rightAction }) => {
  const navigate = useNavigate();

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      navigate(-1);
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-white shadow-sm">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            {showBackButton && (
              <button
                onClick={handleBack}
                className="mr-2 p-2 rounded-full hover:bg-gray-100 text-gray-600"
                aria-label="Go back"
              >
                <ArrowLeftIcon className="h-6 w-6" />
              </button>
            )}
            <h1 className="text-xl font-semibold text-gray-800">{title}</h1>
          </div>
          {rightAction && <div>{rightAction}</div>}
        </div>
      </div>
    </header>
  );
};

export default PageHeader;
