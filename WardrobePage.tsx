import React, { useState, useEffect } from 'react';
import { PageHeader } from '../components/UI/PageHeader';
import { Button } from '../components/UI/Button';
import { Input } from '../components/UI/Input';
import { LoadingSpinner } from '../components/UI/LoadingSpinner';
import { Plus, Search, Filter, Grid, List, Heart, Eye, ShoppingBag } from '../components/icons';
import { useWardrobe } from '../contexts/WardrobeContext';
import { apiService } from '../services/apiService';
import { WardrobeItem, WardrobeStats } from '../types';

export const WardrobePage: React.FC = () => {
  const {
    state,
    setItemsLoading,
    setItems,
    setItemsError,
    setStatsLoading,
    setStats,
    setStatsError,
    updateItem,
    setViewMode: setContextViewMode,
    setFilters
  } = useWardrobe();

  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterSeason, setFilterSeason] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);

  // Extract values from context state
  const { 
    items, 
    itemsLoading: loading, 
    itemsError: error,
    stats,
    statsLoading,
    statsError,
    viewMode
  } = state;

  const categories = [
    'TOPS', 'BOTTOMS', 'DRESSES', 'OUTERWEAR', 'SHOES', 
    'ACCESSORIES', 'BAGS', 'JEWELRY'
  ];

  const seasons = ['SPRING', 'SUMMER', 'FALL', 'WINTER', 'ALL_SEASON'];

  useEffect(() => {
    fetchWardrobeData();
  }, []);

  const fetchWardrobeData = async () => {
    try {
      setItemsLoading(true);
      setStatsLoading(true);

      // Fetch items and stats in parallel
      const [itemsData, statsData] = await Promise.all([
        apiService.getWardrobeItems(),
        apiService.getWardrobeStats()
      ]);

      setItems(itemsData);
      setStats(statsData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      setItemsError(errorMessage);
      setStatsError(errorMessage);
    } finally {
      setItemsLoading(false);
      setStatsLoading(false);
    }
  };

  const handleItemClick = (item: WardrobeItem) => {
    // Navigate to item detail or open modal
    console.log('Item clicked:', item);
  };

  const handleAddItem = () => {
    // Navigate to add item page or open modal
    console.log('Add item clicked');
  };

  const handleToggleFavorite = async (itemId: string) => {
    try {
      const item = items.find(i => i.id === itemId);
      if (!item) return;

      const updatedItem = await apiService.updateWardrobeItem(itemId, {
        is_favorite: !item.is_favorite
      });

      updateItem(itemId, { is_favorite: updatedItem.is_favorite });
    } catch (error) {
      console.error('Error toggling favorite:', error);
      // Could show a toast notification here
    }
  };

  const filteredItems = items.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.brand?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.color.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCategory = !filterCategory || item.category === filterCategory;
    const matchesSeason = !filterSeason || item.season.includes(filterSeason);
    const matchesFavorites = !showFavoritesOnly || item.is_favorite;

    return matchesSearch && matchesCategory && matchesSeason && matchesFavorites;
  });

  if (loading || statsLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (error || statsError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600 mb-4">{error || statsError}</p>
          <Button onClick={fetchWardrobeData}>Reintentar</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <PageHeader 
        title="Mi Armario Virtual" 
        subtitle={`${stats?.total_items || 0} prendas en total`}
      />

      {/* Stats Cards */}
      {stats && (
        <div className="px-4 py-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Grid className="w-5 h-5 text-purple-600" />
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-500">Total Items</p>
                  <p className="text-2xl font-semibold text-gray-900">{stats.total_items}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center">
                <div className="p-2 bg-pink-100 rounded-lg">
                  <Heart className="w-5 h-5 text-pink-600" />
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-500">Favoritos</p>
                  <p className="text-2xl font-semibold text-gray-900">{stats.favorite_items.length}</p>
                </div>
              </div>
            </div>

            {stats.total_value && (
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <ShoppingBag className="w-5 h-5 text-green-600" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-500">Valor Total</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      ${stats.total_value.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {stats.average_cost_per_wear && (
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Eye className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-500">Costo/Uso</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      ${stats.average_cost_per_wear.toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <div className="px-4 mb-6">
        <div className="bg-white rounded-lg p-4 shadow-sm">
          <div className="flex flex-col space-y-4">
            {/* Search Bar */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                type="text"
                placeholder="Buscar por nombre, marca o color..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Filter Controls */}
            <div className="flex flex-wrap items-center gap-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center gap-2"
              >
                <Filter className="w-4 h-4" />
                Filtros
              </Button>

              <Button
                variant={showFavoritesOnly ? "primary" : "outline"}
                size="sm"
                onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
                className="flex items-center gap-2"
              >
                <Heart className={`w-4 h-4 ${showFavoritesOnly ? 'text-white' : 'text-gray-600'}`} />
                Solo Favoritos
              </Button>

              <div className="flex-1" />

              {/* View Mode Toggle */}
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setContextViewMode('grid')}
                  className={`p-2 rounded ${
                    viewMode === 'grid' 
                      ? 'bg-white shadow text-purple-600' 
                      : 'text-gray-600'
                  }`}
                >
                  <Grid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setContextViewMode('list')}
                  className={`p-2 rounded ${
                    viewMode === 'list' 
                      ? 'bg-white shadow text-purple-600' 
                      : 'text-gray-600'
                  }`}
                >
                  <List className="w-4 h-4" />
                </button>
              </div>

              <Button onClick={handleAddItem} className="flex items-center gap-2">
                <Plus className="w-4 h-4" />
                Agregar
              </Button>
            </div>

            {/* Expanded Filters */}
            {showFilters && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Categoría
                  </label>
                  <select
                    value={filterCategory}
                    onChange={(e) => setFilterCategory(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="">Todas las categorías</option>
                    {categories.map(category => (
                      <option key={category} value={category}>
                        {category.toLowerCase().replace('_', ' ')}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Temporada
                  </label>
                  <select
                    value={filterSeason}
                    onChange={(e) => setFilterSeason(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="">Todas las temporadas</option>
                    {seasons.map(season => (
                      <option key={season} value={season}>
                        {season.toLowerCase().replace('_', ' ')}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Items Grid/List */}
      <div className="px-4 pb-20">
        {filteredItems.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-24 h-24 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              <Grid className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {items.length === 0 ? 'Tu armario está vacío' : 'No se encontraron prendas'}
            </h3>
            <p className="text-gray-500 mb-4">
              {items.length === 0 
                ? 'Comienza agregando tu primera prenda' 
                : 'Intenta ajustar los filtros de búsqueda'
              }
            </p>
            {items.length === 0 && (
              <Button onClick={handleAddItem}>Agregar mi primera prenda</Button>
            )}
          </div>
        ) : (
          <div className={
            viewMode === 'grid' 
              ? 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4'
              : 'space-y-4'
          }>
            {filteredItems.map((item) => (
              <div
                key={item.id}
                onClick={() => handleItemClick(item)}
                className={`bg-white rounded-lg shadow-sm cursor-pointer hover:shadow-md transition-shadow ${
                  viewMode === 'list' ? 'flex items-center p-4' : 'overflow-hidden'
                }`}
              >
                {viewMode === 'grid' ? (
                  <>
                    {/* Grid View */}
                    <div className="aspect-square bg-gray-100 relative">
                      {item.thumbnail_url || item.image_url[0] ? (
                        <img
                          src={item.thumbnail_url || item.image_url[0]}
                          alt={item.name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Grid className="w-8 h-8 text-gray-400" />
                        </div>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleToggleFavorite(item.id);
                        }}
                        className="absolute top-2 right-2 p-1 bg-white rounded-full shadow-sm"
                      >
                        <Heart
                          className={`w-4 h-4 ${
                            item.is_favorite ? 'text-red-500 fill-current' : 'text-gray-400'
                          }`}
                        />
                      </button>
                    </div>
                    <div className="p-3">
                      <h4 className="font-medium text-gray-900 truncate">{item.name}</h4>
                      {item.brand && (
                        <p className="text-sm text-gray-500 truncate">{item.brand}</p>
                      )}
                      <div className="flex items-center justify-between mt-2">
                        <span
                          className="w-4 h-4 rounded-full border border-gray-200"
                          style={{ backgroundColor: item.color.toLowerCase() }}
                        />
                        <span className="text-xs text-gray-500">
                          {item.times_worn} usos
                        </span>
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    {/* List View */}
                    <div className="w-16 h-16 bg-gray-100 rounded-lg flex-shrink-0 mr-4">
                      {item.thumbnail_url || item.image_url[0] ? (
                        <img
                          src={item.thumbnail_url || item.image_url[0]}
                          alt={item.name}
                          className="w-full h-full object-cover rounded-lg"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Grid className="w-6 h-6 text-gray-400" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-medium text-gray-900 truncate">{item.name}</h4>
                          {item.brand && (
                            <p className="text-sm text-gray-500">{item.brand}</p>
                          )}
                          <p className="text-xs text-gray-400 capitalize">
                            {item.category.toLowerCase().replace('_', ' ')}
                          </p>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleToggleFavorite(item.id);
                          }}
                          className="ml-2 p-1"
                        >
                          <Heart
                            className={`w-4 h-4 ${
                              item.is_favorite ? 'text-red-500 fill-current' : 'text-gray-400'
                            }`}
                          />
                        </button>
                      </div>
                      <div className="flex items-center justify-between mt-2">
                        <div className="flex items-center gap-2">
                          <span
                            className="w-3 h-3 rounded-full border border-gray-200"
                            style={{ backgroundColor: item.color.toLowerCase() }}
                          />
                          <span className="text-xs text-gray-500">{item.color}</span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {item.times_worn} usos
                        </span>
                      </div>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
