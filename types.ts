
export interface User {
  id: string;
  fullName: string;
  email: string;
  joinedDate?: string; // e.g., "Joined 2022"
}

// --- Basic Enums ---
export enum FaceShape {
  Ovalado = "Ovalado",
  Redondo = "Redondo",
  Cuadrado = "Cuadrado",
  Rectangular = "Rectangular",
  Corazon = "Corazón",
  Diamante = "Diamante",
  Triangular = "Triangular", // or Triangulo Invertido
  Unknown = "Unknown"
}

export enum SkinUndertone {
  Frio = "Frío", // Cool
  Calido = "Cálido", // Warm
  Neutro = "Neutro", // Neutral
  Unknown = "Unknown"
}

export enum ColorSeason {
  Invierno = "Invierno", // Winter (Cool & Bright/Deep)
  Primavera = "Primavera", // Spring (Warm & Bright/Light)
  Verano = "Verano", // Summer (Cool & Muted/Soft)
  Otono = "Otoño", // Autumn (Warm & Muted/Deep)
  Unknown = "Unknown"
}

// --- Recommendation Item Structures ---
export interface RecomendacionItem {
  nombre?: string; // For haircuts
  tipo?: string; // For glasses, necklines
  descripcion?: string; // Optional detailed description
  explicacion: string;
  // imagen_ilustrativa?: string; // URL, future enhancement
}

export interface ColorRecomendacionItem {
  color: string;
  codigo_hex: string;
  explicacion: string;
  // imagen_ilustrativa?: string; // URL, future enhancement
}

// --- Gemini API Input Parts ---
export interface ImagePart {
  inlineData: {
    mimeType: string;
    data: string; // base64 encoded string
  };
}

export interface TextPart {
  text: string;
}

// --- Facial Analysis (from Gemini) ---
export interface FacialRecomendacionesAPI {
  cortes_pelo: RecomendacionItem[];
  gafas: RecomendacionItem[];
  escotes: RecomendacionItem[];
}

export interface FacialAnalysisDataAPI {
  forma_rostro: FaceShape | string; // Gemini might return a string
  caracteristicas_destacadas: string[];
  confianza_analisis: number; // 0-100
  recomendaciones: FacialRecomendacionesAPI;
  // proporciones?: string; // "proporciones faciales generales" - from "Refinamiento", less prominent in "Final MVP" prompt
}

// --- Chromatic Analysis (Quiz-based local determination) ---
export interface LocalChromaticAnalysis {
  season: ColorSeason;
  undertone: SkinUndertone;
  confidence: number; // 0-100
  scores: Record<string, number>; // Raw scores for each season
}

// --- Chromatic Analysis (from Gemini, based on quiz answers) ---
export interface ChromaticAnalysisDataAPI {
  estacion: ColorSeason | string; // Gemini might return a string
  subtono: SkinUndertone | string;
  descripcion: string; // General description of the color station
  confianza_analisis?: number; // 0-100 (added based on prompt asking for it)
  paleta_primaria: ColorRecomendacionItem[];
  colores_evitar: ColorRecomendacionItem[];
}

// --- User Analysis Context State ---
export interface UserAnalysis {
  facialData: FacialAnalysisDataAPI | null;
  // For chromatic, we store both local determination and Gemini's detailed palette
  localChromatic: LocalChromaticAnalysis | null;
  geminiChromatic: ChromaticAnalysisDataAPI | null;
  quizAnswers: Record<string, string>; // Raw answers from the quiz
  faceImageForAnalysis?: string; // base64 image used for analysis
}

// --- Chromatic Quiz ---
export interface ChromaticQuizQuestion {
  id: string; // e.g., "color_venas", "reaccion_sol"
  text: string;
  options: { text: string; value: string }[];
  image?: string; // Optional reference image for the question
}

// --- Style Tips (General or derived from DBs) ---
export interface StyleTip {
  id: string;
  title: string;
  description: string;
  imageUrl: string;
  category: "faceShape" | "colorSeason" | "general";
  appliesTo?: FaceShape | ColorSeason; // For better filtering
}

// --- Static DB Structures ---
export interface DBRecomendaciones {
  cortes_pelo: RecomendacionItem[];
  gafas: RecomendacionItem[];
  escotes: RecomendacionItem[];
  // accesorios?: RecomendacionItem[]; // As per "Refinamiento" doc
}
export interface DBFaceShapeDetail {
  descripcion: string;
  caracteristicas: string[];
  recomendaciones: DBRecomendaciones;
}
export type FacialShapesDB = Record<string, DBFaceShapeDetail>; // Keyed by FaceShape string

