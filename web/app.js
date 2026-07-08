// Duypt2 Task Manager - Application Logic with GitHub API Sync

// --- App State ---
let tasks = [];
let categories = [
  { id: "cat-1", name: "Cá nhân", color: "#ff00ff" },
  { id: "cat-2", name: "Công việc", color: "#00ccff" },
  { id: "cat-3", name: "Học tập", color: "#39ff14" },
  { id: "cat-4", name: "Dự án", color: "#ffff00" }
];
let currentTab = "dashboard";
let currentEditingTaskId = null;
let currentMonth = new Date().getMonth();
let currentYear = new Date().getFullYear();

// GitHub Sync variables
let gitConfig = {
  username: "ptduy19",
  email: "ptduy19@gmail.com",
  repo: "Quan-ly-cong-viec-ca-nhan",
  branch: "main",
  path: "web/tasks.json",
  token: ""
};
let gitSha = null; // Store SHA of tasks.json for overwrite verification
let isGitConnected = false;

// --- Notifications State ---
let notifications = [];

// --- Date Utils ---
function isTaskOverdue(task) {
  if (task.progress >= 100) return false;
  if (!task.deadline_date) return false;
  
  const now = new Date();
  const deadlineStr = `${task.deadline_date}T${task.deadline_time || "23:59"}:00`;
  const deadline = new Date(deadlineStr);
  return deadline < now;
}

// --- Initialize App ---
document.addEventListener("DOMContentLoaded", () => {
  initPWA();
  loadLocalCategories();
  loadLocalNotifications();
  loadGitConfig();
  setupEventListeners();
  renderApp();
  
  // Start deadline checker
  checkDeadlines();
  setInterval(checkDeadlines, 30000); // every 30 seconds
  
  // Request Notification Permission
  if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission();
  }
});

// --- PWA Setup ---
function initPWA() {
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("./sw.js")
        .then((reg) => console.log("Service Worker registered successfully.", reg.scope))
        .catch((err) => console.log("Service Worker registration failed: ", err));
    });
  }
}

// --- Local Data Loading ---
function loadLocalCategories() {
  const localCats = localStorage.getItem("duypt2_categories");
  if (localCats) {
    categories = JSON.parse(localCats);
  } else {
    localStorage.setItem("duypt2_categories", JSON.stringify(categories));
  }
}

function loadLocalTasks() {
  const localTasks = localStorage.getItem("duypt2_tasks");
  tasks = localTasks ? JSON.parse(localTasks) : [];
  updateCalculations();
}

function saveLocalTasks() {
  localStorage.setItem("duypt2_tasks", JSON.stringify(tasks));
  updateCalculations();
  renderTasks();
  renderCalendar();
  renderDashboardUrgent();
}

function loadLocalNotifications() {
  const localNotifs = localStorage.getItem("duypt2_notifications");
  notifications = localNotifs ? JSON.parse(localNotifs) : [];
  updateNotificationBadge();
}

function saveLocalNotifications() {
  localStorage.setItem("duypt2_notifications", JSON.stringify(notifications));
  updateNotificationBadge();
  renderNotifications();
}

// --- GitHub Sync Operations ---
function loadGitConfig() {
  const configStr = localStorage.getItem("duypt2_git_config");
  if (configStr) {
    try {
      gitConfig = { ...gitConfig, ...JSON.parse(configStr) };
    } catch (e) {
      console.error("Failed to parse stored Git config", e);
    }
  }

  // Populate inputs in UI
  document.getElementById("git-username").value = gitConfig.username || "ptduy19";
  document.getElementById("git-email").value = gitConfig.email || "ptduy19@gmail.com";
  document.getElementById("git-repo").value = gitConfig.repo || "Quan-ly-cong-viec-ca-nhan";
  document.getElementById("git-branch").value = gitConfig.branch || "main";
  document.getElementById("git-path").value = gitConfig.path || "web/tasks.json";
  document.getElementById("git-token").value = gitConfig.token || "";

  if (gitConfig.token) {
    connectGitHub();
  } else {
    loadLocalTasks();
  }
}

