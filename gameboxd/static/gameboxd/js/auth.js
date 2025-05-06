document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('register-modal');
    const openBtn = document.getElementById('open-register-modal');
    const closeBtn = document.getElementById('close-register-modal');
  
    if (openBtn && modal) {
      openBtn.addEventListener('click', () => {
        modal.classList.add('is-active');
      });
    }
  
    if (closeBtn && modal) {
      closeBtn.addEventListener('click', () => {
        modal.classList.remove('is-active');
      });
    }
  
    // Ferme si on clique en dehors (le background)
    const modalBg = modal.querySelector('.modal-background');
    if (modalBg) {
      modalBg.addEventListener('click', () => {
        modal.classList.remove('is-active');
      });
    }
    if (typeof window.openRegisterModal !== 'undefined' && window.openRegisterModal === true) {
        const modal = document.getElementById('register-modal');
        if (modal) {
          modal.classList.add('is-active');
        }
      }
    setTimeout(() => {
    const flash = document.getElementById('flash-message');
    if (flash) {
        flash.style.opacity = '0';
        setTimeout(() => flash.remove(), 500);
    }
    }, 4000);
    const loginModal = document.getElementById('login-modal');
    const openLoginBtn = document.getElementById('open-login-modal');
    const closeLoginBtn = document.getElementById('close-login-modal');

    if (openLoginBtn && loginModal) {
    openLoginBtn.addEventListener('click', () => {
        loginModal.classList.add('is-active');
    });
    }
    if (closeLoginBtn && loginModal) {
    closeLoginBtn.addEventListener('click', () => {
        loginModal.classList.remove('is-active');
    });
    }
    const loginModalBg = loginModal?.querySelector('.modal-background');
    if (loginModalBg) {
    loginModalBg.addEventListener('click', () => {
        loginModal.classList.remove('is-active');
    });
    }

    if (typeof window.openLoginModal !== 'undefined' && window.openLoginModal === true) {
    loginModal?.classList.add('is-active');
    }
    const switchToRegister = document.getElementById('switch-to-register');
    const switchToLogin = document.getElementById('switch-to-login');

    if (switchToRegister) {
    switchToRegister.addEventListener('click', (e) => {
        e.preventDefault();
        const registerModal = document.getElementById('register-modal');
        const loginModal = document.getElementById('login-modal');
        loginModal?.classList.remove('is-active');
        registerModal?.classList.add('is-active');
    });
    }

    if (switchToLogin) {
    switchToLogin.addEventListener('click', (e) => {
        e.preventDefault();
        const registerModal = document.getElementById('register-modal');
        const loginModal = document.getElementById('login-modal');
        registerModal?.classList.remove('is-active');
        loginModal?.classList.add('is-active');
    });
    }
    const openHeroBtn = document.getElementById('open-register-modal-hero');
    const registerModal = document.getElementById('register-modal'); // Assure-toi que ça existe ici aussi
    
    if (openHeroBtn && registerModal) {
      openHeroBtn.addEventListener('click', () => {
        registerModal.classList.add('is-active');
      });
    }
  });

// Connexion

