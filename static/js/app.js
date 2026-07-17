/* ============================================================
   app.js – ShopSmart AI
   Global JavaScript utilities and helpers
   ============================================================ */

'use strict';

// ── Toast Notification ────────────────────────────────────────
window.showToast = function(message, type = 'success') {
  const container = document.getElementById('toastContainer') || createToastContainer();
  const id = 'toast_' + Date.now();
  const colours = {success:'bg-success', danger:'bg-danger', warning:'bg-warning text-dark', info:'bg-info'};
  const icons = {success:'check-circle-fill', danger:'x-circle-fill', warning:'exclamation-triangle-fill', info:'info-circle-fill'};
  container.insertAdjacentHTML('beforeend', `
    <div id="${id}" class="toast align-items-center text-white ${colours[type]||'bg-secondary'} border-0" role="alert">
      <div class="d-flex">
        <div class="toast-body"><i class="bi bi-${icons[type]||'bell-fill'} me-2"></i>${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>
  `);
  const el = document.getElementById(id);
  const toast = new bootstrap.Toast(el, {autohide: true, delay: 3500});
  toast.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
};

function createToastContainer() {
  const div = document.createElement('div');
  div.id = 'toastContainer';
  div.className = 'position-fixed bottom-0 end-0 p-3';
  div.style.zIndex = '9999';
  document.body.appendChild(div);
  return div;
}

// ── Format currency ───────────────────────────────────────────
window.formatINR = function(value) {
  return '₹' + parseFloat(value).toLocaleString('en-IN');
};

// ── Wishlist global handler ───────────────────────────────────
document.addEventListener('click', function(e) {
  const btn = e.target.closest('.global-wishlist-btn');
  if (!btn) return;
  const pid = btn.dataset.pid;
  fetch('/api/wishlist/toggle', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({product_id: pid})
  })
  .then(r => r.json())
  .then(d => {
    showToast(d.action === 'added' ? '❤️ Added to Wishlist!' : '💔 Removed from Wishlist');
    btn.innerHTML = d.action === 'added'
      ? '<i class="bi bi-heart-fill text-danger"></i>'
      : '<i class="bi bi-heart"></i>';
  });
});

// ── Debounce helper ───────────────────────────────────────────
window.debounce = function(fn, delay = 300) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
};

// ── Copy to clipboard ─────────────────────────────────────────
window.copyText = function(text) {
  navigator.clipboard?.writeText(text).then(() => showToast('Copied to clipboard!', 'info'));
};

// ── Scroll to top ─────────────────────────────────────────────
const scrollTopBtn = document.createElement('button');
scrollTopBtn.innerHTML = '<i class="bi bi-arrow-up"></i>';
scrollTopBtn.className = 'btn btn-primary btn-sm rounded-circle position-fixed d-none';
scrollTopBtn.id = 'scrollTopBtn';
scrollTopBtn.style.cssText = 'bottom:20px;right:20px;width:42px;height:42px;z-index:999;';
scrollTopBtn.addEventListener('click', () => window.scrollTo({top: 0, behavior: 'smooth'}));
document.body.appendChild(scrollTopBtn);

window.addEventListener('scroll', () => {
  scrollTopBtn.classList.toggle('d-none', window.scrollY < 400);
});

// ── Active nav link highlight ─────────────────────────────────
document.querySelectorAll('.navbar .nav-link').forEach(link => {
  if (link.href === window.location.href) {
    link.classList.add('active');
  }
});

// ── Auto-dismiss alerts ───────────────────────────────────────
document.querySelectorAll('.alert-dismissible').forEach(alert => {
  setTimeout(() => {
    const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
    if (bsAlert) bsAlert.close();
  }, 5000);
});

// ── Tooltip initialisation ────────────────────────────────────
document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
  new bootstrap.Tooltip(el);
});

console.log('%cShopSmart AI 🛒', 'color:#2563eb;font-size:1.2rem;font-weight:bold');
console.log('%cPowered by IBM Granite | IBM Orchestrate | ChromaDB RAG', 'color:#7c3aed');
