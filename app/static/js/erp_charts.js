/**
 * erp_charts.js - Live ERP Charts for Admin Dashboard and Reports
 * Styled for consistent Dark Theme readability and high contrast.
 */

document.addEventListener("DOMContentLoaded", function () {
  const trendsCanvas = document.getElementById("monthlyTrendsChart");
  const categoryCanvas = document.getElementById("categoryDistChart");
  const inventoryCanvas = document.getElementById("inventoryHealthChart");

  if (!trendsCanvas && !categoryCanvas && !inventoryCanvas) {
    return;
  }

  // Set global Chart.js defaults for dark theme
  if (typeof Chart !== "undefined") {
    Chart.defaults.color = "#AAB4C3";
    Chart.defaults.borderColor = "#303B4B";
    Chart.defaults.plugins.tooltip.backgroundColor = "#1C2330";
    Chart.defaults.plugins.tooltip.titleColor = "#F1F5F9";
    Chart.defaults.plugins.tooltip.bodyColor = "#AAB4C3";
    Chart.defaults.plugins.tooltip.borderColor = "#303B4B";
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.legend.labels.color = "#F1F5F9";
  }

  fetch("/admin/api/chart-data")
    .then((res) => {
      if (!res.ok) throw new Error("Failed to load chart data");
      return res.json();
    })
    .then((data) => {
      // 1. Monthly Trends Chart (Orders & Revenue)
      if (trendsCanvas && data.monthly_trends) {
        new Chart(trendsCanvas.getContext("2d"), {
          type: "line",
          data: {
            labels: data.monthly_trends.labels,
            datasets: [
              {
                label: "Order Volume",
                data: data.monthly_trends.order_counts,
                borderColor: "#3B82F6",
                backgroundColor: "rgba(59, 130, 246, 0.15)",
                pointBackgroundColor: "#3B82F6",
                tension: 0.3,
                fill: true,
                yAxisID: "yOrders",
              },
              {
                label: "Sales Value (₹)",
                data: data.monthly_trends.sales_values,
                borderColor: "#14B8A6",
                backgroundColor: "transparent",
                pointBackgroundColor: "#14B8A6",
                borderDash: [5, 5],
                tension: 0.3,
                yAxisID: "ySales",
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: {
                grid: { color: "#303B4B" },
                ticks: { color: "#AAB4C3" },
              },
              yOrders: {
                type: "linear",
                position: "left",
                beginAtZero: true,
                grid: { color: "#303B4B" },
                ticks: { color: "#AAB4C3" },
                title: { display: true, text: "Orders Count", color: "#F1F5F9" },
              },
              ySales: {
                type: "linear",
                position: "right",
                beginAtZero: true,
                grid: { drawOnChartArea: false },
                ticks: { color: "#AAB4C3" },
                title: { display: true, text: "Sales (₹)", color: "#F1F5F9" },
              },
            },
            plugins: {
              legend: {
                labels: { color: "#F1F5F9" },
              },
            },
          },
        });
      }

      // 2. Category Distribution (Doughnut Chart)
      if (categoryCanvas && data.category_distribution) {
        new Chart(categoryCanvas.getContext("2d"), {
          type: "doughnut",
          data: {
            labels: data.category_distribution.labels,
            datasets: [
              {
                data: data.category_distribution.product_counts,
                borderColor: "#1C2330",
                borderWidth: 2,
                backgroundColor: [
                  "#3B82F6",
                  "#14B8A6",
                  "#F59E0B",
                  "#8B5CF6",
                  "#EC4899",
                  "#06B6D4",
                  "#64748B",
                  "#22C55E",
                ],
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: "bottom",
                labels: { color: "#F1F5F9" },
              },
            },
          },
        });
      }

      // 3. Inventory Health (Bar Chart)
      if (inventoryCanvas && data.inventory_health) {
        new Chart(inventoryCanvas.getContext("2d"), {
          type: "bar",
          data: {
            labels: data.inventory_health.labels,
            datasets: [
              {
                label: "Inventory Units",
                data: data.inventory_health.data,
                backgroundColor: data.inventory_health.colors,
                borderColor: "#303B4B",
                borderWidth: 1,
                borderRadius: 6,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: {
                grid: { display: false },
                ticks: { color: "#AAB4C3" },
              },
              y: {
                beginAtZero: true,
                grid: { color: "#303B4B" },
                ticks: { color: "#AAB4C3", precision: 0 },
              },
            },
            plugins: {
              legend: {
                labels: { color: "#F1F5F9" },
              },
            },
          },
        });
      }
    })
    .catch((err) => {
      console.error("Error loading ERP chart data:", err);
    });
});
