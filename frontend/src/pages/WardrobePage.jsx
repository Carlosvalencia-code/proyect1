import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom'; // Link for Add New Item button/page
import apiClient from '../services/api';
import ClothingItemCard from '../components/ClothingItemCard.jsx';
// import { useAuth } from '../contexts/AuthContext'; // If needed for user-specific actions not covered by API client

const WardrobePage = () => {
  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // Filters state
  const [filterCategory, setFilterCategory] = useState('');
  const [filterColor, setFilterColor] = useState('');
  const [filterFormality, setFilterFormality] = useState('');

  const fetchWardrobeItems = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      if (filterCategory) params.append('category', filterCategory);
      if (filterColor) params.append('color', filterColor);
      if (filterFormality) params.append('formality', filterFormality);

      const response = await apiClient.get(`/wardrobe/items?${params.toString()}`);
      setItems(response.data || []); // Ensure items is always an array
    } catch (err) {
      console.error('Error fetching wardrobe items:', err);
      setError('No se pudieron cargar las prendas. Por favor, inténtalo de nuevo más tarde.');
      setItems([]); // Clear items on error
    } finally {
      setIsLoading(false);
    }
  }, [filterCategory, filterColor, filterFormality]);

  useEffect(() => {
    fetchWardrobeItems();
  }, [fetchWardrobeItems]);

  const handleDeleteItem = async (itemId) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar esta prenda?')) {
      try {
        await apiClient.delete(`/wardrobe/items/${itemId}`);
        setItems(prevItems => prevItems.filter(item => item.id !== itemId));
        // Optionally, show a success notification
      } catch (err) {
        console.error('Error deleting item:', err);
        setError(err.response?.data?.detail || 'No se pudo eliminar la prenda.');
      }
    }
  };

  const handleEditItem = (itemToEdit) => {
    // Navigate to the Add/Edit page, passing the item's data for pre-filling the form
    navigate('/wardrobe/edit-item', { state: { itemToEdit } });
  };

  // Unique values for filter dropdowns - could be optimized by fetching from backend or constants
  const categories = items.length > 0 ? [...new Set(items.map(item => item.category))] : [];
  const colors = items.length > 0 ? [...new Set(items.map(item => item.color))] : [];
  const formalities = items.length > 0 ? [...new Set(items.map(item => item.formality))] : [];


  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row justify-between items-center mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold font-display text-seentia-graphite-gray mb-4 sm:mb-0">
          Mi Guardarropa Virtual
        </h1>
        <Link
          to="/wardrobe/add-item" // Route for adding a new item
          className="px-6 py-3 text-sm font-medium text-white bg-seentia-golden-amber rounded-lg shadow hover:opacity-90 transition-opacity focus:outline-none focus:ring-2 focus:ring-seentia-golden-amber focus:ring-offset-2"
        >
          Añadir Nueva Prenda
        </Link>
      </div>

      {/* Filters Section */}
      <div className="mb-6 p-4 bg-white rounded-lg shadow">
        <h3 className="text-lg font-semibold text-seentia-graphite-gray mb-3">Filtrar Prendas</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="filterCategory" className="block text-xs font-medium text-gray-700">Categoría:</label>
            <select id="filterCategory" value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)} className="mt-1 block w-full p-2 border-gray-300 rounded-md shadow-sm text-sm focus:ring-seentia-golden-amber focus:border-seentia-golden-amber">
              <option value="">Todas</option>
              {categories.map(cat => <option key={cat} value={cat} className="capitalize">{cat}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="filterColor" className="block text-xs font-medium text-gray-700">Color:</label>
            <input type="text" id="filterColor" value={filterColor} onChange={(e) => setFilterColor(e.target.value)} placeholder="Ej: Azul" className="mt-1 block w-full p-2 border-gray-300 rounded-md shadow-sm text-sm focus:ring-seentia-golden-amber focus:border-seentia-golden-amber"/>
          </div>
          <div>
            <label htmlFor="filterFormality" className="block text-xs font-medium text-gray-700">Formalidad:</label>
            <select id="filterFormality" value={filterFormality} onChange={(e) => setFilterFormality(e.target.value)} className="mt-1 block w-full p-2 border-gray-300 rounded-md shadow-sm text-sm focus:ring-seentia-golden-amber focus:border-seentia-golden-amber">
              <option value="">Todas</option>
              {formalities.map(form => <option key={form} value={form}>{form}</option>)}
            </select>
          </div>
        </div>
      </div>


      {isLoading && (
        <div className="text-center py-10">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-seentia-golden-amber mx-auto"></div>
          <p className="mt-3 text-seentia-graphite-gray">Cargando prendas...</p>
        </div>
      )}

      {error && !isLoading && (
        <div className="p-4 my-4 text-sm text-center text-red-700 bg-red-100 rounded-lg shadow" role="alert">
          <span className="font-medium">Error:</span> {error}
        </div>
      )}

      {!isLoading && !error && items.length === 0 && (
        <div className="text-center py-10">
          <p className="text-xl text-seentia-graphite-gray mb-2">Tu guardarropa está vacío.</p>
          <p className="text-sm text-gray-500">¡Comienza añadiendo tus prendas favoritas!</p>
        </div>
      )}

      {!isLoading && !error && items.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {items.map(item => (
            <ClothingItemCard
              key={item.id}
              item={item}
              onDelete={handleDeleteItem}
              onEdit={handleEditItem}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default WardrobePage;
