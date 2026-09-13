
import React from 'react';
import { NavLink } from 'react-router-dom';
import { HomeIcon, SparklesIcon, UserCircleIcon, Grid, Shirt } from '../icons';

interface NavItemProps {
  to: string;
  icon: React.ElementType;
  label: string;
}

const NavItem: React.FC<NavItemProps> = ({ to, icon: Icon, label }) => {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex flex-col items-center justify-center w-1/5 py-2 px-1 text-xs transition-colors duration-200 ${
          isActive ? 'text-blue-600' : 'text-gray-500 hover:text-blue-500'
        }`
      }
    >
      <Icon className="h-6 w-6 mb-0.5" />
      <span>{label}</span>
    </NavLink>
  );
};

const BottomNavigationBar: React.FC = () => {
  // Updated navigation for wardrobe virtual features
  // Home (Page 17) -> /
  // Style (Consultation, Page 10) -> /style-consultation
  // Wardrobe (Virtual Closet) -> /wardrobe
  // Outfits (Outfit Generator) -> /outfit-generator
  // Profile (Page 15) -> /profile

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 shadow-top">
      <div className="max-w-4xl mx-auto flex justify-around items-center h-16 sm:h-20">
        <NavItem to="/" icon={HomeIcon} label="Home" />
        <NavItem to="/style-consultation" icon={SparklesIcon} label="Style AI" />
        <NavItem to="/wardrobe" icon={Grid} label="Armario" /> 
        <NavItem to="/outfit-generator" icon={Shirt} label="Outfits" />
        <NavItem to="/profile" icon={UserCircleIcon} label="Profile" />
      </div>
    </nav>
  );
};

export default BottomNavigationBar;
