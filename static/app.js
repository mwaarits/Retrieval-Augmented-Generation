const TOKEN_KEY = "rag_token";
const USER_KEY = "rag_user";

const loginScreen = document.getElementById("login-screen");
const loginForm = document.getElementById("login-form");
const loginUsername = document.getElementById("login-username");
const loginPassword = document.getElementById("login-password");
const loginError = document.getElementById("login-error");
const logoutBtn = document.getElementById("logout-btn");
const panels = document.querySelector(".panels");

const fileInput = document.getElementById("file-input");
const uploadBtn = document.getElementById("upload-btn");
const dropzone = document.getElementById("dropzone");
const fileList = document.getElementById("file-list");
const chatForm = document.getElementById("chat-form");
const questionInput = document.getElementById("question-input");
const sendBtn = document.getElementById("send-btn");
const messages = document.getElementById("messages");
const errorBanner = document.getElementById("error-banner");

let pendingFiles = [];
let uploading = false;

// ---------- Auth ----------

function getToken() {
  return localStorage.getItem(TOKEN_KEY) ?? "";
}

function getUser() {
  return localStorage.getItem(USER_KEY) ?? "";
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function resetUI() {
  pendingFiles = [];
  uploading = false;
  fileList.innerHTML = "";
  messages.innerHTML = "";
  errorBanner.hidden = true;
  questionInput.value = "";
}

function showLogin(msg) {
  panels.hidden = true;
  logoutBtn.hidden = true;
  loginScreen.hidden = false;
  if (msg) {
    loginError.textContent = msg;
    loginError.hidden = false;
  }
}

function showApp() {
  loginScreen.hidden = true;
  panels.hidden = false;
  logoutBtn.hidden = false;
}

function logout() {
  fetch("/auth/logout", { method: "POST", headers: authHeaders() }).catch(() => {});
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  resetUI();
  showLogin();
}

logoutBtn.addEventListener("click", logout);

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  loginError.hidden = true;
  const username = loginUsername.value.trim();
  const password = loginPassword.value;
  if (!username || !password) return;

  const btn = loginForm.querySelector("button");
  btn.disabled = true;
  try {
    const res = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const body = await res.json().catch(() => null);
    if (!res.ok || !body || !body.token) {
      throw new Error((body && body.detail) || "Login gagal");
    }
    localStorage.setItem(TOKEN_KEY, body.token);
    localStorage.setItem(USER_KEY, body.user_id);
    loginUsername.value = "";
    loginPassword.value = "";
    showApp();
    loadDocuments().catch(() => {});
  } catch (err) {
    loginError.textContent = err.message;
    loginError.hidden = false;
  } finally {
    btn.disabled = false;
  }
});

// ---------- Documents (panel kiri) ----------

async function loadDocuments() {
  const res = await fetch("/documents", { headers: authHeaders() });
  const body = await res.json().catch(() => null);
  if (res.status === 401) {
    logout();
    return;
  }
  if (!res.ok) throw new Error((body && body.detail) || "Gagal memuat dokumen");
  renderDocuments(body.documents || []);
}

function renderDocuments(files) {
  fileList.innerHTML = "";
  for (const name of files) {
    const li = document.createElement("li");
    li.className = "file-row";

    const docName = document.createElement("span");
    docName.className = "file-name";
    docName.textContent = name;

    const status = document.createElement("span");
    status.className = "file-status ok";
    status.textContent = "terindex";

    li.append(docName, status);
    fileList.appendChild(li);
  }
}

// ---------- Upload ----------

function refreshUploadBtn() {
  uploadBtn.disabled = pendingFiles.length === 0 || uploading;
}

function addFiles(files) {
  for (const file of files) {
    pendingFiles.push(file);

    const li = document.createElement("li");
    li.className = "file-row";

    const name = document.createElement("span");
    name.className = "file-name";
    name.textContent = file.name;

    const status = document.createElement("span");
    status.className = "file-status";
    status.textContent = "menunggu…";

    li.append(name, status);
    fileList.appendChild(li);
    file._statusEl = status;
  }
  refreshUploadBtn();
}

