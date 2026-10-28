
const API = window.location.origin;

function makeSessionId() {
    if (window.crypto?.randomUUID) {
        return 'session_' + window.crypto.randomUUID();
    }

    return 'session_' +
        Date.now().toString(36) + '_' +
        Math.random().toString(36).slice(2);
}

let sessionId = localStorage.getItem('SESSION_ID');

if (!sessionId) {
    sessionId = makeSessionId();
    localStorage.setItem('SESSION_ID', sessionId);
}

let SESSION_ID = sessionId;
let isProc = false;

const HISTORY_KEYS = ['phqHistory', 'gadHistory', 'esteemHistory'];

function readHistory(key) {
    try {
        const value = JSON.parse(localStorage.getItem(key) || '[]');
        return Array.isArray(value) ? value : [];
    } catch (error) {
        console.error('Could not read history:', key, error);
        return [];
    }
}

function sessionStorageKey(key, session = SESSION_ID) {
    return `session:${session}:${key}`;
}

// Initialize all three histories together, so migration happens once.
function ensureSessionHistoriesInitialized() {
    const marker = `session:${SESSION_ID}:history_migrated`;

    if (localStorage.getItem(marker) !== null) {
        return;
    }

    const alreadyScoped = HISTORY_KEYS.some(
        key => localStorage.getItem(sessionStorageKey(key)) !== null
    );

    HISTORY_KEYS.forEach(key => {
        const scopedKey = sessionStorageKey(key);

        if (localStorage.getItem(scopedKey) === null) {
            const history = alreadyScoped ? [] : readHistory(key);
            saveSessionHistory(key, history);
        }
    });

    localStorage.setItem(marker, '1');
}

function getSessionHistory(key) {
    ensureSessionHistoriesInitialized();
    return readHistory(sessionStorageKey(key));
}

function saveSessionHistory(key, items) {
    localStorage.setItem(
        sessionStorageKey(key),
        JSON.stringify(Array.isArray(items) ? items : [])
    );
}

async function syncData(endpoint, storageKey) {
    const items = readHistory(storageKey);

    try {
        await fetch(API + endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: SESSION_ID,
                items
            })
        });
    } catch (error) {
        console.error('Failed to sync', storageKey, error);
    }
}

async function syncTests() {
    const phq = getSessionHistory('phqHistory')
        .map(t => ({ ...t, name: 'PHQ-9' }));

    const gad = getSessionHistory('gadHistory')
        .map(t => ({ ...t, name: 'GAD-7' }));

    const esteem = getSessionHistory('esteemHistory')
        .map(t => ({ ...t, name: 'Rosenberg' }));

    try {
        await fetch(API + '/api/sync/tests', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: SESSION_ID,
                items: phq.concat(gad, esteem)
            })
        });
    } catch (error) {
        console.error('Failed to sync tests', error);
    }
}

function createNewSession() {
    const previousSessionId = SESSION_ID;
    const newSessionId = makeSessionId();

    // If this fails, the current session remains active.
    localStorage.setItem('SESSION_ID', newSessionId);

    try {
        SESSION_ID = newSessionId;

        HISTORY_KEYS.forEach(key => saveSessionHistory(key, []));
        localStorage.setItem(
            `session:${SESSION_ID}:history_migrated`,
            '1'
        );

        return SESSION_ID;
    } catch (error) {
        SESSION_ID = previousSessionId;

        try {
            localStorage.setItem('SESSION_ID', previousSessionId);
        } catch (restoreError) {
            console.error(
                'Could not restore previous session ID:',
                restoreError
            );
        }

        throw error;
    }
}
