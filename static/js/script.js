document.addEventListener('DOMContentLoaded', function() {
    console.log('ParkWise loaded');
});

function refreshSlots() {
    location.reload();
}

function endBooking(bookingId) {
    if (confirm('End this booking?')) {
        fetch(`/end-booking/${bookingId}`, {
            method: 'POST'
        })
        .then(r => r.json())
        .then(data => {
            alert('Booking ended');
            location.reload();
        })
        .catch(err => console.error(err));
    }
}
