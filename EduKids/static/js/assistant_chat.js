(() => {
  // Only run this script on the assistant chat page.
  if (!document.getElementById('assistant-chat-root') && !location.pathname.startsWith('/assistant/chat')) {
    // not on assistant page — skip initialization to avoid adding Lottie or sockets on other pages
    return;
  }
  const wsProto = location.protocol === 'https:' ? 'wss' : 'ws';
  const wsUrl = `${wsProto}://${location.host}/ws/assistant/`;
  let socket = null;
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 10;
  const pendingMessages = [];
  // Reuse a conversation id while the chat modal is open. Stored per-tab.
  let currentConversationId = sessionStorage.getItem('assistant_conversation_id');

  function createSocket() {
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      reconnectAttempts = 0;
      appendMessage('Connecté à l\'assistant…', 'assistant');
      // flush pending messages
      while (pendingMessages.length && socket.readyState === WebSocket.OPEN) {
        const m = pendingMessages.shift();
        socket.send(JSON.stringify(m));
      }
      // enable send button
      if (sendBtn) sendBtn.disabled = false;
    };

    socket.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        // Conversation id response from server (created or confirmed)
        if (data.type === 'conversation' && data.id) {
          currentConversationId = String(data.id);
          try { sessionStorage.setItem('assistant_conversation_id', currentConversationId); } catch (e) { /* ignore */ }
          // update UI title if provided
          if (data.title) {
            const topicBadge = document.getElementById('assistant-topic-badge');
            if (topicBadge) topicBadge.textContent = data.title;
          }
          return; // conversation notice doesn't need further handling
        }
        if (data.type === 'partial') {
          // show partial (append as assistant partial or update last)
          appendMessage(data.text, 'assistant');
          // Don't speak partials - wait for complete response
        } else if (data.type === 'quiz_start') {
          // WebSocket-initiated quiz (server pushed)
          // data: { type: 'quiz_start', title, question: {id, question, choices: []} }
          renderWsQuizStart(data);
        } else if (data.type === 'quiz_question') {
          renderWsQuizQuestion(data.question || data);
        } else if (data.type === 'quiz_feedback') {
          // feedback contains result and explanation
          const fb = data.result || {};
          const explanation = fb.explanation || data.result?.explanation || JSON.stringify(fb);
          appendMessage(`Feedback: ${explanation}`, 'assistant');
        } else if (data.type === 'quiz_done') {
          appendMessage(data.summary || 'Quiz terminé', 'assistant');
        } else if (data.type === 'image') {
          // image sent as base64 over websocket
          try {
            const b64 = data.image_b64;
            const blob = b64ToBlob(b64, data.content_type || 'image/png');
            const url = URL.createObjectURL(blob);
            const img = document.createElement('img'); img.src = url; img.style.maxWidth = '100%'; img.style.border = '3px solid #667eea'; img.style.borderRadius = '12px';
            messagesEl.appendChild(img);
            messagesEl.scrollTop = messagesEl.scrollHeight;
          } catch (e) {
            appendMessage('Erreur affichage image', 'assistant');
          }
        } else if (data.type === 'pdf') {
          try {
            const b64 = data.pdf_b64;
            const blob = b64ToBlob(b64, data.content_type || 'application/pdf');
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = url; a.download = data.filename || 'document.pdf'; a.textContent = `Télécharger ${data.filename || 'document.pdf'}`;
            a.style.cssText = 'display:inline-block;margin:8px;padding:8px;border-radius:8px;background:#eef2ff;color:#333;border:1px solid #667eea;';
            messagesEl.appendChild(a);
            messagesEl.scrollTop = messagesEl.scrollHeight;
          } catch (e) {
            appendMessage('Erreur affichage PDF', 'assistant');
          }
        } else if (data.type === 'done') {
          // Response complete - replace last assistant chunk with sanitized final text
          if (window._lastAssistantMsg && data.text) {
            window._lastAssistantMsg.textContent = data.text;
          }
          // Now speak it if TTS is enabled
          if (ttsEl && ttsEl.checked && window._lastAssistantMsg) {
            const fullText = window._lastAssistantMsg.textContent;
            speak(fullText, langEl.value);
          }
          // Mark the end of this response
          window._lastAssistantMsg = null;
        } else if (data.type === 'error') {
          appendMessage('❌ Erreur: ' + data.text, 'assistant');
          window._lastAssistantMsg = null;
        }
      } catch (err) {
        appendMessage(e.data, 'assistant');
      }
    };

    socket.onclose = () => {
      appendMessage('Déconnecté', 'assistant');
      if (sendBtn) sendBtn.disabled = true;
      // try reconnect with backoff
      if (reconnectAttempts < maxReconnectAttempts) {
        const delay = Math.min(30000, 1000 * Math.pow(2, reconnectAttempts));
        reconnectAttempts += 1;
        setTimeout(() => { createSocket(); }, delay);
      }
    };

    socket.onerror = (err) => {
      console.warn('WebSocket error', err);
    };
  }

  // initialize socket
  createSocket();

  const messagesEl = document.getElementById('messages');
  const inputEl = document.getElementById('input');
  const sendBtn = document.getElementById('send');
  const langEl = document.getElementById('language');
  const ttsEl = document.getElementById('tts');
  const searchInput = document.getElementById('search-query');
  const searchBtn = document.getElementById('search-btn');
  const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
  const deleteAllBtn = document.getElementById('delete-all-btn');
  // searchResults can be provided either by the page (id="search-results") or inside
  // the assistant modal (id="assistant-search-results"). We resolve it at runtime
  // because the modal markup may be created dynamically.
  function getSearchResultsElement() {
    return document.getElementById('assistant-search-results') || document.getElementById('search-results');
  }
  let searchResults = null;
  let studentId = localStorage.getItem('edukids_student_id');
  if (!studentId) {
    studentId = prompt('Entrez votre student_id (ex: 1) pour enregistrer les conversations:');
    if (studentId) localStorage.setItem('edukids_student_id', studentId);
  }
  // Elements for lottie + start button
  const lottieContainer = document.getElementById('assistant-lottie');
  const startBtn = document.getElementById('start-discussion');
  // If the assistant modal is present, clear conversation id when it is closed so a new
  // conversation starts on the next open. While the modal remains open, the same
  // conversation id will be reused for all messages.
  const assistantModalEl = document.getElementById('assistantChatModal');
  if (assistantModalEl) {
    assistantModalEl.addEventListener('hidden.bs.modal', () => {
      try { sessionStorage.removeItem('assistant_conversation_id'); } catch (e) { /* ignore */ }
      currentConversationId = null;
    });
  }

  // Load lottie animation from static asset if lottie is available
  try {
    if (window.lottie && lottieContainer && !window.__lottie_animation_loaded) {
      window.__lottie_animation_loaded = true;
      // Clear any existing SVG
      lottieContainer.innerHTML = '';
      fetch('/static/animations/assistant_lottie.json')
        .then(r => r.json())
        .then(data => {
          window.lottie.loadAnimation({
            container: lottieContainer,
            renderer: 'svg',
            loop: true,
            autoplay: true,
            animationData: data
          });
        }).catch(()=>{});
    }
  } catch(e) {
    // ignore
  }

  if (startBtn) {
    startBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      inputEl.focus();
    });
  }

  function appendMessage(text, cls) {
    const div = document.createElement('div');
    div.className = 'msg ' + cls;
    
    // For assistant messages, accumulate partial responses into complete paragraphs
    // to make TTS more natural and readable
    if (cls === 'assistant' && window._lastAssistantMsg && !text.includes('[error]') && !text.includes('Erreur')) {
      // This is a partial chunk - append to the last assistant message
      window._lastAssistantMsg.textContent += text;
      messagesEl.scrollTop = messagesEl.scrollHeight;
      return;
    }
    
    // Format text for better readability (preserve line breaks but make them paragraphs)
    const formattedText = text.trim();
    div.textContent = formattedText;
    
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    
    // Track last assistant message for accumulation
    if (cls === 'assistant') {
      window._lastAssistantMsg = div;
    } else {
      // Clear tracking when student sends a message
      window._lastAssistantMsg = null;
    }
    
    // Add a clearfix div to ensure proper float clearing
    const clearDiv = document.createElement('div');
    clearDiv.style.clear = 'both';
    messagesEl.appendChild(clearDiv);
  }

  // Helper to display a topic string nicely (Title Case)
  function displayTopic(topic) {
    if (!topic) return 'Général';
    return topic.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  }

  function renderMessage(msg) {
    // msg: {id, sender_type, content}
    const div = document.createElement('div');
    const cls = msg.sender_type === 'student' ? 'student' : 'assistant';
    div.className = 'msg ' + cls;
    div.dataset.messageId = msg.id;
    div.textContent = (msg.content || '').trim();
    messagesEl.appendChild(div);
    messagesEl.appendChild(Object.assign(document.createElement('div'), { style: 'clear:both' }));

    if (cls === 'student') {
      // Add action buttons (edit/delete)
      const actions = document.createElement('div');
      actions.className = 'msg-actions';
      const editBtn = document.createElement('button');
      editBtn.className = 'icon-btn';
      editBtn.title = 'Modifier';
      editBtn.textContent = '✏️';
      editBtn.style.marginLeft = '8px';
      editBtn.addEventListener('click', () => openInlineEditor(div, msg));
      const delBtn = document.createElement('button');
      delBtn.className = 'icon-btn';
      delBtn.title = 'Delete';
      delBtn.textContent = '🗑️';
      delBtn.style.marginLeft = '8px';
      delBtn.addEventListener('click', () => deleteMessage(msg.id));
      actions.appendChild(editBtn);
      actions.appendChild(delBtn);
      messagesEl.appendChild(actions);
    }
  }

  function openInlineEditor(messageDiv, msg) {
    // Prevent multiple editors
    const next = messageDiv.nextSibling;
    if (next && next.classList && next.classList.contains('inline-editor')) return;

    const editor = document.createElement('div');
    editor.className = 'inline-editor';
    editor.style.cssText = 'clear:both;margin:6px 0;padding:8px;border:2px dashed #667eea;border-radius:12px;background:#fff;';

    const ta = document.createElement('textarea');
    ta.value = (msg && msg.content) || messageDiv.textContent || '';
    ta.style.cssText = 'width:100%;min-height:60px;padding:8px;border-radius:10px;border:2px solid #667eea;font-family:inherit;font-size:14px;';

    const actionRow = document.createElement('div');
    actionRow.style.cssText = 'text-align:right;margin-top:6px;';
    const saveBtn = document.createElement('button');
    saveBtn.className = 'icon-btn';
    saveBtn.title = 'Enregistrer';
    saveBtn.textContent = '�';
    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'icon-btn';
    cancelBtn.title = 'Annuler';
    cancelBtn.textContent = '✖️';
    cancelBtn.style.marginLeft = '8px';

    saveBtn.addEventListener('click', () => {
      const content = ta.value.trim();
      if (!content) return;
      fetch(`/assistant/api/message/${msg.id}/edit/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId, content })
      }).then(r => r.json()).then(resp => {
        if (resp && resp.status === 'ok') {
          messageDiv.textContent = content;
          editor.remove();
        }
      }).catch(e => console.error('Erreur modification message', e));
    });

    cancelBtn.addEventListener('click', () => editor.remove());
    ta.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { e.preventDefault(); editor.remove(); }
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); saveBtn.click(); }
    });

    actionRow.appendChild(saveBtn);
    actionRow.appendChild(cancelBtn);
    editor.appendChild(ta);
    editor.appendChild(actionRow);
    messagesEl.insertBefore(editor, messageDiv.nextSibling);
    ta.focus();
  }

  // (socket handlers are attached in createSocket)

  sendBtn.addEventListener('click', sendMessage);
  inputEl.addEventListener('keydown', (ev) => { if (ev.key === 'Enter' && !ev.shiftKey) { ev.preventDefault(); sendMessage(); } });

  function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;
    // Intercept special commands: quiz:, image:, pdf:
    if (text.toLowerCase().startsWith('quiz:')) {
      const topic = text.slice(5).trim() || 'Quiz';
      generateQuiz(topic);
      inputEl.value = '';
      return;
    }
    if (text.toLowerCase().startsWith('image:')) {
      const label = text.slice(6).trim() || 'EduKids Image';
      generateImage(label);
      inputEl.value = '';
      return;
    }
    if (text.toLowerCase().startsWith('pdf:')) {
      const title = text.slice(4).trim() || 'EduKids Document';
      generatePdf(title);
      inputEl.value = '';
      return;
    }
    const payload = {
      action: 'message',
      content: text,
      language: langEl.value,
      // assistant_id and student_id could be provided here
      student_id: studentId,
      conversation_id: currentConversationId ? Number(currentConversationId) : undefined,
    };
    // if socket not open, queue message and try reconnect
    try {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(payload));
      } else {
        pendingMessages.push(payload);
        // try to create socket if not already connecting
        if (!socket || socket.readyState === WebSocket.CLOSED) createSocket();
        appendMessage('(En attente de connexion) ' + text, 'student');
        inputEl.value = '';
        return;
      }
    } catch (err) {
      // socket may be in CLOSING or CLOSED state
      pendingMessages.push(payload);
      if (!socket || socket.readyState === WebSocket.CLOSED) createSocket();
      appendMessage('(En attente de connexion) ' + text, 'student');
      inputEl.value = '';
      return;
    }
    appendMessage(text, 'student');
    inputEl.value = '';
  }

  function generateQuiz(topic) {
    appendMessage(`(Génération du quiz: ${topic})`, 'assistant');
    fetch('/assistant/api/generate_quiz/', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, num_questions: 5 })
    }).then(r => r.json()).then(data => {
      if (data.quiz) renderQuiz(data.quiz);
      else appendMessage('Erreur lors de la génération du quiz.', 'assistant');
    }).catch(e => { console.error(e); appendMessage('Erreur quiz.', 'assistant'); });
  }

  function renderQuiz(quiz) {
    const box = document.createElement('div');
    box.style.cssText = 'background:#fff;border:3px solid #667eea;border-radius:16px;padding:12px;margin:8px 0;';
    const title = document.createElement('div');
    title.style.cssText = 'font-weight:bold;color:#667eea;margin-bottom:8px;';
    title.textContent = `📝 ${quiz.title || 'Quiz'}`;
    box.appendChild(title);

    const form = document.createElement('form');
    quiz.questions.forEach(q => {
      const qDiv = document.createElement('div');
      qDiv.style.cssText = 'margin:10px 0;padding:8px;border-radius:12px;background:#f7f7ff;';
      const qLabel = document.createElement('div');
      qLabel.style.cssText = 'font-weight:bold;margin-bottom:6px;';
      qLabel.textContent = q.question;
      qDiv.appendChild(qLabel);
      q.choices.forEach((ch, idx) => {
        const id = `q_${q.id}_${idx}`;
        const row = document.createElement('div');
        const radio = document.createElement('input');
        radio.type = 'radio'; radio.name = `q_${q.id}`; radio.value = String(idx); radio.id = id;
        const lab = document.createElement('label'); lab.setAttribute('for', id); lab.textContent = ch;
        row.appendChild(radio); row.appendChild(lab);
        qDiv.appendChild(row);
      });
      form.appendChild(qDiv);
    });
    const submit = document.createElement('button');
    submit.type = 'submit'; submit.textContent = 'Corriger';
    submit.style.cssText = 'padding:8px 14px;border-radius:12px;background:#667eea;color:#fff;border:none;font-weight:bold;';
    form.appendChild(submit);
    box.appendChild(form);
    messagesEl.appendChild(box);
    messagesEl.scrollTop = messagesEl.scrollHeight;

    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const answers = {};
      quiz.questions.forEach(q => {
        const picked = form.querySelector(`input[name="q_${q.id}"]:checked`);
        if (picked) answers[q.id] = parseInt(picked.value, 10);
      });
      fetch('/assistant/api/grade_quiz/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quiz, answers })
      }).then(r => r.json()).then(res => {
        appendMessage(`Score: ${res.correct}/${res.total}`, 'assistant');
      }).catch(e => { console.error(e); appendMessage('Erreur correction.', 'assistant'); });
    });
  }

  function generateImage(text) {
    fetch('/assistant/api/generate_image/', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    }).then(r => r.blob()).then(blob => {
      const url = URL.createObjectURL(blob);
      const img = document.createElement('img');
      img.src = url; img.style.maxWidth = '100%'; img.style.border = '3px solid #667eea'; img.style.borderRadius = '12px';
      messagesEl.appendChild(img);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }).catch(e => { console.error(e); appendMessage('Erreur image.', 'assistant'); });
  }

  // Convert base64 string to Blob
  function b64ToBlob(b64, contentType='application/octet-stream') {
    const byteChars = atob(b64);
    const byteNumbers = new Array(byteChars.length);
    for (let i = 0; i < byteChars.length; i++) {
      byteNumbers[i] = byteChars.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: contentType });
  }

  // Render a quiz initiated by the websocket (interactive flow)
  function renderWsQuizStart(data) {
    const quizTitle = data.title || 'Quiz';
    const q = (data.question || {});
    const box = document.createElement('div');
    box.className = 'ws-quiz-box';
    box.style.cssText = 'background:#fff;border:3px solid #34a853;border-radius:12px;padding:12px;margin:8px 0;';
    const title = document.createElement('div'); title.style.cssText = 'font-weight:bold;color:#34a853;margin-bottom:8px;'; title.textContent = `📝 ${quizTitle}`;
    box.appendChild(title);
    const qDiv = document.createElement('div'); qDiv.style.cssText = 'margin:8px 0;padding:8px;border-radius:8px;background:#f7fff7;';
    const qLabel = document.createElement('div'); qLabel.style.cssText = 'font-weight:bold;margin-bottom:6px;'; qLabel.textContent = q.question || 'Question';
    qDiv.appendChild(qLabel);
    (q.choices || []).forEach((ch, idx) => {
      const btn = document.createElement('button'); btn.textContent = ch; btn.style.cssText = 'display:block;margin:6px 0;padding:8px;border-radius:8px;background:#34a853;color:#fff;border:none;cursor:pointer;';
      btn.addEventListener('click', () => {
        // Send the chosen index as a normal chat message so server will grade it
        const payload = { action: 'message', content: String(idx), language: langEl.value, student_id: studentId, conversation_id: currentConversationId ? Number(currentConversationId) : undefined };
        if (socket && socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify(payload));
        appendMessage(ch, 'student');
      });
      qDiv.appendChild(btn);
    });
    box.appendChild(qDiv);
    messagesEl.appendChild(box);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function renderWsQuizQuestion(q) {
    // q: { id, question, choices }
    const box = document.createElement('div');
    box.style.cssText = 'background:#fff;border:2px dashed #667eea;border-radius:12px;padding:10px;margin:8px 0;';
    const qLabel = document.createElement('div'); qLabel.style.cssText = 'font-weight:bold;margin-bottom:6px;'; qLabel.textContent = q.question || 'Question';
    box.appendChild(qLabel);
    (q.choices || []).forEach((ch, idx) => {
      const btn = document.createElement('button'); btn.textContent = ch; btn.style.cssText = 'margin:6px 6px 6px 0;padding:6px 10px;border-radius:8px;background:#667eea;color:#fff;border:none;cursor:pointer;';
      btn.addEventListener('click', () => {
        const payload = { action: 'message', content: String(idx), language: langEl.value, student_id: studentId, conversation_id: currentConversationId ? Number(currentConversationId) : undefined };
        if (socket && socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify(payload));
        appendMessage(ch, 'student');
      });
      box.appendChild(btn);
    });
    messagesEl.appendChild(box);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function generatePdf(title) {
    const paras = Array.from(messagesEl.querySelectorAll('.msg.assistant')).slice(-3).map(n => n.textContent);
    fetch('/assistant/api/generate_pdf/', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, paragraphs: paras })
    }).then(r => r.blob()).then(blob => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = (title || 'document') + '.pdf'; a.click();
      URL.revokeObjectURL(url);
    }).catch(e => { console.error(e); appendMessage('Erreur PDF.', 'assistant'); });
  }

  function speak(text, lang) {
    if (!('speechSynthesis' in window)) return;
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = lang;
    // Allow adjustable TTS rate via localStorage key 'tts_rate'.
    // Default to 1.2 (20% faster) to "accélérer le lecteur vocale un peu".
    // Clamp to reasonable bounds supported by browsers.
    const stored = localStorage.getItem('tts_rate');
    const rate = stored ? parseFloat(stored) : 1.5;
    utter.rate = Math.min(Math.max(isNaN(rate) ? 1.2 : rate, 0.5), 2.0);
    // Cancel any ongoing speech to avoid overlap, then speak the new utterance.
    try { window.speechSynthesis.cancel(); } catch (e) { /* ignore */ }
    window.speechSynthesis.speak(utter);
  }

  // Microphone / SpeechRecognition support (if available)
  const micBtn = document.getElementById('mic-btn');
  let recognition, recognizing = false;
  if (micBtn && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SR();
    recognition.lang = langEl ? langEl.value || 'fr-FR' : 'fr-FR';
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    micBtn.addEventListener('click', () => {
      if (!recognizing) {
        try {
          recognition.lang = langEl ? langEl.value : 'fr';
          recognition.start();
          recognizing = true;
          micBtn.classList.add('btn-danger');
        } catch (e) { console.warn('SpeechRecognition start failed', e); }
      } else {
        recognition.stop();
        recognizing = false;
        micBtn.classList.remove('btn-danger');
      }
    });

    recognition.onresult = (event) => {
      let interim = '';
      let final = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) final += event.results[i][0].transcript;
        else interim += event.results[i][0].transcript;
      }
      // show interim in input and final when finished
      if (inputEl) inputEl.value = (final || interim).trim();
      if (final && final.trim()) {
        // send automatically after a short debounce
        setTimeout(() => { if (inputEl.value.trim()) sendMessage(); }, 300);
      }
    };

    recognition.onerror = (e) => { 
      // Ignore common errors that don't affect functionality
      const ignoredErrors = ['no-speech', 'aborted', 'network'];
      if (!ignoredErrors.includes(e.error)) {
        console.warn('SpeechRecognition error:', e.error);
      }
      recognizing = false; 
      if (micBtn) micBtn.classList.remove('btn-danger'); 
    };
    recognition.onend = () => { 
      recognizing = false; 
      if (micBtn) micBtn.classList.remove('btn-danger'); 
    };
  } else if (micBtn) {
    // hide mic if not supported
    micBtn.style.display = 'none';
  }

  // load conversation history for this student - CHARGE TOUT L'HISTORIQUE
  function loadHistory() {
    if (!studentId) return;
  fetch(`/assistant/api/history/?student_id=${encodeURIComponent(studentId)}&limit=50`)
      .then(r => r.json())
      .then(payload => {
        if (!payload || !payload.conversations) return;
        
        // Effacer les messages existants
        messagesEl.innerHTML = '';
        
        // Grouper par sujet
        const byTopic = {};
        const topicOrder = [];
        (payload.conversations || []).forEach(c => {
          const t = c.topic || 'general';
          if (!byTopic[t]) { byTopic[t] = []; topicOrder.push(t); }
          byTopic[t].push(c);
        });

        // Render topic header using the topic string (short summary generated server-side)

        topicOrder.forEach(topic => {
          // En-tête de sujet
          const th = document.createElement('div');
          th.style.cssText = 'clear:both;text-align:center;padding:10px;margin:10px 0;border-top:3px solid #667eea;';
          th.innerHTML = `<strong style="background:#fff;padding:4px 10px;border-radius:12px;color:#667eea;">🏷️ ${displayTopic(topic)}</strong>`;
          messagesEl.appendChild(th);

          // Conversations de ce sujet
          byTopic[topic].forEach(conv => {
            const ch = document.createElement('div');
            ch.style.cssText = 'display:flex;justify-content:space-between;align-items:center;padding:6px 8px;margin:6px 0;background:#fff;border:2px dashed #667eea;border-radius:12px;';
              const title = (conv.title || 'Conversation');
              const left = document.createElement('div');
              left.style.cssText = 'display:flex;flex-direction:column;gap:4px;';
              left.innerHTML = `<div style="font-weight:700;color:#333">${title}</div><div style="font-size:12px;color:#666">${displayTopic(conv.topic)}</div>`;
            const right = document.createElement('div');
            const openBtn = document.createElement('button');
            openBtn.textContent = 'Open';
            openBtn.style.cssText = 'padding:6px 10px;border-radius:12px;background:#667eea;color:#fff;border:none;cursor:pointer;font-weight:bold;margin-right:8px;';
            openBtn.addEventListener('click', () => loadConversation(conv.id));
            const delC = document.createElement('button');
            delC.textContent = 'Delete';
            delC.style.cssText = 'padding:6px 10px;border-radius:12px;background:#f5576c;color:#fff;border:none;cursor:pointer;font-weight:bold;';
            delC.addEventListener('click', () => deleteConversation(conv.id));
            right.appendChild(openBtn);
            right.appendChild(delC);
            ch.appendChild(left);
            ch.appendChild(right);
            messagesEl.appendChild(ch);
          });
        });
        
        // Faire défiler vers le bas pour voir les messages les plus récents
        messagesEl.scrollTop = messagesEl.scrollHeight;
      }).catch((err) => {
        console.error('Erreur chargement historique:', err);
      });
  }

  // try to load history on start
  loadHistory();

  // Load a single conversation into the UI
  function loadConversation(conversationId) {
    if (!studentId) return;
    fetch(`/assistant/api/conversation/${conversationId}/?student_id=${encodeURIComponent(studentId)}`)
      .then(r => r.json())
      .then(data => {
        if (!data || !data.conversation) return;
        messagesEl.innerHTML = '';
        const header = document.createElement('div');
        header.style.cssText = 'clear:both;text-align:center;padding:12px 0;margin:8px 0;border-top:2px dashed #667eea;';
      
    messagesEl.appendChild(header);
    const topicBadge = document.createElement('div');
    topicBadge.style.cssText = 'text-align:center;margin:6px 0;';
    topicBadge.innerHTML = `<small style="background:#fff;padding:6px 10px;border-radius:12px;color:#444;border:1px solid #eee;">🏷️ ${displayTopic(data.conversation.topic)}</small>`;
    messagesEl.appendChild(topicBadge);
  const delC = document.createElement('button');
  delC.textContent = 'Delete';
  delC.style.cssText = 'margin:6px 0;padding:6px 10px;border-radius:12px;background:#f5576c;color:#fff;border:none;cursor:pointer;font-weight:bold;';
    delC.addEventListener('click', () => deleteConversation(conversationId));
    messagesEl.appendChild(delC);

        data.conversation.messages.forEach(m => renderMessage(m));
        messagesEl.scrollTop = messagesEl.scrollHeight;
      }).catch(e => console.error('Erreur chargement conversation', e));
  }

  // Search functionality
  function doSearch() {
    const q = (searchInput && searchInput.value || '').trim();
    if (!q) { 
      if (searchResults) {
        searchResults.style.display = 'none';
        searchResults.innerHTML = '';
      }
      loadHistory(); // Reload full history when search is cleared
      return; 
    }
    // Refresh reference to the proper search-results container (modal-scoped preferred)
    searchResults = getSearchResultsElement();
    fetch(`/assistant/api/search/?student_id=${encodeURIComponent(studentId)}&q=${encodeURIComponent(q)}&limit=20`)
      .then(r => r.json())
      .then(data => {
        if (!searchResults) return;
        const results = data && data.results || [];
        if (!results.length) {
          searchResults.style.display = 'block';
          searchResults.innerHTML = '<div style="text-align:center;padding:20px;color:#666;"><strong>🔍 Aucun résultat trouvé</strong><br><small>Essayez des mots-clés différents</small></div>';
          return;
        }
        searchResults.style.display = 'block';
        searchResults.innerHTML = '<div style="text-align:center;padding:8px;background:#667eea;color:#fff;font-weight:bold;border-radius:8px;margin-bottom:10px;">🔍 Résultats de recherche pour "' + q + '" (' + results.length + ' trouvé' + (results.length > 1 ? 's' : '') + ')</div>';
        results.forEach(item => {
          const row = document.createElement('div');
          row.style.cssText = 'display:flex;justify-content:space-between;align-items:center;padding:10px 12px;border-bottom:1px solid #eee;background:#fafafa;border-radius:8px;margin-bottom:6px;transition:all 0.2s;';
          row.onmouseenter = () => row.style.background = '#f0f0ff';
          row.onmouseleave = () => row.style.background = '#fafafa';
          
          const leftPart = document.createElement('div');
          leftPart.style.cssText = 'flex:1;';
          
          const link = document.createElement('a');
          link.href = 'javascript:void(0)';
          link.style.cssText = 'color:#667eea;font-weight:bold;font-size:15px;text-decoration:none;display:block;margin-bottom:4px;';
          link.textContent = `📁 ${item.title || 'Conversation'}`;
          link.addEventListener('click', () => {
            loadConversation(item.id);
            searchResults.style.display = 'none';
          });
          
          const dateSpan = document.createElement('small');
          dateSpan.style.cssText = 'color:#999;font-size:12px;';
          dateSpan.textContent = new Date(item.started_at).toLocaleString('fr-FR');
          
          leftPart.appendChild(link);
          leftPart.appendChild(dateSpan);
          
          const del = document.createElement('button');
          del.textContent = '🗑️ Supprimer';
          del.style.cssText = 'padding:8px 14px;border-radius:12px;background:#f5576c;color:#fff;border:none;cursor:pointer;font-weight:bold;font-size:13px;transition:all 0.2s;';
          del.onmouseenter = () => del.style.background = '#e04555';
          del.onmouseleave = () => del.style.background = '#f5576c';
          del.addEventListener('click', () => {
            if (confirm('Supprimer cette conversation ?')) {
              deleteConversation(item.id);
              doSearch(); // Refresh search results
            }
          });
          
          row.appendChild(leftPart);
          row.appendChild(del);
          searchResults.appendChild(row);
        });
        
        // Add clear search button
        const clearBtn = document.createElement('button');
        clearBtn.textContent = '❌ Effacer la recherche';
        clearBtn.style.cssText = 'width:100%;margin-top:10px;padding:10px;border-radius:12px;background:#764ba2;color:#fff;border:none;cursor:pointer;font-weight:bold;';
        clearBtn.addEventListener('click', () => {
          searchInput.value = '';
          searchResults.style.display = 'none';
          loadHistory();
        });
        searchResults.appendChild(clearBtn);
      }).catch(e => {
        console.error('Erreur recherche', e);
        if (searchResults) {
          searchResults.style.display = 'block';
          searchResults.innerHTML = '<div style="text-align:center;padding:20px;color:#f5576c;"><strong>❌ Erreur de recherche</strong><br><small>Veuillez réessayer</small></div>';
        }
      });
  }

  if (searchBtn) searchBtn.addEventListener('click', doSearch);
  if (searchInput) searchInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') doSearch(); });

  // Delete conversation
  function deleteConversation(conversationId) {
    if (!confirm('Supprimer définitivement cette conversation ?')) return;
    fetch(`/assistant/api/conversation/${conversationId}/delete/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ student_id: studentId })
    }).then(r => r.json()).then(() => {
      // Refresh view
      loadHistory();
      if (searchResults) searchResults.style.display = 'none';
    }).catch(e => console.error('Erreur suppression conversation', e));
  }

  // Edit message
  function editMessage(messageId) {
    const content = prompt('Modifier votre question :');
    if (content == null) return;
    fetch(`/assistant/api/message/${messageId}/edit/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ student_id: studentId, content })
    }).then(r => r.json()).then(resp => {
      if (resp && resp.status === 'ok') {
        loadHistory();
      }
    }).catch(e => console.error('Erreur modification message', e));
  }

  // Delete message
  function deleteMessage(messageId) {
    if (!confirm('Supprimer ce message ?')) return;
    fetch(`/assistant/api/message/${messageId}/delete/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ student_id: studentId })
    }).then(r => r.json()).then(resp => {
      if (resp && resp.status === 'ok') {
        loadHistory();
      }
    }).catch(e => console.error('Erreur suppression message', e));
  }

  // Bulk delete old conversations
  if (bulkDeleteBtn) {
    bulkDeleteBtn.addEventListener('click', () => {
      const choice = prompt('Supprimer les conversations plus anciennes que N jours (ex: 30), ou taper "garder:N" pour garder seulement les N plus récentes.');
      if (!choice) return;
      let body = { student_id: studentId };
      if (choice.toLowerCase().startsWith('garder:')) {
        const n = parseInt(choice.split(':')[1], 10);
        if (!isNaN(n)) body.keep_recent = n;
      } else {
        const days = parseInt(choice, 10);
        if (!isNaN(days)) body.older_than_days = days;
      }
      fetch('/assistant/api/bulk_delete/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      }).then(r => r.json()).then(() => {
        loadHistory();
      }).catch(e => console.error('Erreur suppression ancienne', e));
    });
  }

  // Delete ALL conversations
  if (deleteAllBtn) {
    deleteAllBtn.addEventListener('click', () => {
      if (!confirm('Supprimer TOUTES vos conversations ? Cette action est irréversible.')) return;
      fetch('/assistant/api/bulk_delete/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId, keep_recent: 0 })
      }).then(r => r.json()).then(() => {
        messagesEl.innerHTML = '';
        if (searchResults) searchResults.style.display = 'none';
      }).catch(e => console.error('Erreur suppression totale', e));
    });
  }

  // ========= PDF HISTORY PANEL =========
  const togglePdfHistoryBtn = document.getElementById('toggle-pdf-history');
  const pdfHistoryPanel = document.getElementById('pdf-history-panel');
  const closeHistoryBtn = document.getElementById('close-history');
  const pdfListContainer = document.getElementById('pdf-list-container');

  // Toggle PDF history panel
  if (togglePdfHistoryBtn) {
    togglePdfHistoryBtn.addEventListener('click', () => {
      pdfHistoryPanel.classList.toggle('active');
      if (pdfHistoryPanel.classList.contains('active')) {
        loadPDFHistory();
      }
    });
  }

  // Close PDF history panel
  if (closeHistoryBtn) {
    closeHistoryBtn.addEventListener('click', () => {
      pdfHistoryPanel.classList.remove('active');
    });
  }

  // Load PDF history from API
  function loadPDFHistory() {
    pdfListContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">⏳</div>
        <p>Chargement des PDFs...</p>
      </div>
    `;

    fetch(`/assistant/api/pdf_history/?student_id=${studentId}`)
      .then(response => response.json())
      .then(data => {
        if (!data.pdfs || data.pdfs.length === 0) {
          pdfListContainer.innerHTML = `
            <div class="empty-state">
              <div class="empty-state-icon">📭</div>
              <p>Aucun PDF trouvé. Demande à l'assistant de créer un PDF !</p>
            </div>
          `;
          return;
        }

        // Render PDF list with pastel colors
        const pdfItems = data.pdfs.map((pdf, index) => {
          const colors = ['#FFD6E8', '#D6E8FF', '#FFF9D6', '#D6FFE8', '#E8D6FF', '#FFE8D6', '#D6FFF0'];
          const bgColor = colors[index % colors.length];
          const date = new Date(pdf.created_at);
          const formattedDate = date.toLocaleDateString('fr-FR', { 
            day: '2-digit', 
            month: 'long', 
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          });

          return `
            <div class="pdf-item" style="background: ${bgColor};">
              <div class="pdf-icon">📄</div>
              <div class="pdf-info">
                <h4 class="pdf-title">${pdf.title || 'Document PDF'}</h4>
                <div class="pdf-meta">
                  📅 ${formattedDate}
                  ${pdf.conversation_title ? `<br>💬 ${pdf.conversation_title}` : ''}
                </div>
              </div>
              <div class="pdf-actions">
                <a href="${pdf.file_url}" target="_blank" class="btn-download" download>
                  ⬇️ Télécharger
                </a>
              </div>
            </div>
          `;
        }).join('');

        pdfListContainer.innerHTML = `<div class="pdf-list">${pdfItems}</div>`;
      })
      .catch(error => {
        console.error('Erreur lors du chargement des PDFs:', error);
        pdfListContainer.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">⚠️</div>
            <p>Erreur lors du chargement des PDFs. Réessaye plus tard.</p>
          </div>
        `;
      });
  }
})();
