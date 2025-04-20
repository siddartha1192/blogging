document.addEventListener('DOMContentLoaded', function() {
    // Initialize featured slider with 5-second interval
    const featuredCarousel = document.getElementById('featuredCarousel');
    if (featuredCarousel) {
        const carousel = new bootstrap.Carousel(featuredCarousel, {
            interval: 5000,
            pause: 'hover'
        });
    }
    
    // Newsletter form submission
    const newsletterForm = document.getElementById('newsletterForm');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const emailInput = this.querySelector('input[type="email"]');
            const email = emailInput.value.trim();
            
            if (!email) {
                showAlert('Please enter your email address.', 'danger');
                return;
            }
            
            // Simulate form submission
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;
            
            submitButton.disabled = true;
            submitButton.textContent = 'Subscribing...';
            
            setTimeout(() => {
                showAlert('You have been successfully subscribed to our newsletter!', 'success');
                emailInput.value = '';
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }, 1000);
        });
    }
    
    // Helper function to show alerts
    function showAlert(message, type) {
        const alertContainer = document.querySelector('.alert-container');
        if (!alertContainer) return;
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.role = 'alert';
        
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        alertContainer.appendChild(alert);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => {
                alert.remove();
            }, 150);
        }, 5000);
    }
});