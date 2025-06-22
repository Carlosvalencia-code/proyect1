
import { ChromaticQuizQuestion, ColorSeason, FaceShape, SkinUndertone, StyleTip, FacialShapesDB, ColorSeasonsDB, LocalChromaticAnalysis } from './types';

export const APP_NAME = "SYNTHIA STYLE";
export const APP_SLOGAN = "Tu Estilo. Más Inteligente.";

export const DEFAULT_USER_AVATAR = "https://picsum.photos/seed/profileavatar/100/100";

// --- QUIZ QUESTIONS ---
// Aligned with keys used in determine_color_season from "Desarrollo Final del MVP"
export const QUIZ_QUESTIONS: ChromaticQuizQuestion[] = [
  {
    id: 'color_venas', // Vein color
    text: 'Observa las venas en la parte interior de tu muñeca. ¿De qué color son predominantemente?',
    options: [
      { text: 'Azules o moradas', value: 'azul' },
      { text: 'Verdes', value: 'verde' },
      { text: 'Una mezcla de azul y verde, o no estás seguro', value: 'mixto_o_desconocido' }, // Neutral/Fallback
    ],
    // image: 'url_to_vein_example_image.jpg' // Example of how an image could be added
  },
  {
    id: 'reaccion_sol', // Sun reaction
    text: '¿Cómo reacciona tu piel normalmente a la exposición solar (sin protección)?',
    options: [
      { text: 'Me quemo fácilmente, rara vez me bronceo', value: 'quemadura' }, // Cool/Winter
      { text: 'Me bronceo con facilidad, casi nunca me quemo', value: 'bronceado' }, // Warm/Autumn
      { text: 'Me quemo primero y luego me bronceo un poco', value: 'quemadura_luego_bronceo' }, // Neutral/Summer/Spring
      { text: 'Mi piel es oscura y se broncea más profundamente', value: 'bronceado_profundo' }, // Can be any, but often warm
    ],
  },
  {
    id: 'joyeria', // Jewelry preference
    text: '¿Qué tipo de joyería sientes que resalta más tu tono de piel?',
    options: [
      { text: 'Plata, oro blanco o platino', value: 'plata' },
      { text: 'Oro amarillo u oro rosado', value: 'oro' },
      { text: 'Ambos me quedan igual de bien', value: 'ambos' },
    ],
  },
  {
    id: 'colores_favorables', // Preferred color groups
    text: '¿Con qué grupo de colores te sientes más atraído/a o recibes más cumplidos?',
    // Values map to groups in determine_color_season
    options: [
      { text: 'Colores fríos e intensos (ej: azul rey, fucsia, negro, blanco puro)', value: 'frios_intensos' }, // Invierno
      { text: 'Colores fríos y suaves (ej: lavanda, rosa palo, azul cielo, gris perla)', value: 'frios_suaves' }, // Verano
      { text: 'Colores cálidos e intensos/tierra (ej: terracota, mostaza, verde oliva oscuro, borgoña)', value: 'calidos_intensos' }, // Otoño
      { text: 'Colores cálidos y brillantes/claros (ej: coral, durazno, verde manzana, turquesa brillante)', value: 'calidos_brillantes' }, // Primavera
    ],
  },
  {
    id: 'base_maquillaje', // Foundation base color (optional, or if user wears makeup)
    text: 'Si usas base de maquillaje, ¿cuál de estos tonos se funde mejor con tu piel?',
    options: [
      { text: 'Tonos rosados o beige rosado', value: 'rosados' },
      { text: 'Tonos dorados, beige amarillento o durazno', value: 'amarillos' },
      { text: 'Tonos neutros, ni muy rosados ni muy amarillos', value: 'neutros' },
      { text: 'No uso base / No estoy seguro/a', value: 'no_sabe' },
    ],
  },
];


