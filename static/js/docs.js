/**
 * CoreAPI — Documentation & Interactive Playground Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  initPlayground();
  initSidebarSpy();
});

/**
 * Initialize interactive API playground
 */
function initPlayground() {
  const input = document.getElementById('question-input');
  const submitBtn = document.getElementById('btn-submit-playground');
  const submitText = document.getElementById('btn-submit-text');
  const submitIcon = document.getElementById('btn-submit-icon');
  const spinner = document.getElementById('playground-spinner');
  const clearBtn = document.getElementById('btn-clear-playground');
  const copyBtn = document.getElementById('btn-copy-response');
  const statusBadge = document.getElementById('playground-status-badge');
  const timeBadge = document.getElementById('playground-time-badge');
  const responseBlock = document.getElementById('playground-response');
  const charCurrent = document.getElementById('char-current');
  const samplePills = document.querySelectorAll('.sample-pill, .sample-pill-glass, .sample-pill-light');

  if (!submitBtn || !input || !responseBlock) return;

  // Real-time character count tracker
  input.addEventListener('input', () => {
    if (charCurrent) {
      charCurrent.textContent = input.value.length;
    }
  });

  // Sample prompt pills click handler
  samplePills.forEach((pill) => {
    pill.addEventListener('click', () => {
      const prompt = pill.getAttribute('data-prompt');
      if (prompt) {
        input.value = prompt;
        if (charCurrent) charCurrent.textContent = prompt.length;
        input.focus();
      }
    });
  });

  // Clear button
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      input.value = '';
      if (charCurrent) charCurrent.textContent = '0';
      setStatus('idle', 'Kutilmoqda');
      if (timeBadge) timeBadge.style.display = 'none';
      responseBlock.textContent = '// So‘rov yuborilgach, AI modeli javobi shu yerda aks etadi...';
      input.focus();
    });
  }

  // Copy response button
  if (copyBtn) {
    copyBtn.addEventListener('click', async () => {
      const content = responseBlock.textContent || '';
      if (!content || content.startsWith('//')) return;

      try {
        await navigator.clipboard.writeText(content);
        const label = copyBtn.querySelector('.copy-label');
        const originalText = label ? label.textContent : 'Nusxalash';

        copyBtn.classList.add('copied');
        if (label) label.textContent = 'Nusxalandi!';

        setTimeout(() => {
          copyBtn.classList.remove('copied');
          if (label) label.textContent = originalText;
        }, 2000);
      } catch (err) {
        console.error('Nusxalashda xatolik:', err);
      }
    });
  }

  // Handle Ctrl+Enter to submit
  input.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      submitBtn.click();
    }
  });

  // Main Submit Action
  submitBtn.addEventListener('click', async () => {
    const rawQuestion = input.value.trim();

    if (!rawQuestion) {
      setStatus('error', 'Savol bo‘sh');
      responseBlock.textContent = JSON.stringify(
        {
          success: false,
          error: {
            code: 'missing_question',
            message: 'Iltimos, avval savolingizni kiriting.'
          }
        },
        null,
        2
      );
      input.focus();
      return;
    }

    // Set loading state
    setLoading(true);
    setStatus('loading', 'Yuborilmoqda...');
    responseBlock.textContent = '// AI modelidan javob kutilmoqda...\n// Bu bir necha soniya vaqt olishi mumkin.';

    const startTime = performance.now();

    try {
      // Relative path to current website origin
      const response = await fetch('/api/v1/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ question: rawQuestion })
      });

      const elapsed = Math.round(performance.now() - startTime);
      if (timeBadge) {
        timeBadge.textContent = `${elapsed} ms`;
        timeBadge.style.display = 'inline-block';
      }

      let data;
      try {
        data = await response.json();
      } catch {
        data = {
          success: false,
          error: {
            code: 'invalid_json_response',
            message: 'Serverdan kutilmagan formatda javob qaytdi.'
          }
        };
      }

      // Safe rendering using textContent
      responseBlock.textContent = JSON.stringify(data, null, 2);

      // Status badge reflection
      if (response.ok && data.success) {
        setStatus('success', `${response.status} OK`);
      } else {
        const statusText = `${response.status} ${response.statusText || 'Error'}`;
        setStatus('error', statusText);
      }
    } catch (networkError) {
      const elapsed = Math.round(performance.now() - startTime);
      if (timeBadge) {
        timeBadge.textContent = `${elapsed} ms`;
        timeBadge.style.display = 'inline-block';
      }

      setStatus('error', 'Tarmoq xatosi');
      responseBlock.textContent = JSON.stringify(
        {
          success: false,
          error: {
            code: 'network_error',
            message: 'Tarmoq xatoligi yuz berdi. Serverga ulanib bo‘lmadi yoki so‘rov bekor qilindi.'
          }
        },
        null,
        2
      );
    } finally {
      setLoading(false);
    }
  });

  function setLoading(isLoading) {
    submitBtn.disabled = isLoading;
    if (isLoading) {
      if (spinner) spinner.style.display = 'inline-block';
      if (submitIcon) submitIcon.style.display = 'none';
      if (submitText) submitText.textContent = 'Yuklanmoqda...';
    } else {
      if (spinner) spinner.style.display = 'none';
      if (submitIcon) submitIcon.style.display = 'inline-block';
      if (submitText) submitText.textContent = 'So‘rov yuborish';
    }
  }

  function setStatus(type, text) {
    if (!statusBadge) return;
    statusBadge.className = `status-badge-light status-badge-terminal status-badge-glass ${type}`;
    statusBadge.textContent = text;
  }
}

/**
 * Active navigation spy for docs sidebar
 */
function initSidebarSpy() {
  const links = document.querySelectorAll('.sidebar-nav .sidebar-link');
  const sections = document.querySelectorAll('.docs-section');

  if (!links.length || !sections.length) return;

  window.addEventListener('scroll', () => {
    let currentId = '';
    const scrollPos = window.scrollY + 120;

    sections.forEach((section) => {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      if (scrollPos >= top && scrollPos < top + height) {
        currentId = section.getAttribute('id');
      }
    });

    if (currentId) {
      links.forEach((link) => {
        const href = link.getAttribute('href');
        if (href === `#${currentId}`) {
          link.classList.add('active');
        } else {
          link.classList.remove('active');
        }
      });
    }
  });
}
