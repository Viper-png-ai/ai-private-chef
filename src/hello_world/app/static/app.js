const sessionKey = "ai-chef-session-id";

const bootScreen = document.querySelector("#boot-screen");
const appShell = document.querySelector("#app-shell");
const sidebar = document.querySelector("#sidebar");
const sidebarBackdrop = document.querySelector("#sidebar-backdrop");
const messages = document.querySelector("#messages");
const chatStatus = document.querySelector("#chat-status");
const sessionList = document.querySelector("#session-list");
const sessionCount = document.querySelector("#session-count");
const usernameLabel = document.querySelector("#username-label");
const userAvatar = document.querySelector("#user-avatar");
const newChatButton = document.querySelector("#new-chat-button");
const clearChatButton = document.querySelector("#clear-chat-button");
const logoutButton = document.querySelector("#logout-button");
const menuButton = document.querySelector("#menu-button");
const uploadButton = document.querySelector("#upload-button");
const fileInput = document.querySelector("#file-input");
const messageInput = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const imagePreview = document.querySelector("#image-preview");
const previewImage = document.querySelector("#preview-image");
const previewName = document.querySelector("#preview-name");
const removeImageButton = document.querySelector("#remove-image-button");
const toast = document.querySelector("#toast");
const markdown = window.markdownit
  ? window.markdownit({
      html: false,
      linkify: true,
      breaks: true,
      typographer: true,
    })
  : null;
let sessionId = localStorage.getItem(sessionKey) || createId();
let selectedImage = null;
let streaming = false;

localStorage.setItem(sessionKey, sessionId);

function createId() {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function setStatus(text) {
  chatStatus.textContent = text;
}

function showToast(text, error = false) {
  toast.textContent = text;
  toast.classList.toggle("error", error);
  toast.hidden = false;
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    toast.hidden = true;
  }, 3200);
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (response.status === 401) {
    window.location.href = "/login";
    throw new Error("登录状态已失效。");
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || `请求失败：${response.status}`);
  }

  return data;
}

function openSidebar() {
  sidebar.classList.add("open");
  sidebarBackdrop.hidden = false;
}

function closeSidebar() {
  sidebar.classList.remove("open");
  sidebarBackdrop.hidden = true;
}

function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

function renderEmpty() {
  messages.innerHTML = `
    <div class="empty-chat">
      <div class="empty-visual">
        <div>
          <h2>把冰箱里的食材，变成今天的一顿饭。</h2>
          <p>上传照片、读取库存、检查过敏，再为你规划真正能执行的菜谱。</p>
        </div>
      </div>
      <div class="suggestions">
        <button class="suggestion" type="button">根据库存推荐晚餐</button>
        <button class="suggestion" type="button">看看哪些食材快过期</button>
        <button class="suggestion" type="button">推荐一道简单的快手菜</button>
      </div>
    </div>
  `;

  messages.querySelectorAll(".suggestion").forEach((button) => {
    button.addEventListener("click", () => {
      messageInput.value = button.textContent.trim();
      messageInput.focus();
    });
  });
}

function appendImage(container, url, alt = "参考图片") {
  const image = document.createElement("img");
  image.src = url;
  image.alt = alt;
  image.loading = "lazy";

  image.addEventListener("error", () => {
    const fallback = document.createElement("a");
    fallback.href = url;
    fallback.target = "_blank";
    fallback.rel = "noreferrer";
    fallback.textContent = url;
    image.replaceWith(fallback);
  });

  container.append(image);
}

function renderRichText(container, content) {
  if (!markdown) {
    container.textContent = content || "";
    return;
  }

  container.innerHTML = markdown.render(content || "");

  container.querySelectorAll("a").forEach((link) => {
    link.target = "_blank";
    link.rel = "noreferrer";
  });

  container.querySelectorAll("img").forEach((image) => {
    image.loading = "lazy";
    image.alt ||= "AI 返回的参考图片";

    image.addEventListener("error", () => {
      const fallback = document.createElement("a");
      fallback.href = image.src;
      fallback.target = "_blank";
      fallback.rel = "noreferrer";
      fallback.textContent = image.src;
      image.replaceWith(fallback);
    });
  });
}

