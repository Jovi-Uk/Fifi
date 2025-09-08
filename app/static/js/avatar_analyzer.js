/* Avatar Analyzer */

class AvatarAnalyzer {
    constructor() {
        this.form = document.getElementById('avatarForm');
        this.submitBtn = document.getElementById('generateBtn'); 
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.btnText = document.getElementById('btnText');
        this.errorMessage = document.getElementById('errorMessage');
        
        this.init();
    }

    init() {
        if (!this.form || !this.submitBtn) {
            console.error("Form or submit button not found!");
            return;
        }
        
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        this.setupValidation();
        this.updateSubmitButton();
        
        
        document.addEventListener('photosUpdated', () => {
            this.updateSubmitButton();
        });
        
        
        if (!window.sessionStartTime) {
            window.sessionStartTime = Date.now();
        }
    }

    setupValidation() {
        const heightInput = document.getElementById('height');
        const weightInput = document.getElementById('weight');
        
        
        if (heightInput) {
            heightInput.addEventListener('input', () => {
                this.validateInput(heightInput, 120, 220);
                this.updateSubmitButton();
            });
        }
        
        if (weightInput) {
            weightInput.addEventListener('input', () => {
                this.validateInput(weightInput, 30, 200);
                this.updateSubmitButton();
            });
        }
        
        
        const genderInputs = document.querySelectorAll('input[name="gender"]');
        genderInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.updateSubmitButton();
            });
        });
    }

    validateInput(input, min, max) {
        const value = parseFloat(input.value);
        
        if (value < min || value > max) {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
            return false;
        } else {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            return true;
        }
    }

    updateSubmitButton() {
        if (!this.submitBtn) return;
        
        const hasPhotos = window.cameraController && window.cameraController.hasAllPhotos();
        const btnText = this.btnText || this.submitBtn.querySelector('#btnText') || this.submitBtn;
        
        if (hasPhotos) {
            if (btnText.innerHTML !== undefined) {
                btnText.innerHTML = '🚀 Generate Enhanced 3D Avatar';
            } else {
                btnText.textContent = '🚀 Generate Enhanced 3D Avatar';
            }
            this.submitBtn.style.background = 'linear-gradient(135deg, #28a745, #34ce57)';
            this.submitBtn.title = 'Enhanced accuracy with timer-captured photos';
            this.submitBtn.classList.add('enhanced');
        } else {
            if (btnText.innerHTML !== undefined) {
                btnText.innerHTML = '📊 Generate 3D Avatar (Basic)';
            } else {
                btnText.textContent = '📊 Generate 3D Avatar (Basic)';
            }
            this.submitBtn.style.background = 'linear-gradient(135deg, var(--primary-color), var(--accent-color))';
            this.submitBtn.title = 'Basic analysis with measurements only';
            this.submitBtn.classList.remove('enhanced');
        }
    }

    showError(message) {
        if (this.errorMessage) {
            this.errorMessage.textContent = message;
            this.errorMessage.style.display = 'block';
            
            
            setTimeout(() => {
                this.errorMessage.style.display = 'none';
            }, 6000);
        } else {
            alert(`Error: ${message}`); 
        }
    }

    hideError() {
        if (this.errorMessage) {
            this.errorMessage.style.display = 'none';
        }
    }

    setLoading(loading) {
        if (!this.submitBtn) return;
        
        if (loading) {
            this.submitBtn.disabled = true;
            if (this.loadingSpinner) this.loadingSpinner.style.display = 'inline-block';
            
            const hasPhotos = window.cameraController && window.cameraController.hasAllPhotos();
            const btnText = this.btnText || this.submitBtn.querySelector('#btnText') || this.submitBtn;
            
            if (hasPhotos) {
                if (btnText.textContent !== undefined) {
                    btnText.textContent = 'Analyzing timer photos & generating avatar...';
                }
            } else {
                if (btnText.textContent !== undefined) {
                    btnText.textContent = 'Generating avatar...';
                }
            }
        } else {
            this.submitBtn.disabled = false;
            if (this.loadingSpinner) this.loadingSpinner.style.display = 'none';
            this.updateSubmitButton();
        }
    }

    async handleSubmit(e) {
        e.preventDefault();
        this.hideError();

        
        const formData = new FormData(this.form);
        const basicData = {
            height: parseFloat(formData.get('height')),
            weight: parseFloat(formData.get('weight')),
            gender: formData.get('gender')
        };

        
        if (!this.validateData(basicData)) {
            return;
        }

        this.setLoading(true);

        try {
            
            let submissionData;
            let isEnhanced = false;

            
            if (window.cameraController && window.cameraController.hasAllPhotos()) {
                submissionData = this.prepareEnhancedSubmission(basicData);
                isEnhanced = true;
                
                
                this.logTimerUsage();
            } else {
                submissionData = this.prepareBasicSubmission(basicData);
            }

            
            const endpoint = isEnhanced ? '/api/analyze-enhanced' : '/api/analyze';
            const response = await this.submitData(endpoint, submissionData, isEnhanced);

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    
                    if (isEnhanced) {
                        result.timer_analytics = this.getTimerAnalytics();
                    }
                    this.redirectToResults(result);
                } else {
                    this.showError(result.error || 'Failed to generate avatar. Please try again.');
                }
            } else {
                const errorResult = await response.json().catch(() => ({}));
                this.showError(errorResult.error || `Server error (${response.status}). Please try again.`);
            }

        } catch (error) {
            console.error('Error:', error);
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                this.showError('Network error. Please check your connection and try again.');
            } else {
                this.showError('An unexpected error occurred. Please try again.');
            }
        } finally {
            this.setLoading(false);
        }
    }

    prepareBasicSubmission(basicData) {
        return {
            type: 'basic',
            data: basicData
        };
    }

    prepareEnhancedSubmission(basicData) {
        
        const formData = new FormData();
        
        
        formData.append('height', basicData.height);
        formData.append('weight', basicData.weight);
        formData.append('gender', basicData.gender);
        formData.append('analysis_type', 'enhanced');
        
        
        const photos = window.cameraController.getCapturedPhotos();
        photos.forEach((photo, index) => {
            formData.append(`photo_${photo.pose}`, photo.blob, `${photo.pose}.jpg`);
        });
        
        
        const enhancedMetadata = {
            capture_timestamp: Date.now(),
            poses: photos.map(p => p.pose),
            total_photos: photos.length,
            timer_settings: {
                timers_used: photos.map(p => p.timerUsed),
                average_timer: photos.reduce((sum, p) => sum + p.timerUsed, 0) / photos.length,
                timer_consistency: this.calculateTimerConsistency(photos),
                capture_method: 'timer_guided'
            },
            photo_quality: {
                estimated_quality: this.estimatePhotoQuality(photos),
                capture_intervals: this.calculateCaptureIntervals(photos)
            },
            user_experience: {
                total_session_time: this.calculateSessionTime(),
                retakes_count: this.countRetakes(),
                timer_cancellations: this.countTimerCancellations()
            }
        };
        
        formData.append('photo_metadata', JSON.stringify(enhancedMetadata));
        
        return formData;
    }

    calculateTimerConsistency(photos) {
        const timers = photos.map(p => p.timerUsed);
        const uniqueTimers = [...new Set(timers)];
        return uniqueTimers.length === 1 ? 'consistent' : 'mixed';
    }

    estimatePhotoQuality(photos) {
        
        const avgFileSize = photos.reduce((sum, p) => sum + p.blob.size, 0) / photos.length;
        
        if (avgFileSize > 500000) return 'high';
        if (avgFileSize > 200000) return 'medium';
        return 'low';
    }

    calculateCaptureIntervals(photos) {
        if (photos.length < 2) return [];
        
        const intervals = [];
        for (let i = 1; i < photos.length; i++) {
            intervals.push(photos[i].timestamp - photos[i-1].timestamp);
        }
        return intervals;
    }

    calculateSessionTime() {
        
        return Date.now() - (window.sessionStartTime || Date.now());
    }

    countRetakes() {
        
        return window.cameraController?.retakeCount || 0;
    }

    countTimerCancellations() {
        
        return window.cameraController?.timerCancellationCount || 0;
    }

    logTimerUsage() {
        
        const photos = window.cameraController.getCapturedPhotos();
        const timerData = {
            total_photos: photos.length,
            timer_5s_usage: photos.filter(p => p.timerUsed === 5).length,
            timer_10s_usage: photos.filter(p => p.timerUsed === 10).length,
            session_timestamp: Date.now()
        };
        
        console.log('Timer usage analytics:', timerData);
        
        
        
    }

    getTimerAnalytics() {
        if (!window.cameraController || !window.cameraController.hasAllPhotos()) {
            return null;
        }
        
        const photos = window.cameraController.getCapturedPhotos();
        return {
            timer_5s_count: photos.filter(p => p.timerUsed === 5).length,
            timer_10s_count: photos.filter(p => p.timerUsed === 10).length,
            most_used_timer: this.getMostUsedTimer(photos),
            timer_effectiveness: this.calculateTimerEffectiveness(photos)
        };
    }

    getMostUsedTimer(photos) {
        const timer5Count = photos.filter(p => p.timerUsed === 5).length;
        const timer10Count = photos.filter(p => p.timerUsed === 10).length;
        
        if (timer5Count > timer10Count) return '5s';
        if (timer10Count > timer5Count) return '10s';
        return 'equal';
    }

    calculateTimerEffectiveness(photos) {
        
        const consistency = this.calculateTimerConsistency(photos);
        const avgFileSize = photos.reduce((sum, p) => sum + p.blob.size, 0) / photos.length;
        
        let score = 0;
        if (consistency === 'consistent') score += 50;
        if (avgFileSize > 300000) score += 30; 
        if (photos.length === 4) score += 20; 
        
        return Math.min(100, score);
    }

    async submitData(endpoint, data, isEnhanced) {
        const options = {
            method: 'POST'
        };

        if (isEnhanced) {
            
            options.body = data;
            
        } else {
            
            options.headers = {
                'Content-Type': 'application/json'
            };
            options.body = JSON.stringify(data.data);
        }

        return fetch(endpoint, options);
    }

    validateData(data) {
        
        if (data.height < 120 || data.height > 220) {
            this.showError('Height must be between 120cm and 220cm');
            return false;
        }

        
        if (data.weight < 30 || data.weight > 200) {
            this.showError('Weight must be between 30kg and 200kg');
            return false;
        }

        
        if (!data.gender || !['male', 'female'].includes(data.gender)) {
            this.showError('Please select a gender');
            return false;
        }

        return true;
    }

    redirectToResults(result) {
        
        sessionStorage.setItem('avatarResult', JSON.stringify(result));
        
        
        if (result.timer_analytics) {
            sessionStorage.setItem('timerAnalytics', JSON.stringify(result.timer_analytics));
        }
        
        
        window.location.href = '/report';
    }
}

