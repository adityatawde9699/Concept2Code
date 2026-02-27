function endBooking(bookingId) {
  if (confirm('Check out this booking?')) {
    fetch(`/end-booking/${bookingId}`, { method: 'POST' })
      .then(r => r.json())
      .then(d => {
        if (d.status === 'success') {
          alert('Checked out successfully. Total cost: ₹' + d.total_cost);
          location.reload();
        } else {
          alert('Error checking out');
        }
      })
      .catch(err => console.error('Error:', err));
  }
}

document.addEventListener('DOMContentLoaded', function() {
  const startInput = document.querySelector('[name="start_time"]');
  const endInput = document.querySelector('[name="end_time"]');
  const priceEl = document.getElementById('estimatedPrice');
  
  if (endInput && startInput && priceEl) {
    const rate = parseFloat(endInput.dataset.rate || 0);
    endInput.addEventListener('change', function() {
      const start = new Date(startInput.value);
      const end = new Date(this.value);
      if (start && end && end > start) {
        const hours = (end - start) / (1000 * 60 * 60);
        const cost = (hours * rate).toFixed(2);
        priceEl.textContent = '₹' + cost;
      }
    });
  }
});

