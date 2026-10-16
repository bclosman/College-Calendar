"use strict";

(() => {
  const $ = (id) => document.getElementById(id);
  const palette = ["#527f9b", "#8c72a7", "#5e8971", "#b58a3e", "#ae6a6d", "#638d92", "#9a795e", "#777fb0"];
  const coursePalette = ["#2e7dac", "#8757ad", "#38825b", "#b87917", "#b84b60", "#2e8591", "#a56c38", "#5f67af"];
  const state = { calendars: [], assignments: [], events: [], hidden: new Set(), assignmentColors: {}, timezone: Intl.DateTimeFormat().resolvedOptions().timeZone, month: new Date(), selected: null, view: "upcoming", loaded: false, busy: false };
  let dayFormatter;

  function configureDates() {
    dayFormatter = new Intl.DateTimeFormat("en-US", { timeZone: state.timezone, year: "numeric", month: "2-digit", day: "2-digit" });
  }
  configureDates();
  function keyOf(date) {
    const parts = Object.fromEntries(dayFormatter.formatToParts(date).map((part) => [part.type, part.value]));
    return `${parts.year}-${parts.month}-${parts.day}`;
  }
  function localKey(date) { return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`; }
  function calendarDate(key) { const [y, m, d] = key.split("-").map(Number); return new Date(y, m - 1, d, 12); }
  function addDays(key, count) { const date = calendarDate(key); date.setDate(date.getDate() + count); return localKey(date); }
  function dateOnly(value) { return typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value); }
  function parsed(value) {
    if (!value) return null;
    const date = new Date(String(value).replace(" ", "T"));
    return Number.isNaN(date.getTime()) ? null : date;
  }
  function dateKey(value) { return dateOnly(value) ? value : parsed(value) ? keyOf(parsed(value)) : null; }
  function clock(value, options = {}) {
    const date = parsed(value);
    return date ? new Intl.DateTimeFormat("en-US", { timeZone: state.timezone, hour: "numeric", minute: "2-digit", ...options }).format(date) : "";
  }
  function sortKey(value) {
    if (dateOnly(value)) return `${value}T23:59:59`;
    const date = parsed(value);
    if (!date) return "";
    return keyOf(date) + "T" + new Intl.DateTimeFormat("en-GB", { timeZone: state.timezone, hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23" }).format(date);
  }
  function labelDate(key, long = false) { return calendarDate(key).toLocaleDateString("en-US", { weekday: long ? "long" : "short", month: long ? "long" : "short", day: "numeric" }); }
  function colorFor(name, configured, colors = palette) {
    if (/^#[0-9a-f]{6}$/i.test(configured || "")) return configured;
    let hash = 0;
    for (const char of String(name)) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
    return colors[hash % colors.length];
  }
  function colorElement(element, color) {
    element.style.setProperty("--color", color);
    element.style.setProperty("--tint", color + "60");
    const channels = [1, 3, 5].map((offset) => parseInt(color.slice(offset, offset + 2), 16));
    const textColor = "#" + channels.map((channel) => Math.round(channel * 0.5).toString(16).padStart(2, "0")).join("");
    element.style.setProperty("--color-text", textColor);

  }
  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function safeLink(value) {
    try { const url = new URL(value); return ["http:", "https:"].includes(url.protocol) ? url.href : null; }
    catch { return null; }
  }
  function calendarColor(name) { return colorFor(name, state.calendars.find((c) => c.name === name)?.color); }
  function courseKey(assignment) { return String(assignment.course_code || assignment.course_name || "Other"); }
  function assignmentColor(assignment) { return colorFor(courseKey(assignment), state.assignmentColors[courseKey(assignment)], coursePalette); }

  function assignmentForEvent(event) {
    if (String(event.calendar).toLowerCase() !== "canvas") return null;
    const reference = `${event.uid || ""} ${event.url || ""}`;
    const id = reference.match(/assignment(?:s\/|_)(\d+)/i)?.[1];
    const assignment = id && state.assignments.find((item) => String(item.id) === id);
    if (assignment) return assignment;
    // Completed assignments may no longer appear in the unsubmitted sidebar.
    const course = String(event.name || "").match(/\b([A-Z]+-\d+\.\d+\.\d+)\b/);
    return course && (id || /assignment/i.test(reference)) ? { course_code: course[1] } : null;
  }
  function eventColor(event) {
    const assignment = assignmentForEvent(event);
    return assignment ? assignmentColor(assignment) : calendarColor(event.calendar);
  }
  function compactAssignment(event) { return Boolean(assignmentForEvent(event)) && dateOnly(event.start); }
  function visibleEventsCount(events, available, expanded, small) {
    const height = (event) => compactAssignment(event) ? (small ? 20 : 23) : expanded ? (small ? 34 : 49) : (small ? 16 : 20);
    if (events.reduce((sum, event) => sum + height(event), 0) <= available) return events.length;
    const budget = Math.max(0, available - (small ? 13 : 16));
    let used = 0, count = 0;
    for (const event of events) {
      if (used + height(event) > budget) break;
      used += height(event);
      count++;
    }
    return count;
  }

  async function request(url) {
    const response = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(15000) });
    if (!response.ok) {
      const error = new Error(`Unable to load ${url.split("?")[0].split("/").pop()} (${response.status}).`);
      try {
        const body = await response.json();
        error.code = body.detail?.code;
      } catch { /* Non-JSON server errors keep the general error message. */ }
      throw error;
    }
    return response.json();
  }
  async function fetchRows(path) {
    const rows = [];
    for (let offset = 0; ; offset += 500) {
      const page = await request(`${path}${path.includes("?") ? "&" : "?"}limit=500&offset=${offset}`);
      if (!Array.isArray(page)) throw new Error("The server returned an unexpected response.");
      rows.push(...page);
      if (page.length < 500) return rows;
    }
  }
  async function loadCalendarConfig() {
    try {
      return await request("/api/calendars");
    } catch (error) {
      if (error.code !== "calendar_config_missing") throw error;
      return {
        calendars: [...state.calendars],
        assignment_colors: state.assignmentColors,
        timezone: state.timezone,
        warning: "calendars.json was not found. Showing stored events and assignments with saved or default colors. Restore the file in the project folder to resume calendar syncing. The dashboard will check again in five minutes; reload to check sooner."
      };
    }
  }
  async function loadData() {
    if (state.busy) return;
    state.busy = true;
    $("sync-status").textContent = "Updating…";
    try {
      const [config, assignments, events] = await Promise.all([loadCalendarConfig(), fetchRows("/api/assignments?submitted=false"), fetchRows("/api/events")]);
      state.calendars = config.calendars;
      state.assignmentColors = config.assignment_colors || {};
      state.timezone = config.timezone || state.timezone;
      configureDates();
      if (!state.loaded) state.month = calendarDate(keyOf(new Date()));
      state.assignments = assignments.filter((a) => dateKey(a.due_at));
      state.events = events.filter((e) => dateKey(e.start));
      for (const name of new Set(state.events.map((event) => event.calendar))) {
        if (!state.calendars.some((calendar) => calendar.name === name)) state.calendars.push({ name, color: colorFor(name) });
      }
      state.loaded = true;
      $("error").textContent = config.warning || "";
      $("error").hidden = !config.warning;
      $("calendar-loading").hidden = true;
      renderFilters(); renderCourses(); renderCalendar(); renderAssignments();
      $("sync-status").textContent = "Updated " + new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
    } catch (error) {
      $("error").textContent = `${error.message} ${state.loaded ? "Showing the last successful update." : "Check that the API is running."} The dashboard will retry in five minutes. Reload the page to try sooner.`;
      $("error").hidden = false;
      $("sync-status").textContent = "Update failed";
      if (!state.loaded) { $("calendar-loading").textContent = "Calendar unavailable"; $("assignment-list").replaceChildren(element("p", "empty", "Assignments could not be loaded.")); }
    } finally { state.busy = false; }
  }

  function renderFilters() {
    $("calendar-filters").replaceChildren();
    for (const calendar of state.calendars) {
      const label = element("label", "calendar-toggle");
      colorElement(label, calendarColor(calendar.name));
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = !state.hidden.has(calendar.name);
      checkbox.addEventListener("change", () => { checkbox.checked ? state.hidden.delete(calendar.name) : state.hidden.add(calendar.name); renderCalendar(); });
      label.append(checkbox, document.createTextNode(calendar.name));
      $("calendar-filters").append(label);
    }
  }
  function renderCourses() {
    const previous = $("course").value;
    const courses = new Map(state.assignments.map((a) => [courseKey(a), a.course_name || courseKey(a)]));
    $("course").replaceChildren(new Option("All courses", ""));
    for (const [key, name] of [...courses].sort((a, b) => a[1].localeCompare(b[1]))) $("course").add(new Option(name, key));
    if (courses.has(previous)) $("course").value = previous;
  }
  function eventsOn(key) {
    return state.events.filter((event) => {
      if (state.hidden.has(event.calendar)) return false;
      const start = dateKey(event.start);
      const end = dateKey(event.end) || start;
      if (dateOnly(event.start) && event.end) return start <= key && key < end;
      // Timed events ending at midnight do not occupy the following day.
      const effectiveEnd = event.end && !dateOnly(event.end) && parsed(event.end) ? keyOf(new Date(parsed(event.end).getTime() - 1)) : end;
      return start <= key && key <= (effectiveEnd < start ? start : effectiveEnd);
    }).sort((a, b) => Number(!dateOnly(a.start)) - Number(!dateOnly(b.start)) || sortKey(a.start).localeCompare(sortKey(b.start)));
  }
  function calendarLayout(year, month, today, selected) {
    const first = new Date(year, month, 1, 12);
    const rows = Math.ceil((first.getDay() + new Date(year, month + 1, 0).getDate()) / 7);
    first.setDate(first.getDate() - first.getDay());
    const start = localKey(first), end = addDays(start, rows * 7);
    const focus = selected && selected >= start && selected < end ? selected : today;
    let focusWeek = -1;
    for (let row = 0; row < rows; row++) {
      if (focus >= addDays(start, row * 7) && focus < addDays(start, (row + 1) * 7)) focusWeek = row;
    }
    return { first, rows, focusWeek };
  }
  function renderCalendar() {
    const year = state.month.getFullYear(), month = state.month.getMonth();
    $("month-label").textContent = state.month.toLocaleDateString("en-US", { month: "long", year: "numeric" });
    $("calendar-grid").setAttribute("aria-label", $("month-label").textContent);
    $("calendar-grid").replaceChildren();
    const today = keyOf(new Date());
    const { first, rows, focusWeek } = calendarLayout(year, month, today, state.selected);
    const weights = Array.from({ length: rows }, (_, row) => row === focusWeek ? 2.8 : 1);
    $("calendar-grid").style.gridTemplateRows = weights.map((weight) => `minmax(0, ${weight}fr)`).join(" ");
    const gridHeight = $("calendar-grid").clientHeight;
    const small = window.matchMedia("(max-width: 760px)").matches;
    const totalWeight = weights.reduce((sum, weight) => sum + weight, 0);
    const monthStart = localKey(new Date(year, month, 1));
    const monthEnd = localKey(new Date(year, month + 1, 1));
    const monthEvents = state.events.filter((e) => !state.hidden.has(e.calendar) && dateKey(e.start) < monthEnd && (dateKey(e.end) || dateKey(e.start)) >= monthStart);
    $("month-count").textContent = `${monthEvents.length} event${monthEvents.length === 1 ? "" : "s"}`;
    for (let i = 0; i < rows * 7; i++) {
      const date = new Date(first); date.setDate(first.getDate() + i);
      const key = localKey(date);
      const expanded = Math.floor(i / 7) === focusWeek;
      const cell = element("div", "day-cell" + (expanded ? " focus-week" : "") + (date.getMonth() !== month ? " outside" : "") + (key === today ? " is-today" : "") + (key === state.selected ? " selected" : ""));
      cell.setAttribute("role", "gridcell");
      cell.setAttribute("aria-selected", String(key === state.selected));
      const top = element("div", "day-top");
      const number = element("button", "day-number", date.getDate());
      number.setAttribute("aria-label", `Filter assignments for ${labelDate(key, true)}`);
      if (key === today) number.setAttribute("aria-current", "date");
      number.addEventListener("click", () => { state.selected = state.selected === key ? null : key; renderCalendar(); renderAssignments(); });
      top.append(number); cell.append(top);
      const events = eventsOn(key);
      const rowHeight = gridHeight * weights[Math.floor(i / 7)] / totalWeight;
      const topHeight = small ? 23 : 34;
      const compressed = rowHeight < topHeight + (small ? 13 : 16);
      if (compressed) cell.classList.add("compact-day");
      const available = Math.max(0, rowHeight - topHeight);
      const visibleCount = visibleEventsCount(events, available, expanded, small);
      const eventList = element("div", "day-events");
      cell.append(eventList);
      for (const event of events.slice(0, visibleCount)) {
        const compact = compactAssignment(event);
        const button = element("button", "event" + (compact ? " all-day-assignment" : ""));
        colorElement(button, eventColor(event));
        if (!dateOnly(event.start) && dateKey(event.start) === key) button.append(element("span", "event-time", clock(event.start).replace(":00", "").replace(" ", "")));
        if (expanded && dateOnly(event.start) && !compact) button.append(element("span", "event-time", "All day"));
        button.append(element("span", "event-title", event.name || "Untitled event"));
        button.title = `${event.calendar}: ${event.name || "Untitled event"}`;
        button.addEventListener("click", () => showEvent(event));
        eventList.append(button);
      }
      if (events.length > visibleCount) {
        const more = element("button", "more", compressed ? String(events.length) : `+${events.length - visibleCount} more`);
        more.setAttribute("aria-label", `View all ${events.length} events for ${labelDate(key, true)}`);
        more.addEventListener("click", () => showDay(key, events));
        if (compressed) top.insertBefore(more, number);
        else cell.append(more);
      }
      $("calendar-grid").append(cell);
    }
    $("clear-day").hidden = !state.selected;
  }
  function eventDescription(event) {
    const start = dateKey(event.start), end = dateKey(event.end);
    if (dateOnly(event.start)) return `${labelDate(start, true)}${end && end > addDays(start, 1) ? " – " + labelDate(addDays(end, -1), true) : ""} · All day`;
    return `${labelDate(start, true)} · ${clock(event.start)}${event.end ? " – " + (end !== start ? labelDate(end) + " " : "") + clock(event.end) : ""} (${state.timezone})`;
  }
  function resetDialog() { $("event-dialog").querySelector(".dialog-event-list")?.remove(); $("event-link").hidden = true; }
  function showEvent(event) {
    resetDialog();
    $("event-calendar").textContent = event.calendar;
    $("event-calendar").style.color = eventColor(event);
    $("event-title").textContent = event.name || "Untitled event";
    $("event-time").textContent = eventDescription(event);
    const url = safeLink(event.url);
    if (url) { $("event-link").href = url; $("event-link").hidden = false; }
    if (!$("event-dialog").open) $("event-dialog").showModal();
  }
  function showDay(key, events) {
    resetDialog();
    $("event-calendar").textContent = "YOUR DAY";
    $("event-calendar").style.color = "";
    $("event-title").textContent = labelDate(key, true);
    $("event-time").textContent = `${events.length} events`;
    const list = element("div", "dialog-event-list");
    for (const event of events) {
      const button = element("button", "day-event");
      colorElement(button, eventColor(event));
      button.append(
        element("span", "day-event-time", dateOnly(event.start) ? "All day" : clock(event.start)),
        element("span", "day-event-title", event.name || "Untitled event"),
        element("span", "day-event-source", event.calendar)
      );
      button.addEventListener("click", () => showEvent(event));
      list.append(button);
    }
    $("event-dialog").append(list);
    $("event-dialog").showModal();
  }

  function renderAssignments() {
    const today = keyOf(new Date()), now = sortKey(new Date().toISOString());
    const search = $("search").value.trim().toLowerCase(), course = $("course").value;
    const rows = state.assignments.filter((a) => {
      const due = sortKey(a.due_at), key = dateKey(a.due_at);
      return (!course || courseKey(a) === course) && (!state.selected || key === state.selected) && (!search || `${a.name} ${a.course_name} ${a.course_code}`.toLowerCase().includes(search)) && (state.view === "all" || (state.view === "upcoming" ? due >= now : due < now));
    }).sort((a, b) => sortKey(a.due_at).localeCompare(sortKey(b.due_at)));
    $("assignment-count").textContent = rows.length;
    $("selected-date").hidden = !state.selected;
    $("selected-date").textContent = state.selected ? `Showing ${labelDate(state.selected)}` : "";
    $("assignment-list").replaceChildren();
    if (!rows.length) { $("assignment-list").append(element("p", "empty", state.assignments.length ? "No assignments match this view. Try another date or filter." : "You’re all caught up. No unsubmitted assignments to show.")); return; }
    let previousDay;
    for (const assignment of rows) {
      const key = dateKey(assignment.due_at), overdue = sortKey(assignment.due_at) < now;
      if (key !== previousDay) {
        const label = key === today ? "Today" : key === addDays(today, 1) ? "Tomorrow" : labelDate(key);
        const heading = element("h3", "group-title", label);
        heading.append(element("span", "", calendarDate(key).toLocaleDateString("en-US", { month: "short", day: "numeric" })));
        $("assignment-list").append(heading); previousDay = key;
      }
      const card = element("article", "assignment-card"); colorElement(card, assignmentColor(assignment));
      const top = element("div", "card-top");
      top.append(element("span", "course-badge", assignment.course_name || courseKey(assignment)), element("span", "due-status" + (overdue ? " late" : key === today ? " urgent" : ""), overdue ? "Overdue" : key === today ? "Due today" : key === addDays(today, 1) ? "Tomorrow" : "Upcoming"));
      const title = element("h4", "assignment-name");
      const url = safeLink(assignment.url);
      if (url) { const link = element("a", "", assignment.name); link.href = url; link.target = "_blank"; link.rel = "noopener noreferrer"; title.append(link); }
      else title.textContent = assignment.name;
      const bottom = element("div", "card-bottom");
      bottom.append(element("span", "", `◷ ${dateOnly(assignment.due_at) ? "11:59 PM · No time listed" : clock(assignment.due_at)}`));
      if (url) { const link = element("a", "assignment-link", "↗"); link.href = url; link.target = "_blank"; link.rel = "noopener noreferrer"; link.setAttribute("aria-label", `Open ${assignment.name}`); bottom.append(link); }
      card.append(top, title, bottom); $("assignment-list").append(card);
    }
  }

  async function toggleFullscreen() {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch {
      $("sync-status").textContent = "Fullscreen is unavailable in this browser view. Use the browser's fullscreen menu.";
    }
  }
  function handleFullscreenKey(event) {
    if (event.repeat) return;
    if (event.key === "F11" && (document.fullscreenElement || document.fullscreenEnabled)) {
      event.preventDefault();
      void toggleFullscreen();
    } else if (event.key === "Escape" && document.fullscreenElement) {
      event.preventDefault();
      void toggleFullscreen();
    }
  }

  function setupThemeToggle() {
    const button = $("theme-toggle");
    const applyTheme = (dark) => {
      document.documentElement.dataset.theme = dark ? "dark" : "light";
      button.textContent = dark ? "☀" : "☾";
      button.setAttribute("aria-pressed", String(dark));
      button.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
      button.title = button.getAttribute("aria-label");
    };
    applyTheme(document.documentElement.dataset.theme === "dark");
    button.addEventListener("click", () => {
      const dark = document.documentElement.dataset.theme !== "dark";
      applyTheme(dark);
      try { localStorage.setItem("college-calendar-theme", dark ? "dark" : "light"); }
      catch { /* The toggle still works if browser storage is unavailable. */ }
    });
  }

  function setupIdleCursor() {
    let idleTimer;
    const showCursor = () => {
      clearTimeout(idleTimer);
      document.documentElement.classList.remove("cursor-idle");
    };
    const resetCursor = () => {
      showCursor();
      idleTimer = setTimeout(() => document.documentElement.classList.add("cursor-idle"), 3000);
    };
    document.addEventListener("pointermove", resetCursor, { passive: true });
    document.addEventListener("pointerdown", resetCursor, { passive: true });
    document.addEventListener("keydown", resetCursor);
    document.addEventListener("wheel", resetCursor, { passive: true });
    window.addEventListener("blur", showCursor);
    window.addEventListener("focus", resetCursor);
    resetCursor();
  }

  $("previous").addEventListener("click", () => { state.month = new Date(state.month.getFullYear(), state.month.getMonth() - 1, 1, 12); renderCalendar(); });
  $("next").addEventListener("click", () => { state.month = new Date(state.month.getFullYear(), state.month.getMonth() + 1, 1, 12); renderCalendar(); });
  $("today").addEventListener("click", () => { state.month = calendarDate(keyOf(new Date())); state.selected = null; renderCalendar(); renderAssignments(); });
  $("clear-day").addEventListener("click", () => { state.selected = null; renderCalendar(); renderAssignments(); });
  $("search").addEventListener("input", renderAssignments);
  $("course").addEventListener("change", renderAssignments);
  document.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => { state.view = button.dataset.view; document.querySelectorAll("[data-view]").forEach((tab) => tab.setAttribute("aria-pressed", String(tab === button))); renderAssignments(); }));
  $("close-dialog").addEventListener("click", () => $("event-dialog").close());
  document.addEventListener("keydown", handleFullscreenKey);
  let resizeFrame;
  new ResizeObserver(() => {
    cancelAnimationFrame(resizeFrame);
    resizeFrame = requestAnimationFrame(renderCalendar);
  }).observe($("calendar-grid"));

  setupThemeToggle();
  setupIdleCursor();
  renderCalendar();
  loadData();
  setInterval(() => { if (state.loaded) { renderCalendar(); renderAssignments(); } loadData(); }, 5 * 60 * 1000);
})();
