





document.addEventListener('DOMContentLoaded', function() {
    console.log('Fifi App: Core JavaScript loaded');
    
    
    initializeNavigation();
    initializeAnimations();
    initializeUtilities();
});


function initializeNavigation() {
    
    const navLinks = document.querySelectorAll('a[href^="#"]');
    
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            
            if (targetSection) {
                e.preventDefault();
                
                
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                
                history.pushState(null, null, targetId);
            }
        });
    });
    
    
    const sections = document.querySelectorAll('section[id]');
    const navItems = document.querySelectorAll('.nav-links a');
    
    window.addEventListener('scroll', () => {
        let current = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            
            
            if (window.scrollY >= sectionTop - 100) {
                current = section.getAttribute('id');
            }
        });
        
        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('href').slice(1) === current) {
                item.classList.add('active');
            }
        });
    });
}


function initializeAnimations() {
    
    
    const animationObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                
                entry.target.classList.add('animate-in');
                
                
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1, 
        rootMargin: '0px 0px -50px 0px' 
    });
    
    
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    
    animatedElements.forEach(element => {
        animationObserver.observe(element);
    });
}


function initializeUtilities() {
    
    
    window.debounce = function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    };
    
    
    
    window.throttle = function(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    };
    
    
    window.formatNumber = function(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    };
    
    
    window.isValidEmail = function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    };
    
    
    window.showToast = function(message, type = 'info') {
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        
        document.body.appendChild(toast);
        
        
        setTimeout(() => toast.classList.add('show'), 10);
        
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    };
}


window.setLoading = function(isLoading, buttonElement) {
    if (isLoading) {
        
        buttonElement.dataset.originalText = buttonElement.textContent;
        
        
        buttonElement.classList.add('loading');
        buttonElement.disabled = true;
        buttonElement.innerHTML = '<span class="loading-spinner"></span> Processing...';
    } else {
        
        buttonElement.classList.remove('loading');
        buttonElement.disabled = false;
        buttonElement.textContent = buttonElement.dataset.originalText || 'Submit';
    }
};


window.apiRequest = async function(url, options = {}) {
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, finalOptions);
        
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error('API Request failed:', error);
        
        
        showToast('Something went wrong. Please try again.', 'error');
        
        throw error;
    }
};


window.validateForm = function(formElement) {
    const inputs = formElement.querySelectorAll('[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        
        input.classList.remove('is-valid', 'is-invalid');
        
        
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            
            if (input.type === 'email' && !isValidEmail(input.value)) {
                input.classList.add('is-invalid');
                isValid = false;
            } else {
                input.classList.add('is-valid');
            }
        }
    });
    
    return isValid;
};


const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
const navLinks = document.querySelector('.nav-links');

if (mobileMenuToggle) {
    mobileMenuToggle.addEventListener('click', function() {
        navLinks.classList.toggle('active');
        this.classList.toggle('active');
    });
    
    
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.nav-container')) {
            navLinks.classList.remove('active');
            mobileMenuToggle.classList.remove('active');
        }
    });
}


window.addEventListener('beforeunload', function() {
    document.body.classList.add('page-transition');
});


window.addEventListener('load', function() {
    document.body.classList.remove('page-transition');
});


    window.showToast = function(message, type = 'info') {
        
        const existingToasts = document.querySelectorAll('.toast');
        existingToasts.forEach(toast => toast.remove());
        
        
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 9999;
            `;
            document.body.appendChild(toastContainer);
        }
        
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        
        const baseStyles = `
            padding: 16px 24px;
            border-radius: 8px;
            color: white;
            font-size: 16px;
            margin-bottom: 10px;
            min-width: 250px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        
        const typeStyles = {
            'success': 'background: #4ecdc4;',
            'error': 'background: #ff6b6b;',
            'info': 'background: #45b7d1;',
            'warning': 'background: #f39c12;'
        };
        
        toast.style.cssText = baseStyles + (typeStyles[type] || typeStyles['info']);
        toast.textContent = message;
        
        
        toastContainer.appendChild(toast);
        
        
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateX(0)';
        }, 10);
        
        
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                toast.remove();
                
                if (toastContainer.children.length === 0) {
                    toastContainer.remove();
                }
            }, 300);
        }, 3000);
    };