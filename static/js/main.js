

document.addEventListener('DOMContentLoaded', () => {
  initCopyButtons();
  initMobileNav();
});

function initMobileNav() {
  const toggleBtn = document.getElementById('mobile-nav-toggle');
  const navMenu = document.getElementById('primary-nav-menu');

  if (!toggleBtn || !navMenu) return;

  function closeMenu() {
    navMenu.classList.remove('is-open');
    toggleBtn.classList.remove('is-active');
    toggleBtn.setAttribute('aria-expanded', 'false');
  }

  function openMenu() {
    navMenu.classList.add('is-open');
    toggleBtn.classList.add('is-active');
    toggleBtn.setAttribute('aria-expanded', 'true');
  }

  toggleBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = navMenu.classList.contains('is-open');
    if (isOpen) {
      closeMenu();
    } else {
      openMenu();
    }
  });
  navMenu.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      closeMenu();
    });
  });
  document.addEventListener('click', (e) => {
    if (navMenu.classList.contains('is-open')) {
      if (!navMenu.contains(e.target) && !toggleBtn.contains(e.target)) {
        closeMenu();
      }
    }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && navMenu.classList.contains('is-open')) {
      closeMenu();
    }
  });
}

function initCopyButtons() {
  const copyButtons = document.querySelectorAll('.btn-copy-code[data-target]');

  copyButtons.forEach((btn) => {
    btn.addEventListener('click', async () => {
      const targetId = btn.getAttribute('data-target');
      const targetElement = document.getElementById(targetId);

      if (!targetElement) return;

      const codeText = targetElement.textContent || targetElement.innerText;

      try {
        await navigator.clipboard.writeText(codeText.trim());

        const labelSpan = btn.querySelector('.copy-label');
        const originalText = labelSpan ? labelSpan.textContent : 'Nusxalash';

        btn.classList.add('copied');
        if (labelSpan) labelSpan.textContent = 'Nusxalandi!';

        setTimeout(() => {
          btn.classList.remove('copied');
          if (labelSpan) labelSpan.textContent = originalText;
        }, 2000);
      } catch (err) {
        console.error('Nusxalashda xatolik:', err);
      }
    });
  });
}
