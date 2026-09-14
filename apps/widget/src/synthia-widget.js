/**
 * Synthia Commerce AI - Embeddable B2B Stylist & Virtual Try-On Widget
 * (c) 2026 Synthia AI - B2B Fashion & Eyewear Visagism & Colorimetry Engine
 */

(function (window, document) {
  'use strict';

  const DEMO_FRAMES = [
    {
      sku: 'OPT-CAREY-01',
      title: "Carey 'Capri'",
      shape: 'Rectangular Polarizada',
      price: 289.0,
      currency: 'S/',
      score: 95,
      badge: 'Match Perfecto ⭐',
      svgUrl: '../src/assets/frames/opt-carey-01.svg',
      advice: 'Líneas rectas que balancean facciones redondeadas y tono ámbar ideal para pieles cálidas.'
    },
    {
      sku: 'OPT-TITAN-02',
      title: "Titanio 'Aero'",
      shape: 'Redonda Minimalista',
      price: 345.0,
      currency: 'S/',
      score: 92,
      badge: 'Muy Favorecedor',
      svgUrl: '../src/assets/frames/opt-titan-02.svg',
      advice: 'Montura ultraligera de hilo de titanio que suaviza mandíbulas angulosas.'
    },
    {
      sku: 'OPT-AVIAT-03',
      title: "Aviador 'Solstice'",
      shape: 'Aviador Dorado',
      price: 310.0,
      currency: 'S/',
      score: 89,
      badge: 'Equilibrado',
      svgUrl: '../src/assets/frames/opt-aviat-03.svg',
      advice: 'Doble puente dorado con caída en lágrima que acentúa pómulos altos.'
    },
    {
      sku: 'OPT-BLACK-04',
      title: "Black 'Onyx'",
      shape: 'Cuadrada Bold',
      price: 260.0,
      currency: 'S/',
      score: 91,
      badge: 'Audaz & Elegante',
      svgUrl: '../src/assets/frames/opt-black-04.svg',
      advice: 'Acetato negro piano con alto contraste que resalta miradas profundas.'
    },
    {
      sku: 'OPT-CAT-05',
      title: "Cat-Eye 'Milano'",
      shape: 'Cat-Eye Borgoña',
      price: 295.0,
      currency: 'S/',
      score: 94,
      badge: 'Estilizado ⭐',
      svgUrl: '../src/assets/frames/opt-cat-05.svg',
      advice: 'Bisel ascendente color borgoña que estiliza el mentón y eleva la mirada.'
    }
  ];

  const DEFAULT_CONFIG = {
    apiUrl: 'http://localhost:8000/api/v1/widget',
    merchantKey: 'demo-eyewear-brand',
    sku: 'OPT-CAREY-01',
    containerSelector: '#synthia-widget-container',
    buttonText: '✨ Probar con Asesor de Estilo Virtual (AI)',
    tryonButtonText: '🪞 Probarme en Vivo (Espejo Virtual)',
    theme: 'light'
  };

  class SynthiaWidget {
    constructor(userConfig = {}) {
      this.config = { ...DEFAULT_CONFIG, ...userConfig };
      this.currentAnalysis = null;
      this.currentMode = 'tryon'; // 'tryon' | 'visagism'
      this.activeQuizTab = 'quiz'; // 'quiz' | 'photo'

      // Try-On Engine State
      this.tryonState = {
        activeSku: this.config.sku || 'OPT-CAREY-01',
        scale: 1.0,
        offsetX: 0,
        offsetY: 0,
        isDragging: false,
        dragStartX: 0,
        dragStartY: 0,
        cameraActive: false,
        stream: null,
        photoImg: null
      };

      this.frameImages = {};
      this._animFrameId = null;

      this.init();
    }

    init() {
      this.ensureCssLoaded();
      this.preloadFrames();
      this.mountTriggerButtons();
      this.createModal();
      this.bindEvents();
    }

    preloadFrames() {
      DEMO_FRAMES.forEach((frame) => {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.src = frame.svgUrl;
        this.frameImages[frame.sku] = img;
      });
    }

    getActiveFrame() {
      return (
        DEMO_FRAMES.find((f) => f.sku === this.tryonState.activeSku) ||
        DEMO_FRAMES[0]
      );
    }

    ensureCssLoaded() {
      if (!document.getElementById('synthia-widget-css')) {
        const link = document.createElement('link');
        link.id = 'synthia-widget-css';
        link.rel = 'stylesheet';
        link.href = this.config.cssUrl || '../src/synthia-widget.css';
        document.head.appendChild(link);
      }
    }

    mountTriggerButtons() {
      const container = document.querySelector(this.config.containerSelector);
      if (!container) return;

      container.innerHTML = '';

      // Primary Try-On Live Mirror Button
      const tryonBtn = document.createElement('button');
      tryonBtn.type = 'button';
      tryonBtn.className = 'synthia-tryon-trigger-btn';
      tryonBtn.setAttribute('aria-label', 'Abrir probador virtual en vivo');
      tryonBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>
          <path d="M2 12h20"/>
        </svg>
        <span>${this.config.tryonButtonText}</span>
      `;
      tryonBtn.addEventListener('click', () => this.openModal('tryon'));

      // Secondary Visagism & Stylist Advice Button
      const stylistBtn = document.createElement('button');
      stylistBtn.type = 'button';
      stylistBtn.className = 'synthia-trigger-btn';
      stylistBtn.setAttribute('aria-label', 'Abrir asesor de visagismo y color con IA');
      stylistBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3z"/>
        </svg>
        <span>${this.config.buttonText}</span>
      `;
      stylistBtn.addEventListener('click', () => this.openModal('visagism'));

      container.appendChild(tryonBtn);
      container.appendChild(stylistBtn);
    }

    createModal() {
      if (document.getElementById('synthia-modal-overlay')) return;

      const overlay = document.createElement('div');
      overlay.id = 'synthia-modal-overlay';
      overlay.className = 'synthia-modal-overlay';
      overlay.innerHTML = `
        <div class="synthia-modal-card" role="dialog" aria-modal="true" aria-labelledby="synthia-title">
          <div class="synthia-modal-header">
            <div class="synthia-modal-title" id="synthia-title">
              <span>✨</span>
              <span>Synthia AI • Probador Virtual & Visagismo</span>
            </div>
            <button class="synthia-close-btn" id="synthia-close-btn" aria-label="Cerrar">&times;</button>
          </div>

          <!-- Mode Navigation Tabs: Try-On vs Visagismo -->
          <div class="synthia-mode-nav">
            <button type="button" class="synthia-mode-btn active" id="synthia-nav-tryon">
              🪞 Espejo Virtual (VTO)
            </button>
            <button type="button" class="synthia-mode-btn" id="synthia-nav-visagism">
              ⚡ Asesor de Visagismo
            </button>
          </div>

          <!-- ============================================================
               VIEW 1: VIRTUAL TRY-ON (VTO) LIVE MIRROR
               ============================================================ -->
          <div id="synthia-view-tryon" class="synthia-tryon-view">
            <!-- Active Model Status Header -->
            <div class="synthia-tryon-header-status">
              <div class="synthia-tryon-model-name">
                <span>🕶️</span>
                <span id="synthia-tryon-active-name">Carey 'Capri'</span>
              </div>
              <div class="synthia-tryon-match-badge" id="synthia-tryon-active-badge">
                Match 95% ⭐
              </div>
            </div>

            <!-- Canvas Display Area -->
            <div class="synthia-tryon-canvas-wrap" id="synthia-tryon-canvas-wrap">
              <canvas id="synthia-tryon-canvas" width="600" height="450"></canvas>
              <div class="synthia-tryon-hint" id="synthia-tryon-hint">
                <span>✋</span> Arrastra la montura para calibrar sobre tu rostro
              </div>

              <!-- Hidden WebRTC Video Element -->
              <video id="synthia-tryon-video" autoplay playsinline muted style="display: none;"></video>

              <!-- Empty State / Camera Activation Prompt -->
              <div class="synthia-tryon-empty-state" id="synthia-tryon-empty">
                <svg class="synthia-empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                  <circle cx="12" cy="13" r="4"/>
                </svg>
                <div class="synthia-empty-title">Espejo Virtual en Vivo</div>
                <div class="synthia-empty-desc">
                  Mírate con las gafas puestas en tiempo real a través de tu cámara o sube una fotografía de tu rostro.
                </div>
                <div class="synthia-empty-actions">
                  <button type="button" class="synthia-btn-activate-cam" id="synthia-start-cam-btn">
                    📷 Activar Cámara en Vivo
                  </button>
                  <button type="button" class="synthia-btn-upload-photo" id="synthia-tryon-upload-btn">
                    📁 Subir Selfie
                  </button>
                </div>
                <button type="button" class="synthia-btn-demo-face" id="synthia-use-demo-face-btn">
                  O probar con rostro demo frontal
                </button>
                <input type="file" id="synthia-tryon-file-input" accept="image/*" style="display: none;" />
              </div>
            </div>

            <!-- Calibration Sliders Toolbar -->
            <div class="synthia-calibration-bar">
              <div class="synthia-slider-item">
                <label for="synthia-zoom-slider">Zoom:</label>
                <input type="range" id="synthia-zoom-slider" min="60" max="150" value="100" />
              </div>
              <div class="synthia-slider-item">
                <label for="synthia-posy-slider">Altura:</label>
                <input type="range" id="synthia-posy-slider" min="-120" max="120" value="0" />
              </div>
              <button type="button" class="synthia-btn-reset-pos" id="synthia-reset-pos-btn" title="Restablecer posición inicial">
                ↺ Centrar
              </button>
            </div>

            <!-- Horizontal Frame Carousel -->
            <div>
              <div class="synthia-carousel-section-title">
                <span>Prueba otros modelos del catálogo:</span>
                <span id="synthia-tryon-price" style="font-weight: 800; color: var(--synthia-primary);">S/ 289.00</span>
              </div>
              <div class="synthia-frame-carousel" id="synthia-frame-carousel">
                <!-- Injected dynamically -->
              </div>
            </div>

            <!-- Try-On Actions Footer -->
            <div class="synthia-tryon-actions">
              <button type="button" class="synthia-btn-snapshot" id="synthia-btn-snapshot">
                📸 Guardar Look
              </button>
              <button type="button" class="synthia-btn-add-cart" id="synthia-btn-add-cart">
                🛍️ Añadir a la Cesta
              </button>
            </div>
          </div>

          <!-- ============================================================
               VIEW 2: VISAGISM & COLORIMETRY ASSESSMENT
               ============================================================ -->
          <div id="synthia-view-visagism" style="display: none;">
            <div id="synthia-form-view">
              <p style="font-size: 13px; color: var(--synthia-muted); margin-bottom: 14px;">
                Descubre qué silueta de montura equilibra tus proporciones óseas según la geometría facial y la teoría del color.
              </p>

              <div class="synthia-tabs">
                <button type="button" class="synthia-tab-btn active" id="synthia-tab-quiz">⚡ Test Rápido</button>
                <button type="button" class="synthia-tab-btn" id="synthia-tab-photo">📸 Subir Foto / Selfie</button>
              </div>

              <!-- TAB 1: QUICK QUIZ -->
              <div id="synthia-content-quiz">
                <div style="margin-bottom: 12px;">
                  <label style="display: block; font-size: 12px; font-weight: 600; margin-bottom: 6px; color: var(--synthia-text);">
                    1. ¿Cuál es la forma predominante de tu rostro?
                  </label>
                  <select id="synthia-input-face" style="width: 100%; padding: 8px 10px; border-radius: 8px; border: 1px solid var(--synthia-border); font-size: 13px;">
                    <option value="ROUND">Rostro Redondo (Mejillas suaves, proporciones circulares)</option>
                    <option value="SQUARE">Rostro Cuadrado (Mandíbula angular y marcada)</option>
                    <option value="OVAL" selected>Rostro Ovalado (Proporciones balanceadas, mentón curvo)</option>
                    <option value="HEART">Rostro Corazón (Frente amplia, mentón en punta)</option>
                    <option value="DIAMOND">Rostro Diamante (Pómulos altos y marcados)</option>
                  </select>
                </div>

                <div style="margin-bottom: 12px;">
                  <label style="display: block; font-size: 12px; font-weight: 600; margin-bottom: 6px; color: var(--synthia-text);">
                    2. ¿Qué subtono de piel tienes al exponerte al sol?
                  </label>
                  <select id="synthia-input-tone" style="width: 100%; padding: 8px 10px; border-radius: 8px; border: 1px solid var(--synthia-border); font-size: 13px;">
                    <option value="warm" selected>Cálido (Me bronceo con facilidad, dorados me favorecen)</option>
                    <option value="cool">Frío (Tiendo a enrojecerme, plateados me favorecen)</option>
                    <option value="neutral">Neutro (Equilibrio armónico entre dorados y plateados)</option>
                  </select>
                </div>

                <div style="margin-bottom: 16px;">
                  <label style="display: block; font-size: 12px; font-weight: 600; margin-bottom: 6px; color: var(--synthia-text);">
                    3. ¿Cuál es tu objetivo de estilo?
                  </label>
                  <select id="synthia-input-style" style="width: 100%; padding: 8px 10px; border-radius: 8px; border: 1px solid var(--synthia-border); font-size: 13px;">
                    <option value="equilibrar">Equilibrar y suavizar facciones</option>
                    <option value="destacar">Resaltar la mirada con carácter audaz</option>
                    <option value="elegante">Estilo sobrio, minimalista y profesional</option>
                  </select>
                </div>
              </div>

              <!-- TAB 2: PHOTO UPLOAD -->
              <div id="synthia-content-photo" style="display: none;">
                <div style="border: 2px dashed var(--synthia-border); border-radius: 12px; padding: 24px; text-align: center; cursor: pointer; background: var(--synthia-card); margin-bottom: 16px;" id="synthia-dropzone">
                  <input type="file" id="synthia-file-input" accept="image/*" style="display: none;" />
                  <div id="synthia-photo-preview" style="display: none; margin-bottom: 10px;">
                    <img id="synthia-preview-img" src="" alt="Vista previa" style="max-height: 120px; border-radius: 8px; margin: 0 auto; display: block;" />
                  </div>
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--synthia-muted)" stroke-width="2" style="margin: 0 auto 8px; display: block;">
                    <rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>
                    <circle cx="9" cy="9" r="2"/>
                    <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>
                  </svg>
                  <p style="font-size: 13px; font-weight: 600; color: var(--synthia-text); margin: 0;">Haz clic para subir un selfie o foto frontal</p>
                  <p style="font-size: 11px; color: var(--synthia-muted); margin: 4px 0 0;">Luz natural frontal para máxima precisión de colorimetría</p>
                </div>
              </div>

              <button type="button" id="synthia-analyze-btn" style="width: 100%; padding: 12px; font-size: 14px; font-weight: 700; color: #fff; background: var(--synthia-primary); border: none; border-radius: var(--synthia-radius); cursor: pointer; transition: background 0.2s;">
                Calcular Armonía Estilística
              </button>
            </div>

            <!-- LOADING STATE -->
            <div id="synthia-loading-view" style="display: none; text-align: center; padding: 40px 10px;">
              <div class="synthia-spinner" style="width: 44px; height: 44px; border: 4px solid var(--synthia-border); border-top-color: var(--synthia-accent); border-radius: 50%; margin: 0 auto 16px; animation: synthia-spin 0.8s linear infinite;"></div>
              <h4 style="font-size: 16px; font-weight: 700; color: var(--synthia-primary); margin: 0 0 6px;">Analizando fisonomía y colorimetría con IA...</h4>
              <p style="font-size: 13px; color: var(--synthia-muted); margin: 0;">Mapeando proporciones biométricas y afinidad de catálogo</p>
            </div>

            <!-- RESULTS VIEW -->
            <div id="synthia-result-view" style="display: none;">
              <div class="synthia-score-banner">
                <div class="synthia-score-number" id="synthia-score-display">--%</div>
                <div class="synthia-score-label" id="synthia-score-verdict">Compatibilidad Óptima</div>
              </div>

              <div class="synthia-advice-box" id="synthia-advice-display"></div>

              <div style="margin-bottom: 14px;">
                <h5 style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: var(--synthia-muted); margin: 0 0 8px;">
                  Paleta de colores sugerida para tu subtono:
                </h5>
                <div id="synthia-swatches-container" style="display: flex; gap: 8px; align-items: center;"></div>
              </div>

              <div style="margin-top: 18px;">
                <h5 style="font-size: 13px; font-weight: 700; color: var(--synthia-primary); margin: 0 0 10px; display: flex; justify-content: space-between;">
                  <span>Piezas recomendadas del catálogo</span>
                  <span style="font-size: 11px; font-weight: 400; color: var(--synthia-muted);">En stock</span>
                </h5>
                <div class="synthia-catalog-grid" id="synthia-catalog-container"></div>
              </div>

              <button type="button" id="synthia-reset-btn" style="width: 100%; margin-top: 18px; padding: 10px; font-size: 12px; font-weight: 600; color: var(--synthia-muted); background: transparent; border: 1px solid var(--synthia-border); border-radius: var(--synthia-radius); cursor: pointer;">
                ↻ Probar con otros parámetros
              </button>
            </div>
          </div>
        </div>
      `;

      document.body.appendChild(overlay);

      // Render carousel items
      this.renderFrameCarousel();

      // Add keyframes for spinner if missing
      if (!document.getElementById('synthia-spin-keyframes')) {
        const style = document.createElement('style');
        style.id = 'synthia-spin-keyframes';
        style.innerHTML = `@keyframes synthia-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`;
        document.head.appendChild(style);
      }
    }

    renderFrameCarousel() {
      const container = document.getElementById('synthia-frame-carousel');
      if (!container) return;

      container.innerHTML = '';
      DEMO_FRAMES.forEach((frame) => {
        const item = document.createElement('div');
        item.className = `synthia-frame-item ${frame.sku === this.tryonState.activeSku ? 'active' : ''}`;
        item.dataset.sku = frame.sku;
        item.innerHTML = `
          <img src="${frame.svgUrl}" alt="${frame.title}" class="synthia-frame-thumb" />
          <span class="synthia-frame-label">${frame.title}</span>
          <span class="synthia-frame-score">${frame.score}%</span>
        `;
        item.addEventListener('click', () => this.selectFrame(frame.sku));
        container.appendChild(item);
      });
    }

    selectFrame(sku) {
      const frame = DEMO_FRAMES.find((f) => f.sku === sku);
      if (!frame) return;

      this.tryonState.activeSku = sku;

      // Update active title & badge in Try-On view
      const activeName = document.getElementById('synthia-tryon-active-name');
      const activeBadge = document.getElementById('synthia-tryon-active-badge');
      const priceTag = document.getElementById('synthia-tryon-price');

      if (activeName) activeName.textContent = frame.title;
      if (activeBadge) activeBadge.textContent = `${frame.badge} (${frame.score}%)`;
      if (priceTag) priceTag.textContent = `${frame.currency} ${Number(frame.price).toFixed(2)}`;

      // Update active item in carousel
      document.querySelectorAll('.synthia-frame-item').forEach((el) => {
        el.classList.toggle('active', el.dataset.sku === sku);
      });

      // Redraw canvas
      this.renderTryOn();
    }

    bindEvents() {
      const overlay = document.getElementById('synthia-modal-overlay');
      const closeBtn = document.getElementById('synthia-close-btn');

      // Top Mode Switchers
      const navTryon = document.getElementById('synthia-nav-tryon');
      const navVisagism = document.getElementById('synthia-nav-visagism');

      closeBtn.addEventListener('click', () => this.closeModal());
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) this.closeModal();
      });

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') this.closeModal();
      });

      navTryon.addEventListener('click', () => this.switchMode('tryon'));
      navVisagism.addEventListener('click', () => this.switchMode('visagism'));

      // Try-On Controls
      const startCamBtn = document.getElementById('synthia-start-cam-btn');
      const tryonUploadBtn = document.getElementById('synthia-tryon-upload-btn');
      const tryonFileInput = document.getElementById('synthia-tryon-file-input');
      const demoFaceBtn = document.getElementById('synthia-use-demo-face-btn');

      startCamBtn.addEventListener('click', () => this.startWebcam());
      tryonUploadBtn.addEventListener('click', () => tryonFileInput.click());
      tryonFileInput.addEventListener('change', (e) => this.handleTryOnPhotoUpload(e));
      demoFaceBtn.addEventListener('click', () => this.loadDemoFace());

      // Calibration Sliders
      const zoomSlider = document.getElementById('synthia-zoom-slider');
      const posYSlider = document.getElementById('synthia-posy-slider');
      const resetPosBtn = document.getElementById('synthia-reset-pos-btn');

      zoomSlider.addEventListener('input', (e) => {
        this.tryonState.scale = parseFloat(e.target.value) / 100;
        this.renderTryOn();
      });

      posYSlider.addEventListener('input', (e) => {
        this.tryonState.offsetY = parseFloat(e.target.value);
        this.renderTryOn();
      });

      resetPosBtn.addEventListener('click', () => {
        this.tryonState.scale = 1.0;
        this.tryonState.offsetX = 0;
        this.tryonState.offsetY = 0;
        zoomSlider.value = 100;
        posYSlider.value = 0;
        this.renderTryOn();
      });

      // Canvas Drag Calibration
      const canvas = document.getElementById('synthia-tryon-canvas');
      this.bindCanvasInteractions(canvas);

      // Snapshot & Cart Actions
      const snapshotBtn = document.getElementById('synthia-btn-snapshot');
      const addCartBtn = document.getElementById('synthia-btn-add-cart');

      snapshotBtn.addEventListener('click', () => this.exportSnapshot());
      addCartBtn.addEventListener('click', () => {
        const frame = this.getActiveFrame();
        alert(`¡Excelente elección! Se añadió al carrito: ${frame.title} (${frame.currency} ${frame.price.toFixed(2)})`);
      });

      // Visagism Tab Navigation & Events
      const tabQuiz = document.getElementById('synthia-tab-quiz');
      const tabPhoto = document.getElementById('synthia-tab-photo');
      const contentQuiz = document.getElementById('synthia-content-quiz');
      const contentPhoto = document.getElementById('synthia-content-photo');
      const analyzeBtn = document.getElementById('synthia-analyze-btn');
      const resetBtn = document.getElementById('synthia-reset-btn');
      const dropzone = document.getElementById('synthia-dropzone');
      const fileInput = document.getElementById('synthia-file-input');

      tabQuiz.addEventListener('click', () => {
        tabQuiz.classList.add('active');
        tabPhoto.classList.remove('active');
        contentQuiz.style.display = 'block';
        contentPhoto.style.display = 'none';
        this.activeQuizTab = 'quiz';
      });

      tabPhoto.addEventListener('click', () => {
        tabPhoto.classList.add('active');
        tabQuiz.classList.remove('active');
        contentPhoto.style.display = 'block';
        contentQuiz.style.display = 'none';
        this.activeQuizTab = 'photo';
      });

      dropzone.addEventListener('click', () => fileInput.click());
      fileInput.addEventListener('change', (e) => this.handleQuizFileSelect(e));
      analyzeBtn.addEventListener('click', () => this.performAnalysis());
      resetBtn.addEventListener('click', () => this.resetQuizForm());
    }

    bindCanvasInteractions(canvas) {
      if (!canvas) return;

      const getPos = (e) => {
        const rect = canvas.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        return {
          x: (clientX - rect.left) * scaleX,
          y: (clientY - rect.top) * scaleY
        };
      };

      const startDrag = (e) => {
        const pos = getPos(e);
        this.tryonState.isDragging = true;
        this.tryonState.dragStartX = pos.x - this.tryonState.offsetX;
        this.tryonState.dragStartY = pos.y - this.tryonState.offsetY;
      };

      const moveDrag = (e) => {
        if (!this.tryonState.isDragging) return;
        if (e.cancelable) e.preventDefault();
        const pos = getPos(e);
        this.tryonState.offsetX = pos.x - this.tryonState.dragStartX;
        this.tryonState.offsetY = pos.y - this.tryonState.dragStartY;

        // Keep position slider synchronized
        const posYSlider = document.getElementById('synthia-posy-slider');
        if (posYSlider) {
          posYSlider.value = Math.max(-120, Math.min(120, Math.round(this.tryonState.offsetY)));
        }

        this.renderTryOn();
      };

      const endDrag = () => {
        this.tryonState.isDragging = false;
      };

      canvas.addEventListener('mousedown', startDrag);
      window.addEventListener('mousemove', moveDrag);
      window.addEventListener('mouseup', endDrag);

      canvas.addEventListener('touchstart', startDrag, { passive: false });
      window.addEventListener('touchmove', moveDrag, { passive: false });
      window.addEventListener('touchend', endDrag);
    }

    switchMode(mode) {
      this.currentMode = mode;
      const navTryon = document.getElementById('synthia-nav-tryon');
      const navVisagism = document.getElementById('synthia-nav-visagism');
      const viewTryon = document.getElementById('synthia-view-tryon');
      const viewVisagism = document.getElementById('synthia-view-visagism');

      if (mode === 'tryon') {
        navTryon.classList.add('active');
        navVisagism.classList.remove('active');
        viewTryon.style.display = 'flex';
        viewVisagism.style.display = 'none';
        this.renderTryOn();
      } else {
        navVisagism.classList.add('active');
        navTryon.classList.remove('active');
        viewVisagism.style.display = 'block';
        viewTryon.style.display = 'none';
      }
    }

    openModal(initialMode = 'tryon', targetSku = null) {
      const overlay = document.getElementById('synthia-modal-overlay');
      if (overlay) {
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
      }

      if (targetSku) {
        this.selectFrame(targetSku);
      }

      this.switchMode(initialMode);
    }

    closeModal() {
      const overlay = document.getElementById('synthia-modal-overlay');
      if (overlay) {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
      }
      this.stopWebcam();
    }

    // =========================================================================
    // WEBRTC & CANVAS TRY-ON ENGINE
    // =========================================================================

    async startWebcam() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'user',
            width: { ideal: 640 },
            height: { ideal: 480 }
          }
        });

        this.tryonState.stream = stream;
        const video = document.getElementById('synthia-tryon-video');
        video.srcObject = stream;
        await video.play();

        this.tryonState.cameraActive = true;
        this.tryonState.photoImg = null;

        document.getElementById('synthia-tryon-empty').style.display = 'none';
        this.startRenderLoop();
      } catch (err) {
        console.warn('[Synthia VTO] Webcam access denied or not available:', err);
        alert('No se pudo acceder a la cámara. Puedes subir una fotografía o usar la imagen de demostración.');
      }
    }

    stopWebcam() {
      if (this.tryonState.stream) {
        this.tryonState.stream.getTracks().forEach((track) => track.stop());
        this.tryonState.stream = null;
      }
      this.tryonState.cameraActive = false;
      if (this._animFrameId) {
        cancelAnimationFrame(this._animFrameId);
        this._animFrameId = null;
      }
    }

    handleTryOnPhotoUpload(e) {
      const file = e.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        const img = new Image();
        img.onload = () => {
          this.stopWebcam();
          this.tryonState.photoImg = img;
          document.getElementById('synthia-tryon-empty').style.display = 'none';
          this.renderTryOn();
        };
        img.src = event.target.result;
      };
      reader.readAsDataURL(file);
    }

    loadDemoFace() {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        this.stopWebcam();
        this.tryonState.photoImg = img;
        document.getElementById('synthia-tryon-empty').style.display = 'none';
        this.renderTryOn();
      };
      img.src = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=700&q=80';
    }

    startRenderLoop() {
      if (this._animFrameId) cancelAnimationFrame(this._animFrameId);
      const loop = () => {
        this.renderTryOn();
        if (this.tryonState.cameraActive) {
          this._animFrameId = requestAnimationFrame(loop);
        }
      };
      this._animFrameId = requestAnimationFrame(loop);
    }

    renderTryOn() {
      const canvas = document.getElementById('synthia-tryon-canvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const width = canvas.width;
      const height = canvas.height;

      ctx.clearRect(0, 0, width, height);

      // 1. Draw Background (Webcam Stream or Photo or Solid Placeholder)
      if (this.tryonState.cameraActive && this.tryonState.stream) {
        const video = document.getElementById('synthia-tryon-video');
        if (video && video.videoWidth > 0) {
          ctx.save();
          // Horizontal mirror flip for natural webcam mirror perception
          ctx.translate(width, 0);
          ctx.scale(-1, 1);
          ctx.drawImage(video, 0, 0, width, height);
          ctx.restore();
        }
      } else if (this.tryonState.photoImg) {
        const img = this.tryonState.photoImg;
        const hRatio = width / img.width;
        const vRatio = height / img.height;
        const ratio = Math.max(hRatio, vRatio);
        const shiftX = (width - img.width * ratio) / 2;
        const shiftY = (height - img.height * ratio) / 2;
        ctx.drawImage(img, 0, 0, img.width, img.height, shiftX, shiftY, img.width * ratio, img.height * ratio);
      } else {
        // Dark placeholder background
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(0, 0, width, height);
      }

      // 2. Draw Active SVG Glasses Overlay
      const activeFrame = this.getActiveFrame();
      let frameImg = this.frameImages[activeFrame.sku];

      if (!frameImg || !frameImg.complete) {
        frameImg = new Image();
        frameImg.crossOrigin = 'anonymous';
        frameImg.src = activeFrame.svgUrl;
        this.frameImages[activeFrame.sku] = frameImg;
      }

      if (frameImg && frameImg.complete && frameImg.naturalWidth > 0) {
        // Compute responsive frame dimensions and center
        const baseWidth = width * 0.54; // Natural proportion on human face
        const frameW = baseWidth * (this.tryonState.scale || 1.0);
        const frameH = frameW * (160 / 500); // 500x160 native viewBox aspect ratio

        const centerX = width / 2 + (this.tryonState.offsetX || 0);
        const centerY = height * 0.42 + (this.tryonState.offsetY || 0);

        const x = centerX - frameW / 2;
        const y = centerY - frameH / 2;

        ctx.drawImage(frameImg, x, y, frameW, frameH);
      }
    }

    exportSnapshot() {
      const canvas = document.getElementById('synthia-tryon-canvas');
      if (!canvas) return;

      const activeFrame = this.getActiveFrame();
      const link = document.createElement('a');
      link.download = `synthia-tryon-${activeFrame.sku.toLowerCase()}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    }

    // =========================================================================
    // VISAGISM & STYLIST ENGINE
    // =========================================================================

    handleQuizFileSelect(e) {
      const file = e.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        const preview = document.getElementById('synthia-photo-preview');
        const img = document.getElementById('synthia-preview-img');
        img.src = event.target.result;
        preview.style.display = 'block';
        this.photoBase64 = event.target.result;
      };
      reader.readAsDataURL(file);
    }

    async performAnalysis() {
      const formView = document.getElementById('synthia-form-view');
      const loadingView = document.getElementById('synthia-loading-view');
      const resultView = document.getElementById('synthia-result-view');

      formView.style.display = 'none';
      loadingView.style.display = 'block';
      resultView.style.display = 'none';

      const faceShape = document.getElementById('synthia-input-face').value;
      const undertone = document.getElementById('synthia-input-tone').value;
      const styleGoal = document.getElementById('synthia-input-style').value;

      const payload = {
        sku: this.config.sku,
        category: 'eyewear',
        quiz_data: {
          face_shape: faceShape,
          undertone: undertone,
          style_goal: styleGoal,
          season: undertone === 'warm' ? 'AUTUMN' : 'WINTER'
        },
        image_base64: this.activeQuizTab === 'photo' ? this.photoBase64 : null
      };

      try {
        const response = await fetch(`${this.config.apiUrl}/recommend`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Merchant-Key': this.config.merchantKey
          },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();
        this.renderResults(data);
      } catch (err) {
        console.warn('[Synthia Widget] Fallback local scoring due to network:', err.message);
        const fallbackData = this.generateFallbackData(faceShape, undertone);
        this.renderResults(fallbackData);
      } finally {
        loadingView.style.display = 'none';
        resultView.style.display = 'block';
      }
    }

    generateFallbackData(faceShape, undertone) {
      const isMatch = (faceShape === 'ROUND' && this.config.sku.includes('CAREY')) || undertone === 'warm';
      const score = isMatch ? 95 : 88;
      return {
        current_product_score: score,
        fit_verdict: score >= 90 ? 'PERFECT_MATCH' : 'GOOD_MATCH',
        stylist_advice: `Al contar con facciones ${faceShape.toLowerCase()}s y subtono ${undertone}, las monturas con geometría angular y contrastes cálidos aportan estructura y estilizan tu rostro armónicamente.`,
        colorimetry: {
          best_colors:
            undertone === 'warm'
              ? ['#C19A6B', '#D4AF37', '#808000', '#795548']
              : ['#000000', '#C0C0C0', '#1C39BB', '#4A0E4E']
        },
        recommended_catalog: [
          {
            sku: 'OPT-CAREY-01',
            title: "Carey 'Capri' Polarizadas",
            price: 289.0,
            currency: 'S/',
            image_url: 'https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500&q=80',
            harmony_score: 95,
            match_tag: 'Match Perfecto ⭐'
          },
          {
            sku: 'OPT-AVIAT-03',
            title: "Aviador 'Solstice'",
            price: 310.0,
            currency: 'S/',
            image_url: 'https://images.unsplash.com/photo-1508296695146-257a814070b4?w=500&q=80',
            harmony_score: 89,
            match_tag: 'Muy Favorecedor'
          }
        ]
      };
    }

    renderResults(data) {
      const scoreDisplay = document.getElementById('synthia-score-display');
      const verdictDisplay = document.getElementById('synthia-score-verdict');
      const adviceDisplay = document.getElementById('synthia-advice-display');
      const swatchesContainer = document.getElementById('synthia-swatches-container');
      const catalogContainer = document.getElementById('synthia-catalog-container');

      const score = data.current_product_score || 92;
      scoreDisplay.textContent = `${score}%`;
      verdictDisplay.textContent = score >= 90 ? 'Match Perfecto con este Modelo ⭐' : 'Armonía Muy Favorable';
      adviceDisplay.textContent = data.stylist_advice;

      // Color Swatches
      swatchesContainer.innerHTML = '';
      if (data.colorimetry && data.colorimetry.best_colors) {
        data.colorimetry.best_colors.forEach((hex) => {
          const swatch = document.createElement('span');
          swatch.style.display = 'inline-block';
          swatch.style.width = '24px';
          swatch.style.height = '24px';
          swatch.style.borderRadius = '50%';
          swatch.style.backgroundColor = hex;
          swatch.style.border = '2px solid #fff';
          swatch.style.boxShadow = '0 2px 4px rgba(0,0,0,0.15)';
          swatch.title = hex;
          swatchesContainer.appendChild(swatch);
        });
      }

      // Recommendations Catalog Grid
      catalogContainer.innerHTML = '';
      if (data.recommended_catalog && data.recommended_catalog.length) {
        data.recommended_catalog.forEach((item) => {
          const card = document.createElement('div');
          card.className = 'synthia-product-card';
          card.innerHTML = `
            <img src="${item.image_url}" alt="${item.title}" class="synthia-product-img" />
            <div class="synthia-product-badge">${item.match_tag || 'Recomendado'} (${item.harmony_score}%)</div>
            <div class="synthia-product-title" title="${item.title}">${item.title}</div>
            <div class="synthia-product-price">${item.currency || 'S/'} ${Number(item.price).toFixed(2)}</div>
            <button type="button" class="synthia-tryon-card-btn" data-sku="${item.sku}">
              🪞 Probarme este modelo
            </button>
          `;

          // Direct switch to Try-On with this SKU
          const tryonBtn = card.querySelector('.synthia-tryon-card-btn');
          tryonBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectFrame(item.sku);
            this.switchMode('tryon');
          });

          catalogContainer.appendChild(card);
        });
      }
    }

    resetQuizForm() {
      const formView = document.getElementById('synthia-form-view');
      const loadingView = document.getElementById('synthia-loading-view');
      const resultView = document.getElementById('synthia-result-view');

      resultView.style.display = 'none';
      loadingView.style.display = 'none';
      formView.style.display = 'block';
    }
  }

  // Global exposure
  window.SynthiaWidget = SynthiaWidget;

  // Auto-init via data attributes on current script
  document.addEventListener('DOMContentLoaded', () => {
    const currentScript = document.currentScript || document.querySelector('script[data-synthia-auto-init]');
    if (currentScript && currentScript.dataset.synthiaAutoInit !== 'false') {
      const config = {
        merchantKey: currentScript.dataset.merchantKey || DEFAULT_CONFIG.merchantKey,
        apiUrl: currentScript.dataset.apiUrl || DEFAULT_CONFIG.apiUrl,
        sku: currentScript.dataset.sku || DEFAULT_CONFIG.sku,
        containerSelector: currentScript.dataset.container || DEFAULT_CONFIG.containerSelector
      };
      window._synthiaInstance = new SynthiaWidget(config);
    }
  });

})(window, document);