// --- LOCAL ALGORITHM FOR COLOR SEASON DETERMINATION ---
// Based on "Desarrollo Final del MVP", pages 4-5
export const determine_color_season = (answers: Record<string, string>): LocalChromaticAnalysis => {
  const scores: Record<ColorSeason, number> = {
    [ColorSeason.Invierno]: 0,
    [ColorSeason.Primavera]: 0,
    [ColorSeason.Verano]: 0,
    [ColorSeason.Otono]: 0,
    [ColorSeason.Unknown]: 0,
  };

  // 1. Color de venas
  if (answers.color_venas === 'azul') {
    scores[ColorSeason.Invierno] += 2;
    scores[ColorSeason.Verano] += 2;
  } else if (answers.color_venas === 'verde') {
    scores[ColorSeason.Primavera] += 2;
    scores[ColorSeason.Otono] += 2;
  }

  // 2. Reacción al sol
  if (answers.reaccion_sol === 'quemadura') { // Primarily cool
    scores[ColorSeason.Invierno] += 1; // Original doc said Invierno +2
    scores[ColorSeason.Verano] += 1;
  } else if (answers.reaccion_sol === 'bronceado') { // Primarily warm
    scores[ColorSeason.Otono] += 1; // Original doc said Otoño +2
    scores[ColorSeason.Primavera] +=1;
  } else if (answers.reaccion_sol === 'quemadura_luego_bronceo') {
     // Can be Spring or Summer
     scores[ColorSeason.Primavera] += 0.5;
     scores[ColorSeason.Verano] += 0.5;
  }


  // 3. Joyería
  if (answers.joyeria === 'plata') {
    scores[ColorSeason.Invierno] += 2;
    scores[ColorSeason.Verano] += 1;
  } else if (answers.joyeria === 'oro') {
    scores[ColorSeason.Primavera] += 2;
    scores[ColorSeason.Otono] += 1;
  }

  // 4. Colores favorables
  if (answers.colores_favorables === 'frios_intensos') {
    scores[ColorSeason.Invierno] += 3;
  } else if (answers.colores_favorables === 'frios_suaves') {
    scores[ColorSeason.Verano] += 3;
  } else if (answers.colores_favorables === 'calidos_intensos') {
    scores[ColorSeason.Otono] += 3;
  } else if (answers.colores_favorables === 'calidos_brillantes') {
    scores[ColorSeason.Primavera] += 3;
  }

  // 5. Base de maquillaje
  if (answers.base_maquillaje === 'rosados') {
    scores[ColorSeason.Invierno] += 1;
    scores[ColorSeason.Verano] += 1;
  } else if (answers.base_maquillaje === 'amarillos') {
    scores[ColorSeason.Primavera] += 1;
    scores[ColorSeason.Otono] += 1;
  }
  
  // Remove Unknown from scoring before finding max
  const validScores = { ...scores };
  delete (validScores as any)[ColorSeason.Unknown];


  let season: ColorSeason = ColorSeason.Unknown;
  // Determine the season with the highest score
  let maxScore = -1;
  for (const s of [ColorSeason.Invierno, ColorSeason.Primavera, ColorSeason.Verano, ColorSeason.Otono]) {
      if (validScores[s] > maxScore) {
          maxScore = validScores[s];
          season = s as ColorSeason;
      }
  }


  // Calculate confidence
  const total_points = Object.values(validScores).reduce((sum, val) => sum + Math.max(0,val), 0); // Ensure positive scores
  let confidence = total_points > 0 ? Math.round((scores[season] / total_points) * 100) : 50;

  // Determine undertone
  let undertone: SkinUndertone = SkinUndertone.Unknown;
  if (season === ColorSeason.Invierno || season === ColorSeason.Verano) {
    undertone = SkinUndertone.Frio;
  } else if (season === ColorSeason.Primavera || season === ColorSeason.Otono) {
    undertone = SkinUndertone.Calido;
  }

  // Reduce confidence if the difference between the top two seasons is small
  const sorted_seasons = Object.entries(validScores)
    .sort(([, a_score], [, b_score]) => b_score - a_score) as [ColorSeason, number][];

  if (sorted_seasons.length > 1 && (sorted_seasons[0][1] - sorted_seasons[1][1] < 2)) {
    confidence = Math.max(50, confidence - 20); // Reduce confidence but not below 50%
  }
  
  // Ensure confidence is within 0-100
  confidence = Math.max(0, Math.min(100, confidence));


  return {
    season,
    undertone,
    confidence,
    scores: scores, // Return raw scores as well
  };
};