function appendRichText(container, content) {
  const raw = (container.dataset.rawText || "") + content;
  container.dataset.rawText = raw;
  renderRichText(container, raw);
}

function renderMessage(role, content = "", imageUrl = null) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "user" ? "我" : "厨";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";

  if (imageUrl) {
    appendImage(bubble, imageUrl, "用户上传的食材");
  }

  const text = document.createElement("div");
  text.dataset.rawText = content;
  renderRichText(text, content);
  bubble.append(text);

  article.append(avatar, bubble);
  messages.append(article);
  scrollToBottom();

  return { article, bubble, text };
}

function showTyping(bubble) {
  bubble.innerHTML = `
    <div class="typing-dots">
      <span></span><span></span><span></span>
    </div>
  `;
}

function renderSessions(items) {
  sessionList.replaceChildren();
  sessionCount.textContent = String(items.length);

  if (!items.length) {
    const empty = document.createElement("div");
    empty.style.padding = "10px 8px";
    empty.style.color = "#89938d";
    empty.style.fontSize = "12px";
    empty.textContent = "还没有历史会话";
    sessionList.append(empty);
    return;
  }

  items.forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "session-item";
    button.textContent = item.title || "未命名会话";
    button.title = item.title || "未命名会话";

    if (item.session_id === sessionId) {
      button.classList.add("active");
    }

    button.addEventListener("click", async () => {
      sessionId = item.session_id;
      localStorage.setItem(sessionKey, sessionId);
      selectedImage = null;
      imagePreview.hidden = true;
      closeSidebar();
      await refreshSessions();
      await loadHistory();
    });

    sessionList.append(button);
  });
}

async function refreshSessions() {
  try {
    const data = await api("/api/v1/chat/sessions");
    const items = data.sessions || [];

    const exists = items.some((item) => item.session_id === sessionId);

    if (!exists) {
      items.unshift({
        session_id: sessionId,
        title: "当前会话",
      });
    }

    renderSessions(items);
  } catch (error) {
    showToast(error.message, true);
  }
}

async function loadHistory() {
  try {
    const data = await api(
      `/api/v1/chat/history?session_id=${encodeURIComponent(sessionId)}`,
    );

    if (!data.messages?.length) {
      renderEmpty();
      return;
    }

    messages.replaceChildren();

    data.messages.forEach((message) => {
      renderMessage(message.role, message.content);
    });

    scrollToBottom();
  } catch (error) {
    renderEmpty();
    showToast(error.message, true);
  }
}

async function uploadImage(file) {
  setStatus("正在上传图片...");
  uploadButton.disabled = true;

  try {
    const presign = await api("/api/v1/oss/presign", {
      method: "POST",
      body: JSON.stringify({
        filename: file.name,
        content_type: file.type || "image/jpeg",
        session_id: sessionId,
      }),
    });

    const response = await fetch(presign.upload_url, {
      method: presign.method,
      headers: presign.headers,
      body: file,
    });

    if (!response.ok) {
      throw new Error(`OSS 上传失败：${response.status}`);
    }

    selectedImage = {
      key: presign.object_key,
      url: presign.public_url,
      name: file.name,
    };

    previewImage.src = presign.public_url;
    previewName.textContent = file.name;
    imagePreview.hidden = false;
    setStatus("图片已上传，可以发送");
  } catch (error) {
    showToast(error.message, true);
    setStatus("准备开始今天的一餐");
  } finally {
    uploadButton.disabled = false;
    fileInput.value = "";
  }
}

function setStreaming(value) {
  streaming = value;
  sendButton.disabled = value;
  uploadButton.disabled = value;
  messageInput.disabled = value;
  sendButton.classList.toggle("is-loading", value);
}

