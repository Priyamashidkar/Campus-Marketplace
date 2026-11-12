/**
 * main.js - Campus Marketplace Client Script
 */

document.addEventListener("DOMContentLoaded", function () {
  // Auto-dismiss bootstrap alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert.alert-dismissible");
  alerts.forEach((alert) => {
    setTimeout(() => {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 6000);
  });

  // Enable Bootstrap tooltips if any
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});
