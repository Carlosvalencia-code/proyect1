import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import {
  WardrobeItem,
  Outfit,
  WardrobeStats,
  OutfitSuggestion,
  WardrobeAnalysis
} from '../types';

// =============================================================================
// STATE INTERFACE
// =============================================================================

interface WardrobeState {
  // Wardrobe Items
  items: WardrobeItem[];
  selectedItem: WardrobeItem | null;
  itemsLoading: boolean;
  itemsError: string | null;
  
  // Outfits
  outfits: Outfit[];
  selectedOutfit: Outfit | null;
  outfitsLoading: boolean;
  outfitsError: string | null;
  
  // Outfit Suggestions
  suggestions: OutfitSuggestion[];
  suggestionsLoading: boolean;
  suggestionsError: string | null;
  
  // Statistics
  stats: WardrobeStats | null;
  statsLoading: boolean;
  statsError: string | null;
  
  // Analysis
  analysis: WardrobeAnalysis | null;
  analysisLoading: boolean;
  analysisError: string | null;
  
  // Filters
  activeFilters: {
    category?: string;
    color?: string;
    season?: string;
    occasion?: string;
    style?: string;
    is_favorite?: boolean;
  };
  
  // View Settings
  viewMode: 'grid' | 'list';
  sortBy: 'name' | 'date_added' | 'times_worn' | 'cost_per_wear';
  sortOrder: 'asc' | 'desc';
}

// =============================================================================
// ACTIONS
// =============================================================================

type WardrobeAction =
  // Items actions
  | { type: 'SET_ITEMS_LOADING'; payload: boolean }
  | { type: 'SET_ITEMS'; payload: WardrobeItem[] }
  | { type: 'SET_ITEMS_ERROR'; payload: string | null }
  | { type: 'ADD_ITEM'; payload: WardrobeItem }
  | { type: 'UPDATE_ITEM'; payload: { id: string; updates: Partial<WardrobeItem> } }
  | { type: 'REMOVE_ITEM'; payload: string }
  | { type: 'SET_SELECTED_ITEM'; payload: WardrobeItem | null }
  
  // Outfits actions
  | { type: 'SET_OUTFITS_LOADING'; payload: boolean }
  | { type: 'SET_OUTFITS'; payload: Outfit[] }
  | { type: 'SET_OUTFITS_ERROR'; payload: string | null }
  | { type: 'ADD_OUTFIT'; payload: Outfit }
  | { type: 'UPDATE_OUTFIT'; payload: { id: string; updates: Partial<Outfit> } }
  | { type: 'REMOVE_OUTFIT'; payload: string }
  | { type: 'SET_SELECTED_OUTFIT'; payload: Outfit | null }
  
  // Suggestions actions
  | { type: 'SET_SUGGESTIONS_LOADING'; payload: boolean }
  | { type: 'SET_SUGGESTIONS'; payload: OutfitSuggestion[] }
  | { type: 'SET_SUGGESTIONS_ERROR'; payload: string | null }
  | { type: 'CLEAR_SUGGESTIONS' }
  
  // Stats actions
  | { type: 'SET_STATS_LOADING'; payload: boolean }
  | { type: 'SET_STATS'; payload: WardrobeStats | null }
  | { type: 'SET_STATS_ERROR'; payload: string | null }
  
  // Analysis actions
  | { type: 'SET_ANALYSIS_LOADING'; payload: boolean }
  | { type: 'SET_ANALYSIS'; payload: WardrobeAnalysis | null }
  | { type: 'SET_ANALYSIS_ERROR'; payload: string | null }
  
  // Filter actions
  | { type: 'SET_FILTERS'; payload: WardrobeState['activeFilters'] }
  | { type: 'CLEAR_FILTERS' }
  
  // View actions
  | { type: 'SET_VIEW_MODE'; payload: 'grid' | 'list' }
  | { type: 'SET_SORT'; payload: { sortBy: WardrobeState['sortBy']; sortOrder: WardrobeState['sortOrder'] } }
  
  // Reset actions
  | { type: 'RESET_WARDROBE' };

// =============================================================================
// INITIAL STATE
// =============================================================================

