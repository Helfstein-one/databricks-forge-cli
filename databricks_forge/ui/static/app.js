/**
 * Databricks Forge — OpenWebUI Frontend Engine
 * Modern SPA with SSE streaming, native AbortController stop button, DeepSeek-R1 thinking folding & Mermaid.js.
 */

// Initialize Mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  themeVariables: {
    primaryColor: '#ff3621',
    edgeColor: '#00F0FF',
    lineColor: '#00F0FF',
    textColor: '#f1f5f9',
    mainBkg: '#161b22',
    nodeBorder: '#30363d',
  },
});

// Configure Marked for code highlighting
marked.setOptions({
  highlight: function (code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang }).value;
      } catch (_) {}
    }
    return hljs.highlightAuto(code).value;
  },
  breaks: true,
});

// App State
let state = {
  currentModel: 'llama3.2:3b',
  models: [],
  history: [],
  abortController: null,
  isGenerating: false,
  catalog: [],
};

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const stopBtn = document.getElementById('stopBtn');
const welcomeHero = document.getElementById('welcomeHero');
const modelSelectorBtn = document.getElementById('modelSelectorBtn');
const modelDropdown = document.getElementById('modelDropdown');
const modelOptionsList = document.getElementById('modelOptionsList');
const currentModelLabel = document.getElementById('currentModelLabel');
const catalogEntitiesList = document.getElementById('catalogEntitiesList');
const syncCatalogBtn = document.getElementById('syncCatalogBtn');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const shutdownServerBtn = document.getElementById('shutdownServerBtn');
const toggleSidebarBtn = document.getElementById('toggleSidebarBtn');
const openSidebarBtn = document.getElementById('openSidebarBtn');
const sidebar = document.getElementById('sidebar');

// -------------------------------------------------------------
// Initialization
// -------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
  lucide.createIcons();
  await loadModels();
  await loadCatalog();
  setupEventListeners();
});

function setupEventListeners() {
  // Chat input submit on Enter (without Shift)
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
    // ESC to trigger Stop during generation
    if (e.key === 'Escape' && state.isGenerating) {
      stopGeneration();
    }
  });

  // Auto-resize input
  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 180) + 'px';
  });

  sendBtn.addEventListener('click', handleSubmit);
  stopBtn.addEventListener('click', stopGeneration);

  // Model Dropdown Toggle
  modelSelectorBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    modelDropdown.classList.toggle('hidden');
  });

  document.addEventListener('click', () => {
    modelDropdown.classList.add('hidden');
  });

  // Sidebar toggles
  toggleSidebarBtn.addEventListener('click', () => {
    sidebar.classList.add('-ml-72');
    openSidebarBtn.classList.remove('hidden');
  });

  openSidebarBtn.addEventListener('click', () => {
    sidebar.classList.remove('-ml-72');
    openSidebarBtn.classList.add('hidden');
  });

  // Sync Catalog
  syncCatalogBtn.addEventListener('click', syncCatalog);

  // Clear History
  clearHistoryBtn.addEventListener('click', clearHistory);

  // Shutdown Server
  shutdownServerBtn.addEventListener('click', shutdownServer);

  // Quick Prompt Buttons
  document.querySelectorAll('.quick-prompt-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const prompt = btn.getAttribute('data-prompt');
      if (prompt) {
        chatInput.value = prompt;
        handleSubmit();
      }
    });
  });
}

// -------------------------------------------------------------
// API Calls: Models & Catalog
// -------------------------------------------------------------
async function loadModels() {
  try {
    const res = await fetch('/api/models');
    const data = await res.json();
    state.models = data.models || [];
    state.currentModel = data.default_model || 'llama3.2:3b';
    currentModelLabel.textContent = state.currentModel;

    const statusBadge = document.getElementById('ollamaStatusText');
    if (data.status === 'online') {
      statusBadge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Conectado (${state.models.length})`;
    } else {
      statusBadge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-red-400"></span> Offline`;
      statusBadge.className = 'text-red-400 font-medium flex items-center gap-1';
    }

    renderModelOptions();
  } catch (err) {
    console.warn('Failed to load models:', err);
  }
}