// Initialize when DOM is loaded
let avatarAnalyzer;
document.addEventListener('DOMContentLoaded', () => {
    
    if (!window.sessionStartTime) {
        window.sessionStartTime = Date.now();
    }
    
    avatarAnalyzer = new AvatarAnalyzer();
    
    
    if (window.cameraController) {
        
        const originalUpdatePhotoStatus = window.cameraController.updatePhotoStatus;
        if (originalUpdatePhotoStatus) {
            window.cameraController.updatePhotoStatus = function() {
                originalUpdatePhotoStatus.call(this);
                document.dispatchEvent(new CustomEvent('photosUpdated'));
            };
        }
    }
});

// Add enhanced visual feedback for form interactions
document.addEventListener('DOMContentLoaded', () => {
    
    const inputs = document.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.addEventListener('focus', () => {
            if (input.parentElement) {
                input.parentElement.classList.add('focused');
                input.parentElement.style.transform = 'translateY(-2px)';
            }
        });
        
        input.addEventListener('blur', () => {
            if (!input.value && input.parentElement) {
                input.parentElement.classList.remove('focused');
            }
            if (input.parentElement) {
                input.parentElement.style.transform = 'translateY(0)';
            }
        });
    });

    
    const genderLabels = document.querySelectorAll('.gender-label');
    genderLabels.forEach(label => {
        label.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                border-radius: 50%;
                background: rgba(108, 123, 138, 0.3);
                transform: scale(0);
                animation: ripple 0.6s linear;
                left: ${x}px;
                top: ${y}px;
                width: ${size}px;
                height: ${size}px;
                pointer-events: none;
                z-index: 1;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });

    
    const submitBtn = document.getElementById('generateBtn');
    if (submitBtn) {
        submitBtn.addEventListener('mouseenter', () => {
            if (!submitBtn.disabled) {
                submitBtn.style.transform = 'translateY(-3px)';
                submitBtn.style.boxShadow = '0 12px 30px rgba(108, 123, 138, 0.5)';
            }
        });

        submitBtn.addEventListener('mouseleave', () => {
            if (!submitBtn.disabled) {
                submitBtn.style.transform = 'translateY(0)';
                submitBtn.style.boxShadow = '0 8px 25px rgba(108, 123, 138, 0.4)';
            }
        });
    }
});

// Enhanced CSS animations
const enhancedStyle = document.createElement('style');
enhancedStyle.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    @keyframes enhanced-pulse {
        0%, 100% {
            transform: scale(1);
            opacity: 1;
        }
        50% {
            transform: scale(1.05);
            opacity: 0.9;
        }
    }
    
    .timer-enhancement-indicator {
        position: relative;
    }
    
    .timer-enhancement-indicator::after {
        content: '⏱️';
        position: absolute;
        top: -5px;
        right: -5px;
        background: #17a2b8;
        color: white;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        animation: enhanced-pulse 2s infinite;
    }
    
    .btn.enhanced {
        background: linear-gradient(135deg, #28a745, #34ce57) !important;
        box-shadow: 0 8px 25px rgba(40, 167, 69, 0.4);
    }
`;
document.head.appendChild(enhancedStyle);