export interface DBColorSeasonDetail {
  subtono: SkinUndertone | string;
  descripcion: string;
  paleta_primaria: ColorRecomendacionItem[];
  colores_evitar: ColorRecomendacionItem[];
  // combinaciones_recomendadas?: any[]; // As per "Refinamiento" doc
  // colores_a_evitar_explicacion?: string;
}
export type ColorSeasonsDB = Record<string, DBColorSeasonDetail>; // Keyed by ColorSeason string

// --- Feedback ---
export interface FeedbackSubmission {
  type: 'bug' | 'feature' | 'general' | 'analysis_accuracy';
  title: string;
  description: string;
  rating?: number; // 1-5 stars
  analysis_id?: string; // If feedback is about a specific analysis
  user_email?: string;
  user_context?: {
    page: string;
    user_agent: string;
    timestamp: string;
  };
}

// =============================================================================
// WARDROBE VIRTUAL TYPES
// =============================================================================

// --- Wardrobe Item ---
export interface WardrobeItem {
  id: string;
  name: string;
  description?: string;
  brand?: string;
  color: string;
  category: ClothingCategory;
  subcategory?: ClothingSubcategory;
  style: ClothingStyle[];
  season: Season[];
  occasions: Occasion[];
  fit_type?: FitType;
  size?: string;
  purchase_price?: number;
  purchase_date?: string;
  times_worn: number;
  cost_per_wear?: number;
  image_url: string[];
  thumbnail_url?: string;
  is_favorite: boolean;
  versatility_score?: number;
  ai_analysis?: {
    color_analysis: string;
    style_description: string;
    versatility_notes: string;
    styling_tips: string[];
  };
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

// --- Outfit ---
export interface Outfit {
  id: string;
  name: string;
  description?: string;
  style: ClothingStyle[];
  occasion: Occasion[];
  season: Season;
  status: OutfitStatus;
  items: WardrobeItem[];
  times_worn: number;
  rating?: number;
  notes?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

// --- Outfit Suggestion ---
export interface OutfitSuggestion {
  items: WardrobeItem[];
  confidence: number;
  style_coherence: number;
  color_harmony: {
    harmony_score: number;
    harmony_type: string;
  };
  appropriateness: number;
  reasoning: string;
  tips: string[];
}

// --- Outfit Generation Request ---
export interface OutfitGenerationRequest {
  occasion: string;
  season?: string;
  weather?: string;
  temperature?: number;
  preferred_styles: string[];
  color_preferences: string[];
  must_include_items: string[];
  exclude_items: string[];
  max_suggestions: number;
}

// --- Outfit Generation Response ---
export interface OutfitGenerationResponse {
  suggestions: OutfitSuggestion[];
  total_suggestions: number;
  generation_metadata: {
    request_id: string;
    processing_time: number;
    model_version: string;
  };
}

// --- Wardrobe Statistics ---
export interface WardrobeStats {
  total_items: number;
  items_by_category: Record<string, number>;
  items_by_color: Record<string, number>;
  items_by_season: Record<string, number>;
  items_by_style: Record<string, number>;
  total_value?: number;
  average_cost_per_wear?: number;
  most_worn_items: WardrobeItem[];
  least_worn_items: WardrobeItem[];
  favorite_items: WardrobeItem[];
  recent_additions: WardrobeItem[];
}

// --- Wardrobe Analysis ---
export interface WardrobeAnalysis {
  id: string;
  analysis_type: WardrobeAnalysisType;
  results: {
    summary: string;
    recommendations: string[];
    gaps_identified: Array<{
      category: string;
      description: string;
      priority: 'HIGH' | 'MEDIUM' | 'LOW';
      suggested_items: string[];
    }>;
    statistics: Record<string, any>;
  };
  confidence_score: number;
  created_at: string;
}

// --- Style Preferences ---
export interface StylePreference {
  id: string;
  preferred_styles: ClothingStyle[];
  preferred_colors: string[];
  preferred_occasions: Occasion[];
  budget_range: {
    min_price?: number;
    max_price?: number;
  };
  size_preferences: {
    top_size?: string;
    bottom_size?: string;
    shoe_size?: string;
    fit_preference?: FitType;
  };
  lifestyle_factors: {
    activity_level: 'LOW' | 'MEDIUM' | 'HIGH';
    work_environment: 'CASUAL' | 'BUSINESS' | 'FORMAL' | 'CREATIVE';
    social_activities: string[];
  };
  body_preferences: {
    areas_to_highlight: string[];
    areas_to_minimize: string[];
  };
  created_at: string;
  updated_at: string;
}

// =============================================================================
// ENUMS FOR WARDROBE
// =============================================================================

export enum ClothingCategory {
  TOPS = "TOPS",
  BOTTOMS = "BOTTOMS",
  DRESSES = "DRESSES",
  OUTERWEAR = "OUTERWEAR",
  SHOES = "SHOES",
  ACCESSORIES = "ACCESSORIES",
  BAGS = "BAGS",
  JEWELRY = "JEWELRY",
  UNDERWEAR = "UNDERWEAR",
  ACTIVEWEAR = "ACTIVEWEAR"
}

export enum ClothingSubcategory {
  // TOPS
  T_SHIRT = "T_SHIRT",
  BLOUSE = "BLOUSE",
  SHIRT = "SHIRT",
  TANK_TOP = "TANK_TOP",
  SWEATER = "SWEATER",
  CARDIGAN = "CARDIGAN",
  HOODIE = "HOODIE",
  
