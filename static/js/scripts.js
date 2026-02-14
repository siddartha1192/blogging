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

    const emailInput = document.getElementById("subscriber-email");
    const responseEl = document.getElementById("subscription-response");
    const postUrl = form.getAttribute("data-url");

    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        const email = emailInput.value.trim();

        if (!email) {
            responseEl.innerHTML = `<div class="alert alert-warning">Please enter a valid email address.</div>`;
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
                body: JSON.stringify({ email })
            });

            const result = await response.json();
            responseEl.innerHTML = `<div class="alert alert-${result.status} alert-dismissible fade show">
                ${result.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`;

            // Clear input on success
            if (result.status === 'success') {
                emailInput.value = '';
            }
        } catch (err) {
            responseEl.innerHTML = `<div class="alert alert-danger alert-dismissible fade show">
                An error occurred. Please try again.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`;
        } finally {
            // Re-enable button
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnHtml;
        }
    });
});

