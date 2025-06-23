import React from 'react';
import { Link } from 'react-router-dom'; // For Edit button

// Placeholder image if item.imageUrl is not available
const PLACEHOLDER_IMAGE_URL = 'https://via.placeholder.com/150/FAF0E6/2C3A47?text=Prenda';

const ClothingItemCard = ({ item, onDelete, onEdit }) => {
  if (!item) return null;

  const { id, category, type, color, pattern, material, brand, image_url, notes, formality, isSpring, isSummer, isAutumn, isWinter } = item;

  const seasons = [
    isSpring && "Primavera",
    isSummer && "Verano",
    isAutumn && "Otoño",
    isWinter && "Invierno"
  ].filter(Boolean).join(', ');

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden transition-transform hover:scale-105 duration-300 ease-in-out flex flex-col">
      <div className="w-full h-48 sm:h-56 bg-gray-200 flex items-center justify-center">
        <img
          src={image_url || PLACEHOLDER_IMAGE_URL}
          alt={`${type} - ${color}`}
          className="w-full h-full object-cover"
          onError={(e) => { e.target.onerror = null; e.target.src = PLACEHOLDER_IMAGE_URL; }}
        />
      </div>
      <div className="p-4 flex flex-col flex-grow">
        <h3 className="text-lg font-semibold font-display text-seentia-graphite-gray mb-1 capitalize">
          {type || "Prenda"} <span className="text-sm font-normal text-gray-500">({category})</span>
        </h3>

        <div className="text-xs space-y-1 mb-3 text-seentia-graphite-gray/80">
          <p><strong>Color:</strong> <span className="capitalize">{color}</span></p>
          {pattern && <p><strong>Estampado:</strong> <span className="capitalize">{pattern}</span></p>}
          {material && <p><strong>Material:</strong> <span className="capitalize">{material}</span></p>}
          {brand && <p><strong>Marca:</strong> {brand}</p>}
          {formality && <p><strong>Formalidad:</strong> {formality}</p>}
          {seasons && <p><strong>Temporadas:</strong> {seasons}</p>}
          {notes && <p className="mt-1 italic"><strong>Notas:</strong> {notes}</p>}
        </div>

        <div className="mt-auto pt-3 border-t border-gray-200 flex space-x-2">
          <button
            onClick={() => onEdit(item)} // Pass the whole item to pre-fill form
            className="flex-1 text-xs bg-blue-500 hover:bg-blue-600 text-white py-2 px-3 rounded-md transition-colors"
          >
            Editar
          </button>
          <button
            onClick={() => onDelete(id)}
            className="flex-1 text-xs bg-red-500 hover:bg-red-600 text-white py-2 px-3 rounded-md transition-colors"
          >
            Eliminar
          </button>
        </div>
      </div>
    </div>
  );
};

export default ClothingItemCard;