function renderModelOptions() {
  modelOptionsList.innerHTML = '';
  if (!state.models.length) {
    modelOptionsList.innerHTML = '<div class="px-3 py-2 text-xs text-gray-500">Nenhum modelo encontrado</div>';
    return;
  }

  state.models.forEach((model) => {
    const item = document.createElement('button');
    const isSelected = model === state.currentModel;
    item.className = `w-full text-left px-3 py-1.5 text-xs rounded-lg flex items-center justify-between hover:bg-surfaceBorder/60 transition ${
      isSelected ? 'text-cyberCyan font-semibold bg-surfaceBorder/30' : 'text-gray-300'
    }`;
    item.innerHTML = `
      <span class="truncate">${model}</span>
      ${isSelected ? '<i data-lucide="check" class="w-3.5 h-3.5 text-cyberCyan"></i>' : ''}
    `;
    item.addEventListener('click', () => {
      state.currentModel = model;
      currentModelLabel.textContent = model;
      modelDropdown.classList.add('hidden');
      renderModelOptions();
      lucide.createIcons();
      showToast(`Modelo alterado para ${model}`);
    });
    modelOptionsList.appendChild(item);
  });
  lucide.createIcons();
}

async function loadCatalog() {
  try {
    const res = await fetch('/api/catalog');
    const data = await res.json();
    state.catalog = data.entities || [];

    const dbxStatusText = document.getElementById('dbxStatusText');
    if (data.dbx_connected) {
      dbxStatusText.textContent = 'Unity Catalog Online';
      dbxStatusText.className = 'text-emerald-400 font-medium';
    } else {
      dbxStatusText.textContent = 'Catálogo Local (Cache)';
      dbxStatusText.className = 'text-blue-400 font-medium';
    }

    renderCatalog();
  } catch (err) {
    console.warn('Failed to load catalog:', err);
  }
}

function renderCatalog() {
  catalogEntitiesList.innerHTML = '';
  if (!state.catalog.length) {
    catalogEntitiesList.innerHTML = '<div class="text-gray-500 text-xs px-1">Nenhuma tabela cadastrada</div>';
    return;
  }

  state.catalog.forEach((ent) => {
    const badge = ent.layer === 'gold' ? '🥇' : ent.layer === 'silver' ? '🥈' : '🥉';
    const card = document.createElement('div');
    card.className = 'p-2 rounded-lg bg-surfaceDark/70 border border-surfaceBorder hover:border-surfaceBorder/80 transition text-xs space-y-1';
    card.innerHTML = `
      <div class="font-semibold text-gray-200 flex items-center justify-between">
        <span class="truncate">${badge} ${ent.name}</span>
        <span class="text-[10px] text-gray-500 uppercase">${ent.layer}</span>
      </div>
      <div class="text-[11px] text-gray-400 truncate">${ent.description || ent.full_table_name}</div>
      <div class="flex flex-wrap gap-1 pt-0.5">
        ${ent.dimensions.map((d) => `<span class="text-[9px] bg-surfaceBorder/60 text-gray-300 px-1 py-0.5 rounded font-mono">${d}</span>`).join('')}
      </div>
    `;
    card.addEventListener('click', () => {
      chatInput.value = `Explique a tabela ${ent.name} e mostre suas métricas homologadas`;
      chatInput.focus();
    });
    catalogEntitiesList.appendChild(card);
  });
}

async function syncCatalog() {
  syncCatalogBtn.classList.add('animate-spin');
  try {
    const res = await fetch('/api/catalog/sync', { method: 'POST' });
    const data = await res.json();
    await loadCatalog();
    showToast(`✅ ${data.message}`);
  } catch (err) {
    showToast('Erro ao sincronizar catálogo', true);
  } finally {
    syncCatalogBtn.classList.remove('animate-spin');
  }
}

