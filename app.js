const currencies = ["MYR", "KRW", "USD", "SGD", "JPY", "EUR", "GBP", "AUD", "CAD", "THB", "IDR", "PHP", "VND", "CNY", "INR"];
const WEB3FORMS_ACCESS_KEY = "a6512cd8-7846-472b-8394-a72bce8bc06f";

const storageKeys = {
  saved: "bounce.savedTrips",
  recent: "bounce.recentTrips"
};

const state = {
  currentTrip: null,
  listMode: "saved",
  isLoggedIn: false,
  user: null
};

const destinationInput = document.querySelector("#destination");
const heroDestinationInput = document.querySelector("#hero-destination");
const suggestionBox = document.querySelector("#destination-suggestions");
const customPlacesInput = document.querySelector("#custom-places");
const currencySelect = document.querySelector("#currency");
const tripForm = document.querySelector("#trip-form");
const resultSection = document.querySelector("#result");
const tripList = document.querySelector("#trip-list");
const savedCount = document.querySelector("#saved-count");
const recentCount = document.querySelector("#recent-count");
const budgetTip = document.querySelector("#budget-tip");
const navToggle = document.querySelector(".nav-toggle");
const toast = document.querySelector("#toast");
const adminDestinations = document.querySelector("#admin-destinations");
const adminAttractions = document.querySelector("#admin-attractions");
const feedbackForm = document.querySelector("#feedback-form");
const feedbackMessageInput = document.querySelector("#feedback-message");

function init() {
  populateCurrencies();
  applyAuthState();
  showAuthRedirectMessage();
  refreshSession();
  updateBudgetTip();
  updateAdminStats();
  updateCounts();
  renderTripList();
  bindEvents();
}

function bindEvents() {
  navToggle.addEventListener("click", () => {
    const isOpen = document.body.classList.toggle("nav-open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
  });

  document.querySelectorAll(".site-nav a").forEach((link) => {
    link.addEventListener("click", () => document.body.classList.remove("nav-open"));
  });

  document.querySelector("[data-jump-planner]").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!state.isLoggedIn) {
      openAuth("login");
      return;
    }
    if (heroDestinationInput.value.trim()) {
      destinationInput.value = heroDestinationInput.value.trim();
      updateBudgetTip();
    }
    document.querySelector("#planner").scrollIntoView({ behavior: "smooth" });
    destinationInput.focus();
  });

  destinationInput.addEventListener("input", handleDestinationInput);
  destinationInput.addEventListener("blur", () => setTimeout(() => suggestionBox.classList.remove("active"), 160));
  destinationInput.addEventListener("change", () => {
    updateBudgetTip();
  });

  tripForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!state.isLoggedIn) {
      openAuth("login");
      return;
    }
    const submitButton = tripForm.querySelector("[type='submit']");
    const originalLabel = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.textContent = "Generating...";
    resultSection.innerHTML = `
      <div class="loading-result" role="status" aria-live="polite">
        <img class="loading-logo" src="assets/bounce-logo.svg" alt="Bounce logo" />
        <p>Building your itinerary with AI...</p>
      </div>
    `;
    resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
    try {
      const trip = await buildTrip(new FormData(tripForm));
      state.currentTrip = trip;
      saveRecentTrip(trip);
      renderResult(trip);
      updateCounts();
      renderTripList();
    } catch (error) {
      const failureMessage = "Something went wrong. Please try again later.";
      resultSection.innerHTML = `<div class="empty-result"><h2>Something went wrong</h2><p>${failureMessage}</p></div>`;
      showToast(failureMessage);
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = originalLabel;
    }
  });

  tripForm.addEventListener("reset", () => {
    setTimeout(() => {
      updateBudgetTip();
    }, 0);
  });

  document.querySelector("#show-saved").addEventListener("click", () => {
    state.listMode = "saved";
    renderTripList();
  });

  document.querySelector("#show-recent").addEventListener("click", () => {
    state.listMode = "recent";
    renderTripList();
  });

  document.querySelectorAll("[data-auth-open]").forEach((button) => {
    button.addEventListener("click", () => openAuth(button.dataset.authOpen));
  });

  document.querySelectorAll("[data-auth-tab]").forEach((button) => {
    button.addEventListener("click", () => switchAuthTab(button.dataset.authTab));
  });

  document.querySelector("#login-demo").addEventListener("click", emailAuthUnavailable);
  document.querySelector("#register-demo").addEventListener("click", emailAuthUnavailable);
  document.querySelectorAll("[data-google-auth]").forEach((button) => {
    button.addEventListener("click", startGoogleAuth);
  });
  document.querySelector("#logout-button").addEventListener("click", logoutUser);
  document.querySelector("#nav-logout-button").addEventListener("click", logoutUser);

  feedbackForm.addEventListener("submit", submitFeedback);
  feedbackMessageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      feedbackForm.requestSubmit();
    }
  });
}