const initialState: WardrobeState = {
  // Items
  items: [],
  selectedItem: null,
  itemsLoading: false,
  itemsError: null,
  
  // Outfits
  outfits: [],
  selectedOutfit: null,
  outfitsLoading: false,
  outfitsError: null,
  
  // Suggestions
  suggestions: [],
  suggestionsLoading: false,
  suggestionsError: null,
  
  // Stats
  stats: null,
  statsLoading: false,
  statsError: null,
  
  // Analysis
  analysis: null,
  analysisLoading: false,
  analysisError: null,
  
  // Filters
  activeFilters: {},
  
  // View Settings
  viewMode: 'grid',
  sortBy: 'date_added',
  sortOrder: 'desc',
};

// =============================================================================
// REDUCER
// =============================================================================

function wardrobeReducer(state: WardrobeState, action: WardrobeAction): WardrobeState {
  switch (action.type) {
    // Items
    case 'SET_ITEMS_LOADING':
      return { ...state, itemsLoading: action.payload };
    
    case 'SET_ITEMS':
      return { ...state, items: action.payload, itemsLoading: false, itemsError: null };
    
    case 'SET_ITEMS_ERROR':
      return { ...state, itemsError: action.payload, itemsLoading: false };
    
    case 'ADD_ITEM':
      return { ...state, items: [action.payload, ...state.items] };
    
    case 'UPDATE_ITEM':
      return {
        ...state,
        items: state.items.map(item =>
          item.id === action.payload.id
            ? { ...item, ...action.payload.updates }
            : item
        ),
        selectedItem: state.selectedItem?.id === action.payload.id
          ? { ...state.selectedItem, ...action.payload.updates }
          : state.selectedItem
      };
    
    case 'REMOVE_ITEM':
      return {
        ...state,
        items: state.items.filter(item => item.id !== action.payload),
        selectedItem: state.selectedItem?.id === action.payload ? null : state.selectedItem
      };
    
    case 'SET_SELECTED_ITEM':
      return { ...state, selectedItem: action.payload };
    
    // Outfits
    case 'SET_OUTFITS_LOADING':
      return { ...state, outfitsLoading: action.payload };
    
    case 'SET_OUTFITS':
      return { ...state, outfits: action.payload, outfitsLoading: false, outfitsError: null };
    
    case 'SET_OUTFITS_ERROR':
      return { ...state, outfitsError: action.payload, outfitsLoading: false };
    
    case 'ADD_OUTFIT':
      return { ...state, outfits: [action.payload, ...state.outfits] };
    
    case 'UPDATE_OUTFIT':
      return {
        ...state,
        outfits: state.outfits.map(outfit =>
          outfit.id === action.payload.id
            ? { ...outfit, ...action.payload.updates }
            : outfit
        ),
        selectedOutfit: state.selectedOutfit?.id === action.payload.id
          ? { ...state.selectedOutfit, ...action.payload.updates }
          : state.selectedOutfit
      };
    
    case 'REMOVE_OUTFIT':
      return {
        ...state,
        outfits: state.outfits.filter(outfit => outfit.id !== action.payload),
        selectedOutfit: state.selectedOutfit?.id === action.payload ? null : state.selectedOutfit
      };
    
    case 'SET_SELECTED_OUTFIT':
      return { ...state, selectedOutfit: action.payload };
    
    // Suggestions
    case 'SET_SUGGESTIONS_LOADING':
      return { ...state, suggestionsLoading: action.payload };
    
    case 'SET_SUGGESTIONS':
      return { ...state, suggestions: action.payload, suggestionsLoading: false, suggestionsError: null };
    
    case 'SET_SUGGESTIONS_ERROR':
      return { ...state, suggestionsError: action.payload, suggestionsLoading: false };
    
    case 'CLEAR_SUGGESTIONS':
      return { ...state, suggestions: [], suggestionsError: null };
    
    // Stats
    case 'SET_STATS_LOADING':
      return { ...state, statsLoading: action.payload };
    
    case 'SET_STATS':
      return { ...state, stats: action.payload, statsLoading: false, statsError: null };
    
    case 'SET_STATS_ERROR':
      return { ...state, statsError: action.payload, statsLoading: false };
    
    // Analysis
    case 'SET_ANALYSIS_LOADING':
      return { ...state, analysisLoading: action.payload };
    
    case 'SET_ANALYSIS':
      return { ...state, analysis: action.payload, analysisLoading: false, analysisError: null };
    
    case 'SET_ANALYSIS_ERROR':
      return { ...state, analysisError: action.payload, analysisLoading: false };
    
    // Filters
    case 'SET_FILTERS':
      return { ...state, activeFilters: action.payload };
    
    case 'CLEAR_FILTERS':
      return { ...state, activeFilters: {} };
    
    // View
    case 'SET_VIEW_MODE':
      return { ...state, viewMode: action.payload };
    
    case 'SET_SORT':
      return { ...state, sortBy: action.payload.sortBy, sortOrder: action.payload.sortOrder };
    
    // Reset
    case 'RESET_WARDROBE':
      return initialState;
    
    default:
      return state;
  }
}

