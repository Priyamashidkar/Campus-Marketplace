/**
 * erp_charts.js - Live ERP Charts for Admin Dashboard and Reports
 */

document.addEventListener("DOMContentLoaded", function () {
  const trendsCanvas = document.getElementById("monthlyTrendsChart");
  const categoryCanvas = document.getElementById("categoryDistChart");
  const inventoryCanvas = document.getElementById("inventoryHealthChart");

  if (!trendsCanvas && !categoryCanvas && !inventoryCanvas) {
    return;
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
                borderColor: "#1e3a8a",
                backgroundColor: "rgba(30, 58, 138, 0.1)",
                tension: 0.3,
                fill: true,
                yAxisID: "yOrders",
              },
              {
                label: "Sales Value (₹)",
                data: data.monthly_trends.sales_values,
                borderColor: "#0d9488",
                backgroundColor: "transparent",
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
              yOrders: {
                type: "linear",
                position: "left",
                beginAtZero: true,
                title: { display: true, text: "Orders Count" },
              },
              ySales: {
                type: "linear",
                position: "right",
                beginAtZero: true,
                grid: { drawOnChartArea: false },
                title: { display: true, text: "Sales (₹)" },
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
                backgroundColor: [
                  "#1e3a8a",
                  "#0d9488",
                  "#f59e0b",
                  "#8b5cf6",
                  "#ec4899",
                  "#06b6d4",
                  "#64748b",
                  "#10b981",
                ],
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: "bottom" },
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
                borderRadius: 6,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: { beginAtZero: true, ticks: { precision: 0 } },
            },
          },
        });
      }
    })
    .catch((err) => {
      console.error("Error loading ERP chart data:", err);
    });
});