function populateCurrencies() {
  currencies.forEach((code) => {
    const option = document.createElement("option");
    option.value = code;
    option.textContent = code;
    if (code === "USD") option.selected = true;
    currencySelect.append(option);
  });
}

function handleDestinationInput() {
  suggestionBox.innerHTML = "";
  suggestionBox.classList.remove("active");
}

function updateBudgetTip() {
  const place = destinationInput.value.trim() || "your destination";
  budgetTip.textContent = `${place}: AI will adapt the budget to your selected style and requested places.`;
}

async function buildTrip(formData) {
  const destination = formData.get("destination").trim();
  const budget = Number(formData.get("budget"));
  const currency = formData.get("currency");
  const travelers = Number(formData.get("travelers"));
  const days = Number(formData.get("days"));
  const interests = formData.getAll("interests");
  const budgetStyle = formData.get("budgetStyle");
  const customPlaces = parseCustomPlaces(formData.get("customPlaces"));
  const tripName = formData.get("tripName").trim() || `${destination} ${days}-Day Trip`;
  const request = { destination, budget, currency, travelers, days, interests, budgetStyle, customPlaces, tripName };
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 180000);
  let response;
  try {
    response = await fetch("/api/itinerary", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal: controller.signal
    });
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("The AI planner took too long to respond. Please try fewer days or try again.");
    }
    throw new Error("The itinerary server could not be reached.");
  } finally {
    clearTimeout(timeout);
  }

  {
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const messages = {
        unauthorized: "Please log in before generating an itinerary.",
        missing_ai_config: "AI generation is not configured yet. Add the AI API key on the server.",
        ai_generation_failed: "AI could not generate the itinerary. Please try again later."
      };
      const detail = payload.detail ? ` ${payload.detail}` : "";
      throw new Error(`${messages[payload.error] || payload.error || "The itinerary server could not be reached."}${detail}`);
    }
    return normalizeGeneratedTrip(request, payload.itinerary || {});
  }
}

function parseCustomPlaces(value) {
  return [...new Set(String(value || "")
    .split(/[\n,;]+/)
    .map((place) => place.trim())
    .filter(Boolean))];
}

function normalizeGeneratedTrip(request, generated) {
  const destination = generated.destination || request.destination;
  const country = generated.country || "";
  const food = Array.isArray(generated.food) && generated.food.length
    ? generated.food.map(stringifyValue)
    : ["Local market meals", "Popular neighborhood restaurants", "Regional snacks"];
  return {
    id: crypto.randomUUID(),
    name: request.tripName,
    destination,
    country,
    budget: request.budget,
    currency: request.currency,
    travelers: request.travelers,
    days: request.days,
    interests: request.interests,
    budgetStyle: request.budgetStyle,
    customPlaces: request.customPlaces,
    summary: generated.summary || "",
    schedule: normalizeSchedule(generated.schedule, request),
    breakdown: normalizeBreakdown(generated.breakdown, request),
    transport: stringifyValue(generated.transport) || "Use local transit, walking routes, and ride-hailing where practical.",
    food,
    createdAt: new Date().toISOString()
  };
}