// --- MOCK STYLE TIPS (can be expanded or replaced by DB lookups) ---
export const MOCK_STYLE_TIPS: StyleTip[] = [
  {
    id: 'tip1',
    title: 'Embrace Your Autumn Palette',
    description: 'As a \'Deep Autumn,\' your rich, warm undertones harmonize beautifully with earthy hues. Think olive green, rust, and deep browns. These colors will enhance your natural radiance.',
    imageUrl: 'https://picsum.photos/seed/styletip1/200/200',
    category: 'colorSeason',
    appliesTo: ColorSeason.Otono,
  },
  {
    id: 'tip2',
    title: 'Highlight Your Heart-Shaped Face',
    description: 'Your heart-shaped face is characterized by a wider forehead and narrower chin. Opt for styles that add volume at the jawline, such as A-line skirts or flared pants, to balance your proportions.',
    imageUrl: 'https://picsum.photos/seed/styletip2/200/200',
    category: 'faceShape',
    appliesTo: FaceShape.Corazon,
  },
];

// --- DESCRIPTIONS ---
export const getSeasonDescription = (season: ColorSeason | string | null): string => {
  switch (season) {
    case ColorSeason.Primavera:
      return color_seasons_db[ColorSeason.Primavera]?.descripcion || "Tu análisis indica que eres Primavera. Esta paleta presenta tonos claros, cálidos y brillantes que realzan tu vitalidad natural. Adopta estos colores vivos para un look fresco y enérgico.";
    case ColorSeason.Verano:
      return color_seasons_db[ColorSeason.Verano]?.descripcion || "Tu análisis indica que eres Verano. Esta paleta presenta tonos fríos, suaves y apagados que complementan tu elegancia natural. Adopta estos colores suaves para un look sofisticado y armonioso.";
    case ColorSeason.Otono:
      return color_seasons_db[ColorSeason.Otono]?.descripcion || "Tu análisis indica que eres Otoño. Esta paleta presenta tonos apagados y cálidos que realzan tu belleza natural. Adopta estos colores para un look armonioso.";
    case ColorSeason.Invierno:
      return color_seasons_db[ColorSeason.Invierno]?.descripcion || "Tu análisis indica que eres Invierno. Esta paleta presenta tonos fríos, claros y a menudo profundos o brillantes que acentúan tu llamativo contraste. Adopta estos colores audaces para un look dramático y seguro.";
    default:
      return "Tu análisis de estación de color está pendiente o no se pudo determinar. Completa el cuestionario para obtener recomendaciones personalizadas.";
  }
};

export const getFaceShapeDescription = (shape: FaceShape | string | null): string => {
    const shapeKey = (shape as string)?.toLowerCase(); // Convert to lowercase string for key matching
    if (shapeKey && facial_shapes_db[shapeKey]) {
        return facial_shapes_db[shapeKey].descripcion;
    }
    switch(shape) { // Fallback for direct enum match if needed, though db should be primary
        case FaceShape.Ovalado: return "Tu forma de rostro es ovalada, caracterizada por proporciones equilibradas y una barbilla ligeramente más estrecha. Esta forma versátil se adapta a una amplia gama de estilos.";
        case FaceShape.Redondo: return "Tu forma de rostro es redonda, con anchura y longitud similares y líneas suaves y curvas. Los estilos que añaden altura y alargan el rostro suelen ser favorecedores.";
        // Add other default descriptions if db lookup fails
        default: return "Tu análisis de forma de rostro está pendiente.";
    }
};

export const getUndertoneDescription = (undertone: SkinUndertone | string | null): string => {
    switch(undertone) {
        case SkinUndertone.Calido: return "Tu subtono de piel es cálido, con matices dorados, durazno o amarillos. Este subtono complementa los colores tierra y los cálidos vibrantes.";
        case SkinUndertone.Frio: return "Tu subtono de piel es frío, con matices rosados, rojos o azulados. Este subtono armoniza bien con los tonos joya, azules y rojos verdaderos.";
        case SkinUndertone.Neutro: return "Tu subtono de piel es neutro, lo que significa que no es predominantemente cálido ni frío, o un equilibrio de ambos. Probablemente puedas usar una amplia gama de colores.";
        default: return "Tu análisis de subtono de piel está pendiente.";
    }
};


