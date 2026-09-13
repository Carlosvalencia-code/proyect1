/**
 * Synthia Commerce AI - Embeddable B2B Stylist Widget
 * (c) 2026 Synthia AI - B2B Fashion & Eyewear Visagism & Colorimetry Engine
 */

(function (window, document) {
  'use strict';

  const DEFAULT_CONFIG = {
    apiUrl: 'http://localhost:8000/api/v1/widget',
    merchantKey: 'demo-eyewear-brand',
    sku: 'OPT-CAREY-01',
    containerSelector: '#synthia-widget-container',
    buttonText: '✨ Probar con Asesor de Estilo Virtual (AI)',
    theme: 'light'
  };

  class SynthiaWidget {
    constructor(userConfig = {}) {
      this.config = { ...DEFAULT_CONFIG, ...userConfig };
      this.currentAnalysis = null;
      this.activeTab = 'quiz';
      this.init();
    }

    init() {
      this.ensureCssLoaded();
      this.mountTriggerButton();
      this.createModal();
      this.bindEvents();
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

    mountTriggerButton() {
      const container = document.querySelector(this.config.containerSelector);
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'synthia-trigger-btn';
      btn.setAttribute('aria-label', 'Abrir asesor de estilo y visagismo con IA');
      btn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3z"/>
        </svg>
        <span>${this.config.buttonText}</span>
      `;
      btn.addEventListener('click', () => this.openModal());

      if (container) {
        container.innerHTML = '';
        container.appendChild(btn);
      } else {
        // Fallback: floating pill button
        btn.style.position = 'fixed';
        btn.style.bottom = '24px';
        btn.style.right = '24px';
        btn.style.zIndex = '99999';
        btn.style.width = 'auto';
        btn.style.boxShadow = '0 10px 25px rgba(217, 119, 6, 0.3)';
        document.body.appendChild(btn);
      }
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
              <span>Synthia AI • Asesor de Visagismo & Color</span>
            </div>
            <button class="synthia-close-btn" id="synthia-close-btn" aria-label="Cerrar">&times;</button>
          </div>

          <div id="synthia-form-view">
            <p style="font-size: 13px; color: var(--synthia-muted); margin-bottom: 14px;">
              Descubre si este modelo armoniza con la geometría de tu rostro y tu tono de piel según la ciencia del visagismo.
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
                  <option value="ROUND">Rostro Redondo (Mejillas suaves, ancho similar al largo)</option>
                  <option value="SQUARE">Rostro Cuadrado (Mandíbula marcada y angulosa)</option>
                  <option value="OVAL" selected>Rostro Ovalado (Proporciones balanceadas, mentón curvo)</option>
                  <option value="HEART">Rostro Corazón (Frente amplia, mentón afinado)</option>
                  <option value="DIAMOND">Rostro Diamante (Pómulos altos y definidos)</option>
                </select>
              </div>

              <div style="margin-bottom: 12px;">
                <label style="display: block; font-size: 12px; font-weight: 600; margin-bottom: 6px; color: var(--synthia-text);">
                  2. ¿Qué subtono de piel tienes al exponerte al sol?
                </label>
                <select id="synthia-input-tone" style="width: 100%; padding: 8px 10px; border-radius: 8px; border: 1px solid var(--synthia-border); font-size: 13px;">
                  <option value="warm" selected>Cálido (Me bronceo con facilidad, venas verdosas, dorados me favorecen)</option>
                  <option value="cool">Frío (Tiendo a enrojecerme, venas azuladas, plateados me favorecen)</option>
                  <option value="neutral">Neutro (Equilibrio entre tonos dorados y rosados)</option>
                </select>
              </div>

              <div style="margin-bottom: 16px;">
                <label style="display: block; font-size: 12px; font-weight: 600; margin-bottom: 6px; color: var(--synthia-text);">
                  3. ¿Cuál es tu objetivo de estilo?
                </label>
                <select id="synthia-input-style" style="width: 100%; padding: 8px 10px; border-radius: 8px; border: 1px solid var(--synthia-border); font-size: 13px;">
                  <option value="equilibrar">Equilibrar y suavizar facciones</option>
                  <option value="destacar">Resaltar la mirada con alto contraste</option>
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
                <p style="font-size: 11px; color: var(--synthia-muted); margin: 4px 0 0;">Luz natural y rostro despejado para máxima precisión</p>
              </div>
            </div>

            <button type="button" id="synthia-analyze-btn" style="width: 100%; padding: 12px; font-size: 14px; font-weight: 700; color: #fff; background: var(--synthia-primary); border: none; border-radius: var(--synthia-radius); cursor: pointer; transition: background 0.2s;">
              Calcular Armonía Estilística
            </button>
          </div>

          <!-- LOADING STATE -->
          <div id="synthia-loading-view" style="display: none; text-align: center; padding: 40px 10px;">
            <div class="synthia-spinner" style="width: 44px; height: 44px; border: 4px solid var(--synthia-border); border-top-color: var(--synthia-accent); border-radius: 50%; margin: 0 auto 16px; animation: synthia-spin 0.8s linear infinite;"></div>
            <h4 style="font-size: 16px; font-weight: 700; color: var(--synthia-primary); margin: 0 0 6px;">Procesando fisonomía con IA...</h4>
            <p style="font-size: 13px; color: var(--synthia-muted); margin: 0;">Mapeando proporciones biométricas y afinidad de catálogo</p>
          </div>

          <!-- RESULTS VIEW -->
          <div id="synthia-result-view" style="display: none;">
            <div class="synthia-score-banner">
              <div class="synthia-score-number" id="synthia-score-display">--%</div>
              <div class="synthia-score-label" id="synthia-score-verdict">Compatibilidad Óptima</div>
            </div>

            <div class="synthia-advice-box" id="synthia-advice-display">
              <!-- Consejo de estilista inyectado dinámicamente -->
            </div>

            <div style="margin-bottom: 14px;">
              <h5 style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: var(--synthia-muted); margin: 0 0 8px;">
                Colores más favorecedores para tu subtono:
              </h5>
              <div id="synthia-swatches-container" style="display: flex; gap: 8px; align-items: center;"></div>
            </div>

            <div style="margin-top: 18px;">
              <h5 style="font-size: 13px; font-weight: 700; color: var(--synthia-primary); margin: 0 0 10px; display: flex; justify-content: space-between;">
                <span>Piezas del catálogo recomendadas para ti</span>
                <span style="font-size: 11px; font-weight: 400; color: var(--synthia-muted);">En stock</span>
              </h5>
              <div class="synthia-catalog-grid" id="synthia-catalog-container">
                <!-- Tarjetas de catálogo -->
              </div>
            </div>

            <button type="button" id="synthia-reset-btn" style="width: 100%; margin-top: 18px; padding: 10px; font-size: 12px; font-weight: 600; color: var(--synthia-muted); background: transparent; border: 1px solid var(--synthia-border); border-radius: var(--synthia-radius); cursor: pointer;">
              ↻ Probar con otros parámetros
            </button>
          </div>
        </div>
      `;

      document.body.appendChild(overlay);

      // Add keyframes for spinner if missing
      if (!document.getElementById('synthia-spin-keyframes')) {
        const style = document.createElement('style');
        style.id = 'synthia-spin-keyframes';
        style.innerHTML = `@keyframes synthia-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`;
        document.head.appendChild(style);
      }
    }

    bindEvents() {
      const overlay = document.getElementById('synthia-modal-overlay');
      const closeBtn = document.getElementById('synthia-close-btn');
      const tabQuiz = document.getElementById('synthia-tab-quiz');
      const tabPhoto = document.getElementById('synthia-tab-photo');
      const contentQuiz = document.getElementById('synthia-content-quiz');
      const contentPhoto = document.getElementById('synthia-content-photo');
      const analyzeBtn = document.getElementById('synthia-analyze-btn');
      const resetBtn = document.getElementById('synthia-reset-btn');
      const dropzone = document.getElementById('synthia-dropzone');
      const fileInput = document.getElementById('synthia-file-input');

      closeBtn.addEventListener('click', () => this.closeModal());
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) this.closeModal();
      });

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') this.closeModal();
      });

      // Tabs
      tabQuiz.addEventListener('click', () => {
        tabQuiz.classList.add('active');
        tabPhoto.classList.remove('active');
        contentQuiz.style.display = 'block';
        contentPhoto.style.display = 'none';
        this.activeTab = 'quiz';
      });

      tabPhoto.addEventListener('click', () => {
        tabPhoto.classList.add('active');
        tabQuiz.classList.remove('active');
        contentPhoto.style.display = 'block';
        contentQuiz.style.display = 'none';
        this.activeTab = 'photo';
      });

      // Photo upload trigger
      dropzone.addEventListener('click', () => fileInput.click());
      fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

      // Analyze Button
      analyzeBtn.addEventListener('click', () => this.performAnalysis());

      // Reset Button
      resetBtn.addEventListener('click', () => this.resetForm());
    }

    openModal() {
      const overlay = document.getElementById('synthia-modal-overlay');
      if (overlay) {
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
      }
    }

    closeModal() {
      const overlay = document.getElementById('synthia-modal-overlay');
      if (overlay) {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
      }
    }

    handleFileSelect(e) {
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
        image_base64: this.activeTab === 'photo' ? this.photoBase64 : null
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
        // Resilient Fallback Demo Data so shopper always gets value
        const fallbackData = this.generateFallbackData(faceShape, undertone);
        this.renderResults(fallbackData);
      } finally {
        loadingView.style.display = 'none';
        resultView.style.display = 'block';
      }
    }

    generateFallbackData(faceShape, undertone) {
      const isMatch = (faceShape === 'ROUND' && this.config.sku.includes('CAREY')) || undertone === 'warm';
      const score = isMatch ? 94 : 86;
      return {
        current_product_score: score,
        fit_verdict: score >= 90 ? 'PERFECT_MATCH' : 'GOOD_MATCH',
        stylist_advice: `Al contar con proporciones ${faceShape.toLowerCase()}s y subtono ${undertone}, las monturas con contrastes marcados y líneas definidas aportan estructura y realzan tu mirada naturalmente.`,
        colorimetry: {
          best_colors: undertone === 'warm' ? ['#C19A6B', '#D4AF37', '#808000', '#795548'] : ['#000000', '#C0C0C0', '#1C39BB', '#4A0E4E']
        },
        recommended_catalog: [
          {
            sku: 'OPT-CAREY-01',
            title: "Gafas de Sol Carey 'Capri'",
            price: 289.0,
            currency: 'PEN',
            image_url: 'https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500&q=80',
            harmony_score: 95,
            match_tag: 'Match Perfecto ⭐'
          },
          {
            sku: 'OPT-AVIAT-03',
            title: "Aviador Dorado 'Solstice'",
            price: 310.0,
            currency: 'PEN',
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

      const score = data.current_product_score || 90;
      scoreDisplay.textContent = `${score}%`;
      verdictDisplay.textContent = score >= 90 ? 'Match Perfecto con este Modelo ⭐' : 'Armonía Muy Favorable';

      adviceDisplay.textContent = data.stylist_advice;

      // Render swatches
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

      // Render catalog grid
      catalogContainer.innerHTML = '';
      if (data.recommended_catalog && data.recommended_catalog.length) {
        data.recommended_catalog.forEach((item) => {
          const card = document.createElement('div');
          card.className = 'synthia-product-card';
          card.innerHTML = `
            <img src="${item.image_url}" alt="${item.title}" class="synthia-product-img" />
            <div class="synthia-product-badge">${item.match_tag || 'Recomendado'} (${item.harmony_score}%)</div>
            <div class="synthia-product-title" title="${item.title}">${item.title}</div>
            <div class="synthia-product-price">${item.currency} ${Number(item.price).toFixed(2)}</div>
          `;
          card.addEventListener('click', () => {
            alert(`Navegando a producto: ${item.title} (SKU: ${item.sku})`);
          });
          catalogContainer.appendChild(card);
        });
      }
    }

    resetForm() {
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
