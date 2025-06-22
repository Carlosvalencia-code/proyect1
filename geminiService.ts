
import { GoogleGenAI, GenerateContentResponse } from "@google/genai";
import { 
    FaceShape, 
    FacialAnalysisDataAPI, 
    ChromaticAnalysisDataAPI,
    ImagePart, 
    TextPart,
    RecomendacionItem,
    ColorRecomendacionItem,
    SkinUndertone,
    ColorSeason
} from '../types';

const API_KEY = process.env.API_KEY;

if (!API_KEY) {
  console.warn("API_KEY for Gemini is not set. AI features will not work. Please set the API_KEY environment variable.");
}

const ai = API_KEY ? new GoogleGenAI({ apiKey: API_KEY }) : null;
const facialAnalysisModel = 'gemini-2.5-flash-preview-04-17';
const colorAnalysisModel = 'gemini-2.5-flash-preview-04-17';


// Helper to parse JSON, removing markdown fences and extracting the main JSON block
const parseJsonFromGeminiResponse = <T>(text: string | undefined): T | null => {
  if (!text) return null;
  
  let processedText = text.trim();

  // 1. Remove Markdown Fences
  const fenceRegex = /^```(\w*)?\s*\n?(.*?)\n?\s*```$/s;
  const fenceMatch = processedText.match(fenceRegex);
  if (fenceMatch && fenceMatch[2]) {
    processedText = fenceMatch[2].trim();
  }

  // 2. Extract content between the first '{' and last '}'
  const firstBrace = processedText.indexOf('{');
  const lastBrace = processedText.lastIndexOf('}');

  if (firstBrace === -1 || lastBrace === -1 || lastBrace < firstBrace) {
    console.error("Could not find valid JSON structure (missing {} braces). Raw text:", text);
    return null;
  }
  
  let jsonStr = processedText.substring(firstBrace, lastBrace + 1);

  try {
    return JSON.parse(jsonStr) as T;
  } catch (e) {
    console.error("Failed to parse JSON response (first attempt):", (e as Error).message, "Attempted JSON string:", jsonStr, "Original raw text:", text);
    // Attempt to fix common issues like trailing commas (simple cases)
    try {
        const fixedStr = jsonStr.replace(/,\s*([}\]])/g, '$1');
        return JSON.parse(fixedStr) as T;
    } catch (finalError) {
        console.error("Failed to parse JSON even after attempting fixes:", (finalError as Error).message, "Original raw text:", text);
        return null;
    }
  }
};


// --- FACIAL ANALYSIS ---
const generateFacialAnalysisPrompt = (): string => {
  // Based on "Desarrollo Final del MVP", pages 1-2
  return `Actúa como un experto en análisis facial y asesoría de imagen. Analiza la imagen proporcionada y determina:
1. Forma del rostro: Identifica la forma principal del rostro (ovalado, redondo, cuadrado, rectangular, corazón, diamante o triángulo invertido).
2. Características destacadas: Identifica 3-5 características faciales destacadas (por ejemplo: pómulos prominentes, mandíbula definida, frente amplia, etc.).
3. Nivel de confianza: Indica tu nivel de confianza en el análisis en una escala del 1 al 100.

Basado en la forma del rostro identificada, proporciona recomendaciones específicas para:
A. Cortes de pelo: 3 estilos que favorezcan esta forma facial, con explicación de por qué son adecuados.
B. Gafas: 2 tipos de monturas que complementen esta forma facial, con explicación.
C. Escotes: 2 tipos de escotes que favorezcan esta forma facial, con explicación.

Responde en formato JSON con la siguiente estructura exacta:
{
  "forma_rostro": "forma identificada",
  "caracteristicas_destacadas": ["característica 1", "característica 2", "..."],
  "confianza_analisis": "número del 1 al 100",
  "recomendaciones": {
    "cortes_pelo": [
      {"nombre": "nombre del corte", "descripcion": "descripción breve", "explicacion": "explicación detallada"}
    ],
    "gafas": [
      {"tipo": "tipo de montura", "explicacion": "explicación detallada"}
    ],
    "escotes": [
      {"tipo": "tipo de escote", "explicacion": "explicación detallada"}
    ]
  }
}
Importante: Proporciona solo el JSON sin texto adicional. Asegúrate de que el JSON sea válido y siga exactamente la estructura solicitada.`;
};