// -------------------------------------------------------------
// Chat & Streaming Logic
// -------------------------------------------------------------
async function handleSubmit() {
  const text = chatInput.value.trim();
  if (!text || state.isGenerating) return;

  // Clear input
  chatInput.value = '';
  chatInput.style.height = 'auto';

  // Hide hero if visible
  if (welcomeHero) welcomeHero.style.display = 'none';

  // Append user message
  appendUserMessage(text);
  state.history.push({ role: 'user', content: text });

  // Start generation
  setGenerating(true);
  state.abortController = new AbortController();

  // Create assistant message container
  const assistantMsgObj = appendAssistantMessageContainer();

  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        model: state.currentModel,
        history: state.history,
      }),
      signal: state.abortController.signal,
    });

    if (!response.ok) throw new Error(`HTTP error ${response.status}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let accumulatedText = '';
    let isThinking = false;
    let thinkingText = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // Keep last partial line

      let currentEvent = 'message';
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          const dataStr = line.slice(6);
          if (dataStr === '{}' && currentEvent === 'done') continue;

          try {
            const data = JSON.parse(dataStr);

            // Handle token event (raw streaming)
            if (currentEvent === 'token' && data.token) {
              const chunk = data.token;

              // Check for DeepSeek-R1 <think> tags
              if (chunk.includes('<think>')) {
                isThinking = true;
                assistantMsgObj.enableThinking();
              }

              if (isThinking) {
                if (chunk.includes('</think>')) {
                  isThinking = false;
                  const parts = chunk.split('</think>');
                  thinkingText += parts[0];
                  assistantMsgObj.updateThinking(thinkingText, true);
                  if (parts[1]) {
                    accumulatedText += parts[1];
                    assistantMsgObj.updateText(accumulatedText);
                  }
                } else {
                  thinkingText += chunk.replace('<think>', '');
                  assistantMsgObj.updateThinking(thinkingText, false);
                }
              } else {
                accumulatedText += chunk;
                assistantMsgObj.updateText(accumulatedText);
              }
            }

            // Handle structured message (diagram or etl_proposal)
            if (currentEvent === 'message') {
              if (data.type === 'diagram') {
                assistantMsgObj.updateText(data.text);
                if (data.mermaid) {
                  await assistantMsgObj.renderMermaid(data.mermaid);
                }
              } else if (data.type === 'etl_proposal') {
                assistantMsgObj.updateText(data.text);
                assistantMsgObj.renderETLProposal(data);
                if (data.mermaid) {
                  await assistantMsgObj.renderMermaid(data.mermaid);
                }
              } else {
                accumulatedText = data.text || '';
                assistantMsgObj.updateText(accumulatedText);
                if (data.mermaid) {
                  await assistantMsgObj.renderMermaid(data.mermaid);
                }
              }
            }
          } catch (e) {
            console.error('SSE JSON parse error:', e);
          }
        }
      }
    }

    // Finalize assistant message
    assistantMsgObj.finalize(accumulatedText);
    state.history.push({ role: 'assistant', content: accumulatedText });
  } catch (err) {
    if (err.name === 'AbortError') {
      assistantMsgObj.markAborted();
      showToast('⏹️ Resposta interrompida pelo usuário');
    } else {
      assistantMsgObj.updateText(`❌ Erro de conexão: ${err.message}`);
    }
  } finally {
    setGenerating(false);
    scrollToBottom();
  }
}

// -------------------------------------------------------------
// Native Stop Functionality
// -------------------------------------------------------------
function stopGeneration() {
  if (state.abortController && state.isGenerating) {
    state.abortController.abort();
    setGenerating(false);
  }
}

function setGenerating(isGen) {
  state.isGenerating = isGen;
  if (isGen) {
    sendBtn.classList.add('hidden');
    stopBtn.classList.remove('hidden');
    stopBtn.classList.add('flex');
    chatInput.setAttribute('disabled', 'true');
  } else {
    stopBtn.classList.add('hidden');
    stopBtn.classList.remove('flex');
    sendBtn.classList.remove('hidden');
    chatInput.removeAttribute('disabled');
    chatInput.focus();
  }
  lucide.createIcons();
}

// -------------------------------------------------------------
// Message DOM Rendering
// -------------------------------------------------------------
function appendUserMessage(text) {
  const msgDiv = document.createElement('div');
  msgDiv.className = 'flex justify-end message-fade-in';
  msgDiv.innerHTML = `
    <div class="max-w-[80%] rounded-2xl px-4 py-3 bg-gradient-to-r from-brand/90 to-brand text-white shadow-md text-sm leading-relaxed select-text">
      ${escapeHtml(text)}
    </div>
  `;
  chatMessages.appendChild(msgDiv);
  scrollToBottom();
}

function appendAssistantMessageContainer() {
  const msgDiv = document.createElement('div');
  msgDiv.className = 'flex items-start space-x-3 message-fade-in';

  const avatar = document.createElement('div');
  avatar.className = 'w-8 h-8 rounded-xl bg-surfaceCard border border-surfaceBorder flex items-center justify-center shrink-0 shadow-sm';
  avatar.innerHTML = '<i data-lucide="bot" class="w-4 h-4 text-cyberCyan"></i>';

  const contentBox = document.createElement('div');
  contentBox.className = 'flex-1 space-y-3 prose max-w-none text-sm select-text';

  // Thinking Accordion placeholder
  const thinkingContainer = document.createElement('div');
  thinkingContainer.className = 'thinking-block hidden';
  thinkingContainer.innerHTML = `
    <div class="thinking-header">
      <span class="flex items-center gap-1.5 font-mono">
        <i data-lucide="brain" class="w-3.5 h-3.5 text-cyberCyan animate-pulse"></i>
        <span class="thinking-status">Raciocinando (DeepSeek-R1)...</span>
      </span>
      <i data-lucide="chevron-down" class="w-3.5 h-3.5 transition-transform duration-200"></i>
    </div>
    <div class="thinking-body"></div>
  `;
  contentBox.appendChild(thinkingContainer);

  const textBody = document.createElement('div');
  textBody.className = 'text-body typing-cursor';
  contentBox.appendChild(textBody);

  const extraContainer = document.createElement('div');
  extraContainer.className = 'extra-content space-y-3';
  contentBox.appendChild(extraContainer);

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(contentBox);
  chatMessages.appendChild(msgDiv);

  lucide.createIcons();
  scrollToBottom();

  const thinkingHeader = thinkingContainer.querySelector('.thinking-header');
  const thinkingBody = thinkingContainer.querySelector('.thinking-body');
  const thinkingStatus = thinkingContainer.querySelector('.thinking-status');
  thinkingHeader.addEventListener('click', () => {
    thinkingBody.classList.toggle('hidden');
    thinkingHeader.querySelector('[data-lucide="chevron-down"]').classList.toggle('rotate-180');
  });

  return {
    enableThinking() {
      thinkingContainer.classList.remove('hidden');
      lucide.createIcons();
    },
    updateThinking(text, done) {
      thinkingBody.textContent = text;
      if (done) {
        thinkingStatus.textContent = 'Raciocínio finalizado';
        thinkingHeader.querySelector('[data-lucide="brain"]').classList.remove('animate-pulse');
        thinkingBody.classList.add('hidden'); // collapse by default once done
      }
      scrollToBottom();
    },
    updateText(rawMarkdown) {
      textBody.innerHTML = marked.parse(rawMarkdown);
      scrollToBottom();
    },
    finalize(rawMarkdown) {
      textBody.classList.remove('typing-cursor');
      textBody.innerHTML = marked.parse(rawMarkdown);
      addCodeCopyButtons(textBody);
      lucide.createIcons();
      scrollToBottom();
    },
    markAborted() {
      textBody.classList.remove('typing-cursor');
      const badge = document.createElement('div');
      badge.className = 'inline-flex items-center gap-1 mt-2 text-xs text-amber-400 bg-amber-400/10 px-2.5 py-1 rounded-md border border-amber-400/20';
      badge.innerHTML = '<i data-lucide="stop-circle" class="w-3.5 h-3.5"></i> Resposta interrompida pelo usuário';
      contentBox.appendChild(badge);
      lucide.createIcons();
    },
    async renderMermaid(mermaidCode) {
      const wrapper = document.createElement('div');
      wrapper.className = 'mermaid-wrapper';
      const id = 'mermaid_' + Math.random().toString(36).substring(2, 9);
      try {
        const { svg } = await mermaid.render(id, mermaidCode);
        wrapper.innerHTML = `
          <div class="flex items-center justify-between pb-2 border-b border-surfaceBorder mb-2">
            <span class="text-[11px] font-mono text-cyberCyan flex items-center gap-1">
              <i data-lucide="git-merge" class="w-3 h-3"></i> Diagrama Mermaid
            </span>
            <button class="copy-mermaid-btn text-[11px] text-gray-400 hover:text-white px-2 py-0.5 rounded bg-surfaceBorder/40 transition flex items-center gap-1">
              <i data-lucide="copy" class="w-3 h-3"></i> Copiar Código
            </button>
          </div>
          <div class="overflow-x-auto py-2">${svg}</div>
        `;
        wrapper.querySelector('.copy-mermaid-btn').addEventListener('click', () => {
          navigator.clipboard.writeText(mermaidCode);
          showToast('Código Mermaid copiado!');
        });
        extraContainer.appendChild(wrapper);
        lucide.createIcons();
      } catch (err) {
        console.error('Mermaid render error:', err);
      }
    },
    renderETLProposal(proposal) {
      const card = document.createElement('div');
      card.className = 'rounded-xl bg-surfaceCard border border-brand/40 p-4 space-y-3 shadow-xl';
      card.innerHTML = `
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <span class="p-1 rounded-lg bg-brand/20 text-brand"><i data-lucide="cpu" class="w-4 h-4"></i></span>
            <h4 class="font-bold text-sm text-white">${proposal.pipeline_name}</h4>
          </div>
          <span class="text-[11px] px-2 py-0.5 rounded bg-surfaceBorder text-gray-300 font-mono">PySpark Delta</span>
        </div>
        <div class="flex items-center gap-2 text-xs text-gray-400">
          <span>Origem: <code class="text-cyberCyan">${proposal.source_table}</code></span>
          <span>•</span>
          <span>Destino: <code class="text-amber-400">${proposal.target_table}</code></span>
        </div>
        <div class="relative">
          <pre><code class="language-python">${escapeHtml(proposal.code)}</code></pre>
        </div>
        <div class="pt-2 flex items-center justify-between border-t border-surfaceBorder">
          <span class="text-[11px] text-gray-400">Validação e commit automático</span>
          <button class="approve-etl-btn flex items-center space-x-1.5 bg-gradient-to-r from-brand to-brandDark hover:brightness-110 text-white text-xs px-4 py-2 rounded-xl font-semibold shadow-md shadow-brand/20 transition active:scale-95">
            <i data-lucide="rocket" class="w-3.5 h-3.5"></i>
            <span>Executar no Databricks & Enviar para GitHub</span>
          </button>
        </div>
        <div class="etl-status-log hidden text-xs p-3 rounded-lg bg-surfaceDark/80 border border-surfaceBorder space-y-1"></div>
      `;

      // Syntax highlight
      hljs.highlightElement(card.querySelector('code'));

      const approveBtn = card.querySelector('.approve-etl-btn');
      const statusLog = card.querySelector('.etl-status-log');

      approveBtn.addEventListener('click', async () => {
        approveBtn.disabled = true;
        approveBtn.innerHTML = '<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i><span>Executando...</span>';
        statusLog.classList.remove('hidden');
        statusLog.innerHTML = '<div>⏳ Gravando script em <code>notebooks/</code> e atualizando <code>workflow.yaml</code>...</div>';

        try {
          const res = await fetch('/api/etl/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              pipeline_name: proposal.pipeline_name,
              code: proposal.code,
            }),
          });
          const result = await res.json();
          if (result.success) {
            statusLog.innerHTML = `
              <div class="text-emerald-400 font-semibold">✅ Pipeline Executado com Sucesso!</div>
              <div>🧊 Databricks: ${result.databricks_status}</div>
              <div>🐙 GitHub Commit: <code class="text-cyberCyan">${result.commit_hash}</code> na branch <code>${result.branch}</code></div>
            `;
            approveBtn.innerHTML = '<i data-lucide="check" class="w-3.5 h-3.5"></i><span>Sincronizado!</span>';
            approveBtn.className = 'approve-etl-btn flex items-center space-x-1.5 bg-emerald-600 text-white text-xs px-4 py-2 rounded-xl font-semibold cursor-default';
            showToast('🎉 Pipeline comitado e enviado para o GitHub!');
          } else {
            statusLog.innerHTML = `<div class="text-red-400">❌ Falha: ${result.error}</div>`;
            approveBtn.disabled = false;
            approveBtn.innerHTML = '<span>Tentar Novamente</span>';
          }
        } catch (err) {
          statusLog.innerHTML = `<div class="text-red-400">❌ Erro de rede: ${err.message}</div>`;
          approveBtn.disabled = false;
          approveBtn.innerHTML = '<span>Tentar Novamente</span>';
        }
        lucide.createIcons();
      });

      extraContainer.appendChild(card);
      lucide.createIcons();
    },
  };
}

function addCodeCopyButtons(container) {
  container.querySelectorAll('pre').forEach((pre) => {
    if (pre.querySelector('.copy-btn')) return;
    const btn = document.createElement('button');
    btn.className = 'copy-btn absolute top-2 right-2 text-xs text-gray-400 hover:text-white bg-surfaceBorder/60 hover:bg-surfaceBorder px-2 py-1 rounded transition flex items-center gap-1';
    btn.innerHTML = '<i data-lucide="copy" class="w-3 h-3"></i> Copiar';
    pre.style.position = 'relative';
    btn.addEventListener('click', () => {
      const code = pre.querySelector('code').innerText;
      navigator.clipboard.writeText(code);
      btn.innerHTML = '<i data-lucide="check" class="w-3 h-3 text-emerald-400"></i> Copiado!';
      setTimeout(() => {
        btn.innerHTML = '<i data-lucide="copy" class="w-3 h-3"></i> Copiar';
        lucide.createIcons();
      }, 2000);
    });
    pre.appendChild(btn);
  });
}

function clearHistory() {
  state.history = [];
  chatMessages.innerHTML = '';
  if (welcomeHero) {
    welcomeHero.style.display = 'block';
    chatMessages.appendChild(welcomeHero);
  }
  showToast('Histórico limpo');
}

async function shutdownServer() {
  if (confirm('Deseja encerrar o servidor do Databricks Forge?')) {
    try {
      await fetch('/api/shutdown', { method: 'POST' });
    } catch (_) {}
    document.body.innerHTML = `
      <div class="h-screen w-screen flex flex-col items-center justify-center bg-surfaceDark text-gray-300 space-y-3">
        <i data-lucide="power" class="w-12 h-12 text-brand"></i>
        <h2 class="text-xl font-bold text-white">Servidor Encerrado</h2>
        <p class="text-sm text-gray-400">Você já pode fechar esta aba do navegador com segurança.</p>
      </div>
    `;
    lucide.createIcons();
  }
}

// -------------------------------------------------------------
// Utilities
// -------------------------------------------------------------
function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function showToast(message, isError = false) {
  const toast = document.getElementById('toast');
  const toastMessage = document.getElementById('toastMessage');
  const toastIcon = document.getElementById('toastIcon');

  toastMessage.textContent = message;
  toastIcon.innerHTML = isError
    ? '<i data-lucide="alert-circle" class="w-4 h-4 text-red-400"></i>'
    : '<i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-400"></i>';

  toast.classList.remove('hidden');
  lucide.createIcons();

  setTimeout(() => {
    toast.classList.add('hidden');
  }, 3500);
}