function normalizeSchedule(schedule, request) {
  if (!Array.isArray(schedule) || !schedule.length) {
    return Array.from({ length: request.days }, (_, index) => createFallbackDay(request, index));
  }
  const normalizedDays = schedule.slice(0, request.days).map((day, index) => {
    const sourceItems = getDayItems(day);
    const normalizedItems = sourceItems.map((item) => ({
      time: item.time || "09:00",
      title: item.title || item.activity || item.name || "Travel activity",
      notes: item.notes || item.description || item.details || "Balanced activity matched to your trip preferences.",
      cost: normalizeCost(item.cost || { raw: item["cost.raw"], label: item["cost.label"] }, request.currency)
    }));
    while (normalizedItems.length < 4) {
      normalizedItems.push(createFallbackActivity(request, index, normalizedItems.length));
    }
    const rawTotal = Number(day.total?.raw) || normalizedItems.reduce((sum, item) => sum + item.cost.raw, 0);
    return {
      day: Number(day.day) || index + 1,
      title: day.title || `Explore ${request.destination}`,
      items: normalizedItems,
      total: { raw: rawTotal, label: day.total?.label || formatMoney(rawTotal, request.currency) }
    };
  });
  while (normalizedDays.length < request.days) {
    normalizedDays.push(createFallbackDay(request, normalizedDays.length));
  }
  return normalizedDays;
}

function getDayItems(day) {
  if (Array.isArray(day.items)) return day.items;
  if (Array.isArray(day.activities)) return day.activities;
  if (Array.isArray(day.itinerary)) return day.itinerary;
  return [];
}

function createFallbackActivity(request, dayIndex, slotIndex) {
  const times = ["09:00", "13:00", "18:00", "20:00"];
  const titles = [
    `${request.destination} local breakfast and orientation`,
    `${request.destination} cultural highlight`,
    `${request.destination} food and market stop`,
    `${request.destination} evening walk`
  ];
  const raw = Math.round((request.budget / Math.max(request.days, 1)) * [0.08, 0.14, 0.16, 0.1][slotIndex]);
  return {
    time: times[slotIndex] || "09:00",
    title: `${titles[slotIndex] || titles[1]} Day ${dayIndex + 1}`,
    notes: "Fallback activity added because AI omitted this slot.",
    cost: { raw, label: formatMoney(raw, request.currency) }
  };
}

function createFallbackDay(request, dayIndex) {
  const items = [0, 1, 2, 3].map((slotIndex) => createFallbackActivity(request, dayIndex, slotIndex));
  const rawTotal = items.reduce((sum, item) => sum + item.cost.raw, 0);
  return {
    day: dayIndex + 1,
    title: `Explore ${request.destination} Day ${dayIndex + 1}`,
    items,
    total: { raw: rawTotal, label: formatMoney(rawTotal, request.currency) }
  };
}

function formatMoney(amount, currency) {
  return `${currency || ""} ${Number(amount).toLocaleString()}`.trim();
}

function createBudgetBreakdown(budget) {
  return [
    { label: "Accommodation", percent: 36, amount: budget * 0.36 },
    { label: "Food", percent: 20, amount: budget * 0.2 },
    { label: "Transportation", percent: 12, amount: budget * 0.12 },
    { label: "Activities", percent: 18, amount: budget * 0.18 },
    { label: "Buffer", percent: 14, amount: budget * 0.14 }
  ];
}

function normalizeBreakdown(breakdown, request) {
  if (breakdown && !Array.isArray(breakdown) && typeof breakdown === "object") {
    return Object.entries(breakdown).map(([label, value]) => {
      const amount = Number(value?.amount ?? value?.raw ?? value?.cost?.raw ?? value) || 0;
      return {
        label,
        percent: Number(value?.percent) || Math.round((amount / request.budget) * 100) || 0,
        amount
      };
    });
  }
  if (!Array.isArray(breakdown) || !breakdown.length) return createBudgetBreakdown(request.budget);
  return breakdown.map((item) => ({
    label: item.label || "Trip cost",
    percent: Number(item.percent) || 0,
    amount: Number(item.amount ?? item.raw ?? item.cost?.raw) || 0
  }));
}

function normalizeCost(cost, currency) {
  if (typeof cost === "number") return { raw: cost, label: formatMoney(cost, currency) };
  if (typeof cost === "string") {
    const raw = Number(cost.replace(/[^0-9.]/g, "")) || 0;
    return { raw, label: cost || formatMoney(raw, currency) };
  }
  if (!cost || typeof cost !== "object") return { raw: 0, label: formatMoney(0, currency) };
  const raw = Number(cost.raw) || 0;
  return { raw, label: cost.label || formatMoney(raw, currency) };
}