async function sendMessage() {
  const text = messageInput.value.trim();
  if ((!text && !selectedImage) || streaming) {
    return;
  }

  const content = text || "请看看这些食材能做什么菜？";
  const imageUrl = selectedImage?.url || null;

  const empty = messages.querySelector(".empty-chat");
  if (empty) {
    messages.replaceChildren();
  }

  renderMessage("user", content, imageUrl);
  messageInput.value = "";
  messageInput.style.height = "auto";
  selectedImage = null;
  imagePreview.hidden = true;

  const assistant = renderMessage("assistant");
  showTyping(assistant.bubble);

  setStreaming(true);
  setStatus("正在思考...");

  try {
    const response = await fetch("/api/v1/chat/stream", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: content,
        session_id: sessionId,
        image_url: imageUrl,
      }),
    });

    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }

    if (!response.ok || !response.body) {
      throw new Error(`请求失败：${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let hasContent = false;

    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      buffer = buffer.replace(/\r\n/g, "\n");
      const events = buffer.split("\n\n");
      buffer = events.pop() || "";

      for (const event of events) {
        const line = event
          .split("\n")
          .find((item) => item.startsWith("data: "));

        if (!line) {
          continue;
        }

        const data = JSON.parse(line.slice(6));

        if (data.type === "status") {
          setStatus(data.status);
        }

        if (data.type === "delta") {
          if (!hasContent) {
            assistant.bubble.replaceChildren(assistant.text);
            hasContent = true;
          }
          appendRichText(assistant.text, data.content);
          scrollToBottom();
        }

        if (data.type === "error") {
          throw new Error(data.message);
        }
      }
    }

    if (!hasContent) {
      assistant.bubble.replaceChildren(assistant.text);
      assistant.text.textContent = "没有收到有效回答。";
      assistant.text.classList.add("error");
    }

    setStatus("回答完成");
    await refreshSessions();
  } catch (error) {
    assistant.bubble.replaceChildren(assistant.text);
    assistant.text.textContent = `生成失败：${error.message}`;
    assistant.text.classList.add("error");
    setStatus("生成失败");
    showToast(error.message, true);
  } finally {
    setStreaming(false);
  }
}

function autoResizeInput() {
  messageInput.style.height = "auto";
  messageInput.style.height = `${Math.min(
    messageInput.scrollHeight,
    150,
  )}px`;
}

async function clearCurrentChat() {
  try {
    await api(
      `/api/v1/chat/history/${encodeURIComponent(sessionId)}`,
      { method: "DELETE" },
    );
    renderEmpty();
    await refreshSessions();
    setStatus("当前对话已清空");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function startNewChat() {
  sessionId = createId();
  localStorage.setItem(sessionKey, sessionId);
  selectedImage = null;
  imagePreview.hidden = true;
  messageInput.value = "";
  renderEmpty();
  await refreshSessions();
  setStatus("新会话已创建");
  closeSidebar();
}

async function logout() {
  try {
    await api("/api/v1/auth/logout", { method: "POST" });
  } finally {
    window.location.href = "/login";
  }
}

async function init() {
  try {
    const user = await api("/api/v1/auth/me");
    usernameLabel.textContent = user.username;

    const initial = user.username.trim().charAt(0).toUpperCase() || "U";
    userAvatar.textContent = initial;

    await refreshSessions();
    await loadHistory();

    bootScreen.hidden = true;
    appShell.hidden = false;
    window.lucide?.createIcons();
  } catch (error) {
    window.location.href = "/login";
  }
}

sendButton.addEventListener("click", sendMessage);
newChatButton.addEventListener("click", startNewChat);
clearChatButton.addEventListener("click", clearCurrentChat);
logoutButton.addEventListener("click", logout);
menuButton.addEventListener("click", openSidebar);
sidebarBackdrop.addEventListener("click", closeSidebar);

uploadButton.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];
  if (file) {
    await uploadImage(file);
  }
});

removeImageButton.addEventListener("click", () => {
  selectedImage = null;
  imagePreview.hidden = true;
  previewImage.removeAttribute("src");
  previewName.textContent = "";
  setStatus("已移除图片");
});

messageInput.addEventListener("input", autoResizeInput);

messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});

init();