// =============================================================================
// CONTEXT
// =============================================================================

interface WardrobeContextType {
  state: WardrobeState;
  dispatch: React.Dispatch<WardrobeAction>;
  
  // Helper actions
  setItemsLoading: (loading: boolean) => void;
  setItems: (items: WardrobeItem[]) => void;
  setItemsError: (error: string | null) => void;
  addItem: (item: WardrobeItem) => void;
  updateItem: (id: string, updates: Partial<WardrobeItem>) => void;
  removeItem: (id: string) => void;
  selectItem: (item: WardrobeItem | null) => void;
  
  setOutfitsLoading: (loading: boolean) => void;
  setOutfits: (outfits: Outfit[]) => void;
  setOutfitsError: (error: string | null) => void;
  addOutfit: (outfit: Outfit) => void;
  updateOutfit: (id: string, updates: Partial<Outfit>) => void;
  removeOutfit: (id: string) => void;
  selectOutfit: (outfit: Outfit | null) => void;
  
  setSuggestionsLoading: (loading: boolean) => void;
  setSuggestions: (suggestions: OutfitSuggestion[]) => void;
  setSuggestionsError: (error: string | null) => void;
  clearSuggestions: () => void;
  
  setStatsLoading: (loading: boolean) => void;
  setStats: (stats: WardrobeStats | null) => void;
  setStatsError: (error: string | null) => void;
  
  setAnalysisLoading: (loading: boolean) => void;
  setAnalysis: (analysis: WardrobeAnalysis | null) => void;
  setAnalysisError: (error: string | null) => void;
  
  setFilters: (filters: WardrobeState['activeFilters']) => void;
  clearFilters: () => void;
  
  setViewMode: (mode: 'grid' | 'list') => void;
  setSort: (sortBy: WardrobeState['sortBy'], sortOrder: WardrobeState['sortOrder']) => void;
  
  resetWardrobe: () => void;
}

const WardrobeContext = createContext<WardrobeContextType | undefined>(undefined);

// =============================================================================
// PROVIDER
// =============================================================================

interface WardrobeProviderProps {
  children: ReactNode;
}

