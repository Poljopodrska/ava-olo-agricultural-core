/**
 * AVA OLO Accessibility Enhancement
 * Constitutional requirement: Enter key must work on ALL inputs
 */

(function() {
  'use strict';

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAccessibility);
  } else {
    initializeAccessibility();
  }

  function initializeAccessibility() {
    // Universal Enter key handler for form inputs
    setupEnterKeyNavigation();
    
    // Ensure minimum font sizes
    enforceMinimumFontSizes();
    
    // Add skip navigation links
    addSkipNavigation();
    
    // Enhance focus visibility
    enhanceFocusVisibility();
    
    // Add ARIA labels where needed
    enhanceARIALabels();
    
    // Setup version display
    setupVersionDisplay();
  }

  /**
   * Universal Enter key handler
   * Moves to next input or submits form
   */
  function setupEnterKeyNavigation() {
    document.addEventListener('keypress', function(event) {
      // Check if Enter key was pressed
      if (event.key !== 'Enter') return;
      
      const target = event.target;
      
      // Only handle input elements (not textareas)
      if (target.tagName !== 'INPUT') return;
      
      // Don't interfere with submit buttons
      if (target.type === 'submit' || target.type === 'button') return;
      
      event.preventDefault();
      
      // Find the form this input belongs to
      const form = target.closest('form');
      if (!form) return;
      
      // Get all focusable form elements
      const focusableElements = Array.from(
        form.querySelectorAll(
          'input:not([disabled]):not([readonly]), ' +
          'select:not([disabled]):not([readonly]), ' +
          'textarea:not([disabled]):not([readonly]), ' +
          'button:not([disabled])'
        )
      ).filter(el => el.offsetParent !== null); // Only visible elements
      
      // Find current element index
      const currentIndex = focusableElements.indexOf(target);
      
      // Move to next element or submit
      if (currentIndex < focusableElements.length - 1) {
        // Focus next element
        focusableElements[currentIndex + 1].focus();
      } else {
        // Last element - try to submit form
        const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitButton && !submitButton.disabled) {
          submitButton.click();
        } else {
          // Fallback: try form.submit() if no submit button
          if (form.requestSubmit) {
            form.requestSubmit();
          } else {
            form.submit();
          }
        }
      }
    });
  }

  /**
   * Enforce minimum font sizes across all elements
   */
  function enforceMinimumFontSizes() {
    const minFontSize = 18; // Constitutional minimum
    
    // Check on load and after any dynamic content changes
    function checkFontSizes() {
      const allElements = document.querySelectorAll('*');
      
      allElements.forEach(element => {
        const computedStyle = window.getComputedStyle(element);
        const fontSize = parseFloat(computedStyle.fontSize);
        
        if (fontSize < minFontSize && element.textContent.trim()) {
          element.style.fontSize = minFontSize + 'px';
        }
      });
    }
    
    // Initial check
    checkFontSizes();
    
    // Watch for dynamic content
    if (window.MutationObserver) {
      const observer = new MutationObserver(checkFontSizes);
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    }
  }

  /**
   * Add skip navigation link for screen readers
   */
  function addSkipNavigation() {
    if (document.querySelector('.skip-nav')) return;
    
    const skipNav = document.createElement('a');
    skipNav.href = '#main-content';
    skipNav.className = 'skip-nav';
    skipNav.textContent = 'Skip to main content';
    skipNav.style.cssText = `
      position: absolute;
      left: -9999px;
      top: 0;
      z-index: 999;
      padding: 1rem;
      background-color: var(--ava-olive, #6B7D46);
      color: white;
      text-decoration: none;
      font-size: 18px;
    `;
    
    // Show on focus
    skipNav.addEventListener('focus', function() {
      this.style.left = '0';
    });
    
    skipNav.addEventListener('blur', function() {
      this.style.left = '-9999px';
    });
    
    document.body.insertBefore(skipNav, document.body.firstChild);
    
    // Ensure main content has ID
    const main = document.querySelector('main') || document.querySelector('[role="main"]');
    if (main && !main.id) {
      main.id = 'main-content';
    }
  }

  /**
   * Enhance focus visibility for keyboard navigation
   */
  function enhanceFocusVisibility() {
    // Add focus-visible polyfill behavior
    let hadKeyboardEvent = true;
    const keyboardEvents = ['keydown', 'keyup'];
    const pointerEvents = ['mousedown', 'mouseup', 'touchstart', 'touchend'];
    
    // Track keyboard vs pointer
    keyboardEvents.forEach(event => {
      document.addEventListener(event, () => {
        hadKeyboardEvent = true;
      });
    });
    
    pointerEvents.forEach(event => {
      document.addEventListener(event, () => {
        hadKeyboardEvent = false;
      });
    });
    
    // Apply focus styles based on input method
    document.addEventListener('focus', function(event) {
      if (hadKeyboardEvent && event.target.matches('a, button, input, select, textarea')) {
        event.target.classList.add('focus-visible');
      }
    }, true);
    
    document.addEventListener('blur', function(event) {
      event.target.classList.remove('focus-visible');
    }, true);
  }

  /**
   * Enhance ARIA labels for better screen reader support
   */
  function enhanceARIALabels() {
    // Add ARIA labels to icon-only buttons
    document.querySelectorAll('button').forEach(button => {
      if (!button.textContent.trim() && !button.getAttribute('aria-label')) {
        // Try to determine purpose from class or title
        const className = button.className;
        if (className.includes('close')) {
          button.setAttribute('aria-label', 'Close');
        } else if (className.includes('menu')) {
          button.setAttribute('aria-label', 'Menu');
        } else if (className.includes('search')) {
          button.setAttribute('aria-label', 'Search');
        }
      }
    });
    
    // Ensure form inputs have associated labels
    document.querySelectorAll('input, select, textarea').forEach(input => {
      if (!input.id) {
        input.id = 'input-' + Math.random().toString(36).substr(2, 9);
      }
      
      // Check if label exists
      const label = document.querySelector(`label[for="${input.id}"]`);
      if (!label && input.placeholder) {
        // Use placeholder as aria-label if no label
        input.setAttribute('aria-label', input.placeholder);
      }
    });
  }

  /**
   * Setup version display (if not already present)
   */
  function setupVersionDisplay() {
    // Check if version display already exists
    if (document.querySelector('.version-display')) return;
    
    // Get version from meta tag, data attribute, or default
    const versionMeta = document.querySelector('meta[name="version"]');
    const version = versionMeta ? versionMeta.content : 
                   document.body.dataset.version || 
                   'v1.0.0';
    
    // Create version display element
    const versionDisplay = document.createElement('div');
    versionDisplay.className = 'version-display';
    versionDisplay.textContent = version;
    
    // Add to header if exists, otherwise to body
    const header = document.querySelector('.ava-header, header');
    if (header) {
      header.appendChild(versionDisplay);
    } else {
      document.body.appendChild(versionDisplay);
    }
  }

  // Expose functions for external use
  window.AVAAccessibility = {
    enforceMinimumFontSizes,
    setupEnterKeyNavigation,
    addSkipNavigation,
    enhanceFocusVisibility,
    enhanceARIALabels,
    setupVersionDisplay
  };
})();