function stringifyValue(value) {
  if (!value) return "";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map(stringifyValue).filter(Boolean).join(", ");
  if (typeof value === "object") return Object.values(value).map(stringifyValue).filter(Boolean).join(" ");
  return String(value);
}

function renderResult(trip) {
  const safeName = escapeHtml(trip.name);
  const safeDestination = escapeHtml(trip.destination);
  const safeCountry = escapeHtml(trip.country);
  const locationText = safeCountry ? `${safeDestination}, ${safeCountry}` : safeDestination;
  resultSection.innerHTML = `
    <article class="result-card">
      <div class="result-header">
        <div>
          <p class="eyebrow">Generated Itinerary</p>
          <h2>${safeName}</h2>
          <p>${locationText} • ${trip.days} days • ${trip.travelers} travelers • ${escapeHtml(
    trip.budgetStyle || "Comfort"
  )} • ${formatMoney(
    trip.budget,
    trip.currency
  )}</p>
          ${trip.summary ? `<p>${escapeHtml(trip.summary)}</p>` : ""}
        </div>
        <div class="result-actions">
          <button class="secondary-button" type="button" data-action="save">Save</button>
          <button class="ghost-button" type="button" data-action="rename">Rename</button>
          <button class="ghost-button" type="button" data-action="edit">Edit</button>
          <button class="ghost-button" type="button" data-action="print">Export PDF</button>
        </div>
      </div>
      <div class="result-body">
        <div class="day-list">
          ${trip.schedule.map(renderDay).join("")}
        </div>
        <aside class="result-sidebar">
          <section class="budget-card">
            <h3>Budget Breakdown</h3>
            ${trip.breakdown
              .map(
                (item) => `
                <div class="budget-row">
                  <span>${item.label}</span>
                  <strong>${formatMoney(Math.round(item.amount), trip.currency)}</strong>
                  <div class="budget-track"><span style="width: ${item.percent}%"></span></div>
                </div>`
              )
              .join("")}
          </section>
          <section class="transport-card">
            <h3>Transportation</h3>
            <p>${escapeHtml(trip.transport)}</p>
          </section>
          <section class="transport-card">
            <h3>Food Recommendations</h3>
            <p>${trip.food.map(escapeHtml).join(", ")}</p>
          </section>
          ${
            trip.customPlaces?.length
              ? `<section class="transport-card"><h3>Requested Places</h3><p>${trip.customPlaces
                  .map(escapeHtml)
                  .join(", ")}</p></section>`
              : ""
          }
        </aside>
      </div>
    </article>
  `;

  resultSection.querySelector("[data-action='save']").addEventListener("click", () => saveTrip(trip));
  resultSection.querySelector("[data-action='rename']").addEventListener("click", () => renameTrip(trip));
  resultSection.querySelector("[data-action='edit']").addEventListener("click", () => editTrip(trip));
  resultSection.querySelector("[data-action='print']").addEventListener("click", () => window.print());
}

function renderDay(day) {
  return `
    <section class="day-card">
      <h3>Day ${day.day}: ${escapeHtml(day.title)}</h3>
      <ul>
        ${day.items
          .map(
            (item) => `
          <li>
            <span class="time">${item.time}</span>
            <span>${escapeHtml(item.title)}</span>
            <span class="cost-pill">${item.cost.label}</span>
            ${item.notes ? `<small>${escapeHtml(item.notes)}</small>` : ""}
          </li>`
          )
          .join("")}
      </ul>
      <p class="trip-meta">Estimated Cost: ${day.total.label}</p>
    </section>
  `;
}

function getStoredTrips(key) {
  try {
    return JSON.parse(localStorage.getItem(key)) || [];
  } catch {
    return [];
  }
}

function setStoredTrips(key, trips) {
  localStorage.setItem(key, JSON.stringify(trips));
}

function saveRecentTrip(trip) {
  const recent = getStoredTrips(storageKeys.recent).filter((item) => item.id !== trip.id);
  setStoredTrips(storageKeys.recent, [trip, ...recent].slice(0, 6));
}