async function connectGitHub() {
  if (!gitConfig.token) {
    updateGitStatus(false, "Thiếu Token cá nhân.");
    loadLocalTasks();
    return;
  }

  updateGitStatus(false, "Đang kết nối...");

  const url = `https://api.github.com/repos/${gitConfig.username}/${gitConfig.repo}/contents/${gitConfig.path}?ref=${gitConfig.branch}`;
  
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Authorization": `token ${gitConfig.token}`,
        "Accept": "application/vnd.github.v3+json"
      }
    });

    if (response.status === 200) {
      const data = await response.json();
      gitSha = data.sha;
      
      // Decode base64 to Unicode string (supporting Vietnamese diacritics)
      const decodedContent = decodeURIComponent(escape(atob(data.content.replace(/\s/g, ""))));
      tasks = JSON.parse(decodedContent);
      
      isGitConnected = true;
      updateGitStatus(true, "Đã kết nối GitHub!");
      
      // Save locally as cache
      localStorage.setItem("duypt2_tasks", JSON.stringify(tasks));
      
      updateCalculations();
      renderTasks();
      renderCalendar();
      renderDashboardUrgent();
    } else if (response.status === 404) {
      // File not created yet
      gitSha = null;
      tasks = [];
      isGitConnected = true;
      updateGitStatus(true, "Đã kết nối (Tệp mới sẽ được tạo).");
      saveLocalTasks();
    } else {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.message || `Mã lỗi: ${response.status}`);
    }

  } catch (err) {
    console.error("GitHub Connection Error:", err);
    isGitConnected = false;
    updateGitStatus(false, `Lỗi: ${err.message}`);
    loadLocalTasks();
  }
}