// --- IMAGE PLACEHOLDERS ---
export const SEASON_PALETTE_IMAGES: Record<string, string[]> = {
    [ColorSeason.Primavera]: ["https://picsum.photos/seed/spring1/150/150", "https://picsum.photos/seed/spring2/150/150", "https://picsum.photos/seed/spring3/150/150", "https://picsum.photos/seed/spring4/150/150"],
    [ColorSeason.Verano]: ["https://picsum.photos/seed/summer1/150/150", "https://picsum.photos/seed/summer2/150/150", "https://picsum.photos/seed/summer3/150/150", "https://picsum.photos/seed/summer4/150/150"],
    [ColorSeason.Otono]: ["https://picsum.photos/seed/autumnpalette1/150/150", "https://picsum.photos/seed/autumnpalette2/150/150", "https://picsum.photos/seed/autumnpalette3/150/150", "https://picsum.photos/seed/autumnpalette4/150/150"],
    [ColorSeason.Invierno]: ["https://picsum.photos/seed/winter1/150/150", "https://picsum.photos/seed/winter2/150/150", "https://picsum.photos/seed/winter3/150/150", "https://picsum.photos/seed/winter4/150/150"],
    [ColorSeason.Unknown]: ["https://picsum.photos/seed/unknown1/150/150", "https://picsum.photos/seed/unknown2/150/150", "https://picsum.photos/seed/unknown3/150/150", "https://picsum.photos/seed/unknown4/150/150"]
};
export const FACE_SHAPE_IMAGE_URL = "https://picsum.photos/seed/faceshape/150/150";
export const SKIN_UNDERTONE_IMAGE_URL = "https://picsum.photos/seed/undertone/150/100";

// --- DATABASE OF RECOMMENDATIONS (from "Desarrollo Final del MVP") ---