function saveTrip(trip) {
  const saved = getStoredTrips(storageKeys.saved).filter((item) => item.id !== trip.id);
  setStoredTrips(storageKeys.saved, [trip, ...saved]);
  updateCounts();
  renderTripList();
  showToast("Itinerary saved.");
}

function renameTrip(trip) {
  const name = prompt("Rename itinerary", trip.name);
  if (!name) return;
  const renamed = { ...trip, name };
  state.currentTrip = renamed;
  saveRecentTrip(renamed);
  ["saved", "recent"].forEach((type) => {
    const key = storageKeys[type];
    const trips = getStoredTrips(key).map((item) => (item.id === trip.id ? renamed : item));
    setStoredTrips(key, trips);
  });
  renderResult(renamed);
  renderTripList();
}

function editTrip(trip) {
  document.querySelector("#destination").value = trip.destination;
  document.querySelector("#budget").value = trip.budget;
  document.querySelector("#currency").value = trip.currency;
  document.querySelector("#travelers").value = trip.travelers;
  document.querySelector("#days").value = trip.days;
  document.querySelector("#trip-name").value = trip.name;
  customPlacesInput.value = (trip.customPlaces || trip.selectedPlaces || []).join(", ");

  document.querySelectorAll("[name='interests']").forEach((checkbox) => {
    checkbox.checked = trip.interests.includes(checkbox.value);
  });

  document.querySelectorAll("[name='budgetStyle']").forEach((input) => {
    input.checked = input.value === (trip.budgetStyle || "Comfort");
  });

  document.querySelector("#planner").scrollIntoView({ behavior: "smooth" });
}

function duplicateTrip(trip) {
  const copy = {
    ...trip,
    id: crypto.randomUUID(),
    name: `${trip.name} Copy`,
    createdAt: new Date().toISOString()
  };
  saveTrip(copy);
}

function deleteTrip(tripId) {
  const key = storageKeys[state.listMode];
  setStoredTrips(
    key,
    getStoredTrips(key).filter((trip) => trip.id !== tripId)
  );
  updateCounts();
  renderTripList();
}

function updateCounts() {
  savedCount.textContent = getStoredTrips(storageKeys.saved).length;
  recentCount.textContent = getStoredTrips(storageKeys.recent).length;
}

function renderTripList() {
  const key = storageKeys[state.listMode];
  const trips = getStoredTrips(key);
  document.querySelector("#show-saved").className = state.listMode === "saved" ? "secondary-button" : "ghost-button";
  document.querySelector("#show-recent").className = state.listMode === "recent" ? "secondary-button" : "ghost-button";

  if (!trips.length) {
    tripList.innerHTML = `<div class="empty-result"><h3>No ${escapeHtml(
      state.listMode
    )} trips yet</h3><p>Generate an itinerary and save it to build your history.</p></div>`;
    return;
  }

  tripList.innerHTML = trips
    .map(
      (trip) => `
      <article class="trip-card">
        <h3>${escapeHtml(trip.name)}</h3>
        <p class="trip-meta">${escapeHtml(trip.destination)} • ${trip.days} days • ${formatMoney(
        trip.budget,
        trip.currency
      )}</p>
        <div class="trip-actions">
          <button type="button" data-trip-action="view" data-id="${trip.id}">View</button>
          <button type="button" data-trip-action="rename" data-id="${trip.id}">Rename</button>
          <button type="button" data-trip-action="duplicate" data-id="${trip.id}">Duplicate</button>
          <button type="button" data-trip-action="delete" data-id="${trip.id}">Delete</button>
        </div>
      </article>`
    )
    .join("");

  tripList.querySelectorAll("[data-trip-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const trip = trips.find((item) => item.id === button.dataset.id);
      if (!trip) return;
      if (button.dataset.tripAction === "view") {
        state.currentTrip = trip;
        renderResult(trip);
        resultSection.scrollIntoView({ behavior: "smooth" });
      }
      if (button.dataset.tripAction === "rename") renameTrip(trip);
      if (button.dataset.tripAction === "duplicate") duplicateTrip(trip);
      if (button.dataset.tripAction === "delete") deleteTrip(trip.id);
    });
  });
}

function openAuth(tab) {
  switchAuthTab(tab);
  document.querySelector("#auth-dialog").showModal();
}

function closeAuthDialog() {
  document.querySelector("#auth-dialog").close();
}

