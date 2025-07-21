/**
 * AVA OLO Constitutional Interactions
 * Shared JavaScript for consistent UI behavior
 */

class AVAConstitutionalUI {
  constructor() {
    this.init();
  }

  init() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setupInteractions());
    } else {
      this.setupInteractions();
    }
  }

  setupInteractions() {
    this.setupEnterKeyNavigation();
    this.setupFormValidation();
    this.setupVersionDisplay();
    this.setupAccessibilityFeatures();
  }

  /**
   * Enter key navigation between form fields
   * Constitutional requirement: Enter key works on ALL inputs
   */
  setupEnterKeyNavigation() {
    document.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && e.target.matches('input:not([type="submit"]):not([type="button"])')) {
        e.preventDefault();
        
        const form = e.target.closest('form');
        if (!form) return;
        
        const formElements = Array.from(form.querySelectorAll(
          'input:not([type="hidden"]):not([type="submit"]):not([type="button"]), select, textarea'
        )).filter(el => !el.disabled && !el.readOnly);
        
        const currentIndex = formElements.indexOf(e.target);
        
        if (currentIndex >= 0) {
          if (currentIndex < formElements.length - 1) {
            // Move to next field
            formElements[currentIndex + 1].focus();
          } else {
            // Last field - submit form or trigger submit button
            const submitButton = form.querySelector('[type="submit"]') || 
                               form.querySelector('.ava-button-primary') ||
                               form.querySelector('button:not([type="button"])');
            
            if (submitButton) {
              submitButton.click();
            } else {
              form.submit();
            }
          }
        }
      }
    });

    // Add visual indicators for keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        document.body.classList.add('keyboard-navigation');
      }
    });

    document.addEventListener('mousedown', () => {
      document.body.classList.remove('keyboard-navigation');
    });
  }

  /**
   * Enhanced form validation with constitutional styling
   */
  setupFormValidation() {
    document.addEventListener('submit', (e) => {
      const form = e.target;
      if (!form.matches('form')) return;

      const requiredFields = form.querySelectorAll('[required]');
      let hasErrors = false;

      requiredFields.forEach(field => {
        if (!field.value.trim()) {
          this.showFieldError(field, 'Este campo es obligatorio');
          hasErrors = true;
        } else {
          this.clearFieldError(field);
        }
      });

      // Email validation
      const emailFields = form.querySelectorAll('[type="email"]');
      emailFields.forEach(field => {
        if (field.value && !this.isValidEmail(field.value)) {
          this.showFieldError(field, 'Por favor ingrese un email válido');
          hasErrors = true;
        }
      });

      if (hasErrors) {
        e.preventDefault();
        const firstError = form.querySelector('.ava-field-error');
        if (firstError) {
          firstError.focus();
          firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    });
  }

  showFieldError(field, message) {
    this.clearFieldError(field);
    
    field.classList.add('ava-field-error');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'ava-error-message';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
  }

  clearFieldError(field) {
    field.classList.remove('ava-field-error');
    
    const existingError = field.parentNode.querySelector('.ava-error-message');
    if (existingError) {
      existingError.remove();
    }
  }

  isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  /**
   * Setup version display in top-right corner
   */
  setupVersionDisplay() {
    // Get version from meta tag or global variable
    const version = document.querySelector('meta[name="app-version"]')?.content ||
                   window.AVA_VERSION ||
                   'unknown';

    // Only add if not already present
    if (!document.querySelector('.ava-version-display')) {
      const versionDiv = document.createElement('div');
      versionDiv.className = 'ava-version-display';
      versionDiv.textContent = `v${version}`;
      document.body.appendChild(versionDiv);
    }
  }

  /**
   * Accessibility enhancements
   */
  setupAccessibilityFeatures() {
    // Add skip link for screen readers
    if (!document.querySelector('.ava-skip-link')) {
      const skipLink = document.createElement('a');
      skipLink.href = '#main-content';
      skipLink.className = 'ava-skip-link';
      skipLink.textContent = 'Saltar al contenido principal';
      skipLink.style.cssText = `
        position: absolute;
        top: -40px;
        left: 6px;
        background: var(--ava-brown-primary);
        color: white;
        padding: 8px;
        text-decoration: none;
        border-radius: 4px;
        z-index: 1000;
        transition: top 0.3s;
      `;
      
      skipLink.addEventListener('focus', () => {
        skipLink.style.top = '6px';
      });
      
      skipLink.addEventListener('blur', () => {
        skipLink.style.top = '-40px';
      });
      
      document.body.insertBefore(skipLink, document.body.firstChild);
    }

    // Add main content landmark if not present
    if (!document.querySelector('#main-content')) {
      const mainContent = document.querySelector('main') || 
                         document.querySelector('.container') ||
                         document.querySelector('.content');
      
      if (mainContent) {
        mainContent.id = 'main-content';
      }
    }

    // Enhance focus indicators for keyboard users
    const style = document.createElement('style');
    style.textContent = `
      .keyboard-navigation *:focus {
        outline: 3px solid var(--ava-olive-primary) !important;
        outline-offset: 2px !important;
      }
      
      .ava-field-error {
        border-color: var(--ava-error) !important;
        box-shadow: 0 0 0 3px rgba(139, 0, 0, 0.1) !important;
      }
      
      .ava-error-message {
        color: var(--ava-error);
        font-size: 16px;
        margin-top: 4px;
        display: block;
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Utility method to add constitutional classes to existing elements
   */
  applyConstitutionalStyling() {
    // Convert existing buttons
    document.querySelectorAll('button:not(.ava-button)').forEach(btn => {
      btn.classList.add('ava-button');
      if (btn.type === 'submit' || btn.classList.contains('btn-primary')) {
        btn.classList.add('ava-button-primary');
      } else {
        btn.classList.add('ava-button-secondary');
      }
    });

    // Convert existing form inputs
    document.querySelectorAll('input:not(.ava-form-input), select:not(.ava-form-select), textarea:not(.ava-form-textarea)').forEach(input => {
      if (input.type !== 'hidden' && input.type !== 'submit' && input.type !== 'button') {
        if (input.tagName === 'INPUT') input.classList.add('ava-form-input');
        if (input.tagName === 'SELECT') input.classList.add('ava-form-select');
        if (input.tagName === 'TEXTAREA') input.classList.add('ava-form-textarea');
      }
    });

    // Convert existing cards
    document.querySelectorAll('.card:not(.ava-card)').forEach(card => {
      card.classList.add('ava-card');
      
      const header = card.querySelector('.card-header');
      if (header) header.classList.add('ava-card-header');
      
      const body = card.querySelector('.card-body');
      if (body) body.classList.add('ava-card-body');
      
      const footer = card.querySelector('.card-footer');
      if (footer) footer.classList.add('ava-card-footer');
    });
  }
}

// Auto-initialize when script loads
window.AVAConstitutionalUI = AVAConstitutionalUI;

// Initialize immediately if DOM is ready, otherwise wait
if (typeof window !== 'undefined') {
  window.avaUI = new AVAConstitutionalUI();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AVAConstitutionalUI;
}