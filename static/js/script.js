document.addEventListener('DOMContentLoaded', function () {
  // Animate stat counters on dashboard
  document.querySelectorAll('.count-up').forEach(el => {
    const target = parseInt(el.dataset.target || el.textContent, 10);
    let current = 0;
    const step = Math.ceil(target / 30);
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current;
      if (current >= target) clearInterval(timer);
    }, 40);
  });

  // Real-time price estimate in booking form
  const startInput = document.getElementById('start_time');
  const endInput   = document.getElementById('end_time');
  const priceRate  = parseFloat(document.getElementById('price_rate')?.dataset.rate || 0);
  const priceEl    = document.getElementById('estimated_price');
  const durationEl = document.getElementById('estimated_duration');

  function updatePrice() {
    if (!startInput || !endInput || !priceEl) return;
    const start = new Date(startInput.value);
    const end   = new Date(endInput.value);
    if (isNaN(start) || isNaN(end) || end <= start) {
      priceEl.textContent = '—';
      if (durationEl) durationEl.textContent = '';
      return;
    }
    const hours = (end - start) / 3600000;
    const cost  = (hours * priceRate).toFixed(2);
    priceEl.textContent = `₹${cost}`;
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    if (durationEl) durationEl.textContent = `${h > 0 ? h + 'h ' : ''}${m}m`;
  }

  if (startInput) startInput.addEventListener('change', updatePrice);
  if (endInput)   endInput.addEventListener('change', updatePrice);

  // Zone filter — instant filter without page reload (fallback: links still work)
  document.querySelectorAll('.zone-tab[data-zone]').forEach(tab => {
    tab.addEventListener('click', function (e) {
      const zone = this.dataset.zone;
      // If server-side filtering is preferred, let the link navigate
      // Otherwise we can client-side show/hide
    });
  });

  // Slot card click navigates to booking if available
  document.querySelectorAll('.slot-card.available[data-href]').forEach(card => {
    card.addEventListener('click', function () {
      window.location.href = this.dataset.href;
    });
  });
});

// End Booking / Check Out
function endBooking(bookingId) {
  if (!confirm('Check out now and end this parking session?')) return;
  fetch(`/end-booking/${bookingId}`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
      if (data.status === 'success') {
        const cost = data.total_cost ? `₹${data.total_cost}` : '';
        showToast(`✅ Checked out! ${cost ? 'Total: ' + cost : ''}`, 'success');
        setTimeout(() => location.reload(), 1800);
      } else {
        showToast('❌ Could not check out. Try again.', 'error');
      }
    })
    .catch(() => showToast('❌ Network error.', 'error'));
}

// Inline toast notification
function showToast(msg, type = 'info') {
  const existing = document.getElementById('pw-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'pw-toast';
  toast.textContent = msg;
  const bg = type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#4f46e5';
  Object.assign(toast.style, {
    position: 'fixed', bottom: '2rem', right: '2rem', zIndex: 9999,
    background: bg, color: '#fff', padding: '1rem 1.5rem',
    borderRadius: '12px', fontFamily: 'Inter, sans-serif',
    fontWeight: '600', fontSize: '0.9rem',
    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
    animation: 'fadeInUp 0.3s ease both',
  });
  document.body.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 400); }, 3000);
}