function setStatus(file, text, cls) {
  file._statusEl.textContent = text;
  file._statusEl.className = "file-status" + (cls ? " " + cls : "");
}

function uploadOne(file) {
  return new Promise((resolve) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/ingest");
    xhr.responseType = "json";
    xhr.setRequestHeader("Authorization", `Bearer ${getToken()}`);

    xhr.upload.addEventListener("load", () => {
      setStatus(file, "proses…", "processing");
    });

    xhr.addEventListener("load", () => {
      if (xhr.status === 401) {
        setStatus(file, "gagal: sesi berakhir", "fail");
        logout();
        return resolve();
      }
      const body = xhr.response;
      if (xhr.status >= 200 && xhr.status < 300 && body) {
        setStatus(file, `sukses (${body.chunks} chunk)`, "ok");
      } else {
        const detail = body && body.detail ? body.detail : `HTTP ${xhr.status}`;
        setStatus(file, `gagal: ${detail}`, "fail");
      }
      resolve();
    });

    xhr.addEventListener("error", () => {
      setStatus(file, "gagal: jaringan", "fail");
      resolve();
    });

    const form = new FormData();
    form.append("file", file);
    setStatus(file, "mengunggah…", "uploading");
    xhr.send(form);
  });
}

async function uploadAll() {
  if (uploading || pendingFiles.length === 0) return;
  uploading = true;
  refreshUploadBtn();

  const queue = pendingFiles;
  pendingFiles = [];
  for (const file of queue) {
    await uploadOne(file); // berurutan: satu per satu
  }

  uploading = false;
  refreshUploadBtn();
  await loadDocuments().catch(() => {});
}

fileInput.addEventListener("change", () => {
  addFiles(fileInput.files);
  fileInput.value = "";
});

uploadBtn.addEventListener("click", uploadAll);

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dragover");
});

dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  addFiles(e.dataTransfer.files);
});

// ---------- Chat ----------

function scrollMessages() {
  messages.scrollTop = messages.scrollHeight;
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  div.appendChild(bubble);
  messages.appendChild(div);
  scrollMessages();
  return div;
}

function showError(text) {
  errorBanner.textContent = text;
  errorBanner.hidden = false;
}

function clearError() {
  errorBanner.hidden = true;
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  clearError();
  addMessage("user", question);
  questionInput.value = "";
  questionInput.disabled = true;
  sendBtn.disabled = true;

  const pending = addMessage("assistant", "…");

  try {
    const res = await fetch("/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify({ question, session_id: getUser() }),
    });
    const body = await res.json().catch(() => null);
    pending.remove();

    if (res.status === 401) {
      showError("Sesi berakhir, silakan login ulang.");
      logout();
      return;
    }

    if (!res.ok || !body) {
      showError(`Gagal memproses pertanyaan: ${body && body.detail ? body.detail : "HTTP " + res.status}`);
      return;
    }

    const div = addMessage("assistant", body.answer);
    const bubble = div.querySelector(".bubble");

    if (body.warning) {
      const warn = document.createElement("div");
      warn.className = "warning";
      warn.textContent = `Peringatan: ${body.warning}`;
      bubble.appendChild(warn);
    }

    if (Array.isArray(body.sources) && body.sources.length > 0) {
      const chips = document.createElement("div");
      chips.className = "sources";
      for (const src of new Set(body.sources)) {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.textContent = src;
        chips.appendChild(chip);
      }
      div.appendChild(chips);
    }
    scrollMessages();
  } catch {
    pending.remove();
    showError("Gagal terhubung ke server.");
  } finally {
    questionInput.disabled = false;
    sendBtn.disabled = false;
    questionInput.focus();
  }
});

// ---------- Init ----------

if (getToken() && getUser()) {
  showApp();
  loadDocuments().catch(() => {});
} else {
  showLogin();
}