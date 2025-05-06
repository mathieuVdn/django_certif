document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('image-modal');
    const modalImg = document.getElementById('modal-image');
  
    window.openModal = function(src) {
      modal.classList.add('is-active');
      modalImg.src = src;
    }
  
    const closeModal = () => {
      modal.classList.remove('is-active');
      modalImg.src = "";
    };
  
    modal.querySelector('.modal-background').addEventListener('click', closeModal);
    modal.querySelector('.modal-close').addEventListener('click', closeModal);
  });
  