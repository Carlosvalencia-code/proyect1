
import React from 'react';
import { Link } from 'react-router-dom';
import Button from '../components/UI/Button';
import PageHeader from '../components/UI/PageHeader';
import { APP_NAME } from '../constants';
import { useAuth } from '../contexts/AuthContext';
import { Cog6ToothIcon, PlusIcon } from '../components/icons';

const HomePage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="flex flex-col min-h-screen">
      <PageHeader 
        title={APP_NAME} 
        rightAction={
          <button className="p-2 text-gray-500 hover:text-gray-700">
            <Cog6ToothIcon className="h-6 w-6" />
          </button>
        }
      />
      <main className="flex-grow flex flex-col items-center justify-center text-center p-6 bg-gradient-to-br from-rose-50 via-white to-teal-50">
        <img src="https://picsum.photos/seed/synthiahome/200/200" alt="Fashion illustration" className="rounded-full w-40 h-40 sm:w-48 sm:h-48 object-cover mb-8 shadow-lg border-4 border-white" />
        <h1 className="text-2xl sm:text-3xl font-semibold text-gray-700 mb-2">
          Hello, {user?.fullName?.split(' ')[0] || 'Style Explorer'}!
        </h1>
        <p className="text-gray-600 mb-8 max-w-md">
          Explore personalized style recommendations and virtual try-ons. Let's discover your perfect look!
        </p>
        <Link to="/style-consultation">
          <Button variant="primary" size="lg">
            Start Style Analysis
          </Button>
        </Link>

        {/* Mock "Add to Home Screen" feature - UI only */}
        <div className="mt-16 p-4 bg-white rounded-lg shadow-md flex items-center space-x-3 max-w-sm w-full">
            <div className="bg-gray-100 p-2 rounded-lg">
                <PlusIcon className="h-6 w-6 text-blue-500" />
            </div>
            <div className="flex-grow text-left">
                <p className="text-sm font-medium text-gray-800">Add to Home Screen</p>
                <p className="text-xs text-gray-500">Access {APP_NAME} instantly from your home.</p>
            </div>
            <Button variant="outline" size="sm">Add</Button>
        </div>
      </main>
    </div>
  );
};

export default HomePage;
