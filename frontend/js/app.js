/**
 * JobScout frontend: search, list, detail pane, client-side filters.
 * Job text is always set with textContent — never innerHTML.
 */

const PAGE_SIZE = 10;
const STORAGE_KEY = "jobscout:lastSearch";

const els = {
  form: document.getElementById("search-form"),
  keyword: document.getElementById("keyword"),
  country: document.getElementById("country"),
  city: document.getElementById("city"),
  findBtn: document.getElementById("find-btn"),
  formError: document.getElementById("form-error"),
  status: document.getElementById("status"),
  resultsSection: document.getElementById("results-section"),
  jobList: document.getElementById("job-list"),
  resultCount: document.getElementById("result-count"),
  filterDate: document.getElementById("filter-date"),
  filterType: document.getElementById("filter-type"),
  filterSource: document.getElementById("filter-source"),
  sort: document.getElementById("sort"),
  clearFilters: document.getElementById("clear-filters"),
  pagination: document.getElementById("pagination"),
  prevPage: document.getElementById("prev-page"),
  nextPage: document.getElementById("next-page"),
  pageInfo: document.getElementById("page-info"),
  detailEmpty: document.getElementById("detail-empty"),
  detailContent: document.getElementById("detail-content"),
  backBtn: document.getElementById("back-btn"),
};

const state = {
  jobs: [],
  selectedId: null,
  page: 1,
  lastQuery: null,
};

function setFormError(message) {
  els.formError.hidden = !message;
  els.formError.textContent = message || "";
}

function setStatus(message) {
  els.status.textContent = message || "";
}

function prettyJobType(value) {
  return String(value || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (ch) => ch.toUpperCase())
    .trim() || "Unknown";
}

function postedLabel(postedAt) {
  if (!postedAt || postedAt === "Unknown") {
    return "Posted date unknown";
  }
  const posted = Date.parse(postedAt + "T00:00:00");
  if (Number.isNaN(posted)) {
    return "Posted date unknown";
  }
  const days = Math.floor((Date.now() - posted) / (1000 * 60 * 60 * 24));
  if (days <= 0) return "Posted today";
  if (days === 1) return "Posted 1 day ago";
  return `Posted ${days} days ago`;
}

function isWithinDays(postedAt, days) {
  if (!postedAt || postedAt === "Unknown") return false;
  const posted = Date.parse(postedAt + "T00:00:00");
  if (Number.isNaN(posted)) return false;
  return Date.now() - posted <= days * 24 * 60 * 60 * 1000;
}

function filtersAreActive() {
  return (
    els.filterDate.value !== "any" ||
    els.filterType.value !== "all" ||
    els.filterSource.value !== "all" ||
    els.sort.value !== "relevance"
  );
}

function filteredJobs() {
  const dateDays = els.filterDate.value;
  const type = els.filterType.value;
  const source = els.filterSource.value;
  const sort = els.sort.value;

  let jobs = state.jobs.filter((job) => {
    if (dateDays !== "any" && !isWithinDays(job.posted_at, Number(dateDays))) {
      return false;
    }
    if (source !== "all" && job.source !== source) {
      return false;
    }
    if (type !== "all") {
      const types = job.job_types || [];
      if (!types.includes(type)) return false;
    }
    return true;
  });

  if (sort === "date") {
    jobs = jobs.slice().sort((a, b) => {
      const aUnknown = !a.posted_at || a.posted_at === "Unknown";
      const bUnknown = !b.posted_at || b.posted_at === "Unknown";
      if (aUnknown && bUnknown) return a._index - b._index;
      if (aUnknown) return 1;
      if (bUnknown) return -1;
      return String(b.posted_at).localeCompare(String(a.posted_at));
    });
  }

  return jobs;
}

function pageSlice(jobs) {
  const start = (state.page - 1) * PAGE_SIZE;
  return jobs.slice(start, start + PAGE_SIZE);
}

