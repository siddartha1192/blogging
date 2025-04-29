// Helper function for showing alerts
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        const dismissButton = alertDiv.querySelector('.btn-close');
        if (dismissButton) {
            dismissButton.click();
        }
    }, 5000);
}

// Newsletter form submission
document.addEventListener('DOMContentLoaded', function() {
    const newsletterForm = document.querySelector('.newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const emailInput = this.querySelector('input[type="email"]');
            const email = emailInput.value.trim();
            
            if (email) {
                // In a real application, this would send the email to a server
                showAlert('Thank you for subscribing to our newsletter!', 'success');
                emailInput.value = '';
            } else {
                showAlert('Please enter a valid email address.', 'danger');
            }
        });
    }
    
    // Featured carousel initialization with 5 second interval
    const featuredCarousel = document.getElementById('featuredCarousel');
    if (featuredCarousel) {
        const carousel = new bootstrap.Carousel(featuredCarousel, {
            interval: 5000,
            ride: 'carousel'
        });
    }
});