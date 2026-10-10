/**
 * CodeAlpha Language Translation Tool - Modern Frontend Application Script
 * Features: DeepL integration, Clean Select Dropdowns, Live Debounced Translate, Sample Chips, Speech TTS
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Element References
    const sourceText = document.getElementById('source-text');
    const targetText = document.getElementById('target-text');
    const sourceLangSelect = document.getElementById('source-lang-select');
    const targetLangSelect = document.getElementById('target-lang-select');
    const swapLangBtn = document.getElementById('swap-lang-btn');
    const translateBtn = document.getElementById('translate-btn');
    const translateSpinner = document.getElementById('translate-spinner');
    const clearInputBtn = document.getElementById('clear-input-btn');
    const pasteInputBtn = document.getElementById('paste-input-btn');
    const copyOutputBtn = document.getElementById('copy-output-btn');
    const copyBtnText = document.getElementById('copy-btn-text');
    const speakOutputBtn = document.getElementById('speak-output-btn');
    const charCount = document.getElementById('char-count');
    const charMeterFill = document.getElementById('char-meter-fill');
    const outputMetaText = document.getElementById('output-meta-text');
    const outputPlaceholder = document.getElementById('output-placeholder');
    const alertBanner = document.getElementById('alert-banner');
    const alertMessage = document.getElementById('alert-message');
    const alertCloseBtn = document.getElementById('alert-close-btn');
    const toastContainer = document.getElementById('toast-container');
    const sampleChips = document.querySelectorAll('.sample-chip');

    let autoTranslateTimer = null;

    // Live Character Counter & Meter Fill
    function updateCharCount() {
        const length = sourceText.value.length;
        const maxLimit = parseInt(sourceText.getAttribute('maxlength') || '5000', 10);
        charCount.textContent = length.toLocaleString();

        if (charMeterFill) {
            const pct = Math.min(100, Math.round((length / maxLimit) * 100));
            charMeterFill.style.width = `${pct}%`;
            if (pct > 85) {
                charMeterFill.style.background = '#f43f5e';
            } else {
                charMeterFill.style.background = 'linear-gradient(135deg, #38bdf8 0%, #818cf8 100%)';
            }
        }
    }

    sourceText.addEventListener('input', () => {
        updateCharCount();
        
        // Debounced Auto-Translate (600ms typing delay)
        clearTimeout(autoTranslateTimer);
        const val = sourceText.value.trim();
        if (val.length >= 3) {
            autoTranslateTimer = setTimeout(() => {
                handleTranslate(true); // silent auto-translate
            }, 600);
        } else if (val.length === 0) {
            targetText.value = '';
            if (outputPlaceholder) outputPlaceholder.classList.remove('hidden');
            copyOutputBtn.disabled = true;
            speakOutputBtn.disabled = true;
            outputMetaText.textContent = 'Ready';
        }
    });

    // Language Select Change Listeners
    sourceLangSelect.addEventListener('change', () => {
        if (sourceText.value.trim().length > 0) {
            handleTranslate();
        }
    });

    targetLangSelect.addEventListener('change', () => {
        if (sourceText.value.trim().length > 0) {
            handleTranslate();
        }
    });

    // Clear Input
    clearInputBtn.addEventListener('click', () => {
        sourceText.value = '';
        targetText.value = '';
        updateCharCount();
        if (outputPlaceholder) outputPlaceholder.classList.remove('hidden');
        copyOutputBtn.disabled = true;
        speakOutputBtn.disabled = true;
        outputMetaText.textContent = 'Ready';
        sourceText.focus();
        showToast('Input cleared');
    });

    // Paste from Clipboard
    pasteInputBtn.addEventListener('click', async () => {
        try {
            if (navigator.clipboard && navigator.clipboard.readText) {
                const text = await navigator.clipboard.readText();
                if (text) {
                    sourceText.value = text;
                    updateCharCount();
                    showToast('Pasted from clipboard');
                    handleTranslate();
                } else {
                    showToast('Clipboard is empty', 'error');
                }
            } else {
                showToast('Clipboard access not supported in this browser', 'error');
            }
        } catch (err) {
            console.warn('Clipboard read error:', err);
            showToast('Unable to access clipboard. Please paste manually.', 'error');
        }
    });

    // Sample Prompt Chips
    sampleChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const sample = chip.getAttribute('data-sample');
            if (sample) {
                sourceText.value = sample;
                updateCharCount();
                handleTranslate();
            }
        });
    });

    // Swap Languages
    swapLangBtn.addEventListener('click', () => {
        const currentSource = sourceLangSelect.value;
        const currentTarget = targetLangSelect.value;

        if (currentSource === 'auto') {
            showAlert('Cannot swap when source is set to "Detect Language". Select a specific language first.');
            return;
        }

        // Swap select values
        sourceLangSelect.value = currentTarget;
        targetLangSelect.value = currentSource;

        // If target had text, move it to source
        if (targetText.value.trim()) {
            const oldSourceText = sourceText.value;
            sourceText.value = targetText.value;
            targetText.value = oldSourceText;
            updateCharCount();
        }

        showToast(`Swapped to ${targetLangSelect.options[targetLangSelect.selectedIndex].text}`);
        if (sourceText.value.trim().length > 0) {
            handleTranslate();
        }
    });

    // Main Translate Action
    async function handleTranslate(isSilent = false) {
        const text = sourceText.value.trim();
        const sourceLang = sourceLangSelect.value;
        const targetLang = targetLangSelect.value;

        hideAlert();

        if (!text) {
            if (!isSilent) {
                showAlert('Please enter some text to translate.');
                sourceText.focus();
            }
            return;
        }

        setLoading(true);
        const startTime = performance.now();

        try {
            const response = await fetch('/api/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    source_lang: sourceLang,
                    target_lang: targetLang
                })
            });

            const data = await response.json();
            const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);

            if (!response.ok || !data.success) {
                const errorMessage = data.error || `Translation request failed (HTTP ${response.status})`;
                showAlert(errorMessage);
                outputMetaText.textContent = 'Translation failed';
                return;
            }

            // Success: update UI
            targetText.value = data.translated_text;
            if (outputPlaceholder) outputPlaceholder.classList.add('hidden');
            
            copyOutputBtn.disabled = false;
            speakOutputBtn.disabled = false;

            const detectedNote = (sourceLang === 'auto' && data.source_lang) ? ` (Detected: ${data.source_lang.toUpperCase()})` : '';
            outputMetaText.textContent = `Completed in ${elapsed}s (${data.character_count} chars)${detectedNote}`;
            
            if (!isSilent) {
                showToast('Translation successful!', 'success');
            }

        } catch (err) {
            console.error('Fetch translation error:', err);
            showAlert('Network error: Unable to reach backend server. Make sure Flask app is running.');
            outputMetaText.textContent = 'Connection error';
        } finally {
            setLoading(false);
        }
    }

    translateBtn.addEventListener('click', () => handleTranslate());

    // Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            handleTranslate();
        }
    });

    // Copy Output to Clipboard
    copyOutputBtn.addEventListener('click', async () => {
        const textToCopy = targetText.value;
        if (!textToCopy) return;

        try {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(textToCopy);
            } else {
                targetText.select();
                document.execCommand('copy');
            }

            copyBtnText.textContent = 'Copied!';
            showToast('Translated text copied to clipboard!', 'success');
            setTimeout(() => {
                copyBtnText.textContent = 'Copy';
            }, 2000);
        } catch (err) {
            console.error('Copy error:', err);
            showToast('Failed to copy text', 'error');
        }
    });

    // Listen / Text-to-Speech
    speakOutputBtn.addEventListener('click', () => {
        const textToSpeak = targetText.value;
        if (!textToSpeak) return;

        if (!('speechSynthesis' in window)) {
            showToast('Text-to-speech not supported in this browser', 'error');
            return;
        }

        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(textToSpeak);
        utterance.lang = targetLangSelect.value;
        utterance.rate = 1.0;
        
        showToast('Playing audio pronunciation...');
        window.speechSynthesis.speak(utterance);
    });

    // Alert Banner Helpers
    function showAlert(msg) {
        alertMessage.textContent = msg;
        alertBanner.classList.remove('hidden');
    }

    function hideAlert() {
        alertBanner.classList.add('hidden');
        alertMessage.textContent = '';
    }

    alertCloseBtn.addEventListener('click', hideAlert);

    // Toast Notification System
    function showToast(message, type = 'default') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;

        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => toast.remove(), 300);
        }, 2800);
    }

    // Loading State Helper
    function setLoading(isLoading) {
        translateBtn.disabled = isLoading;
        if (isLoading) {
            translateSpinner.classList.remove('hidden');
            translateBtn.querySelector('.btn-text').textContent = 'Translating...';
            if (translateBtn.querySelector('.btn-icon')) {
                translateBtn.querySelector('.btn-icon').style.display = 'none';
            }
        } else {
            translateSpinner.classList.add('hidden');
            translateBtn.querySelector('.btn-text').textContent = 'Translate';
            if (translateBtn.querySelector('.btn-icon')) {
                translateBtn.querySelector('.btn-icon').style.display = 'inline-block';
            }
        }
    }

    // Initial setup
    updateCharCount();
});
