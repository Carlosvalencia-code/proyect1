import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, useParams } from 'react-router-dom';
import apiClient from '../services/api';

// Define available options for dropdowns - could be constants or fetched
const CATEGORY_OPTIONS = ["Top", "Bottom", "Outerwear", "Full Body", "Shoes", "Accessory"];
const FORMALITY_OPTIONS = ["Casual", "Smart Casual", "Business Casual", "Business Formal", "Formal/Evening", "Sport"];
// Colors, patterns, materials could be free text or also predefined lists

const AddEditItemPage = () => {
  const navigate = useNavigate();
  const location = useLocation(); // To get itemToEdit passed from WardrobePage
  // const { itemId } = useParams(); // Alternative: if using URL param like /wardrobe/edit/:itemId

  const itemToEdit = location.state?.itemToEdit;
  const isEditing = !!itemToEdit;

  const [formData, setFormData] = useState({
    category: itemToEdit?.category || CATEGORY_OPTIONS[0],
    type: itemToEdit?.type || '',
    color: itemToEdit?.color || '',
    pattern: itemToEdit?.pattern || '',
    material: itemToEdit?.material || '',
    brand: itemToEdit?.brand || '',
    image_url: itemToEdit?.image_url || '', // Field for image URL (if not uploading file directly)
    notes: itemToEdit?.notes || '',
    is_spring: itemToEdit?.is_spring ?? true,
    is_summer: itemToEdit?.is_summer ?? true,
    is_autumn: itemToEdit?.is_autumn ?? true,
    is_winter: itemToEdit?.is_winter ?? true,
    formality: itemToEdit?.formality || FORMALITY_OPTIONS[0],
  });

  // For file upload, if implemented instead of image_url
  // const [imageFile, setImageFile] = useState(null);
  // const [previewUrl, setPreviewUrl] = useState(itemToEdit?.image_url || null);


  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  // const handleFileChange = (e) => {
  //   const file = e.target.files[0];
  //   if (file) {
  //     setImageFile(file);
  //     setPreviewUrl(URL.createObjectURL(file));
  //     setFormData(prev => ({ ...prev, image_url: '' })); // Clear image_url if file is selected
  //   }
  // };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSuccessMessage('');

    // Basic validation
    if (!formData.category || !formData.type || !formData.color) {
        setError("Categoría, Tipo y Color son campos obligatorios.");
        setIsLoading(false);
        return;
    }

    // Prepare payload - this matches the Pydantic model (e.g. ClothingItemCreate/Update)
    // Ensure field names match what the backend expects (e.g., is_spring vs isSpring)
    // The Pydantic models in wardrobe/routes.py used aliases, so form names should match those aliases.
    const payload = {
        category: formData.category,
        type: formData.type,
        color: formData.color,
        pattern: formData.pattern || null, // Send null if empty for optional fields
        material: formData.material || null,
        brand: formData.brand || null,
        imageUrl: formData.image_url || null, // Using imageUrl to match Pydantic alias
        notes: formData.notes || null,
        isSpring: formData.is_spring,
        isSummer: formData.is_summer,
        isAutumn: formData.is_autumn,
        isWinter: formData.is_winter,
        formality: formData.formality,
    };

    // If handling file uploads directly to backend (more complex than just URL):
    // const dataToSend = new FormData();
    // Object.keys(payload).forEach(key => dataToSend.append(key, payload[key]));
    // if (imageFile) {
    //   dataToSend.append('imageFile', imageFile); // 'imageFile' must match backend param
    // }


    try {
      if (isEditing) {
        await apiClient.put(`/wardrobe/items/${itemToEdit.id}`, payload);
        setSuccessMessage('Prenda actualizada con éxito!');
      } else {
        await apiClient.post('/wardrobe/items', payload);
        setSuccessMessage('Prenda añadida con éxito!');
      }
      setTimeout(() => {
        navigate('/wardrobe'); // Redirect back to wardrobe list
      }, 1500);
    } catch (err) {
      console.error('Error saving item:', err.response || err);
      setError(err.response?.data?.detail || `No se pudo ${isEditing ? 'actualizar' : 'añadir'} la prenda.`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-4 sm:p-6 lg:p-8 bg-white rounded-xl shadow-2xl">
      <h1 className="text-2xl sm:text-3xl font-bold font-display text-seentia-graphite-gray mb-8 text-center">
        {isEditing ? 'Editar Prenda' : 'Añadir Nueva Prenda'}
      </h1>

      {error && <p className="mb-4 p-3 bg-red-100 text-red-700 text-sm rounded-md text-center">{error}</p>}
      {successMessage && <p className="mb-4 p-3 bg-green-100 text-green-700 text-sm rounded-md text-center">{successMessage}</p>}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info: Category, Type, Color */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-seentia-graphite-gray mb-1">Categoría*</label>
            <select id="category" name="category" value={formData.category} onChange={handleChange} required className="w-full p-2 border-gray-300 rounded-md shadow-sm focus:ring-seentia-golden-amber focus:border-seentia-golden-amber">
              {CATEGORY_OPTIONS.map(opt => <option key={opt} value={opt}>{opt}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="type" className="block text-sm font-medium text-seentia-graphite-gray mb-1">Tipo*</label>
            <input type="text" id="type" name="type" value={formData.type} onChange={handleChange} required placeholder="Ej: Camiseta, Pantalón Jean" className="w-full p-2 border-gray-300 rounded-md shadow-sm focus:ring-seentia-golden-amber focus:border-seentia-golden-amber"/>
          </div>
          <div>
            <label htmlFor="color" className="block text-sm font-medium text-seentia-graphite-gray mb-1">Color*</label>
            <input type="text" id="color" name="color" value={formData.color} onChange={handleChange} required placeholder="Ej: Azul Marino" className="w-full p-2 border-gray-300 rounded-md shadow-sm focus:ring-seentia-golden-amber focus:border-seentia-golden-amber"/>
          </div>
        </div>

        {/* Optional Details: Pattern, Material, Brand */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label htmlFor="pattern" className="block text-sm font-medium text-seentia-graphite-gray mb-1">Estampado</label>
            <input type="text" id="pattern" name="pattern" value={formData.pattern} onChange={handleChange} placeholder="Ej: Rayas, Floral" className="w-full p-2 border-gray-300 rounded-md shadow-sm focus:ring-seentia-golden-amber focus:border-seentia-golden-amber"/>
          </div>
          <div>
            <label htmlFor="material" className="block text-sm font-medium text-seentia-graphite-gray mb-1">Material</label>
            <input type="text" id="material" name="material" value={formData.material} onChange={handleChange} placeholder="Ej: Algodón, Lino" className="w-full p-2 border-gray-300 rounded-md shadow-sm focus:ring-seentia-golden-amber focus:border-seentia-golden-amber"/>
          </div>
          <div>
            <label htmlFor="brand" className="block text-sm font-medium text-seentia-graphite-gray mb-1">Marca</label>
            <input type="text" id="brand" name="brand" value={formData.brand} onChange={handleChange} placeholder="Ej: Zara, Nike" className="w-full p-2 border-gray-300 rounded-md shadow-sm focus:ring-seentia-golden-amber focus:border-seentia-golden-amber"/>
          </div>
        </div>

        {/* Image URL - Simple version. File upload would require more complex handling. */}
        <div>
            <label htmlFor="image_url" className="block text-sm font-medium text-seentia-graphite-gray mb-1">URL de la Imagen (Opcional)</label>
            <input type="url" id="image_url" name="image_url" value={formData.image_url} onChange={handleChange} placeholder="https://ejemplo.com/imagen.jpg" className="w-full p-2 border-gray-300 rounded-md shadow-sm focus:ring-seentia-golden-amber focus:border-seentia-golden-amber"/>
            {/* {previewUrl && <img src={previewUrl} alt="Preview" className="mt-2 max-h-40 rounded"/>}
            <input type="file" name="imageFile" onChange={handleFileChange} accept="image/*" className="mt-1 text-sm"/> */}
        </div>

        {/* Seasons */}
        <fieldset>
          <legend className="block text-sm font-medium text-seentia-graphite-gray mb-1">Temporadas Adecuadas:</legend>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-2 mt-1">
            {['is_spring', 'is_summer', 'is_autumn', 'is_winter'].map(seasonKey => (
              <div key={seasonKey} className="flex items-center">
                <input
                  id={seasonKey}
                  name={seasonKey}
                  type="checkbox"
                  checked={formData[seasonKey]}
                  onChange={handleChange}
                  className="h-4 w-4 text-seentia-golden-amber border-gray-300 rounded focus:ring-seentia-golden-amber"
                />
                <label htmlFor={seasonKey} className="ml-2 text-sm text-gray-700 capitalize">{seasonKey.substring(3)}</label>
              </div>
            ))}
          </div>
        </fieldset>

        {/* Formality */}
        <div>
            <label htmlFor="formality" className="block text-sm font-medium text-seentia-graphite-gray mb-1">Nivel de Formalidad</label>
            <select id="formality" name="formality" value={formData.formality} onChange={handleChange} className="w-full p-2 border-gray-300 rounded-md shadow-sm focus:ring-seentia-golden-amber focus:border-seentia-golden-amber">
              {FORMALITY_OPTIONS.map(opt => <option key={opt} value={opt}>{opt}</option>)}
            </select>
        </div>

        {/* Notes */}
        <div>
            <label htmlFor="notes" className="block text-sm font-medium text-seentia-graphite-gray mb-1">Notas Adicionales</label>
            <textarea id="notes" name="notes" value={formData.notes} onChange={handleChange} rows="3" placeholder="Ej: Combinar con zapatos blancos, ideal para cenas..." className="w-full p-2 border-gray-300 rounded-md shadow-sm focus:ring-seentia-golden-amber focus:border-seentia-golden-amber"></textarea>
        </div>

        {/* Submit Button */}
        <div className="flex items-center justify-end space-x-3 pt-4">
            <button
                type="button"
                onClick={() => navigate('/wardrobe')}
                className="px-6 py-2 text-sm font-medium text-seentia-graphite-gray bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
            >
                Cancelar
            </button>
            <button
                type="submit"
                disabled={isLoading}
                className="px-6 py-2 text-sm font-medium text-white bg-seentia-golden-amber rounded-lg shadow hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-seentia-golden-amber focus:ring-offset-2 transition-opacity disabled:opacity-70"
            >
                {isLoading ? (isEditing ? 'Actualizando...' : 'Guardando...') : (isEditing ? 'Guardar Cambios' : 'Añadir Prenda')}
            </button>
        </div>
      </form>
    </div>
  );
};

export default AddEditItemPage;