function createEl(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function showSkeletons() {
  els.resultsSection.hidden = false;
  els.jobList.replaceChildren();
  for (let i = 0; i < 4; i += 1) {
    els.jobList.appendChild(createEl("div", "skeleton"));
  }
  els.pagination.hidden = true;
  els.detailEmpty.hidden = false;
  els.detailContent.hidden = true;
  els.detailContent.replaceChildren();
  document.body.classList.remove("detail-open");
}

function rebuildFilterOptions(jobs) {
  const sources = [...new Set(jobs.map((j) => j.source).filter(Boolean))].sort();
  const types = [...new Set(jobs.flatMap((j) => j.job_types || []).filter(Boolean))].sort();

  const typeSelect = els.filterType;
  const sourceSelect = els.filterSource;
  const prevType = typeSelect.value;
  const prevSource = sourceSelect.value;

  typeSelect.replaceChildren(new Option("All types", "all"));
  types.forEach((t) => typeSelect.appendChild(new Option(prettyJobType(t), t)));
  sourceSelect.replaceChildren(new Option("All sources", "all"));
  sources.forEach((s) => sourceSelect.appendChild(new Option(s, s)));

  typeSelect.value = types.includes(prevType) ? prevType : "all";
  sourceSelect.value = sources.includes(prevSource) ? prevSource : "all";
}

function renderDetail(job) {
  els.detailEmpty.hidden = !!job;
  els.detailContent.hidden = !job;
  els.detailContent.replaceChildren();
  if (!job) return;

  const title = createEl("h2", "detail-title", job.title || "Untitled job");
  const company = createEl("p", "detail-company", job.company || "");
  const location = createEl("p", "detail-location", job.location || "");
  const posted = createEl("p", "detail-posted", postedLabel(job.posted_at));

  const badges = createEl("div", "type-badges");
  (job.job_types || []).forEach((t) => {
    if (t) badges.appendChild(createEl("span", "badge", prettyJobType(t)));
  });
  if (job.source) badges.appendChild(createEl("span", "badge", job.source));

  const apply = document.createElement("a");
  apply.className = "apply-btn";
  apply.textContent = "Apply now";
  apply.href = job.url || "#";
  apply.target = "_blank";
  apply.rel = "noopener noreferrer";

  const description = createEl("p", "detail-description", job.description || "No description provided.");

  els.detailContent.append(title, company, location, posted, badges, apply, description);
}

function renderList() {
  const jobs = filteredJobs();
  const totalPages = Math.max(1, Math.ceil(jobs.length / PAGE_SIZE));
  if (state.page > totalPages) state.page = totalPages;

  const pageJobs = pageSlice(jobs);
  els.clearFilters.hidden = !filtersAreActive();
  els.resultCount.textContent = `${jobs.length} job${jobs.length === 1 ? "" : "s"} found`;

  els.jobList.replaceChildren();

  if (state.jobs.length === 0) {
    const empty = createEl("div", "empty-state", "No jobs found, try different keywords.");
    els.jobList.appendChild(empty);
    renderDetail(null);
    els.pagination.hidden = true;
    return;
  }

  if (jobs.length === 0) {
    const empty = createEl("div", "empty-state", "No jobs match these filters.");
    els.jobList.appendChild(empty);
    renderDetail(null);
    els.pagination.hidden = true;
    return;
  }

  if (!pageJobs.some((j) => j.id === state.selectedId)) {
    state.selectedId = pageJobs[0].id;
  }

  pageJobs.forEach((job) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "job-card" + (job.id === state.selectedId ? " selected" : "");
    card.setAttribute("role", "option");
    card.setAttribute("aria-selected", job.id === state.selectedId ? "true" : "false");
    card.dataset.id = job.id;

    card.appendChild(createEl("h3", "job-title", job.title || "Untitled job"));
    card.appendChild(createEl("p", "job-meta", job.company || ""));
    card.appendChild(createEl("p", "job-meta", job.location || ""));
    if (job.source) card.appendChild(createEl("span", "badge", job.source));
    card.appendChild(createEl("p", "job-snippet", job.snippet || ""));
    card.appendChild(createEl("p", "job-posted", postedLabel(job.posted_at)));

    card.addEventListener("click", () => selectJob(job.id, true));
    els.jobList.appendChild(card);
  });

  const selected = jobs.find((j) => j.id === state.selectedId) || pageJobs[0];
  renderDetail(selected);

  const showPager = jobs.length > PAGE_SIZE;
  els.pagination.hidden = !showPager;
  els.prevPage.disabled = state.page <= 1;
  els.nextPage.disabled = state.page >= totalPages;
  els.pageInfo.textContent = `Page ${state.page} of ${totalPages}`;
}

function selectJob(id, openMobile) {
  state.selectedId = id;
  renderList();
  if (openMobile && window.matchMedia("(max-width: 800px)").matches) {
    document.body.classList.add("detail-open");
  }
}