export const facial_shapes_db: FacialShapesDB = {
  "ovalado": { // FaceShape.Ovalado
    "descripcion": "Considerada la forma facial ideal, con proporciones equilibradas y líneas suaves.",
    "caracteristicas": ["Frente ligeramente más ancha que la mandíbula", "Pómulos prominentes", "Línea de la mandíbula suavemente redondeada"],
    "recomendaciones": {
      "cortes_pelo": [
        {"nombre": "Bob clásico", "descripcion": "Corte recto a la altura de la mandíbula", "explicacion": "Esta forma facial versátil puede lucir prácticamente cualquier estilo, pero un bob clásico realza los pómulos y enmarca perfectamente el rostro."},
        {"nombre": "Largo con capas", "descripcion": "Cabello largo con capas suaves desde los pómulos", "explicacion": "Las capas suaves añaden movimiento y volumen mientras mantienen la armonía natural del rostro ovalado."},
        {"nombre": "Pixie con flequillo", "descripcion": "Corte muy corto con flequillo más largo", "explicacion": "Un pixie destaca los rasgos faciales y acentúa los ojos, ideal para rostros ovalados que pueden arriesgarse con cortes más cortos."}
      ],
      "gafas": [
        {"tipo": "Rectangulares", "explicacion": "Las monturas rectangulares añaden ángulos que contrastan elegantemente con las curvas naturales del rostro ovalado."},
        {"tipo": "Wayfarer", "explicacion": "Este estilo clásico proporciona un buen equilibrio entre líneas rectas y curvas que complementan la forma ovalada."}
      ],
      "escotes": [
        {"tipo": "En V", "explicacion": "Alarga visualmente el cuello y crea una línea vertical que equilibra la forma ovalada del rostro."},
        {"tipo": "Barco", "explicacion": "La línea horizontal amplia equilibra la longitud natural del rostro ovalado, creando armonía visual."}
      ]
    }
  },
  "redondo": { // FaceShape.Redondo
    "descripcion": "Rostro con anchura y longitud similares, mejillas llenas y línea de la mandíbula suave.",
    "caracteristicas": ["Anchura y longitud facial similares", "Mejillas llenas y redondeadas", "Línea de la mandíbula suave sin ángulos pronunciados"],
    "recomendaciones": {
      "cortes_pelo": [
        {"nombre": "Long bob asimétrico", "descripcion": "Bob largo con un lado ligeramente más corto", "explicacion": "La asimetría y las líneas angulares crean la ilusión de un rostro más alargado y estilizado."},
        {"nombre": "Capas largas con volumen en la corona", "descripcion": "Cabello largo con capas que añaden altura", "explicacion": "El volumen en la parte superior alarga visualmente el rostro, mientras que las capas laterales suavizan las mejillas."},
        {"nombre": "Side-swept con flequillo largo", "descripcion": "Flequillo largo peinado hacia un lado", "explicacion": "El flequillo lateral crea una línea diagonal que rompe la redondez del rostro, añadiendo definición y ángulos."}
      ],
      "gafas": [
        {"tipo": "Rectangulares angulares", "explicacion": "Las líneas rectas y los ángulos contrastan con la redondez del rostro, añadiendo definición y estructura."},
        {"tipo": "Cat-eye", "explicacion": "La forma elevada en las esquinas exteriores crea un efecto lifting visual que estiliza el rostro redondo."}
      ],
      "escotes": [
        {"tipo": "En V profundo", "explicacion": "Crea una línea vertical pronunciada que alarga visualmente el rostro y el cuello."},
        {"tipo": "Asimétrico", "explicacion": "Rompe la simetría natural del rostro redondo, añadiendo ángulos y definición visual."}
      ]
    }
  },
 "cuadrado": { // FaceShape.Cuadrado
    "descripcion": "Rostro con mandíbula fuerte y angular, frente ancha y líneas definidas.",
    "caracteristicas": ["Mandíbula fuerte y angular", "Frente ancha y recta", "Línea de la mandíbula y pómulos alineados en anchura"],
    "recomendaciones": {
      "cortes_pelo": [
        {"nombre": "Capas suaves alrededor del rostro", "descripcion": "Cabello con capas que enmarcan suavemente el rostro", "explicacion": "Las capas suaves suavizan los ángulos pronunciados de la mandíbula, creando un efecto más delicado."},
        {"nombre": "Long bob ondulado", "descripcion": "Bob largo con ondas suaves", "explicacion": "Las ondas añaden movimiento y suavidad que contrastan con la estructura angular del rostro cuadrado."},
        {"nombre": "Pixie con textura en la parte superior", "descripcion": "Corte corto con textura y volumen arriba", "explicacion": "La textura superior añade altura mientras que los laterales más cortos suavizan la mandíbula cuadrada."}
      ],
      "gafas": [
        {"tipo": "Ovaladas o redondas", "explicacion": "Las formas curvas contrastan con los ángulos del rostro, suavizando la apariencia general."},
        {"tipo": "Aviador", "explicacion": "La forma ligeramente redondeada en la parte inferior suaviza la mandíbula angular."}
      ],
      "escotes": [
        {"tipo": "Redondo", "explicacion": "Las líneas curvas del escote redondo contrastan con los ángulos del rostro, creando equilibrio visual."},
        {"tipo": "Corazón", "explicacion": "La forma suave y romántica suaviza la estructura angular del rostro cuadrado."}
      ]
    }
  },
  "corazón": { // FaceShape.Corazon - Mapped from "corazon"
    "descripcion": "Frente y pómulos anchos que se estrechan hacia una barbilla puntiaguda.",
    "caracteristicas": ["Frente ancha", "Pómulos altos y definidos", "Barbilla estrecha o puntiaguda"],
    "recomendaciones": {
      "cortes_pelo": [
        {"nombre": "Bob con flequillo", "descripcion": "Bob medio con flequillo recto o cortina", "explicacion": "El flequillo equilibra la frente ancha, mientras que la longitud a la altura de la mandíbula añade anchura visual a la parte inferior del rostro."},
        {"nombre": "Melena midi con raya al centro", "descripcion": "Cabello a la altura de los hombros con raya central", "explicacion": "La raya central crea simetría, mientras que el volumen a los lados de la mandíbula equilibra la parte superior más ancha."},
        {"nombre": "Pixie con flequillo largo", "descripcion": "Corte corto con flequillo más largo", "explicacion": "El flequillo cubre parcialmente la frente ancha, mientras que la nuca y laterales cortos destacan los pómulos de forma favorecedora."}
      ],
      "gafas": [
        {"tipo": "Monturas inferiores", "explicacion": "Las monturas que enfatizan la parte inferior añaden anchura visual donde el rostro se estrecha."},
        {"tipo": "Wayfarer ligeras", "explicacion": "Añaden estructura a la parte inferior del rostro sin sobrecargar la parte superior."}
      ],
      "escotes": [
        {"tipo": "Barco o balconette", "explicacion": "La línea horizontal amplia equilibra la forma triangular del rostro, añadiendo anchura visual a la parte inferior."},
        {"tipo": "Palabra de honor", "explicacion": "Crea una línea horizontal que equilibra visualmente la barbilla estrecha con la frente más ancha."}
      ]
    }
  },
  "diamante": { // FaceShape.Diamante
    "descripcion": "Pómulos prominentes con frente y mandíbula más estrechas.",
    "caracteristicas": ["Pómulos altos y prominentes", "Frente relativamente estrecha", "Barbilla puntiaguda o estrecha"],
    "recomendaciones": {
      "cortes_pelo": [
        {"nombre": "Capas suaves a la altura de la mandíbula", "descripcion": "Cabello con capas que terminan a la altura de la mandíbula", "explicacion": "Las capas suaves añaden anchura a la mandíbula, equilibrando los pómulos prominentes."},
        {"nombre": "Flequillo barrido lateral", "descripcion": "Flequillo largo peinado hacia un lado", "explicacion": "Añade anchura a la frente estrecha y crea un marco suave que equilibra los pómulos angulares."},
        {"nombre": "Bob texturizado con volumen", "descripcion": "Bob con textura y volumen en las puntas", "explicacion": "El volumen en las puntas a la altura de la mandíbula equilibra los pómulos anchos, creando armonía facial."}
      ],
      "gafas": [
        {"tipo": "Browline", "explicacion": "Añaden anchura a la frente mientras equilibran los pómulos prominentes."},
        {"tipo": "Ovaladas con detalles superiores", "explicacion": "La forma suave complementa los ángulos del rostro, mientras que los detalles superiores equilibran los pómulos."}
      ],
      "escotes": [
        {"tipo": "Cuello alto", "explicacion": "Equilibra los pómulos prominentes al añadir estructura en la parte inferior del rostro."},
        {"tipo": "Escote cuadrado", "explicacion": "Las líneas rectas contrastan con los ángulos del rostro, creando un equilibrio visual."}
      ]
    }
  },
 "rectangular": { // FaceShape.Rectangular
    "descripcion": "Similar al cuadrado pero más alargado, con frente, mejillas y mandíbula alineadas.",
    "caracteristicas": ["Rostro más largo que ancho", "Frente, mejillas y mandíbula alineadas en anchura", "Mandíbula angular"],
    "recomendaciones": {
      "cortes_pelo": [
        {"nombre": "Capas voluminosas a los lados", "descripcion": "Cabello con volumen lateral y capas medias", "explicacion": "El volumen a los lados añade anchura, equilibrando la longitud del rostro rectangular."},
        {"nombre": "Bob con flequillo recto", "descripcion": "Bob clásico con flequillo a la altura de las cejas", "explicacion": "El flequillo recto acorta visualmente el rostro, mientras que el bob añade anchura a los lados."},
        {"nombre": "Media melena con ondas", "descripcion": "Cabello a la altura de los hombros con ondas suaves", "explicacion": "Las ondas añaden volumen lateral que equilibra la longitud del rostro, suavizando también los ángulos de la mandíbula."}
      ],
      "gafas": [
        {"tipo": "Redondas u ovaladas", "explicacion": "Las formas curvas suavizan los ángulos del rostro rectangular y rompen la longitud vertical."},
        {"tipo": "Oversized con detalles", "explicacion": "Las monturas grandes añaden anchura y los detalles rompen la uniformidad del rostro rectangular."}
      ],
      "escotes": [
        {"tipo": "Redondo amplio", "explicacion": "Añade anchura visual y suaviza los ángulos del rostro rectangular."},
        {"tipo": "Barco", "explicacion": "La línea horizontal amplia crea la ilusión de mayor anchura, equilibrando la longitud del rostro."}
      ]
    }
  },
  "triangular": { // FaceShape.Triangular / triangulo_invertido
    "descripcion": "Frente ancha que se estrecha hacia una mandíbula y barbilla más estrechas.", // Same as Corazon, but triangular in prompt
    "caracteristicas": ["Frente y sienes anchas", "Pómulos altos", "Mandíbula y barbilla estrechas"],
    "recomendaciones": {
      "cortes_pelo": [
        {"nombre": "Capas que añaden volumen en la mandíbula", "descripcion": "Cabello con capas que terminan a la altura de la mandíbula", "explicacion": "Las capas añaden volumen en la parte inferior del rostro, equilibrando la frente más ancha."},
        {"nombre": "Bob invertido", "descripcion": "Bob más corto en la nuca y más largo hacia el rostro", "explicacion": "Añade volumen y anchura en la zona de la mandíbula, creando equilibrio con la parte superior del rostro."},
        {"nombre": "Media melena con raya lateral y volumen", "descripcion": "Cabello a la altura de los hombros con raya lateral", "explicacion": "La raya lateral suaviza la frente ancha, mientras que el volumen en las puntas equilibra la mandíbula estrecha."}
      ],
      "gafas": [
        {"tipo": "Cat-eye o mariposa", "explicacion": "La forma elevada en las esquinas exteriores equilibra la frente ancha con la mandíbula estrecha."},
        {"tipo": "Monturas inferiores o sin montura en la parte superior", "explicacion": "Reducen el énfasis en la parte superior del rostro, creando un mejor equilibrio visual."}
      ],
      "escotes": [
        {"tipo": "Halter o cuello alto", "explicacion": "Añade estructura y volumen en la parte inferior, equilibrando la forma triangular invertida."},
        {"tipo": "Escote asimétrico", "explicacion": "Rompe la simetría y desvía la atención de la parte superior más ancha del rostro."}
      ]
    }
  }
  // Note: "triangulo_invertido" used in OCR, mapped to "triangular" for enum.
};