export const getFacialAnalysisFromGemini = async (base64ImageData: string): Promise<FacialAnalysisDataAPI | null> => {
  if (!ai) {
    console.error("Gemini AI client not initialized. API_KEY might be missing.");
    alert("AI Service is unavailable. Please check API_KEY configuration.");
    return null;
  }

  const imagePart: ImagePart = {
    inlineData: { mimeType: 'image/jpeg', data: base64ImageData },
  };
  const textPart: TextPart = { text: generateFacialAnalysisPrompt() };

  try {
    const response: GenerateContentResponse = await ai.models.generateContent({
      model: facialAnalysisModel,
      contents: { parts: [imagePart, textPart] },
      config: { responseMimeType: "application/json" }
    });
    
    const analysisData = parseJsonFromGeminiResponse<FacialAnalysisDataAPI>(response.text);

    if (!analysisData || !analysisData.forma_rostro || !analysisData.recomendaciones) {
        console.error("Invalid or incomplete facial analysis data received from Gemini.", analysisData, "Raw response text:", response.text);
        throw new Error("Incomplete data from AI. Failed to parse facial analysis.");
    }
    // Validate structure further if needed
    if (typeof analysisData.confianza_analisis !== 'number') {
        analysisData.confianza_analisis = parseInt(String(analysisData.confianza_analisis), 10) || 50; // Default if missing/invalid
    }
     // Attempt to map string to Enum, default to unknown if not matched.
    const faceShapeKey = Object.values(FaceShape).find(fs => fs.toLowerCase() === String(analysisData.forma_rostro).toLowerCase());
    analysisData.forma_rostro = faceShapeKey || FaceShape.Unknown;


    return analysisData;

  } catch (error) {
    console.error("Error analyzing face with Gemini:", error);
    if (error instanceof Error && (error.message.includes("API key not valid") || error.message.includes("API_KEY_INVALID")) ) {
        alert("The Gemini API key is not valid. Please check your configuration.");
    } else {
        alert("Could not analyze face. Please ensure the image is clear and try again.");
    }
    return null;
  }
};


// --- COLOR ANALYSIS (based on Quiz) ---
const generateColorAnalysisPrompt = (quizResponses: Record<string, string>): string => {
  // Based on "Desarrollo Final del MVP", pages 3-4
  const responsesText = Object.entries(quizResponses)
    .map(([key, value]) => `${key.replace(/_/g, ' ')}: ${value}`) // Make keys more readable
    .join("\n");

  return `Actúa como un experto en análisis cromático y asesoría de imagen. Analiza las siguientes respuestas de un quiz de análisis cromático:
${responsesText}

Basado en estas respuestas, determina:
1. Estación de color: Identifica la estación de color principal (invierno, primavera, verano u otoño).
2. Subtono: Indica si el subtono es frío, cálido o neutro.
3. Nivel de confianza: Indica tu nivel de confianza en el análisis en una escala del 1 al 100.
4. Descripción: Proporciona una breve descripción general de la estación de color identificada y sus características principales.

Proporciona una paleta de colores personalizada con:
A. Paleta primaria: 5 colores que favorezcan esta estación, con nombre, código hexadecimal y explicación de por qué son adecuados.
B. Colores a evitar: 3 colores que no favorezcan esta estación, con explicación.

Responde en formato JSON con la siguiente estructura exacta:
{
  "estacion": "estación identificada",
  "subtono": "frío/cálido/neutro",
  "confianza_analisis": "número del 1 al 100",
  "descripcion": "descripción general de esta estación de color",
  "paleta_primaria": [
    {"color": "nombre del color", "codigo_hex": "#RRGGBB", "explicacion": "explicación detallada"}
  ],
  "colores_evitar": [
    {"color": "nombre del color", "codigo_hex": "#RRGGBB", "explicacion": "explicación detallada"}
  ]
}
Importante: Proporciona solo el JSON sin texto adicional. Asegúrate de que el JSON sea válido y siga exactamente la estructura solicitada.`;
};

export const getColorAnalysisFromGemini = async (quizResponses: Record<string, string>): Promise<ChromaticAnalysisDataAPI | null> => {
  if (!ai) {
    console.error("Gemini AI client not initialized. API_KEY might be missing.");
    alert("AI Service is unavailable. Please check API_KEY configuration.");
    return null;
  }

  const prompt = generateColorAnalysisPrompt(quizResponses);
  
  try {
    const response: GenerateContentResponse = await ai.models.generateContent({
      model: colorAnalysisModel,
      contents: prompt,
      config: { responseMimeType: "application/json" }
    });

    const chromaticData = parseJsonFromGeminiResponse<ChromaticAnalysisDataAPI>(response.text);

    if (!chromaticData || !chromaticData.estacion || !chromaticData.paleta_primaria) {
        console.error("Invalid or incomplete chromatic analysis data received from Gemini.", chromaticData, "Raw response text:", response.text);
        throw new Error("Incomplete data from AI. Failed to parse color analysis.");
    }
     if (typeof chromaticData.confianza_analisis !== 'number') {
        chromaticData.confianza_analisis = parseInt(String(chromaticData.confianza_analisis), 10) || 50; // Default if missing/invalid
    }
    // Attempt to map string to Enum
    const seasonKey = Object.values(ColorSeason).find(cs => cs.toLowerCase() === String(chromaticData.estacion).toLowerCase());
    chromaticData.estacion = seasonKey || ColorSeason.Unknown;
    const undertoneKey = Object.values(SkinUndertone).find(su => su.toLowerCase() === String(chromaticData.subtono).toLowerCase());
    chromaticData.subtono = undertoneKey || SkinUndertone.Unknown;

    return chromaticData;

  } catch (error) {
    console.error("Error getting color analysis from Gemini:", error);
    if (error instanceof Error && (error.message.includes("API key not valid") || error.message.includes("API_KEY_INVALID"))) {
        alert("The Gemini API key is not valid. Please check your configuration.");
    } else {
        alert("Could not get detailed color palette. Please try again later.");
    }
    return null;
  }
};


// --- UTILITY ---
export const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const result = reader.result as string;
      resolve(result.split(',')[1]); // Return only base64 part
    };
    reader.onerror = error => reject(error);
  });
};
