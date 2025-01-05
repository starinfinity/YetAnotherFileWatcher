const searchBar = document.getElementById("search-bar");
const tableRows = document.querySelectorAll("#task-table tbody tr");

if (searchBar) {
  searchBar.addEventListener("input", () => {
    const searchTerm = searchBar.value.toLowerCase();

    tableRows.forEach((row) => {
      const taskData = row.textContent.toLowerCase();
      if (taskData.includes(searchTerm)) {
        row.style.display = "";
      } else {
        row.style.display = "none";
      }
    });
  });
}

// Function to open the calendar popup
function openCalendarPopup() {
  // Initialize flatpickr on the timeRange input field
  flatpickr("#timeRange", {
    // Options for the calendar (e.g., mode, dateFormat, etc.)
    mode: "range",
    dateFormat: "Y-m-d",
    onClose: function(selectedDates, dateStr, instance) {
      // Update the timeRange input field with the selected date range
      document.getElementById("timeRange").value = dateStr;
      // Close the calendar popup
      closeCalendarPopup();
    }
  });

  // Show the calendar popup
  document.getElementById("calendarPopup").style.display = "block";
}

// Function to close the calendar popup
function closeCalendarPopup() {
  document.getElementById("calendarPopup").style.display = "none";
}

// Event listener for the calendar button
const calendarButton = document.getElementById("calendarButton");
if (calendarButton) {
  calendarButton.addEventListener("click", openCalendarPopup);
}

// Fetch server keys and populate the dropdown
fetch("/server_keys")
  .then((response) => response.json())
  .then((data) => {
    const serverSelect = document.getElementById("server");
    if (serverSelect) {
      data.forEach((serverKey) => {
        const option = document.createElement("option");
        option.value = serverKey;
        option.text = serverKey;
        serverSelect.add(option);
      });
    }
  })
  .catch((error) => {
    console.error("Error fetching server keys:", error);
  });

// Task Summary Chart
function createTaskSummaryChart(chartType = "pie") {
  const timeRange = document.getElementById("timeRange")?.value || "all";
  const server = document.getElementById("server")?.value || "all";
  const filePattern = document.getElementById("filePattern")?.value || "";

  const url = `/task_summary?time_range=${timeRange}&server=${server}&file_pattern=${filePattern}`;
  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      const ctx = document.getElementById("taskSummaryChart")?.getContext("2d");
      if (window.taskSummaryChart) {
        window.taskSummaryChart.destroy();
      }

      if (ctx) {
        window.taskSummaryChart = new Chart(ctx, {
          type: chartType,
          data: {
            labels: [
              "Running Jobs",
              "Failed Jobs",
              "Waiting Jobs",
              "Retrying Jobs",
              "Other Jobs",
            ],
            datasets: [
              {
                data: [
                  data.running_jobs,
                  data.failed_jobs,
                  data.waiting_jobs,
                  data.retrying_jobs,
                  data.total_jobs
                    - (
                      data.running_jobs +
                      data.failed_jobs +
                      data.waiting_jobs +
                      data.retrying_jobs
                    ),
                ],
                backgroundColor: [
                  "#5cb85c",
                  "#d9534f",
                  "#777",
                  "#f0ad4e",
                  "#5bc0de",
                ],
              },
            ],
          },
          options: {
            // ... (add any options you want to customize the chart) ...
          },
        });
      }
    });
}

if (document.getElementById("taskSummaryChart")) {
  createTaskSummaryChart();
}

const chartTypeSelect = document.getElementById("chartType");
if (chartTypeSelect) {
  chartTypeSelect.addEventListener("change", () => {
    const selectedChartType = chartTypeSelect.value;
    createTaskSummaryChart(selectedChartType);
  });
}

// Recent Activity List with refresh and loading animation
function updateRecentActivity() {
  const activityList = document.getElementById("recentActivityList");
  if (activityList) {
    activityList.classList.add("loading");

    fetch("/recent_activity")
      .then((response) => response.json())
      .then((data) => {
        setTimeout(() => {
          activityList.innerHTML = "";
          if (Array.isArray(data)) {
            data.forEach((item) => {
              const li = document.createElement("li");
              li.textContent = `Task "${item.filename}" ${item.status}`;
              activityList.appendChild(li);
            });
          } else {
            console.error("Invalid data format for recent activity:", data);
            activityList.innerHTML = "<li>Error loading recent activity.</li>";
          }
          activityList.classList.remove("loading");
        }, 300);
      })
      .catch((error) => {
        console.error("Error fetching recent activity:", error);
        activityList.innerHTML = "<li>Error loading recent activity.</li>";
        activityList.classList.remove("loading");
      });
  }
}

if (document.getElementById("recentActivityList")) {
  updateRecentActivity();
  setInterval(updateRecentActivity, 5000);
}

// Page transition animation
const contentDiv = document.querySelector(".content");
function handlePageTransition() {
  if (contentDiv) {
    contentDiv.classList.add("fade-out");
    setTimeout(() => {
      window.location.href = this.href;
    }, 300);
  }
}

const sidebarLinks = document.querySelectorAll(".sidebar a");
sidebarLinks.forEach((link) => {
  link.addEventListener("click", handlePageTransition);
});

// Event listener for "Apply Filters" button
const applyFiltersButton = document.getElementById("applyFilters");
if (applyFiltersButton) {
  applyFiltersButton.addEventListener("click", () => {
    createTaskSummaryChart(
      document.getElementById("chartType")?.value || "pie"
    );
  });
}

// Trend Chart
function createTrendChart() {
  const timeRange = document.getElementById("timeRange")?.value || "all";
  const server = document.getElementById("server")?.value || "all";
  const filePattern = document.getElementById("filePattern")?.value || "";

  const url = `/trend_data?time_range=${timeRange}&server=${server}&file_pattern=${filePattern}`;
  fetch(url)
    .then((response) => response.json())
    .then((data) => {
      const ctx = document.getElementById("trendChart")?.getContext("2d");
      if (ctx) {
        new Chart(ctx, {
          type: "line", // You can change the chart type if needed
          data: {
            labels: data.labels,
            datasets: [
              {
                label: "Successes",
                data: data.successes,
                borderColor: "green",
                backgroundColor: "rgba(0, 128, 0, 0.2)",
                fill: true,
              },
              {
                label: "Failures",
                data: data.failures,
                borderColor: "red",
                backgroundColor: "rgba(255, 0, 0, 0.2)",
                fill: true,
              },
            ],
          },
          options: {
            responsive: true,
            scales: {
              y: {
                beginAtZero: true,
              },
            },
          },
        });
      }
    });
}

if (document.getElementById("trendChart")) {
  createTrendChart();
}
