const BASEURL = "http://127.0.0.1:8000/"

class ToastManager {
    constructor() {
        this.container = document.getElementById('toastContainer');
        this.toasts = [];
    }
    
    show(message, type = 'info', duration = 5000) {
        const toast = this.createToast(message, type, duration);
        this.container.appendChild(toast);
        this.toasts.push(toast);
        
        // Trigger animation
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // Auto remove
        setTimeout(() => {
            this.remove(toast);
        }, duration);
        
        return toast;
    }
    
    createToast(message, type, duration) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Info'
        };
        
        toast.innerHTML = `
            <div class="toast-header">
                <div class="toast-title">
                    <i class="${icons[type]} toast-icon"></i>
                    ${titles[type]}
                </div>
                <button class="toast-close" onclick="toastManager.remove(this.closest('.toast'))">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="toast-message">${message}</div>
            <div class="toast-progress"></div>
        `;
        
        return toast;
    }
    
    remove(toast) {
        if (!toast || !toast.parentNode) return;
        
        toast.classList.add('hide');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            this.toasts = this.toasts.filter(t => t !== toast);
        }, 400);
    }
    
    success(message) {
        return this.show(message, 'success');
    }
    
    error(message) {
        return this.show(message, 'error');
    }
    
    warning(message) {
        return this.show(message, 'warning');
    }
    
    info(message) {
        return this.show(message, 'info');
    }
}


const toast = new ToastManager();
const toastManager = new ToastManager();
function loginWithGoogle(event) {
  event.preventDefault(); // Prevent default button behavior if needed

  toastManager.info('Redirecting to Google...');

  const button = event.target;
  const originalText = button.innerHTML;
  
  button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Connecting...</span>';
  button.disabled = true;

  // Redirect user to Google OAuth endpoint after a short delay to show loading UI
  setTimeout(() => {
    // Redirect browser to your backend Google OAuth start URL
    window.location.href = `${BASEURL}auth/google`;
  }, 1500);
}


// GitHub OAuth signup
function loginWithGithub(event) {
    toastManager.info('Redirecting to Github...');
    
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Connecting...</span>';
    
    setTimeout(() => {
        button.innerHTML = originalText;

        window.location.href = `${BASEURL}auth/github`
    }, 1500);
}


async function handleLogin(event) {
  event.preventDefault();

  const form = event.target;
  const email = form.querySelector('input[type="email"]').value.trim();
  const password = form.querySelector('input[type="password"]').value.trim();

  // Basic validation
  if (!email || !password) {
    toast.error('Please fill in all fields');
    return;
  }

  const button = form.querySelector('button[type="submit"]');
  const originalText = button.innerHTML;

  button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Signing in...</span>';
  button.disabled = true;

  const formData = new FormData();
  formData.append("username", email);
  formData.append("password", password);

  try {
    const response = await fetch(`${BASEURL}login`, {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (!response.ok) {
      toast.error(String(data.detail || "Bad credentials"));
    } else {
      localStorage.setItem("access_token", data.access_token);

      toast.success("Login Successful");
      window.location.href = '/dashboard/dashboard.html';
    }
  } catch (error) {
    console.error(error);
    toast.error("Internal Server Error");
  } finally {
    button.innerHTML = originalText;
    button.disabled = false;
  }
}

// Add parallax effect to orbs (throttled)
let ticking = false;

function updateParallax() {
const scrolled = window.pageYOffset;
const orbs = document.querySelectorAll('.orb');
orbs.forEach((orb, index) => {
    const speed = 0.1 + (index * 0.05);
    orb.style.transform = `translateY(${scrolled * speed}px)`;
});
ticking = false;
}

window.addEventListener('scroll', () => {
if (!ticking) {
    requestAnimationFrame(updateParallax);
    ticking = true;
}
});

// Add subtle animations on load
document.addEventListener('DOMContentLoaded', () => {
const loginCard = document.querySelector('.login-card');
loginCard.style.opacity = '0';
loginCard.style.transform = 'translateY(20px)';

setTimeout(() => {
    loginCard.style.transition = 'all 0.6s ease';
    loginCard.style.opacity = '1';
    loginCard.style.transform = 'translateY(0)';
}, 100);
});