  // BOTTOMS
  JEANS = "JEANS",
  TROUSERS = "TROUSERS",
  SHORTS = "SHORTS",
  SKIRT = "SKIRT",
  LEGGINGS = "LEGGINGS",
  
  // DRESSES
  CASUAL_DRESS = "CASUAL_DRESS",
  FORMAL_DRESS = "FORMAL_DRESS",
  COCKTAIL_DRESS = "COCKTAIL_DRESS",
  MAXI_DRESS = "MAXI_DRESS",
  
  // OUTERWEAR
  JACKET = "JACKET",
  COAT = "COAT",
  BLAZER = "BLAZER",
  VEST = "VEST",
  
  // SHOES
  SNEAKERS = "SNEAKERS",
  HEELS = "HEELS",
  FLATS = "FLATS",
  BOOTS = "BOOTS",
  SANDALS = "SANDALS",
  
  // ACCESSORIES
  HAT = "HAT",
  SCARF = "SCARF",
  BELT = "BELT",
  SUNGLASSES = "SUNGLASSES",
  WATCH = "WATCH",
  
  // BAGS
  HANDBAG = "HANDBAG",
  BACKPACK = "BACKPACK",
  CLUTCH = "CLUTCH",
  TOTE = "TOTE",
  
  // JEWELRY
  NECKLACE = "NECKLACE",
  EARRINGS = "EARRINGS",
  BRACELET = "BRACELET",
  RING = "RING"
}

export enum ClothingStyle {
  CASUAL = "CASUAL",
  FORMAL = "FORMAL",
  BUSINESS = "BUSINESS",
  ELEGANT = "ELEGANT",
  SPORTY = "SPORTY",
  BOHEMIAN = "BOHEMIAN",
  MINIMALIST = "MINIMALIST",
  VINTAGE = "VINTAGE",
  TRENDY = "TRENDY",
  CLASSIC = "CLASSIC",
  EDGY = "EDGY",
  ROMANTIC = "ROMANTIC",
  PREPPY = "PREPPY",
  GRUNGE = "GRUNGE",
  STREETWEAR = "STREETWEAR"
}

export enum Season {
  SPRING = "SPRING",
  SUMMER = "SUMMER",
  FALL = "FALL",
  WINTER = "WINTER",
  ALL_SEASON = "ALL_SEASON"
}

export enum Occasion {
  WORK = "WORK",
  CASUAL = "CASUAL",
  FORMAL = "FORMAL",
  PARTY = "PARTY",
  DATE = "DATE",
  VACATION = "VACATION",
  EXERCISE = "EXERCISE",
  HOME = "HOME",
  TRAVEL = "TRAVEL",
  WEDDING = "WEDDING",
  INTERVIEW = "INTERVIEW",
  BUSINESS_MEETING = "BUSINESS_MEETING"
}

export enum FitType {
  TIGHT = "TIGHT",
  FITTED = "FITTED",
  REGULAR = "REGULAR",
  LOOSE = "LOOSE",
  OVERSIZED = "OVERSIZED"
}

export enum OutfitStatus {
  DRAFT = "DRAFT",
  ACTIVE = "ACTIVE",
  ARCHIVED = "ARCHIVED",
  FAVORITE = "FAVORITE"
}

export enum WardrobeAnalysisType {
  GAPS_ANALYSIS = "GAPS_ANALYSIS",
  STYLE_COHERENCE = "STYLE_COHERENCE",
  COLOR_ANALYSIS = "COLOR_ANALYSIS",
  VERSATILITY_ANALYSIS = "VERSATILITY_ANALYSIS",
  COST_ANALYSIS = "COST_ANALYSIS"
}
