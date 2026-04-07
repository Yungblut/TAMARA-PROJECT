/**
 * TAMARA WebSocket Client
 * Maneja la comunicación con el servidor y la interfaz de usuario.
 */

// ============================================
// Configuration
// ============================================
const CONFIG = {
    wsUrl: `ws://${window.location.host}/ws`,
    reconnectDelay: 3000,
    maxReconnectAttempts: 10,
    keepaliveInterval: 30000
};

// ============================================
// Application State
// ============================================
class AppState {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.isProcessing = false;
        this.audioEnabled = true;
        this.audioQueue = [];
        this.isPlayingAudio = false;
        this.currentAiMessage = null;
        this.reconnectAttempts = 0;
        this.recognition = null;
        this.micEnabled = false;
    }
}

const state = new AppState();

// ============================================
// DOM Elements
// ============================================
const elements = {
    chatHistory: null,
    userInput: null,
    sendButton: null,
    connectionStatus: null,
    statusText: null,
    aiStatus: null,
    aiStatusText: null,
    systemLog: null,
    micButton: null,
    audioToggle: null,
    reconnectBtn: null,
    resetBtn: null,
    audioIndicator: null
};

function initElements() {
    elements.chatHistory = document.getElementById('chatHistory');
    elements.userInput = document.getElementById('userInput');
    elements.sendButton = document.getElementById('sendButton');
    elements.connectionStatus = document.getElementById('connectionStatus');
    elements.statusText = document.getElementById('statusText');
    elements.aiStatus = document.getElementById('aiStatus');
    elements.aiStatusText = document.getElementById('aiStatusText');
    elements.systemLog = document.getElementById('systemLog');
    elements.micButton = document.getElementById('micButton');
    elements.audioToggle = document.getElementById('audioToggle');
    elements.reconnectBtn = document.getElementById('reconnectBtn');
    elements.resetBtn = document.getElementById('resetBtn');
    elements.audioIndicator = document.getElementById('audioIndicator');
}

// ============================================
// Logging
// ============================================
function log(message, type = 'info') {
    if (!elements.systemLog) {
        console.log(`[${type}] ${message}`);
        return;
    }
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    const time = new Date().toLocaleTimeString();
    entry.textContent = `[${time}] ${message}`;
    elements.systemLog.appendChild(entry);
    elements.systemLog.scrollTop = elements.systemLog.scrollHeight;
}

// ============================================
// WebSocket Connection
// ============================================
function connect() {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) return;

    log('Conectando al servidor...', 'info');

    try {
        state.ws = new WebSocket(CONFIG.wsUrl);

        state.ws.onopen = () => {
            state.isConnected = true;
            state.reconnectAttempts = 0;
            updateConnectionStatus(true);
            elements.sendButton.disabled = false;
            log('¡Conectado exitosamente!', 'success');
        };

        state.ws.onclose = () => {
            state.isConnected = false;
            updateConnectionStatus(false);
            elements.sendButton.disabled = true;
            log('Conexión cerrada', 'warning');

            // Auto-reconnect
            if (state.reconnectAttempts < CONFIG.maxReconnectAttempts) {
                state.reconnectAttempts++;
                log(`Reconectando en ${CONFIG.reconnectDelay / 1000}s... (${state.reconnectAttempts}/${CONFIG.maxReconnectAttempts})`, 'info');
                setTimeout(connect, CONFIG.reconnectDelay);
            }
        };

        state.ws.onerror = () => {
            log('Error de conexión', 'error');
        };

        state.ws.onmessage = handleMessage;

    } catch (error) {
        log(`Error: ${error.message}`, 'error');
    }
}

