/**
 * Apartment Visitor Management System – Client-Side JavaScript
 * =============================================================
 * Handles: form validation, modals, mobile menu, flash toasts,
 *          search debounce, confirm dialogs, auto-timestamps
 * Author: Antigravity AI
 */

// ─────────────────────────────────────────────
// Utility: Run after DOM is ready
// ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initFlashMessages();
  initHamburger();
  initModal();
  initVisitorForm();
  initSearchDebounce();
  initDeleteConfirm();
  initDefaultDateTime();
  animateStats();
});


// ─────────────────────────────────────────────
// 1. Flash Messages (Toast Notifications)
// ─────────────────────────────────────────────
function initFlashMessages() {
  const alerts = document.querySelectorAll('.alert');

  alerts.forEach(alert => {
    // Auto-dismiss after 4 seconds
    setTimeout(() => dismissAlert(alert), 4000);

    // Manual dismiss on click
    const dismissBtn = alert.querySelector('.alert-dismiss');
    if (dismissBtn) {
      dismissBtn.addEventListener('click', () => dismissAlert(alert));
    }
  });
}

/**
 * Animate and remove an alert element
 * @param {HTMLElement} alert
 */
function dismissAlert(alert) {
  alert.style.animation = 'fadeOut 0.35s ease forwards';
  setTimeout(() => alert.remove(), 350);
}

/**
 * Show a dynamic toast notification (can be called from JS)
 * @param {string} message - Text to display
 * @param {string} type    - 'success' | 'danger' | 'warning' | 'info'
 */
function showToast(message, type = 'info') {
  const iconMap = { success: '✅', danger: '❌', warning: '⚠️', info: 'ℹ️' };

  const container = document.querySelector('.flash-container') || createFlashContainer();

  const alert = document.createElement('div');
  alert.className = `alert alert-${type}`;
  alert.innerHTML = `
    <span>${iconMap[type] || 'ℹ️'}</span>
    <span>${message}</span>
    <span class="alert-dismiss">✕</span>
  `;

  alert.querySelector('.alert-dismiss').addEventListener('click', () => dismissAlert(alert));
  container.appendChild(alert);

  setTimeout(() => dismissAlert(alert), 4000);
}

function createFlashContainer() {
  const div = document.createElement('div');
  div.className = 'flash-container';
  document.body.appendChild(div);
  return div;
}


// ─────────────────────────────────────────────
// 2. Hamburger / Mobile Navigation Toggle
// ─────────────────────────────────────────────
function initHamburger() {
  const hamburger = document.getElementById('hamburger');
  const navMenu   = document.getElementById('navMenu');

  if (!hamburger || !navMenu) return;

  hamburger.addEventListener('click', () => {
    navMenu.classList.toggle('open');
    // Animate hamburger bars
    hamburger.classList.toggle('active');
  });

  // Close menu when a nav link is clicked (mobile)
  navMenu.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => navMenu.classList.remove('open'));
  });
}


// ─────────────────────────────────────────────
// 3. Modal (Add Visitor popup)
// ─────────────────────────────────────────────
function initModal() {
  const backdrop  = document.getElementById('visitorModal');
  const openBtn   = document.getElementById('openModalBtn');
  const closeBtn  = document.getElementById('closeModalBtn');
  const cancelBtn = document.getElementById('cancelModalBtn');

  if (!backdrop) return;

  function openModal()  {
    backdrop.classList.add('show');
    document.body.style.overflow = 'hidden';
    // Set current date-time as default
    setDefaultDateTime();
  }

  function closeModal() {
    backdrop.classList.remove('show');
    document.body.style.overflow = '';
    clearFormErrors();
  }

  if (openBtn)   openBtn.addEventListener('click', openModal);
  if (closeBtn)  closeBtn.addEventListener('click', closeModal);
  if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

  // Close when clicking outside the modal box
  backdrop.addEventListener('click', e => {
    if (e.target === backdrop) closeModal();
  });

  // ESC key closes modal
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
  });
}