export const color_seasons_db: ColorSeasonsDB = {
  "invierno": { // ColorSeason.Invierno
    "subtono": SkinUndertone.Frio,
    "descripcion": "La estación Invierno se caracteriza por colores fríos, intensos y contrastantes. Las personas con esta estación suelen tener un subtono frío en la piel, con alto contraste entre el color de piel, ojos y cabello.",
    "paleta_primaria": [
      {"color": "Azul eléctrico", "codigo_hex": "#0047AB", "explicacion": "Este azul intenso y frío realza el subtono frío de tu piel, creando un aspecto vibrante y energético."},
      {"color": "Blanco puro", "codigo_hex": "#FFFFFF", "explicacion": "El blanco puro ilumina tu rostro y crea un contraste limpio que favorece tu coloración natural de alto contraste."},
      {"color": "Púrpura intenso", "codigo_hex": "#800080", "explicacion": "Este tono profundo y frío complementa perfectamente tu paleta natural, añadiendo sofisticación y elegancia."},
      {"color": "Rojo cereza", "codigo_hex": "#D2042D", "explicacion": "Un rojo con base azul que añade dramatismo y resalta tus rasgos sin competir con tu coloración natural."},
      {"color": "Esmeralda", "codigo_hex": "#50C878", "explicacion": "Este verde joya con matices fríos realza el brillo natural de tu piel y ojos, creando un aspecto radiante."}
    ],
    "colores_evitar": [
      {"color": "Naranja calabaza", "codigo_hex": "#FF7518", "explicacion": "Este tono cálido y terroso compite con tu subtono frío natural, haciendo que tu piel parezca apagada o amarillenta."},
      {"color": "Beige cálido", "codigo_hex": "#F5F5DC", "explicacion": "Los tonos beige con base amarilla crean un contraste desfavorable con tu subtono frío, restando luminosidad a tu rostro."},
      {"color": "Verde oliva", "codigo_hex": "#808000", "explicacion": "Este verde terroso y cálido no armoniza con tu paleta natural fría, creando un aspecto apagado y cansado."}
    ]
  },
  "primavera": { // ColorSeason.Primavera
    "subtono": SkinUndertone.Calido,
    "descripcion": "La estación Primavera se caracteriza por colores cálidos, brillantes y claros. Las personas con esta estación suelen tener un subtono cálido en la piel, con un aspecto fresco y luminoso.",
    "paleta_primaria": [
      {"color": "Coral brillante", "codigo_hex": "#FF7F50", "explicacion": "Este tono cálido y vibrante complementa perfectamente tu subtono dorado, añadiendo un resplandor saludable a tu rostro."},
      {"color": "Turquesa claro", "codigo_hex": "#40E0D0", "explicacion": "Aunque es un tono frío, este turquesa tiene la claridad y brillo que armoniza con tu paleta primaveral, creando un contraste refrescante."},
      {"color": "Amarillo limón", "codigo_hex": "#FFF700", "explicacion": "Este amarillo brillante y claro realza el brillo natural de tu piel y cabello, creando un efecto luminoso."},
      {"color": "Verde manzana", "codigo_hex": "#8DB600", "explicacion": "Un verde fresco y brillante que complementa tu coloración cálida natural, añadiendo vitalidad a tu apariencia."},
      {"color": "Melocotón", "codigo_hex": "#FFDAB9", "explicacion": "Este tono suave y cálido armoniza perfectamente con tu subtono, creando un aspecto cohesivo y favorecedor."}
    ],
    "colores_evitar": [
      {"color": "Negro intenso", "codigo_hex": "#000000", "explicacion": "El negro puro crea un contraste demasiado duro con tu coloración clara y brillante, pudiendo hacer que parezcas pálido o cansado."},
      {"color": "Burdeos oscuro", "codigo_hex": "#800020", "explicacion": "Los tonos oscuros y apagados como este burdeos pueden resultar demasiado pesados para tu paleta brillante natural."},
      {"color": "Gris carbón", "codigo_hex": "#2C3539", "explicacion": "Los grises oscuros y neutros no complementan tu subtono cálido y pueden restar luminosidad a tu rostro."}
    ]
  },
  "verano": { // ColorSeason.Verano
    "subtono": SkinUndertone.Frio,
    "descripcion": "La estación Verano se caracteriza por colores fríos, suaves y delicados. Las personas con esta estación suelen tener un subtono frío en la piel, con un aspecto suave y de bajo contraste.",
    "paleta_primaria": [
      {"color": "Lavanda", "codigo_hex": "#E6E6FA", "explicacion": "Este tono suave y frío complementa perfectamente tu subtono rosado, creando un aspecto armonioso y delicado."},
      {"color": "Azul acero claro", "codigo_hex": "#B0C4DE", "explicacion": "Este azul suavizado con gris armoniza con tu coloración natural de bajo contraste, realzando sutilmente tus rasgos."},
      {"color": "Rosa pálido", "codigo_hex": "#FFC0CB", "explicacion": "Este rosa suave con base azul ilumina tu rostro y complementa el subtono frío de tu piel."},
      {"color": "Verde salvia", "codigo_hex": "#9DC183", "explicacion": "Un verde suave y apagado que armoniza perfectamente con tu paleta natural, añadiendo frescura sin sobrecargar."},
      {"color": "Azul marino suave", "codigo_hex": "#000080", "explicacion": "Una alternativa más suave al negro que proporciona profundidad sin crear un contraste demasiado duro con tu coloración natural."}
    ],
    "colores_evitar": [
      {"color": "Naranja brillante", "codigo_hex": "#FF4500", "explicacion": "Este tono cálido e intenso crea un contraste desfavorable con tu subtono frío, pudiendo hacer que tu piel parezca rojiza."},
      {"color": "Amarillo mostaza", "codigo_hex": "#FFDB58", "explicacion": "Los amarillos terrosos y cálidos compiten con tu subtono frío natural, restando luminosidad a tu rostro."},
      {"color": "Marrón chocolate", "codigo_hex": "#7B3F00", "explicacion": "Los marrones intensos y cálidos pueden resultar demasiado pesados para tu coloración suave natural."}
    ]
  },
  "otoño": { // ColorSeason.Otono
    "subtono": SkinUndertone.Calido,
    "descripcion": "La estación Otoño se caracteriza por colores cálidos, terrosos y ricos. Las personas con esta estación suelen tener un subtono cálido en la piel, con tonos dorados o cobrizos.",
    "paleta_primaria": [
      {"color": "Verde oliva", "codigo_hex": "#808000", "explicacion": "Este verde terroso y cálido complementa perfectamente tu subtono dorado, creando una armonía natural."},
      {"color": "Terracota", "codigo_hex": "#E2725B", "explicacion": "Este tono cálido y terroso realza el brillo natural de tu piel y cabello, añadiendo calidez a tu rostro."},
      {"color": "Mostaza", "codigo_hex": "#FFDB58", "explicacion": "Este amarillo cálido y apagado armoniza con tu coloración natural, añadiendo un toque de luminosidad sin resultar estridente."},
      {"color": "Marrón coñac", "codigo_hex": "#964B00", "explicacion": "Un marrón rico y cálido que complementa tu paleta natural, añadiendo profundidad y sofisticación."},
      {"color": "Verde bosque", "codigo_hex": "#228B22", "explicacion": "Este verde profundo con matices cálidos realza tu coloración natural, creando un aspecto armonioso y equilibrado."}
    ],
    "colores_evitar": [
      {"color": "Fucsia", "codigo_hex": "#FF00FF", "explicacion": "Este tono frío y brillante crea un contraste desfavorable con tu subtono cálido, pudiendo hacer que tu piel parezca amarillenta."},
      {"color": "Azul hielo", "codigo_hex": "#F0F8FF", "explicacion": "Los azules muy claros y fríos no armonizan con tu coloración cálida y pueden restar vitalidad a tu rostro."},
      {"color": "Negro intenso", "codigo_hex": "#000000", "explicacion": "El negro puro puede resultar demasiado contrastante con tu coloración cálida natural, creando un aspecto duro."}
    ]
  }
};