function handleMessage(event) {
    const data = JSON.parse(event.data);

    switch (data.type) {
        case 'thinking':
            showAiStatus('PENSANDO', 'thinking');
            startAiMessage();
            break;

        case 'token':
            appendToAiMessage(data.content);
            break;

        case 'audio':
            if (state.audioEnabled && data.content) {
                state.audioQueue.push(data.content);
                playNextAudio();
            }
            break;

        case 'done':
            hideAiStatus();
            finishAiMessage();
            state.isProcessing = false;
            break;

        case 'error':
            log(`Error: ${data.content}`, 'error');
            hideAiStatus();
            state.isProcessing = false;
            break;

        case 'pong':
            // Keepalive response
            break;
    }
}

function updateConnectionStatus(connected) {
    elements.connectionStatus.className = `status ${connected ? 'connected' : 'disconnected'}`;
    elements.statusText.textContent = connected ? 'CONECTADO' : 'DESCONECTADO';
}

function showAiStatus(text, type) {
    elements.aiStatus.style.display = 'flex';
    elements.aiStatus.className = `status ${type}`;
    elements.aiStatusText.textContent = text;
}

function hideAiStatus() {
    elements.aiStatus.style.display = 'none';
}

// ============================================
// Chat Functions
// ============================================
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function addUserMessage(text) {
    const div = document.createElement('div');
    div.className = 'message user-message';
    div.innerHTML = `<div class="message-label">TÚ</div>${escapeHtml(text)}`;
    elements.chatHistory.appendChild(div);
    elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
}

function startAiMessage() {
    state.currentAiMessage = document.createElement('div');
    state.currentAiMessage.className = 'message ai-message';
    state.currentAiMessage.innerHTML = `
        <div class="message-label">TAMARA</div>
        <span class="ai-content"></span>
        <div class="typing-indicator">
            <span></span><span></span><span></span>
        </div>
    `;
    elements.chatHistory.appendChild(state.currentAiMessage);
    elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
}

function appendToAiMessage(text) {
    if (state.currentAiMessage) {
        const content = state.currentAiMessage.querySelector('.ai-content');
        if (content) {
            content.textContent += text;
        }
        elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
    }
}

function finishAiMessage() {
    if (state.currentAiMessage) {
        const indicator = state.currentAiMessage.querySelector('.typing-indicator');
        if (indicator) indicator.remove();
        state.currentAiMessage = null;
    }
}

function sendMessage() {
    const text = elements.userInput.value.trim();
    if (!text || !state.isConnected || state.isProcessing) return;

    addUserMessage(text);
    elements.userInput.value = '';
    state.isProcessing = true;

    state.ws.send(JSON.stringify({
        type: 'message',
        content: text
    }));

    log(`Enviado: "${text.substring(0, 30)}..."`, 'info');
}

// ============================================
// Audio Playback
// ============================================
function playNextAudio() {
    if (state.isPlayingAudio || state.audioQueue.length === 0) return;

    state.isPlayingAudio = true;
    elements.audioIndicator.classList.add('visible');
    showAiStatus('HABLANDO', 'connected');

    const base64Audio = state.audioQueue.shift();
    const audio = new Audio(`data:audio/wav;base64,${base64Audio}`);

    audio.onended = () => {
        state.isPlayingAudio = false;
        if (state.audioQueue.length > 0) {
            playNextAudio();
        } else {
            elements.audioIndicator.classList.remove('visible');
            hideAiStatus();
        }
    };

    audio.onerror = () => {
        log('Error reproduciendo audio', 'error');
        state.isPlayingAudio = false;
        elements.audioIndicator.classList.remove('visible');
        playNextAudio();
    };

    audio.play().catch(e => {
        log('Error: ' + e.message, 'error');
        state.isPlayingAudio = false;
        elements.audioIndicator.classList.remove('visible');
    });
}

