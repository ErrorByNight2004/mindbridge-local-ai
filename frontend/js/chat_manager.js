
function sendQuick(txt) {
    document.getElementById('msgInput').value = txt;
    sendMessage();
}

function currentChatLanguage() {
    return (window.getCurrentLanguage && window.getCurrentLanguage()) || 'en';
}

async function sendMessage() {
    const inEl = document.getElementById('msgInput');
    const txt = inEl.value.trim();

    if (!txt || isProc) return;

    if (window.stopMicInput) window.stopMicInput();

    isProc = true;
    inEl.value = '';
    inEl.style.height = 'auto';

    document.getElementById('welcome')?.remove();
    document.getElementById('mainContainer')?.classList.remove('empty-state');

    addMsg('user', txt);
    addMsg(
        'assistant',
        '<i data-lucide="loader-2" style="width:20px;animation:spin 1.5s linear infinite;color:var(--gray);"></i>',
        'loading'
    );

    try {
        const res = await fetch(API + '/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: txt,
                session_id: SESSION_ID,
                language: currentChatLanguage()
            })
        });

        if (!res.ok) {
            throw new Error(`Chat request failed: HTTP ${res.status}`);
        }

        const data = await res.json();
        const loading = document.getElementById('loading');
        if (loading) loading.remove();

        const responseText =
            typeof data.response === 'string' && data.response.trim()
                ? data.response.trim()
                : 'I could not generate a response. Please try again.';

        addMsg('assistant', responseText);

        // Keep knowledge-source details out of the normal chat interface.
        if (Array.isArray(data.client_events)) {
            data.client_events.forEach(ev => {
                if (
                    ev.type === 'add_activity' &&
                    window.addActivityFromAI
                ) {
                    window.addActivityFromAI(ev.text);
                } else if (
                    ev.type === 'add_thought_record' &&
                    window.addThoughtRecordFromAI
                ) {
                    window.addThoughtRecordFromAI(ev.record);
                } else if (
                    ev.type === 'add_sleep_log' &&
                    window.addSleepLogFromAI
                ) {
                    window.addSleepLogFromAI(ev.log);
                } else if (
                    ev.type === 'start_sos_exercise' &&
                    window.startSosExerciseFromAI
                ) {
                    window.startSosExerciseFromAI(ev);
                } else if (
                    ev.type === 'start_breathing' &&
                    window.startBreathingFromAI
                ) {
                    window.startBreathingFromAI();
                } else if (
                    ev.type === 'open_test' &&
                    window.openTestFromAI
                ) {
                    window.openTestFromAI(ev.test_type);
                }
            });
        }

        if (ttsEnabled && window.playAssistantSpeech) {
            await window.playAssistantSpeech(
                responseText,
                currentChatLanguage()
            );
        }
    } catch (error) {
        console.error('MindBridge chat error:', error);

        const loading = document.getElementById('loading');
        if (loading) loading.remove();

        addMsg(
            'assistant',
            currentChatLanguage() === 'en'
                ? 'Sorry, I could not complete that request. Please try again.'
                : 'Извините, не удалось выполнить запрос. Попробуйте ещё раз.'
        );
    } finally {
        isProc = false;
    }
}

function addRagSources(context, trace) {
    // Intentionally hide internal knowledge-source details in the chat UI.
    return;
}

function addMsg(role, content, id = '') {
    const list = document.getElementById('messages');
    if (!list) return;

    // Prevent duplicate message IDs from creating duplicate chat bubbles.
    if (id && document.getElementById(id)) {
        document.getElementById(id).remove();
    }

    const div = document.createElement('div');
    div.className = 'msg ' + role;
    if (id) div.id = id;

    const avatarIcon = role === 'user' ? 'user' : 'sparkles';

    // Escape model text before inserting it into HTML.
    const escapeHtml = value =>
        String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');

    let parsed = escapeHtml(content);

    // Preserve simple Markdown formatting for bold text.
    parsed = parsed.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Convert newlines to paragraph breaks safely.
    parsed = parsed
        .split(/\n{2,}/)
        .map(paragraph => `<p>${paragraph.replace(/\n/g, '<br>')}</p>`)
        .join('');

    div.innerHTML = `
        <div class="msg-avatar">
            <i data-lucide="${avatarIcon}" style="width:18px;"></i>
        </div>
        <div class="msg-content">${parsed}</div>
    `;

    list.appendChild(div);

    if (window.lucide) {
        window.lucide.createIcons();
    }

    list.scrollTop = list.scrollHeight;
}