// ─────────────────────────────────────────────
// 4. Visitor Form Validation
// ─────────────────────────────────────────────
function initVisitorForm() {
  const form = document.getElementById('visitorForm');
  if (!form) return;

  form.addEventListener('submit', e => {
    if (!validateVisitorForm()) {
      e.preventDefault(); // Stop submission if validation fails
    }
  });

  // Live validation on blur (when user leaves a field)
  form.querySelectorAll('.form-control[required]').forEach(field => {
    field.addEventListener('blur', () => validateField(field));
    field.addEventListener('input', () => {
      if (field.classList.contains('error')) validateField(field);
    });
  });
}

/**
 * Validate the entire visitor form
 * @returns {boolean} true if all fields are valid
 */
function validateVisitorForm() {
  const fields = document.querySelectorAll('#visitorForm .form-control[required]');
  let isValid = true;

  fields.forEach(field => {
    if (!validateField(field)) isValid = false;
  });

  // Phone number specific validation
  const phone = document.getElementById('phone');
  if (phone && phone.value.trim()) {
    const phoneRegex = /^[6-9]\d{9}$/; // Indian mobile number format
    if (!phoneRegex.test(phone.value.trim())) {
      showFieldError(phone, 'Enter a valid 10-digit mobile number');
      isValid = false;
    }
  }

  return isValid;
}

/**
 * Validate a single form field
 * @param {HTMLElement} field
 * @returns {boolean}
 */
function validateField(field) {
  const value = field.value.trim();

  if (!value) {
    showFieldError(field, `${getFieldLabel(field)} is required`);
    return false;
  }

  clearFieldError(field);
  return true;
}

function getFieldLabel(field) {
  const label = document.querySelector(`label[for="${field.id}"]`);
  return label ? label.textContent.trim() : 'This field';
}

function showFieldError(field, message) {
  field.classList.add('error');
  let errorMsg = field.parentElement.querySelector('.error-msg');
  if (!errorMsg) {
    errorMsg = document.createElement('span');
    errorMsg.className = 'error-msg';
    field.parentElement.appendChild(errorMsg);
  }
  errorMsg.textContent = message;
  errorMsg.classList.add('show');
}

function clearFieldError(field) {
  field.classList.remove('error');
  const errorMsg = field.parentElement.querySelector('.error-msg');
  if (errorMsg) errorMsg.classList.remove('show');
}

function clearFormErrors() {
  document.querySelectorAll('#visitorForm .form-control.error').forEach(clearFieldError);
  document.getElementById('visitorForm')?.reset();
}


// ─────────────────────────────────────────────
// 5. Search Debounce (avoid too many requests)
// ─────────────────────────────────────────────
function initSearchDebounce() {
  const searchInput = document.getElementById('searchInput');
  if (!searchInput) return;

  let debounceTimer;
  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      // Auto-submit the search form after 400ms of no typing
      searchInput.closest('form')?.submit();
    }, 400);
  });
}


// ─────────────────────────────────────────────
// 6. Delete Confirmation Dialog
// ─────────────────────────────────────────────
function initDeleteConfirm() {
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
      const message = el.getAttribute('data-confirm') || 'Are you sure?';
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });
}


// ─────────────────────────────────────────────
// 7. Auto-fill current date & time in check-in
// ─────────────────────────────────────────────
function initDefaultDateTime() {
  setDefaultDateTime();
}

function setDefaultDateTime() {
  const checkInField = document.getElementById('check_in');
  if (!checkInField) return;

  // Format: YYYY-MM-DDTHH:MM (required for datetime-local input)
  const now = new Date();
  const pad = n => String(n).padStart(2, '0');
  const formatted = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
  checkInField.value = formatted;
}


// ─────────────────────────────────────────────
// 8. Animate Stats Counter (Dashboard)
// ─────────────────────────────────────────────
function animateStats() {
  const statValues = document.querySelectorAll('.stat-value[data-target]');

  statValues.forEach(el => {
    const target = parseInt(el.getAttribute('data-target'), 10);
    let current  = 0;
    const step   = Math.ceil(target / 40) || 1;
    const interval = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current;
      if (current >= target) clearInterval(interval);
    }, 30);
  });
}


// ─────────────────────────────────────────────
// 9. Clock on dashboard (live time display)
// ─────────────────────────────────────────────
const clockEl = document.getElementById('liveClock');
if (clockEl) {
  function updateClock() {
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
  updateClock();
  setInterval(updateClock, 1000);
}
