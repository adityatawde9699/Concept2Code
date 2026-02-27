function endBooking(bookingId) {
  if (!confirm('Check out this booking?')) {
    return;
  }

  fetch(`/end-booking/${bookingId}`, { method: 'POST' })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === 'success') {
        alert(`Checked out successfully. Total cost: ₹${data.total_cost}`);
        window.location.reload();
        return;
      }
      alert('Error checking out booking.');
    })
    .catch(() => {
      alert('Unable to complete checkout right now.');
    });
}

(function initBookingEstimator() {
  const startInput = document.querySelector('[name="start_time"]');
  const endInput = document.querySelector('[name="end_time"]');
  const priceEl = document.getElementById('estimatedPrice');

  if (!startInput || !endInput || !priceEl) {
    return;
  }

  const rate = parseFloat(endInput.dataset.rate || '0');

  const updateEstimate = () => {
    const startValue = startInput.value;
    const endValue = endInput.value;

    if (!startValue || !endValue) {
      priceEl.textContent = '—';
      return;
    }

    const start = new Date(startValue);
    const end = new Date(endValue);

    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end <= start) {
      priceEl.textContent = '—';
      return;
    }

    const hours = (end - start) / (1000 * 60 * 60);
    priceEl.textContent = `₹${(hours * rate).toFixed(2)}`;
  };

  startInput.addEventListener('change', updateEstimate);
  endInput.addEventListener('change', updateEstimate);
})();
