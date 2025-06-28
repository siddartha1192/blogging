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
    const emailInput = document.getElementById("subscriber-email");
    const responseEl = document.getElementById("subscription-response");
    const postUrl = form.getAttribute("data-url");

    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        const email = emailInput.value.trim();

        try {
            const response = await fetch("{{ url_for('subscribe') }}", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email })});

            const result = await response.json();
            responseEl.innerHTML = `<div class="alert alert-${result.status}">${result.message}</div>`;
        } catch (err) {
            responseEl.innerHTML = `<div class="alert alert-danger">An error occurred. Please try again.</div>`;
        }
    });
});

