/* ============================================================
   main.js — IT Inventory
   Theme toggle · Sidebar · HTMX · Toasts · Keyboard shortcuts
   Density toggle · Back-to-top · Import drag-and-drop
   Bootstrap validation (HTMX-compatible)

   Author: Литвин Олег Олегович <qucooper@yandex.ru>
   ============================================================ */

(function () {
  'use strict';

  const html = document.documentElement;

  // ══════════════════════════════════════════════════════════════════════════
  // THEME TOGGLE
  // Uses Bootstrap 5.3 data-bs-theme on <html>.
  // State persisted in localStorage key "invTheme".
  // Note: the initial theme is already applied by the inline <script> in
  //       <head> to prevent flash-of-unstyled-content (FOUC).
  // ══════════════════════════════════════════════════════════════════════════
  const themeToggle = document.getElementById('themeToggle');
  const themeIcon   = document.getElementById('themeIcon');

  function getCurrentTheme() {
    return html.getAttribute('data-bs-theme') || 'light';
  }

  function applyTheme(theme, animate) {
    html.setAttribute('data-bs-theme', theme);
    localStorage.setItem('invTheme', theme);

    if (themeIcon) {
      if (animate) {
        themeIcon.style.transform = 'rotate(360deg)';
        setTimeout(() => { themeIcon.style.transform = ''; }, 400);
      }
      themeIcon.className = theme === 'dark' ? 'bi bi-moon-stars-fill' : 'bi bi-sun-fill';
    }
  }

  // Sync icon on load (theme already set by FOUC script)
  applyTheme(getCurrentTheme(), false);

  themeToggle?.addEventListener('click', () => {
    applyTheme(getCurrentTheme() === 'dark' ? 'light' : 'dark', true);
  });

  // ══════════════════════════════════════════════════════════════════════════
  // SIDEBAR TOGGLE
  //
  // Desktop (≥768px): sidebar narrows (collapsed class, icon-only mode).
  //   State persisted in localStorage so it survives page navigation.
  //
  // Mobile (<768px): sidebar slides in from the left as a full-height drawer.
  //   Uses "mobile-open" class + a backdrop overlay.
  //   Auto-closes when the user taps any nav link.
  //   Auto-collapses when resized to mobile width.
  // ══════════════════════════════════════════════════════════════════════════
  const sidebar    = document.getElementById('sidebar');
  const sidebarBtn = document.getElementById('sidebarToggle');

  const isMobile = () => window.innerWidth < 768;

  /* ── Desktop collapse ──────────────────────────────────────────────────── */
  function setCollapsed(collapsed) {
    if (!sidebar || isMobile()) return;
    sidebar.classList.toggle('collapsed', collapsed);
    localStorage.setItem('invSidebarCollapsed', String(collapsed));
  }

  /* ── Mobile drawer ─────────────────────────────────────────────────────── */
  function getMobileBackdrop() {
    return document.getElementById('sidebarBackdrop');
  }

  function openMobileDrawer() {
    if (!sidebar) return;
    sidebar.classList.add('mobile-open');
    if (!getMobileBackdrop()) {
      const bd = document.createElement('div');
      bd.id = 'sidebarBackdrop';
      bd.className = 'sidebar-backdrop';
      bd.addEventListener('click', closeMobileDrawer);
      document.body.appendChild(bd);
    }
    document.body.style.overflow = 'hidden';   // prevent page scroll behind drawer
  }

  function closeMobileDrawer() {
    if (!sidebar) return;
    sidebar.classList.remove('mobile-open');
    getMobileBackdrop()?.remove();
    document.body.style.overflow = '';
  }

  /* ── Hamburger click ───────────────────────────────────────────────────── */
  sidebarBtn?.addEventListener('click', () => {
    if (isMobile()) {
      sidebar.classList.contains('mobile-open') ? closeMobileDrawer() : openMobileDrawer();
    } else {
      setCollapsed(!sidebar.classList.contains('collapsed'));
    }
  });

  /* ── Auto-close drawer when a nav link is tapped on mobile ────────────── */
  sidebar?.querySelectorAll('.sidebar-link').forEach(link => {
    link.addEventListener('click', () => {
      if (isMobile()) closeMobileDrawer();
    });
  });

  /* ── Restore / initialise sidebar state on load ────────────────────────── */
  if (!isMobile()) {
    const saved = localStorage.getItem('invSidebarCollapsed');
    // Tablets (768–991px) default to collapsed; desktops default to expanded.
    const isTablet = window.innerWidth < 992;
    const shouldCollapse = saved !== null ? saved === 'true' : isTablet;
    if (shouldCollapse) sidebar?.classList.add('collapsed');
  }

  /* ── Close mobile drawer when resized to tablet/desktop ─────────────────── */
  window.addEventListener('resize', () => {
    if (!isMobile() && sidebar?.classList.contains('mobile-open')) {
      closeMobileDrawer();
    }
  }, { passive: true });

  // ══════════════════════════════════════════════════════════════════════════
  // TABLE DENSITY TOGGLE
  // Cycles: normal → compact → comfortable → normal
  // Stored in localStorage key "invDensity"; applied to <html> data-density.
  // ══════════════════════════════════════════════════════════════════════════
  const densityBtn  = document.getElementById('densityToggle');
  const densityIcon = document.getElementById('densityIcon');
  const DENSITIES   = ['normal', 'compact', 'comfortable'];
  const DENSITY_ICONS = {
    normal:      'bi bi-layout-three-columns',
    compact:     'bi bi-list-task',
    comfortable: 'bi bi-view-list',
  };
  const DENSITY_TIPS = {
    normal:      'Нормальная плотность',
    compact:     'Компактная плотность',
    comfortable: 'Просторная плотность',
  };

  function applyDensity(d) {
    html.setAttribute('data-density', d);
    localStorage.setItem('invDensity', d);
    if (densityIcon) densityIcon.className = DENSITY_ICONS[d] || DENSITY_ICONS.normal;
    if (densityBtn) densityBtn.title = DENSITY_TIPS[d] || '';
  }

  // Init icon (density already applied by FOUC script)
  applyDensity(localStorage.getItem('invDensity') || 'normal');

  densityBtn?.addEventListener('click', () => {
    const cur = html.getAttribute('data-density') || 'normal';
    const next = DENSITIES[(DENSITIES.indexOf(cur) + 1) % DENSITIES.length];
    applyDensity(next);
    showToast(DENSITY_TIPS[next], 'info', 1800);
  });

  // ══════════════════════════════════════════════════════════════════════════
  // TOAST helper
  // ══════════════════════════════════════════════════════════════════════════
  const TOAST_ICONS = {
    success: 'bi-check-circle-fill',
    danger:  'bi-x-circle-fill',
    warning: 'bi-exclamation-triangle-fill',
    info:    'bi-info-circle-fill',
  };

  window.showToast = function (message, type = 'success', delay = 4500) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const el = document.createElement('div');
    el.className = `toast align-items-center text-white bg-${type} border-0 shadow`;
    el.setAttribute('role', 'alert');
    el.innerHTML = `
      <div class="d-flex">
        <div class="toast-body d-flex align-items-center gap-2">
          <i class="bi ${TOAST_ICONS[type] || 'bi-bell-fill'}"></i>${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto"
                data-bs-dismiss="toast"></button>
      </div>`;
    container.appendChild(el);

    const bsToast = new bootstrap.Toast(el, { delay });
    bsToast.show();
    el.addEventListener('hidden.bs.toast', () => el.remove());
  };

  // ══════════════════════════════════════════════════════════════════════════
  // AUTO-DISMISS flash messages
  // ══════════════════════════════════════════════════════════════════════════
  document.querySelectorAll('#flash-messages .alert').forEach(el => {
    setTimeout(() => bootstrap.Alert.getOrCreateInstance(el)?.close(), 5500);
  });

  // ══════════════════════════════════════════════════════════════════════════
  // BOOTSTRAP VALIDATION — HTMX compatible
  //
  // When a form with class="needs-validation" is about to be submitted via
  // HTMX, we:
  //   1. Add "was-validated" so Bootstrap's CSS shows valid/invalid states.
  //   2. If the form fails HTML5 checkValidity(), we abort the HTMX request.
  // This pairs with PCForm.__init__() which adds "is-invalid" to widgets
  // that have server-side errors, so both layers work together.
  // ══════════════════════════════════════════════════════════════════════════
  document.body.addEventListener('htmx:configRequest', function (e) {
    const elt = e.detail.elt;
    // Only intercept form elements tagged for validation
    if (!elt || elt.tagName !== 'FORM' || !elt.classList.contains('needs-validation')) return;
    elt.classList.add('was-validated');
    if (!elt.checkValidity()) {
      e.preventDefault();
      // Focus first invalid field so the user sees it
      const firstInvalid = elt.querySelector(':invalid');
      if (firstInvalid) {
        firstInvalid.focus();
        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  });

  // ══════════════════════════════════════════════════════════════════════════
  // HTMX: show Bootstrap modal after content swapped into #modal-container
  // ══════════════════════════════════════════════════════════════════════════
  document.body.addEventListener('htmx:afterSettle', function (e) {
    if (e.detail.target.id === 'modal-container') {
      const modal = e.detail.target.querySelector('.modal');
      if (modal) bootstrap.Modal.getOrCreateInstance(modal).show();
    }
  });

  // ══════════════════════════════════════════════════════════════════════════
  // HTMX: HX-Trigger events — closeModal / pcSaved / pcDeleted
  // ══════════════════════════════════════════════════════════════════════════
  document.body.addEventListener('closeModal', () => {
    const modal = document.querySelector('#modal-container .modal');
    if (modal) bootstrap.Modal.getInstance(modal)?.hide();
  });

  function refreshTable() {
    const wrapper = document.getElementById('pc-table-wrapper');
    if (!wrapper) return;

    const filterForm = document.getElementById('filterForm');
    let url = window.location.pathname;
    if (filterForm) {
      const params = new URLSearchParams();
      new FormData(filterForm).forEach((v, k) => { if (v) params.append(k, v); });
      const qs = params.toString();
      if (qs) url += '?' + qs;
    }
    htmx.ajax('GET', url, { target: '#pc-table-wrapper', swap: 'innerHTML' });
  }

  document.body.addEventListener('pcSaved', function (e) {
    showToast((e.detail?.message) || 'Сохранено', 'success');
    refreshTable();
  });

  document.body.addEventListener('pcDeleted', function (e) {
    showToast((e.detail?.message) || 'Удалено', 'danger');
    refreshTable();
  });

  // ══════════════════════════════════════════════════════════════════════════
  // KEYBOARD SHORTCUTS
  // ══════════════════════════════════════════════════════════════════════════
  document.getElementById('shortcutsLink')?.addEventListener('click', e => {
    e.preventDefault();
    bootstrap.Modal.getOrCreateInstance(document.getElementById('shortcutsModal')).show();
  });

  document.addEventListener('keydown', function (e) {
    const tag = (document.activeElement?.tagName || '').toLowerCase();
    const inInput = ['input', 'textarea', 'select'].includes(tag);

    // Ctrl+B — sidebar (doesn't conflict with browser)
    if (e.ctrlKey && e.key === 'b') {
      e.preventDefault();
      setCollapsed(!sidebar?.classList.contains('collapsed'));
      return;
    }

    if (inInput) return;  // shortcuts below don't fire while typing in fields

    // Esc — close modal
    if (e.key === 'Escape') {
      const modal = document.querySelector('#modal-container .modal.show');
      if (modal) { bootstrap.Modal.getInstance(modal)?.hide(); return; }
    }

    // T — theme toggle  (no Ctrl, no Alt — avoids browser tab shortcut)
    if (e.key === 't' || e.key === 'T') {
      applyTheme(getCurrentTheme() === 'dark' ? 'light' : 'dark', true);
      return;
    }

    // / — focus search
    if (e.key === '/') {
      e.preventDefault();
      const search = document.getElementById('id_search') || document.querySelector('[name="search"]');
      search?.focus();
      return;
    }

    // N — new PC (if on list page)
    if (e.key === 'n' || e.key === 'N') {
      const addBtn = document.querySelector('[hx-get*="pc-create-modal"], [hx-get*="/modal/add/"]');
      if (addBtn) { addBtn.click(); return; }
    }

    // ? — shortcuts help
    if (e.key === '?') {
      bootstrap.Modal.getOrCreateInstance(document.getElementById('shortcutsModal'))?.show();
    }
  });

  // ══════════════════════════════════════════════════════════════════════════
  // BACK TO TOP
  // ══════════════════════════════════════════════════════════════════════════
  const backToTopBtn = document.getElementById('backToTop');
  if (backToTopBtn) {
    const mainContent = document.querySelector('.page-content');
    const scrollable  = mainContent || window;

    const onScroll = () => {
      const scrolled = (mainContent ? mainContent.scrollTop : window.scrollY) > 300;
      backToTopBtn.style.display = scrolled ? 'flex' : 'none';
    };

    scrollable.addEventListener('scroll', onScroll, { passive: true });
    backToTopBtn.addEventListener('click', () => {
      (mainContent || document.documentElement).scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // ══════════════════════════════════════════════════════════════════════════
  // IMPORT: drag-and-drop
  // ══════════════════════════════════════════════════════════════════════════
  const dropArea  = document.getElementById('dropArea');
  const fileInput = document.getElementById('id_file');
  const fileLabel = document.getElementById('fileLabel');

  if (dropArea && fileInput) {
    ['dragenter', 'dragover'].forEach(evt => {
      dropArea.addEventListener(evt, e => { e.preventDefault(); dropArea.classList.add('drag-over'); });
    });
    ['dragleave', 'drop'].forEach(evt => {
      dropArea.addEventListener(evt, () => dropArea.classList.remove('drag-over'));
    });
    dropArea.addEventListener('drop', e => {
      e.preventDefault();
      const files = e.dataTransfer?.files;
      if (files?.length) {
        fileInput.files = files;
        if (fileLabel) fileLabel.textContent = files[0].name;
      }
    });
    fileInput.addEventListener('change', () => {
      if (fileInput.files?.length && fileLabel) fileLabel.textContent = fileInput.files[0].name;
    });
  }

})();