function showError(message) {
  els.resultsSection.hidden = false;
  els.jobList.replaceChildren();
  const box = createEl("div", "error-state");
  box.appendChild(createEl("p", "", message));
  const retry = createEl("button", "", "Try again");
  retry.type = "button";
  retry.addEventListener("click", () => {
    if (state.lastQuery) runSearch(state.lastQuery);
  });
  box.appendChild(retry);
  els.jobList.appendChild(box);
  els.pagination.hidden = true;
  renderDetail(null);
}

async function loadCountries() {
  const response = await fetch("/api/countries");
  if (!response.ok) throw new Error("Could not load countries");
  const data = await response.json();
  const list = data.countries || [];
  els.country.replaceChildren();
  list.forEach((item) => {
    els.country.appendChild(new Option(item.name, item.code));
  });
  if (![...els.country.options].some((o) => o.value === "us")) {
    els.country.appendChild(new Option("United States", "us"));
  }
  els.country.value = "us";
}

function saveLastSearch(query) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(query));
}

function restoreLastSearch() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    if (saved.keyword) els.keyword.value = saved.keyword;
    if (saved.city) els.city.value = saved.city;
    if (saved.country && [...els.country.options].some((o) => o.value === saved.country)) {
      els.country.value = saved.country;
    }
  } catch {
    /* ignore bad localStorage */
  }
}

async function runSearch(query) {
  setFormError("");
  setStatus("Loading jobs…");
  els.findBtn.disabled = true;
  state.lastQuery = query;
  showSkeletons();

  const params = new URLSearchParams();
  params.set("keyword", query.keyword);
  params.set("country", query.country);
  if (query.city) params.set("city", query.city);

  try {
    const response = await fetch("/api/search?" + params.toString());
    if (!response.ok) {
      let detail = "Search failed. Please try again.";
      try {
        const err = await response.json();
        if (err.detail) {
          detail = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
        }
      } catch {
        /* use default message */
      }
      setStatus("");
      showError(detail);
      return;
    }

    const data = await response.json();
    state.jobs = (data.jobs || []).map((job, index) => ({ ...job, _index: index }));
    state.page = 1;
    state.selectedId = state.jobs[0] ? state.jobs[0].id : null;
    rebuildFilterOptions(state.jobs);
    setStatus("");
    renderList();
    if (state.jobs[0] && !window.matchMedia("(max-width: 800px)").matches) {
      document.body.classList.remove("detail-open");
    }
  } catch {
    setStatus("");
    showError("Could not reach the server. Is the API running?");
  } finally {
    els.findBtn.disabled = false;
  }
}

els.form.addEventListener("submit", (event) => {
  event.preventDefault();
  const keyword = els.keyword.value.trim();
  if (!keyword) {
    setFormError("Enter a job title or keyword.");
    els.keyword.focus();
    return;
  }
  const query = {
    keyword,
    country: els.country.value || "us",
    city: els.city.value.trim(),
  };
  saveLastSearch(query);
  runSearch(query);
});

["change"].forEach((evt) => {
  els.filterDate.addEventListener(evt, () => {
    state.page = 1;
    renderList();
  });
  els.filterType.addEventListener(evt, () => {
    state.page = 1;
    renderList();
  });
  els.filterSource.addEventListener(evt, () => {
    state.page = 1;
    renderList();
  });
  els.sort.addEventListener(evt, () => {
    state.page = 1;
    renderList();
  });
});

els.clearFilters.addEventListener("click", () => {
  els.filterDate.value = "any";
  els.filterType.value = "all";
  els.filterSource.value = "all";
  els.sort.value = "relevance";
  state.page = 1;
  renderList();
});

els.prevPage.addEventListener("click", () => {
  if (state.page > 1) {
    state.page -= 1;
    renderList();
    els.jobList.scrollTop = 0;
  }
});

els.nextPage.addEventListener("click", () => {
  state.page += 1;
  renderList();
  els.jobList.scrollTop = 0;
});

els.backBtn.addEventListener("click", () => {
  document.body.classList.remove("detail-open");
});

els.jobList.addEventListener("keydown", (event) => {
  if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
  const cards = [...els.jobList.querySelectorAll(".job-card")];
  if (!cards.length) return;
  const current = document.activeElement;
  const index = cards.indexOf(current);
  const nextIndex = event.key === "ArrowDown"
    ? Math.min(cards.length - 1, (index === -1 ? 0 : index + 1))
    : Math.max(0, (index === -1 ? 0 : index - 1));
  cards[nextIndex].focus();
  event.preventDefault();
});

async function init() {
  try {
    await loadCountries();
    restoreLastSearch();
  } catch {
    setFormError("Could not load countries. Refresh the page.");
  }
}

init();