async function saveTasksToGitHub() {
  if (!isGitConnected || !gitConfig.token) {
    saveLocalTasks();
    return;
  }

  const url = `https://api.github.com/repos/${gitConfig.username}/${gitConfig.repo}/contents/${gitConfig.path}`;
  
  // Encode JSON string to base64 supporting unicode
  const jsonString = JSON.stringify(tasks, null, 2);
  const base64Content = btoa(unescape(encodeURIComponent(jsonString)));

  const payload = {
    message: "chore: update tasks list via web client",
    content: base64Content,
    branch: gitConfig.branch,
    author: {
      name: gitConfig.username,
      email: gitConfig.email
    }
  };

  if (gitSha) {
    payload.sha = gitSha;
  }

  try {
    const response = await fetch(url, {
      method: "PUT",
      headers: {
        "Authorization": `token ${gitConfig.token}`,
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (response.ok) {
      const data = await response.json();
      gitSha = data.content.sha;
      updateGitStatus(true, "Đã đồng bộ lên GitHub!");
      
      // Sync cache
      localStorage.setItem("duypt2_tasks", JSON.stringify(tasks));
      updateCalculations();
      renderTasks();
      renderCalendar();
      renderDashboardUrgent();
    } else {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.message || `Mã lỗi: ${response.status}`);
    }
  } catch (err) {
    console.error("GitHub Write Error:", err);
    updateGitStatus(false, `Lỗi đồng bộ: ${err.message}`);
    alert("Đồng bộ lên GitHub thất bại. Công việc đã được lưu tạm ở máy này.");
    saveLocalTasks();
  }
}

function updateGitStatus(connected, message) {
  const statusEl = document.getElementById("git-status");
  if (statusEl) {
    if (connected) {
      statusEl.textContent = message;
      statusEl.style.color = "#39ff14"; // Neon Green
    } else {
      statusEl.textContent = message;
      statusEl.style.color = "#ff0055"; // Neon Red
    }
  }
}

function saveGitConfigUI() {
  gitConfig.username = document.getElementById("git-username").value.trim();
  gitConfig.email = document.getElementById("git-email").value.trim();
  gitConfig.repo = document.getElementById("git-repo").value.trim();
  gitConfig.branch = document.getElementById("git-branch").value.trim();
  gitConfig.path = document.getElementById("git-path").value.trim();
  gitConfig.token = document.getElementById("git-token").value.trim();

  localStorage.setItem("duypt2_git_config", JSON.stringify(gitConfig));
  connectGitHub();
}

// --- Setup Event Listeners ---
function setupEventListeners() {
  // Navigation Tabs
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach((item) => {
    item.addEventListener("click", (e) => {
      const tab = e.currentTarget.getAttribute("data-tab");
      switchTab(tab);
    });
  });

  // Add Task Buttons
  document.getElementById("btn-add-task-header").addEventListener("click", () => openTaskModal());
  document.getElementById("btn-close-modal").addEventListener("click", closeModal);
  document.getElementById("btn-cancel-modal").addEventListener("click", closeModal);
  
  // Task Form Submit
  document.getElementById("task-form").addEventListener("submit", handleFormSubmit);

  // Settings Save Git config
  document.getElementById("btn-save-git-config").addEventListener("click", saveGitConfigUI);
  
  // Settings Add Category
  document.getElementById("btn-add-category").addEventListener("click", addNewCategoryUI);

  // Filters Event
  document.getElementById("filter-search").addEventListener("input", renderTasks);
  document.getElementById("filter-status").addEventListener("change", renderTasks);
  document.getElementById("filter-priority").addEventListener("change", renderTasks);
  document.getElementById("filter-category").addEventListener("change", renderTasks);

  // Dashboard stat cards & summary cards → task list
  document.querySelectorAll(".clickable-card[data-filter]").forEach((card) => {
    card.addEventListener("click", (e) => {
      if (e.target.closest(".btn-edit, .icon-btn, button")) return;
      navigateToTasksWithFilter(card.getAttribute("data-filter"));
    });
  });
  
  // Search View Event
  document.getElementById("search-input-field").addEventListener("input", performSearch);

  // Calendar Month Navigation
  document.getElementById("cal-prev-month").addEventListener("click", () => changeMonth(-1));
  document.getElementById("cal-next-month").addEventListener("click", () => changeMonth(1));

  // Progress Bar Slider label
  const progressSlider = document.getElementById("task-progress");
  const progressTextVal = document.getElementById("progress-val-text");
  progressSlider.addEventListener("input", (e) => {
    progressTextVal.textContent = `${e.target.value}%`;
  });
  
  // Notifications mark all read
  const btnMarkAllRead = document.getElementById("btn-mark-all-read");
  if (btnMarkAllRead) {
    btnMarkAllRead.addEventListener("click", () => {
      notifications.forEach(n => n.is_read = true);
      saveLocalNotifications();
    });
  }
}

// --- Tab Navigation ---
function switchTab(tabId) {
  currentTab = tabId;
  
  // Update Navigation Bar
  document.querySelectorAll(".nav-item").forEach((item) => {
    if (item.getAttribute("data-tab") === tabId) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  // Update Page Title
  const titles = {
    dashboard: "Dashboard",
    tasks: "Danh sách công việc",
    calendar: "Lịch",
    search: "Tìm kiếm",
    settings: "Cài đặt"
  };
  document.getElementById("view-title").textContent = titles[tabId] || "App";

  // Toggle View Contents
  document.querySelectorAll(".view-content").forEach((view) => {
    if (view.id === `${tabId}-view`) {
      view.classList.add("active");
    } else {
      view.classList.remove("active");
    }
  });

  // Refresh Views
  if (tabId === "tasks") renderTasks();
  if (tabId === "calendar") renderCalendar();
  if (tabId === "settings") renderSettingsCategories();
  if (tabId === "notifications") renderNotifications();
}

// --- Navigate from dashboard to filtered task list ---
function navigateToTasksWithFilter(statusFilter = "all") {
  switchTab("tasks");

  const searchEl = document.getElementById("filter-search");
  const statusEl = document.getElementById("filter-status");
  const priorityEl = document.getElementById("filter-priority");
  const categoryEl = document.getElementById("filter-category");

  if (searchEl) searchEl.value = "";
  if (statusEl) statusEl.value = statusFilter;
  if (priorityEl) priorityEl.value = "all";
  if (categoryEl) categoryEl.value = "all";

  renderTasks();
}

// --- Render Logic ---
function renderApp() {
  populateCategoryDropdowns();
  renderTasks();
  renderCalendar();
  renderSettingsCategories();
}

// Populate Category Comboboxes
function populateCategoryDropdowns() {
  const filterCat = document.getElementById("filter-category");
  const formCat = document.getElementById("task-category");
  
  // Clear options
  filterCat.innerHTML = '<option value="all">Mọi nhóm</option>';
  formCat.innerHTML = "";

  categories.forEach((cat) => {
    // For Filters
    const optFilter = document.createElement("option");
    optFilter.value = cat.id;
    optFilter.textContent = cat.name;
    filterCat.appendChild(optFilter);

    // For Modal Form
    const optForm = document.createElement("option");
    optForm.value = cat.id;
    optForm.textContent = cat.name;
    formCat.appendChild(optForm);
  });
}

// --- Calculations & Dashboard Stats ---
function updateCalculations() {
  const total = tasks.length;
  let completed = 0;
  let pending = 0;
  let overdue = 0;

  const todayStr = new Date().toISOString().split("T")[0];

  tasks.forEach((t) => {
    if (t.progress >= 100) {
      completed++;
    } else {
      pending++;
      // Check if overdue
      if (isTaskOverdue(t)) {
        overdue++;
      }
    }
  });

  // Update stat values
  document.getElementById("stat-total").textContent = total;
  document.getElementById("stat-pending").textContent = pending;
  document.getElementById("stat-completed").textContent = completed;
  document.getElementById("stat-overdue").textContent = overdue;

  // Render SVG Circle progress
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
  document.getElementById("progress-percentage").textContent = `${percentage}%`;

  // Stroke-dasharray of our circle is 377 (2 * pi * r = 2 * 3.14159 * 60)
  const offset = 377 - (377 * percentage) / 100;
  document.getElementById("progress-circle").setAttribute("stroke-dashoffset", offset);
}

// --- Render Task Cards ---
function renderTasks() {
  const container = document.getElementById("main-tasks-list");
  if (!container) return;

  container.innerHTML = "";

  // Get filter settings
  const searchVal = document.getElementById("filter-search").value.toLowerCase();
  const statusVal = document.getElementById("filter-status").value;
  const priorityVal = document.getElementById("filter-priority").value;
  const categoryVal = document.getElementById("filter-category").value;

  const todayStr = new Date().toISOString().split("T")[0];

  const filteredTasks = tasks.filter((task) => {
    // Search Filter
    const matchSearch =
      task.title.toLowerCase().includes(searchVal) ||
      (task.description || "").toLowerCase().includes(searchVal) ||
      (task.assignee || "").toLowerCase().includes(searchVal);

    // Status Filter
    let matchStatus = true;
    if (statusVal === "pending") matchStatus = task.progress < 100;
    else if (statusVal === "completed") matchStatus = task.progress >= 100;
    else if (statusVal === "overdue") matchStatus = isTaskOverdue(task);

    // Priority Filter
    const matchPriority = priorityVal === "all" || task.priority === priorityVal;

    // Category Filter
    const matchCategory = categoryVal === "all" || task.category_id === categoryVal;

    return matchSearch && matchStatus && matchPriority && matchCategory;
  });

  if (filteredTasks.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; color: var(--text-muted); padding: 40px;">
        <i class="fa-solid fa-folder-open" style="font-size: 32px; margin-bottom: 15px; display: block; color: var(--border);"></i>
        Không có công việc nào khớp với bộ lọc.
      </div>
    `;
    return;
  }

  filteredTasks.forEach((task) => {
    container.appendChild(createTaskCardElement(task));
  });
}

function createTaskCardElement(task) {
  const card = document.createElement("div");
  card.className = `task-card priority-${task.priority}`;
  if (task.progress >= 100) card.classList.add("completed");

  const catObj = categories.find((c) => c.id === task.category_id) || { name: "Cá nhân", color: "#8b8fa3" };
  const isCompleted = task.progress >= 100;

  // Format Date display
  const startDisplay = task.start_date ? formatDate(task.start_date) : "";
  const deadlineDisplay = `${formatDate(task.deadline_date)} lúc ${task.deadline_time}`;

  card.innerHTML = `
    <div class="task-left">
      <div class="task-checkbox-container">
        <input type="checkbox" class="task-checkbox" ${isCompleted ? "checked" : ""} data-id="${task.id}">
      </div>
      <div class="task-details">
        <div class="task-title">${escapeHtml(task.title)}</div>
        ${task.description ? `<div class="task-desc">${escapeHtml(task.description)}</div>` : ""}
        <div class="task-meta">
          <span class="badge badge-priority-${task.priority}">${priorityLabel(task.priority)}</span>
          <span class="badge badge-category" style="border-color: ${catObj.color}; color: ${catObj.color};">${escapeHtml(catObj.name)}</span>
          ${startDisplay ? `<span class="meta-item"><i class="fa-solid fa-play"></i> Bắt đầu: ${startDisplay}</span>` : ""}
          <span class="meta-item"><i class="fa-solid fa-flag"></i> Hạn: ${deadlineDisplay}</span>
          ${task.assignee ? `<span class="meta-item"><i class="fa-solid fa-user"></i> ${escapeHtml(task.assignee)}</span>` : ""}
          <span class="meta-item"><i class="fa-solid fa-chart-line"></i> ${task.progress}%</span>
        </div>
      </div>
    </div>
    <div class="task-right">
      <button class="icon-btn btn-edit" data-id="${task.id}"><i class="fa-solid fa-pen"></i></button>
      <button class="icon-btn icon-btn-danger btn-delete" data-id="${task.id}"><i class="fa-solid fa-trash"></i></button>
    </div>
  `;

  // Attach Checkbox click
  card.querySelector(".task-checkbox").addEventListener("change", (e) => {
    toggleTaskComplete(task.id, e.target.checked);
  });

  // Attach Edit click
  card.querySelector(".btn-edit").addEventListener("click", () => {
    openTaskModal(task);
  });

  // Attach Delete click
  card.querySelector(".btn-delete").addEventListener("click", () => {
    deleteTask(task.id);
  });

  return card;
}

// --- Render Urgent List in Dashboard ---
function renderDashboardUrgent() {
  const container = document.getElementById("urgent-tasks-list");
  if (!container) return;

  container.innerHTML = "";

  const todayStr = new Date().toISOString().split("T")[0];

  // Filters overdue or high priority pending tasks
  const urgentTasks = tasks
    .filter((t) => t.progress < 100 && (t.priority === "high" || isTaskOverdue(t)))
    .slice(0, 3); // show top 3

  if (urgentTasks.length === 0) {
    container.innerHTML = `
      <div style="color: var(--success); font-size: 13px; text-align: center; padding: 20px;">
        <i class="fa-solid fa-circle-check" style="margin-right: 6px;"></i>Tuyệt vời! Không có công việc nào khẩn cấp hay quá hạn.
      </div>
    `;
    return;
  }

  urgentTasks.forEach((task) => {
    const card = document.createElement("div");
    card.className = `task-card priority-${task.priority}`;
    card.style.padding = "10px 15px";

    const isOverdue = isTaskOverdue(task);
    const dateColor = isOverdue ? "var(--danger)" : "var(--text-secondary)";

    card.innerHTML = `
      <div class="task-left">
        <div class="task-details">
          <div class="task-title" style="font-size: 14px;">${escapeHtml(task.title)}</div>
          <div class="task-meta" style="font-size: 10px;">
            <span class="badge badge-priority-${task.priority}">${priorityLabel(task.priority)}</span>
            <span class="meta-item" style="color: ${dateColor}; font-weight: bold;">
              <i class="fa-solid fa-circle-exclamation"></i> Hạn: ${formatDate(task.deadline_date)}
            </span>
          </div>
        </div>
      </div>
      <div class="task-right">
        <button class="icon-btn btn-edit" data-id="${task.id}" style="width: 26px; height: 26px;"><i class="fa-solid fa-pen" style="font-size:11px;"></i></button>
      </div>
    `;

    card.querySelector(".btn-edit").addEventListener("click", () => {
      openTaskModal(task);
    });

    container.appendChild(card);
  });
}

// --- Search Implementation ---
function performSearch() {
  const query = document.getElementById("search-input-field").value.toLowerCase().trim();
  const container = document.getElementById("search-results-list");
  if (!container) return;

  container.innerHTML = "";

  if (!query) {
    container.innerHTML = `
      <div style="text-align: center; color: var(--text-muted); padding: 40px;">
        Nhập từ khóa tìm kiếm để hiển thị kết quả.
      </div>
    `;
    return;
  }

  const matches = tasks.filter((t) => {
    return (
      t.title.toLowerCase().includes(query) ||
      (t.description || "").toLowerCase().includes(query) ||
      (t.assignee || "").toLowerCase().includes(query)
    );
  });

  if (matches.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; color: var(--text-muted); padding: 40px;">
        Không tìm thấy kết quả phù hợp với từ khóa "${escapeHtml(query)}".
      </div>
    `;
    return;
  }

  matches.forEach((task) => {
    container.appendChild(createTaskCardElement(task));
  });
}

// --- Calendar Renderer ---
function renderCalendar() {
  const daysGrid = document.getElementById("calendar-days-grid");
  if (!daysGrid) return;

  daysGrid.innerHTML = "";

  // Set month title
  const monthNames = [
    "Tháng 01", "Tháng 02", "Tháng 03", "Tháng 04",
    "Tháng 05", "Tháng 06", "Tháng 07", "Tháng 08",
    "Tháng 09", "Tháng 10", "Tháng 11", "Tháng 12"
  ];
  document.getElementById("calendar-month-title").textContent = `${monthNames[currentMonth]} / ${currentYear}`;

  const firstDay = new Date(currentYear, currentMonth, 1).getDay(); // 0 is Sunday, 1 is Mon...
  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

  // Prev Month Days
  const prevMonthDays = new Date(currentYear, currentMonth, 0).getDate();
  for (let i = firstDay - 1; i >= 0; i--) {
    const cell = document.createElement("div");
    cell.className = "calendar-cell inactive";
    cell.innerHTML = `<span class="calendar-day-num">${prevMonthDays - i}</span>`;
    daysGrid.appendChild(cell);
  }

  // Current Month Days
  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

  for (let d = 1; d <= daysInMonth; d++) {
    const dayStr = `${currentYear}-${String(currentMonth + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    const cell = document.createElement("div");
    cell.className = "calendar-cell";
    if (dayStr === todayStr) cell.classList.add("today");

    // Get tasks on this day
    const dayTasks = tasks.filter((t) => t.deadline_date === dayStr);

    let indicatorHtml = "";
    dayTasks.slice(0, 2).forEach((task) => {
      const isCompleted = task.progress >= 100;
      const indicatorColor = isCompleted ? "var(--success)" : `var(--priority-${task.priority}, var(--accent))`;
      indicatorHtml += `
        <span class="dot-indicator" style="background-color: ${indicatorColor}20; color: ${indicatorColor}; border: 1px solid ${indicatorColor}50;">
          ${escapeHtml(task.title)}
        </span>
      `;
    });

    if (dayTasks.length > 2) {
      indicatorHtml += `<span style="font-size:9px; color: var(--text-muted); text-align:center;">+${dayTasks.length - 2} công việc</span>`;
    }

    cell.innerHTML = `
      <span class="calendar-day-num">${d}</span>
      <div class="calendar-tasks-indicator">
        ${indicatorHtml}
      </div>
    `;

    // Click to add task on this day
    cell.addEventListener("click", () => {
      openTaskModal(null, dayStr);
    });

    daysGrid.appendChild(cell);
  }
}

function changeMonth(dir) {
  currentMonth += dir;
  if (currentMonth < 0) {
    currentMonth = 11;
    currentYear--;
  } else if (currentMonth > 11) {
    currentMonth = 0;
    currentYear++;
  }
  renderCalendar();
}

// --- Settings Categories ---
function renderSettingsCategories() {
  const container = document.getElementById("settings-categories-list");
  if (!container) return;

  container.innerHTML = "";

  categories.forEach((cat) => {
    const chip = document.createElement("span");
    chip.className = "badge";
    chip.style.padding = "6px 12px";
    chip.style.fontSize = "12px";
    chip.style.backgroundColor = `${cat.color}20`;
    chip.style.color = cat.color;
    chip.style.border = `1px solid ${cat.color}50`;
    chip.style.display = "inline-flex";
    chip.style.alignItems = "center";
    chip.style.gap = "8px";
    
    chip.innerHTML = `
      <span>${escapeHtml(cat.name)}</span>
      <i class="fa-solid fa-circle-xmark btn-delete-cat" data-id="${cat.id}" style="cursor:pointer; color: var(--text-muted);"></i>
    `;

    chip.querySelector(".btn-delete-cat").addEventListener("click", (e) => {
      e.stopPropagation();
      deleteCategory(cat.id);
    });

    container.appendChild(chip);
  });
}

function addNewCategoryUI() {
  const input = document.getElementById("new-cat-name");
  const name = input.value.trim();
  if (!name) return;

  // Generate random bright neon color
  const colors = ["#ff0055", "#00ccff", "#39ff14", "#ffff00", "#ff00ff", "#00f0ff", "#ff6600"];
  const color = colors[Math.floor(Math.random() * colors.length)];
  const id = `cat-${Date.now()}`;

  categories.push({ id, name, color });
  localStorage.setItem("duypt2_categories", JSON.stringify(categories));
  
  input.value = "";
  populateCategoryDropdowns();
  renderSettingsCategories();
  renderTasks();
}

function deleteCategory(id) {
  categories = categories.filter((c) => c.id !== id);
  localStorage.setItem("duypt2_categories", JSON.stringify(categories));
  populateCategoryDropdowns();
  renderSettingsCategories();
  renderTasks();
}

// --- Task Modal Operations ---
function openTaskModal(task = null, prefillDate = null) {
  const modal = document.getElementById("task-modal");
  const form = document.getElementById("task-form");
  const title = document.getElementById("modal-task-title");
  
  form.reset();
  currentEditingTaskId = null;

  // Default values
  const todayStr = new Date().toISOString().split("T")[0];
  document.getElementById("task-start-date").value = todayStr;
  document.getElementById("task-deadline-date").value = prefillDate || todayStr;
  document.getElementById("task-deadline-time").value = "23:59";
  document.getElementById("task-progress").value = "0";
  document.getElementById("progress-val-text").textContent = "0%";
  document.getElementById("progress-group").style.display = "none"; // Hide progress on new tasks

  if (task) {
    // Edit Mode
    title.textContent = "Chỉnh sửa công việc";
    currentEditingTaskId = task.id;
    document.getElementById("task-id").value = task.id;
    document.getElementById("task-title-input").value = task.title;
    document.getElementById("task-desc-input").value = task.description || "";
    document.getElementById("task-start-date").value = task.start_date || todayStr;
    document.getElementById("task-deadline-date").value = task.deadline_date;
    document.getElementById("task-deadline-time").value = task.deadline_time || "23:59";
    document.getElementById("task-priority").value = task.priority || "medium";
    document.getElementById("task-category").value = task.category_id || categories[0].id;
    document.getElementById("task-assignee").value = task.assignee || "";
    document.getElementById("task-progress").value = task.progress || 0;
    document.getElementById("progress-val-text").textContent = `${task.progress || 0}%`;
    document.getElementById("progress-group").style.display = "block"; // Show progress on edit
  } else {
    // Add Mode
    title.textContent = "Thêm công việc mới";
    document.getElementById("task-id").value = "";
  }

  modal.classList.add("active");
}

function closeModal() {
  document.getElementById("task-modal").classList.remove("active");
}

// --- Task CRUD Logic ---
function handleFormSubmit(e) {
  e.preventDefault();

  const title = document.getElementById("task-title-input").value.trim();
  const description = document.getElementById("task-desc-input").value.trim();
  const start_date = document.getElementById("task-start-date").value;
  const deadline_date = document.getElementById("task-deadline-date").value;
  const deadline_time = document.getElementById("task-deadline-time").value || "23:59";
  const priority = document.getElementById("task-priority").value;
  const category_id = document.getElementById("task-category").value;
  const assignee = document.getElementById("task-assignee").value.trim();
  
  // Progress computation
  let progress = parseInt(document.getElementById("task-progress").value);
  if (!currentEditingTaskId) {
    progress = 0; // default for new task
  }

  const taskData = {
    title,
    description,
    start_date,
    deadline_date,
    deadline_time,
    priority,
    category_id,
    assignee,
    progress,
    updated_at: new Date().toISOString()
  };

  if (currentEditingTaskId) {
    // Edit existing task
    const idx = tasks.findIndex((t) => t.id === currentEditingTaskId);
    if (idx !== -1) {
      tasks[idx] = { ...tasks[idx], ...taskData };
      saveTasksToGitHub();
    }
    closeModal();
  } else {
    // Create new task
    taskData.created_at = new Date().toISOString();
    const newTask = {
      id: `task-${Date.now()}`,
      ...taskData
    };
    tasks.push(newTask);
    saveTasksToGitHub();
    closeModal();
  }
}

function toggleTaskComplete(id, completed) {
  const progressVal = completed ? 100 : 0;
  const idx = tasks.findIndex((t) => t.id === id);
  if (idx !== -1) {
    tasks[idx].progress = progressVal;
    tasks[idx].updated_at = new Date().toISOString();
    saveTasksToGitHub();
  }
}

function deleteTask(id) {
  if (!confirm("Bạn có chắc chắn muốn xóa công việc này?")) return;

  tasks = tasks.filter((t) => t.id !== id);
  saveTasksToGitHub();
}

// --- Utilities ---
function formatDate(dateStr) {
  if (!dateStr) return "";
  const parts = dateStr.split("-");
  if (parts.length === 3) {
    return `${parts[2]}/${parts[1]}/${parts[0]}`; // DD/MM/YYYY
  }
  return dateStr;
}

function priorityLabel(priority) {
  const map = { high: "Cao", medium: "Trung bình", low: "Thấp" };
  return map[priority] || priority;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.innerText = text;
  return div.innerHTML;
}

// --- Notifications Logic ---
function checkDeadlines() {
  const now = new Date();
  let changed = false;

  tasks.forEach((task) => {
    if (task.progress >= 100) return;
    if (!task.deadline_date) return;

    const deadlineStr = `${task.deadline_date}T${task.deadline_time || "23:59"}:00`;
    const deadline = new Date(deadlineStr);
    const timeDiffMs = deadline - now;
    const totalHours = timeDiffMs / (1000 * 60 * 60);

    // Mốc 1: Quá hạn
    if (totalHours <= 0 && !task.notified_overdue) {
      addNotification("🔴 Quá hạn!", `Công việc "${task.title}" đã quá deadline!`, "danger");
      task.notified_overdue = true;
      changed = true;
    }
    // Mốc 2: Sắp đến hạn (<= 2 giờ)
    else if (totalHours > 0 && totalHours <= 2 && !task.notified_2h) {
      addNotification("⚠️ Sắp đến hạn", `Công việc "${task.title}" sắp đến hạn trong vòng 2 giờ!`, "warning");
      task.notified_2h = true;
      changed = true;
    }
  });

  if (changed) {
    saveTasksToGitHub(); // Update task flags
  }
}

function addNotification(title, message, urgency) {
  const notif = {
    id: `notif-${Date.now()}`,
    title: title,
    message: message,
    urgency: urgency,
    is_read: false,
    created_at: new Date().toISOString()
  };
  
  notifications.unshift(notif); // Add to beginning
  saveLocalNotifications();
  showBrowserNotification(title, message);
}

function showBrowserNotification(title, message) {
  if ("Notification" in window && Notification.permission === "granted") {
    new Notification(title, {
      body: message,
      icon: "assets/icon-192.png"
    });
  }
}

function updateNotificationBadge() {
  const badge = document.getElementById("nav-notification-badge");
  if (!badge) return;

  const unreadCount = notifications.filter(n => !n.is_read).length;
  if (unreadCount > 0) {
    badge.textContent = unreadCount > 99 ? "99+" : unreadCount;
    badge.style.display = "flex";
    badge.style.justifyContent = "center";
    badge.style.alignItems = "center";
  } else {
    badge.style.display = "none";
  }
}

function renderNotifications() {
  const container = document.getElementById("notifications-list");
  if (!container) return;

  container.innerHTML = "";

  if (notifications.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; color: var(--text-muted); padding: 40px;">
        <i class="fa-solid fa-bell-slash" style="font-size: 32px; margin-bottom: 15px; display: block; color: var(--border);"></i>
        Không có thông báo nào.
      </div>
    `;
    return;
  }

  notifications.forEach((notif) => {
    const card = document.createElement("div");
    card.className = `notification-card ${notif.urgency} ${notif.is_read ? "" : "unread"}`;
    
    let iconHTML = \`<i class="fa-solid fa-circle-info" style="color: var(--info); font-size: 20px;"></i>\`;
    if (notif.urgency === "warning") iconHTML = \`<i class="fa-solid fa-triangle-exclamation" style="color: var(--warning); font-size: 20px;"></i>\`;
    if (notif.urgency === "danger") iconHTML = \`<i class="fa-solid fa-circle-exclamation" style="color: var(--danger); font-size: 20px;"></i>\`;

    const timeDate = new Date(notif.created_at);
    const timeStr = \`\${String(timeDate.getHours()).padStart(2, '0')}:\${String(timeDate.getMinutes()).padStart(2, '0')} \${String(timeDate.getDate()).padStart(2, '0')}/\${String(timeDate.getMonth()+1).padStart(2, '0')}\`;

    card.innerHTML = \`
      <div style="display: flex; gap: 15px; align-items: center; flex: 1;">
        <div style="width: 30px; display: flex; justify-content: center;">
          \${iconHTML}
        </div>
        <div class="notif-content" style="flex: 1;">
          <h4>\${escapeHtml(notif.title)}</h4>
          <p>\${escapeHtml(notif.message)}</p>
          <span class="notif-time">\${timeStr}</span>
        </div>
      </div>
      <div class="notif-actions">
        \${!notif.is_read ? \`<button class="btn-mark-read" data-id="\${notif.id}"><i class="fa-solid fa-check"></i> Đã đọc</button>\` : \`<i class="fa-solid fa-check-double" style="color: var(--success); font-size: 14px;"></i>\`}
      </div>
    \`;

    if (!notif.is_read) {
      card.querySelector(".btn-mark-read").addEventListener("click", () => {
        notif.is_read = true;
        saveLocalNotifications();
      });
    }

    container.appendChild(card);
  });
}