// ============================================
// Speech Recognition (Web Speech API)
// ============================================
function initSpeechRecognition() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        log('Speech Recognition no soportado', 'warning');
        elements.micButton.style.opacity = '0.5';
        return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    state.recognition = new SpeechRecognition();
    state.recognition.lang = 'es-ES';
    state.recognition.continuous = true;
    state.recognition.interimResults = true;

    state.recognition.onstart = () => {
        elements.micButton.classList.add('recording', 'active');
        log('🎤 Micrófono ACTIVO (modo continuo)', 'success');
    };

    state.recognition.onresult = (event) => {
        const lastResult = event.results[event.results.length - 1];
        const transcript = lastResult[0].transcript;
        elements.userInput.value = transcript;

        if (lastResult.isFinal && transcript.trim()) {
            sendMessage();
            elements.userInput.value = '';
        }
    };

    state.recognition.onend = () => {
        if (state.micEnabled && !state.isPlayingAudio) {
            setTimeout(() => {
                if (state.micEnabled) {
                    try {
                        state.recognition.start();
                    } catch (e) {
                        // Already started
                    }
                }
            }, 100);
        } else {
            elements.micButton.classList.remove('recording');
            if (!state.micEnabled) {
                elements.micButton.classList.remove('active');
            }
        }
    };

    state.recognition.onerror = (event) => {
        if (event.error !== 'no-speech' && event.error !== 'aborted') {
            log(`Error de voz: ${event.error}`, 'error');
        }

        if (state.micEnabled && event.error !== 'not-allowed') {
            setTimeout(() => {
                if (state.micEnabled) {
                    try {
                        state.recognition.start();
                    } catch (e) { }
                }
            }, 500);
        } else if (event.error === 'not-allowed') {
            state.micEnabled = false;
            elements.micButton.classList.remove('recording', 'active');
            log('Permiso de micrófono denegado', 'error');
        }
    };
}

function toggleMic() {
    if (!state.recognition) return;

    state.micEnabled = !state.micEnabled;

    if (state.micEnabled) {
        try {
            state.recognition.start();
            log('🎤 Micrófono activado (modo continuo)', 'success');
        } catch (e) {
            // Already started
        }
    } else {
        state.recognition.stop();
        elements.micButton.classList.remove('recording', 'active');
        log('🔇 Micrófono desactivado', 'info');
    }
}

// ============================================
// Control Functions
// ============================================
function toggleAudio() {
    state.audioEnabled = !state.audioEnabled;
    elements.audioToggle.classList.toggle('active', state.audioEnabled);
    elements.audioToggle.querySelector('.icon').textContent = state.audioEnabled ? '🔊' : '🔇';
    elements.audioToggle.childNodes[2].textContent = state.audioEnabled ? ' Audio ON' : ' Audio OFF';
    log(`Audio ${state.audioEnabled ? 'activado' : 'desactivado'}`, 'info');
}

async function resetChat() {
    try {
        const response = await fetch('/api/reset', { method: 'POST' });
        if (response.ok) {
            elements.chatHistory.innerHTML = `
                <div class="message ai-message">
                    <div class="message-label">TAMARA</div>
                    ¡Hola! Soy TAMARA, tu asistente inteligente. ¿En qué puedo ayudarte hoy?
                </div>
            `;
            state.audioQueue = [];
            log('Chat reiniciado', 'success');
        }
    } catch (error) {
        log('Error al reiniciar', 'error');
    }
}

function reconnect() {
    state.reconnectAttempts = 0;
    if (state.ws) state.ws.close();
    setTimeout(connect, 500);
}

// ============================================
// Event Listeners
// ============================================
function setupEventListeners() {
    elements.sendButton.addEventListener('click', sendMessage);

    elements.userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    elements.micButton.addEventListener('click', toggleMic);
    elements.audioToggle.addEventListener('click', toggleAudio);
    elements.reconnectBtn.addEventListener('click', reconnect);
    elements.resetBtn.addEventListener('click', resetChat);
}

// ============================================
// Initialization
// ============================================
function init() {
    log('Iniciando TAMARA...', 'info');

    initElements();
    setupEventListeners();
    initSpeechRecognition();
    connect();

    // Keepalive ping
    setInterval(() => {
        if (state.ws && state.ws.readyState === WebSocket.OPEN) {
            state.ws.send(JSON.stringify({ type: 'ping' }));
        }
    }, CONFIG.keepaliveInterval);
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', init);
