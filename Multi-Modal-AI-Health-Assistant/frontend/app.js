/**
 * Multi-Modal AI Health Assistant - Frontend Logic
 * =================================================
 * Handles: Tab navigation, Report analysis, Chat, RL Dashboard
 */

document.addEventListener('DOMContentLoaded', () => {

    // ============================================
    // DOM REFERENCES
    // ============================================
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    // Analysis
    const form = document.getElementById('analysis-form');
    const fileInput = document.getElementById('file-upload');
    const fileDropArea = document.getElementById('file-drop-area');
    const fileMsg = document.getElementById('file-msg');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const spinner = document.getElementById('spinner');
    const emptyState = document.getElementById('empty-state');
    const resultsSection = document.getElementById('results-section');
    const urgencyBanner = document.getElementById('urgency-banner');
    const analysisContent = document.getElementById('analysis-content');
    const rlInfoBar = document.getElementById('rl-info-bar');

    // Chat
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send-btn');
    const chatBtnText = document.getElementById('chat-btn-text');
    const chatSpinner = document.getElementById('chat-spinner');
    const clearChatBtn = document.getElementById('clear-chat-btn');

    // State
    let currentDiagnosisId = null;
    let currentRlState = 'general_query';
    let currentRlAction = 'combined_approach';
    let conversationId = generateId();
    let userLocation = { lat: null, lon: null };
    let chatLoading = false;

    // ============================================
    // INITIALIZATION
    // ============================================
    checkOllamaStatus();
    loadRLDashboard();
    setInterval(checkOllamaStatus, 30000); // Check every 30s

    // Get location
    if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                userLocation.lat = pos.coords.latitude;
                userLocation.lon = pos.coords.longitude;
            },
            () => { /* Location denied - not critical */ }
        );
    }

    // ============================================
    // TAB NAVIGATION
    // ============================================
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;

            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(tc => tc.classList.remove('active'));

            btn.classList.add('active');
            document.getElementById(`tab-${targetTab}`).classList.add('active');

            // Refresh RL dashboard when switching to it
            if (targetTab === 'rl') loadRLDashboard();
        });
    });

    // ============================================
    // FILE UPLOAD UI
    // ============================================
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
            fileMsg.textContent = `✅ ${file.name} (${sizeMB} MB)`;
            fileDropArea.style.borderColor = 'var(--success)';
        }
    });

    // ============================================
    // ANALYSIS FORM SUBMIT
    // ============================================
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Loading state
        btnText.style.display = 'none';
        spinner.style.display = 'block';
        submitBtn.disabled = true;
        emptyState.classList.add('hidden');
        resultsSection.classList.add('hidden');

        const formData = new FormData(form);

        if (userLocation.lat && userLocation.lon) {
            formData.append('latitude', userLocation.lat);
            formData.append('longitude', userLocation.lon);
        }

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                currentDiagnosisId = data.diagnosis_id;
                currentRlState = data.rl_state || 'general_query';
                currentRlAction = data.rl_action || 'combined_approach';

                // Display urgency
                urgencyBanner.className = 'urgency-banner';
                let urgency = (data.urgency_level || 'normal').toLowerCase();
                if (!['critical', 'warning', 'normal'].includes(urgency)) urgency = 'normal';
                urgencyBanner.classList.add(`urgency-${urgency}`);

                const urgencyIcons = { critical: '🚨', warning: '⚠️', normal: '✅' };
                urgencyBanner.textContent = `${urgencyIcons[urgency] || '✅'} URGENCY: ${data.urgency_level || 'NORMAL'}`;

                // Display RL info + engine info
                rlInfoBar.innerHTML = `
                    <span class="rl-tag">🧠 State: ${currentRlState}</span>
                    <span class="rl-tag">⚡ Strategy: ${currentRlAction}</span>
                `;

                // Display analysis
                analysisContent.textContent = data.analysis;

                // Show results
                resultsSection.classList.remove('hidden');
                emptyState.classList.add('hidden');

                // Reset feedback
                document.getElementById('btn-accurate').disabled = false;
                document.getElementById('btn-inaccurate').disabled = false;
                document.getElementById('feedback-thanks').classList.add('hidden');

            } else {
                showAlert('Analysis failed: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            showAlert('Error connecting to server. Make sure the backend is running.\n\nRun: uvicorn backend.main:app --reload');
            console.error(error);
        } finally {
            btnText.style.display = 'inline';
            spinner.style.display = 'none';
            submitBtn.disabled = false;
        }
    });

    // ============================================
    // RL FEEDBACK
    // ============================================
    document.getElementById('btn-accurate').addEventListener('click', () => submitFeedback(true));
    document.getElementById('btn-inaccurate').addEventListener('click', () => submitFeedback(false));

    async function submitFeedback(isAccurate) {
        if (!currentDiagnosisId) return;

        try {
            await fetch('/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    diagnosis_id: currentDiagnosisId,
                    is_accurate: isAccurate,
                    state: currentRlState,
                    action: currentRlAction
                })
            });

            document.getElementById('btn-accurate').disabled = true;
            document.getElementById('btn-inaccurate').disabled = true;
            document.getElementById('feedback-thanks').classList.remove('hidden');

            // Refresh RL dashboard
            loadRLDashboard();
        } catch (e) {
            console.error('Error submitting feedback:', e);
        }
    }

    // ============================================
    // CHAT FUNCTIONALITY
    // ============================================
    chatSendBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !chatLoading) sendChatMessage();
    });
    clearChatBtn.addEventListener('click', clearChat);

    async function sendChatMessage() {
        const message = chatInput.value.trim();
        if (!message || chatLoading) return;

        chatLoading = true;

        // Add user bubble
        addChatBubble(message, 'user');
        chatInput.value = '';

        // Loading state
        chatBtnText.style.display = 'none';
        chatSpinner.style.display = 'block';
        chatSendBtn.disabled = true;

        // Add thinking indicator
        const thinkingBubble = addChatBubble('Thinking...', 'assistant');
        thinkingBubble.querySelector('.bubble-content').style.opacity = '0.5';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    conversation_id: conversationId
                })
            });

            const data = await response.json();

            // Remove thinking bubble
            thinkingBubble.remove();

            if (data.success) {
                const engineInfo = data.engine ? `[${data.engine}]` : '';
                addChatBubble(data.response, 'assistant', engineInfo);
            } else {
                addChatBubble('Sorry, I encountered an error. Please try again.', 'assistant');
            }
        } catch (error) {
            thinkingBubble.remove();
            addChatBubble('Unable to connect to the server. Make sure the backend is running.', 'assistant');
            console.error(error);
        } finally {
            chatBtnText.style.display = 'inline';
            chatSpinner.style.display = 'none';
            chatSendBtn.disabled = false;
            chatLoading = false;
            chatInput.focus();
        }
    }

    function addChatBubble(text, role, engineInfo = '') {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${role}`;

        const content = document.createElement('div');
        content.className = 'bubble-content';

        if (role === 'assistant' && engineInfo) {
            const engineTag = document.createElement('div');
            engineTag.style.cssText = 'font-size:0.7rem;color:var(--text-muted);margin-bottom:6px;font-weight:500;';
            engineTag.textContent = engineInfo;
            content.appendChild(engineTag);
        }

        const textNode = document.createElement('div');
        textNode.style.whiteSpace = 'pre-wrap';
        textNode.textContent = text;
        content.appendChild(textNode);

        bubble.appendChild(content);
        chatMessages.appendChild(bubble);

        chatMessages.scrollTop = chatMessages.scrollHeight;
        return bubble;
    }

    function clearChat() {
        // Keep welcome message, remove the rest
        const bubbles = chatMessages.querySelectorAll('.chat-bubble');
        bubbles.forEach((bubble, index) => {
            if (index > 0) bubble.remove();
        });
        conversationId = generateId();

        // Clear on server
        fetch(`/api/chat/${conversationId}`, { method: 'DELETE' }).catch(() => {});
    }

    // ============================================
    // RL DASHBOARD
    // ============================================
    async function loadRLDashboard() {
        try {
            const response = await fetch('/api/rl/metrics');
            const data = await response.json();

            if (!data.success) return;

            const m = data.metrics;

            // Update stat cards
            document.getElementById('rl-total').textContent = m.total_feedback || 0;
            document.getElementById('rl-positive').textContent = m.positive_feedback || 0;
            document.getElementById('rl-negative').textContent = m.negative_feedback || 0;
            document.getElementById('rl-accuracy').textContent = `${m.accuracy || 0}%`;

            // Epsilon bar
            const epsilonPercent = ((m.epsilon || 1) * 100).toFixed(1);
            document.getElementById('epsilon-bar').style.width = `${epsilonPercent}%`;
            document.getElementById('epsilon-text').textContent =
                `ε = ${(m.epsilon || 1).toFixed(4)} (${epsilonPercent}% Exploration)`;

            // Reward history chart
            renderRewardChart(m.reward_history || []);

            // Q-Table
            renderQTable(m.q_table_summary || {}, m.states || [], m.actions || []);

        } catch (e) {
            // Server not running - silent fail
        }
    }

    function renderRewardChart(rewards) {
        const container = document.getElementById('reward-chart');

        if (!rewards.length) {
            container.innerHTML = '<div class="chart-empty">No data yet. Provide feedback to train the RL agent.</div>';
            return;
        }

        container.innerHTML = '';
        const maxBars = 50;
        const displayRewards = rewards.slice(-maxBars);
        const maxHeight = 120;

        displayRewards.forEach(reward => {
            const bar = document.createElement('div');
            bar.className = `chart-bar ${reward >= 0 ? 'positive' : 'negative'}`;
            const height = Math.abs(reward) * (maxHeight / 2) + 10;
            bar.style.height = `${height}px`;
            bar.title = `Reward: ${reward > 0 ? '+' : ''}${reward}`;
            container.appendChild(bar);
        });
    }

    function renderQTable(summary, states, actions) {
        const container = document.getElementById('q-table-container');

        if (!states || !states.length) {
            container.innerHTML = '<div class="chart-empty">Q-Table will appear after the agent starts learning.</div>';
            return;
        }

        // Check if there's any non-zero data
        const hasData = Object.values(summary).some(s => s && s.q_value !== 0);
        if (!hasData) {
            container.innerHTML = '<div class="chart-empty">Q-Table will populate as the agent receives feedback and learns.</div>';
            return;
        }

        let html = '<table class="q-table"><thead><tr><th>State</th><th>Best Strategy</th><th>Q-Value</th></tr></thead><tbody>';

        states.forEach(state => {
            const info = summary[state];
            if (!info || info.q_value === 0) return;

            const qClass = info.q_value > 0 ? 'q-val-high' : (info.q_value < 0 ? 'q-val-low' : 'q-val-zero');
            html += `<tr>
                <td class="state-name">${formatStateName(state)}</td>
                <td>${formatActionName(info.action)}</td>
                <td class="${qClass}">${info.q_value.toFixed(4)}</td>
            </tr>`;
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    }

    // ============================================
    // OLLAMA STATUS CHECK
    // ============================================
    async function checkOllamaStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            const statusDot = document.querySelector('.status-dot');
            const statusText = document.getElementById('status-text');

            const ollamaUp = data.ollama && data.ollama.running;
            const onlineUp = data.ollama && data.ollama.online_available;
            const provider = data.ollama ? data.ollama.online_provider : '';

            if (ollamaUp && onlineUp) {
                statusDot.className = 'status-dot online';
                statusText.textContent = `Online (${provider}) + Offline (Ollama)`;
            } else if (onlineUp) {
                statusDot.className = 'status-dot online';
                statusText.textContent = `Online (${provider})`;
            } else if (ollamaUp) {
                statusDot.className = 'status-dot online';
                statusText.textContent = 'Offline (Ollama)';
            } else {
                statusDot.className = 'status-dot offline';
                statusText.textContent = 'No AI Available';
            }
        } catch (e) {
            const statusDot = document.querySelector('.status-dot');
            const statusText = document.getElementById('status-text');
            statusDot.className = 'status-dot offline';
            statusText.textContent = 'Server Offline';
        }
    }

    // ============================================
    // UTILITY FUNCTIONS
    // ============================================
    function generateId() {
        return 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    function formatStateName(state) {
        return state.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    function formatActionName(action) {
        const names = {
            'keyword_basic': '🔤 Keyword',
            'knowledge_base': '📚 Knowledge Base',
            'ollama_standard': '🤖 AI Standard',
            'ollama_detailed': '🤖 AI Detailed',
            'combined_approach': '🔗 Combined'
        };
        return names[action] || action;
    }

    function showAlert(message) {
        alert(message);
    }
});