export const WardrobeProvider: React.FC<WardrobeProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(wardrobeReducer, initialState);
  
  // Helper actions
  const setItemsLoading = (loading: boolean) => 
    dispatch({ type: 'SET_ITEMS_LOADING', payload: loading });
  
  const setItems = (items: WardrobeItem[]) => 
    dispatch({ type: 'SET_ITEMS', payload: items });
  
  const setItemsError = (error: string | null) => 
    dispatch({ type: 'SET_ITEMS_ERROR', payload: error });
  
  const addItem = (item: WardrobeItem) => 
    dispatch({ type: 'ADD_ITEM', payload: item });
  
  const updateItem = (id: string, updates: Partial<WardrobeItem>) => 
    dispatch({ type: 'UPDATE_ITEM', payload: { id, updates } });
  
  const removeItem = (id: string) => 
    dispatch({ type: 'REMOVE_ITEM', payload: id });
  
  const selectItem = (item: WardrobeItem | null) => 
    dispatch({ type: 'SET_SELECTED_ITEM', payload: item });
  
  const setOutfitsLoading = (loading: boolean) => 
    dispatch({ type: 'SET_OUTFITS_LOADING', payload: loading });
  
  const setOutfits = (outfits: Outfit[]) => 
    dispatch({ type: 'SET_OUTFITS', payload: outfits });
  
  const setOutfitsError = (error: string | null) => 
    dispatch({ type: 'SET_OUTFITS_ERROR', payload: error });
  
  const addOutfit = (outfit: Outfit) => 
    dispatch({ type: 'ADD_OUTFIT', payload: outfit });
  
  const updateOutfit = (id: string, updates: Partial<Outfit>) => 
    dispatch({ type: 'UPDATE_OUTFIT', payload: { id, updates } });
  
  const removeOutfit = (id: string) => 
    dispatch({ type: 'REMOVE_OUTFIT', payload: id });
  
  const selectOutfit = (outfit: Outfit | null) => 
    dispatch({ type: 'SET_SELECTED_OUTFIT', payload: outfit });
  
  const setSuggestionsLoading = (loading: boolean) => 
    dispatch({ type: 'SET_SUGGESTIONS_LOADING', payload: loading });
  
  const setSuggestions = (suggestions: OutfitSuggestion[]) => 
    dispatch({ type: 'SET_SUGGESTIONS', payload: suggestions });
  
  const setSuggestionsError = (error: string | null) => 
    dispatch({ type: 'SET_SUGGESTIONS_ERROR', payload: error });
  
  const clearSuggestions = () => 
    dispatch({ type: 'CLEAR_SUGGESTIONS' });
  
  const setStatsLoading = (loading: boolean) => 
    dispatch({ type: 'SET_STATS_LOADING', payload: loading });
  
  const setStats = (stats: WardrobeStats | null) => 
    dispatch({ type: 'SET_STATS', payload: stats });
  
  const setStatsError = (error: string | null) => 
    dispatch({ type: 'SET_STATS_ERROR', payload: error });
  
  const setAnalysisLoading = (loading: boolean) => 
    dispatch({ type: 'SET_ANALYSIS_LOADING', payload: loading });
  
  const setAnalysis = (analysis: WardrobeAnalysis | null) => 
    dispatch({ type: 'SET_ANALYSIS', payload: analysis });
  
  const setAnalysisError = (error: string | null) => 
    dispatch({ type: 'SET_ANALYSIS_ERROR', payload: error });
  
  const setFilters = (filters: WardrobeState['activeFilters']) => 
    dispatch({ type: 'SET_FILTERS', payload: filters });
  
  const clearFilters = () => 
    dispatch({ type: 'CLEAR_FILTERS' });
  
  const setViewMode = (mode: 'grid' | 'list') => 
    dispatch({ type: 'SET_VIEW_MODE', payload: mode });
  
  const setSort = (sortBy: WardrobeState['sortBy'], sortOrder: WardrobeState['sortOrder']) => 
    dispatch({ type: 'SET_SORT', payload: { sortBy, sortOrder } });
  
  const resetWardrobe = () => 
    dispatch({ type: 'RESET_WARDROBE' });
  
  const value: WardrobeContextType = {
    state,
    dispatch,
    
    // Helper actions
    setItemsLoading,
    setItems,
    setItemsError,
    addItem,
    updateItem,
    removeItem,
    selectItem,
    
    setOutfitsLoading,
    setOutfits,
    setOutfitsError,
    addOutfit,
    updateOutfit,
    removeOutfit,
    selectOutfit,
    
    setSuggestionsLoading,
    setSuggestions,
    setSuggestionsError,
    clearSuggestions,
    
    setStatsLoading,
    setStats,
    setStatsError,
    
    setAnalysisLoading,
    setAnalysis,
    setAnalysisError,
    
    setFilters,
    clearFilters,
    
    setViewMode,
    setSort,
    
    resetWardrobe,
  };
  
  return (
    <WardrobeContext.Provider value={value}>
      {children}
    </WardrobeContext.Provider>
  );
};

// =============================================================================
// HOOK
// =============================================================================

export const useWardrobe = (): WardrobeContextType => {
  const context = useContext(WardrobeContext);
  if (context === undefined) {
    throw new Error('useWardrobe must be used within a WardrobeProvider');
  }
  return context;
};

export default WardrobeContext;
