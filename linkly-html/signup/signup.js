const BASEAPI = "http://127.0.0.1:8000/"

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



// Password strength checker
function checkPasswordStrength(password) {
    const strengthFill = document.getElementById('strengthFill');
    const strengthText = document.getElementById('strengthText');
    
    let strength = 0;
    let feedback = '';
    
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    strengthFill.className = 'strength-fill';
    
    if (password.length === 0) {
        strengthText.textContent = 'Password must be at least 8 characters long';
        strengthText.className = 'text-xs text-gray-400 mt-2';
        return;
    }
    
    switch (strength) {
        case 0:
        case 1:
            strengthFill.classList.add('strength-weak');
            feedback = 'Weak - Add more characters and variety';
            strengthText.className = 'text-xs text-red-400 mt-2';
            break;
        case 2:
            strengthFill.classList.add('strength-fair');
            feedback = 'Fair - Add uppercase, numbers, or symbols';
            strengthText.className = 'text-xs text-orange-400 mt-2';
            break;
        case 3:
        case 4:
            strengthFill.classList.add('strength-good');
            feedback = 'Good - Strong password';
            strengthText.className = 'text-xs text-green-400 mt-2';
            break;
        case 5:
            strengthFill.classList.add('strength-strong');
            feedback = 'Excellent - Very strong password';
            strengthText.className = 'text-xs text-green-400 mt-2';
            break;
    }
    
    strengthText.textContent = feedback;
}

// Google OAuth signup
function signupWithGoogle(event) {
  event.preventDefault(); // Prevent default button behavior if needed

  toastManager.info('Redirecting to Google...');

  const button = event.target;
  const originalText = button.innerHTML;
  
  button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Connecting...</span>';
  button.disabled = true;

  // Redirect user to Google OAuth endpoint after a short delay to show loading UI
  setTimeout(() => {
    // Redirect browser to your backend Google OAuth start URL
    window.location.href = `${BASEAPI}auth/google`;
  }, 1500);
}


// Initilize the toastmanager
const toastManager = new ToastManager();


// GitHub OAuth signup
function signupWithGithub() {
    toastManager.info('Redirecting to Github...');
    
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Connecting...</span>';
    
    setTimeout(() => {
        button.innerHTML = originalText;

        window.location.href = `${BASEAPI}auth/github`
    }, 1500);
}

// first+last = @gyadrona
// Handle email/password signup
async function handleSignup(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const inputs = form.querySelectorAll('input[required]');

    let isValid = true;
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('border-red-500');
        } else {
            input.classList.remove('border-red-500');
        }
    });

    const passwordInputs = form.querySelectorAll('input[type="password"]');
    const password = passwordInputs[0]?.value;
    const confirmPassword = passwordInputs[1]?.value;

    if (password !== confirmPassword) {
        toastManager.error('Passwords do not match');
        return;
    }

    if (!isValid) {
        toastManager.warning('Please fill in all required fields');
        return;
    }

    const termsCheckbox = form.querySelector('input[type="checkbox"][required]');
    if (!termsCheckbox.checked) {
        toastManager.warning('Please accept the Terms of Service and Privacy Policy');
        return;
    }

    // Collect user details
    const firstName = formData.get('firstName').trim();
    const lastName = formData.get('lastName').trim();
    const email = formData.get('email').trim();

    // Generate unique username
    const uniqueSuffix = Math.random().toString(36).substring(2, 7); // 5 random chars
    const username = `${firstName}${lastName}`.toLowerCase() + '_' + uniqueSuffix;

    const payload = {
        name: username,
        email: email,
        password: password
    };

    const button = form.querySelector('button[type="submit"]');
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Creating account...</span>';
    button.disabled = true;

    try {
        const response = await fetch(`${BASEAPI}register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            console.log(response.json())
            toastManager.error(String(data.detail || 'Signup failed. Try again.'));
        } else {
            toastManager.success('Account created successfully!');
            window.location.href = '/dashboard/dashboard.html';
        }
    } catch (error) {
        console.error(error);
        toastManager.error('Something went wrong. Please try again later.');
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
    const signupCard = document.querySelector('.signup-card');
    signupCard.style.opacity = '0';
    signupCard.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        signupCard.style.transition = 'all 0.6s ease';
        signupCard.style.opacity = '1';
        signupCard.style.transform = 'translateY(0)';
    }, 100);
});