function startGoogleAuth() {
  window.location.href = "/auth/google";
}

function emailAuthUnavailable() {
  showToast("Email login is not enabled yet. Use Google OAuth to continue.");
}

async function refreshSession(showSuccess = false) {
  try {
    const response = await fetch("/api/session", { credentials: "same-origin" });
    const session = await response.json();
    state.isLoggedIn = Boolean(session.authenticated);
    state.user = session.user || null;
    applyAuthState();
    if (state.isLoggedIn && showSuccess) {
      showToast(`Welcome, ${state.user.fullName}. Google authentication completed.`);
    }
  } catch {
    state.isLoggedIn = false;
    state.user = null;
    applyAuthState();
    showToast("Could not verify your session. Please try signing in again.");
  }
}

async function logoutUser() {
  try {
    await fetch("/auth/logout", {
      method: "POST",
      credentials: "same-origin"
    });
  } catch {
    showToast("Logout could not reach the server, but this browser view was locked.");
  }
  state.isLoggedIn = false;
  state.user = null;
  applyAuthState();
  showToast("Logged out. Planner and saved trips are hidden.");
  document.querySelector("#home").scrollIntoView({ behavior: "smooth" });
}

function switchAuthTab(tab) {
  document.querySelectorAll(".auth-tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.authTab === tab);
  });
  document.querySelector("#login-pane").classList.toggle("active", tab === "login");
  document.querySelector("#register-pane").classList.toggle("active", tab === "register");
}

function applyAuthState() {
  document.body.classList.toggle("logged-in", state.isLoggedIn);
  document.body.classList.toggle("logged-out", !state.isLoggedIn);
}

function showAuthRedirectMessage() {
  const params = new URLSearchParams(window.location.search);
  const error = params.get("auth_error");
  const success = params.get("auth") === "success";
  const messages = {
    missing_google_config:
      "Google OAuth is not configured yet. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET on the server.",
    google_cancelled: "Google sign-in was cancelled. No account was created and no session was started.",
    invalid_oauth_state: "Google sign-in could not be verified. Please try again.",
    google_auth_failed: "Google authentication failed. No session was created."
  };

  if (error) {
    showToast(messages[error] || "Google authentication failed. Please try again.");
    window.history.replaceState({}, "", window.location.pathname + window.location.hash);
  }

  if (success) {
    refreshSession(true);
    window.history.replaceState({}, "", window.location.pathname + window.location.hash);
  }
}

function updateAdminStats() {
  adminDestinations.textContent = "AI";
  adminAttractions.textContent = "Live";
}

async function submitFeedback(event) {
  event.preventDefault();
  const message = feedbackMessageInput.value.trim();
  if (message.length < 5) {
    showToast("Please write a little more feedback before sending.");
    feedbackMessageInput.focus();
    return;
  }

  if (!WEB3FORMS_ACCESS_KEY || WEB3FORMS_ACCESS_KEY.includes("PASTE_")) {
    showToast("Feedback form is not configured yet. Add your Web3Forms access key.");
    return;
  }

  const submitButton = feedbackForm.querySelector("[type='submit']");
  const originalLabel = submitButton.textContent;
  submitButton.disabled = true;
  submitButton.textContent = "Sending...";

  try {
    const response = await fetch("https://api.web3forms.com/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        access_key: WEB3FORMS_ACCESS_KEY,
        subject: "Bounce customer feedback",
        from_name: state.user?.fullName || "Bounce user",
        name: state.user?.fullName || "Bounce user",
        email: state.user?.email || "bouncebtoe@gmail.com",
        message,
        page_url: window.location.href,
        botcheck: false
      })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload.success === false) {
      if (response.status === 429) {
        throw new Error("Too many feedback submissions. Please try again later.");
      }
      throw new Error(payload.message || "Bounce could not send the feedback email.");
    }

    feedbackForm.reset();
    showToast("Thanks. Your feedback was sent to Bounce.");
  } catch (error) {
    showToast(error.message || "Bounce could not send the feedback email.");
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = originalLabel;
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    };
    return entities[character];
  });
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("active");
  clearTimeout(showToast.timeout);
  showToast.timeout = setTimeout(() => toast.classList.remove("active"), 2600);
}

init();

