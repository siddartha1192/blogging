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



document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("newsletter-form");
    if (!form) return; // Exit if newsletter form doesn't exist

    const nameInput = document.getElementById("subscriber-name");
    const emailInput = document.getElementById("subscriber-email");
    const phoneInput = document.getElementById("subscriber-phone");
    const responseEl = document.getElementById("subscription-response");
    const postUrl = form.getAttribute("data-url");

    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        const name = nameInput ? nameInput.value.trim() : '';
        const email = emailInput.value.trim();
        const phone = phoneInput ? phoneInput.value.trim() : '';

        if (!email) {
            responseEl.innerHTML = `<div class="alert alert-warning alert-dismissible fade show">
                Please enter a valid email address.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`;
            return;
        }

        // Basic email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            responseEl.innerHTML = `<div class="alert alert-danger alert-dismissible fade show">
                Please enter a valid email address.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`;
            return;
        }

        // Disable button during submission
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Subscribing...';

        try {
            const response = await fetch(postUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    email: email,
                    phone: phone
                })
            });

            const result = await response.json();
            responseEl.innerHTML = `<div class="alert alert-${result.status} alert-dismissible fade show">
                ${result.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`;

            // Clear inputs on success
            if (result.status === 'success') {
                if (nameInput) nameInput.value = '';
                emailInput.value = '';
                if (phoneInput) phoneInput.value = '';

                // Scroll to response message
                responseEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        } catch (err) {
            responseEl.innerHTML = `<div class="alert alert-danger alert-dismissible fade show">
                An error occurred. Please try again later.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`;
        } finally {
            // Re-enable button
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnHtml;
        }
    });
});

