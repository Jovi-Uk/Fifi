// static/js/form-handler.js - Form Validation and Submission



document.addEventListener('DOMContentLoaded', function() {
    console.log('Form Handler: Initializing avatar form');
    
    
    const avatarForm = document.getElementById('avatarForm');
    const submitButton = document.getElementById('generateBtn');
    
    
    if (!avatarForm) {
        console.log('Form Handler: Not on form page, skipping initialization');
        return;
    }
    
    
    initializeFormValidation();
    initializeFormSubmission();
    
    
    document.addEventListener('photosUpdated', function(event) {
        updateFormProgress();
        updateSubmitButtonState();
    });
});


function initializeFormValidation() {
    // Height validation (reasonable human heights)
    const heightInput = document.getElementById('height');
    if (heightInput) {
        heightInput.addEventListener('input', function() {
            const value = parseFloat(this.value);
            const feedback = this.parentElement.nextElementSibling;
            
            if (!value || isNaN(value)) {
                this.classList.remove('is-valid', 'is-invalid');
                feedback.textContent = '';
                feedback.classList.remove('valid', 'invalid');
                return;
            }
            
            if (value < 120) {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
                feedback.textContent = 'Height should be at least 120 cm';
                feedback.classList.add('invalid');
                feedback.classList.remove('valid');
            } else if (value > 220) {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
                feedback.textContent = 'Height should not exceed 220 cm';
                feedback.classList.add('invalid');
                feedback.classList.remove('valid');
            } else {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
                feedback.textContent = 'Perfect!';
                feedback.classList.remove('invalid');
                feedback.classList.add('valid');
            }
            updateFormProgress();
        });
    }
    
    // Weight validation
    const weightInput = document.getElementById('weight');
    if (weightInput) {
        weightInput.addEventListener('input', function() {
            const value = parseFloat(this.value);
            const feedback = this.parentElement.nextElementSibling;
            
            if (!value || isNaN(value)) {
                this.classList.remove('is-valid', 'is-invalid');
                feedback.textContent = '';
                feedback.classList.remove('valid', 'invalid');
                return;
            }
            
            if (value < 30) {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
                feedback.textContent = 'Weight should be at least 30 kg';
                feedback.classList.add('invalid');
                feedback.classList.remove('valid');
            } else if (value > 200) {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
                feedback.textContent = 'Weight should not exceed 200 kg';
                feedback.classList.add('invalid');
                feedback.classList.remove('valid');
            } else {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
                feedback.textContent = 'Great!';
                feedback.classList.remove('invalid');
                feedback.classList.add('valid');
            }
            updateFormProgress();
        });
    }
    
    // Gender selection enhancement
    const genderOptions = document.querySelectorAll('input[name="gender"]');
    genderOptions.forEach(option => {
        option.addEventListener('change', function() {
            
            const allLabels = document.querySelectorAll('.gender-label');
            allLabels.forEach(label => label.classList.remove('selected'));
            
            if (this.checked) {
                this.nextElementSibling.classList.add('selected');
                
                
                updateGenderSpecificUI(this.value);
                updateFormProgress();
            }
        });
    });
}

/* Form Submission Handler */
function initializeFormSubmission() {
    const avatarForm = document.getElementById('avatarForm');
    
    if (!avatarForm) return;
    
    avatarForm.addEventListener('submit', async function(e) {
        
        e.preventDefault();
        
        console.log('Form submission started');
        
        
        if (!validateAvatarForm()) {
            showToast('Please fill in all required fields correctly', 'error');
            return;
        }
        
        
        const formData = collectFormData();
        
        
        const submitButton = document.getElementById('generateBtn');
        setLoading(true, submitButton);
        
        try {
            
            const hasPhotos = window.cameraController && window.cameraController.hasAllPhotos();
            
            if (hasPhotos) {
                
                const response = await submitEnhancedAnalysis(formData);
                handleAnalysisResponse(response);
            } else {
                
                const response = await submitBasicAnalysis(formData);
                handleAnalysisResponse(response);
            }
            
        } catch (error) {
            console.error('Form submission error:', error);
            showToast(error.message || 'Failed to generate avatar. Please try again.', 'error');
        } finally {
            
            setLoading(false, submitButton);
        }
    });
}

/* Submit Basic Analysis */
async function submitBasicAnalysis(formData) {
    console.log('Submitting basic analysis');
    
    const response = await fetch('/api/generate-avatar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            height: formData.height,
            weight: formData.weight,
            gender: formData.gender
        })
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || errorData.message || `Server error (${response.status})`);
    }
    
    return response.json();
}

/*
 * Submit Enhanced Analysis
 * Sends measurements along with timer-captured photos
 */
async function submitEnhancedAnalysis(basicData) {
    console.log('Submitting enhanced analysis with timer photos');
    
    
    const formData = new FormData();
    
    
    formData.append('height', basicData.height);
    formData.append('weight', basicData.weight);
    formData.append('gender', basicData.gender);
    formData.append('analysis_type', 'enhanced');
    
    
    const photos = window.cameraController.getCapturedPhotos();
    
    
    photos.forEach(photo => {
        formData.append(`photo_${photo.pose}`, photo.blob, `${photo.pose}.jpg`);
    });
    
    
    const photoMetadata = {
        capture_timestamp: Date.now(),
        poses: photos.map(p => p.pose),
        total_photos: photos.length,
        timer_settings: {
            timers_used: photos.map(p => p.timerUsed),
            average_timer: photos.reduce((sum, p) => sum + p.timerUsed, 0) / photos.length,
            timer_consistency: calculateTimerConsistency(photos)
        }
    };
    
    formData.append('photo_metadata', JSON.stringify(photoMetadata));
    
    
    const response = await fetch('/api/analyze-enhanced', {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Server error (${response.status})`);
    }
    
    return response.json();
}

/*
 * Handle Analysis Response
 * Process the response and redirect to results
 */
function handleAnalysisResponse(response) {
    console.log('Analysis response:', response);
    
    if (response.success || response.analysis_complete) {
        
        // IMPORTANT: Using 'avatarResult' as the unified key
        sessionStorage.setItem('avatarResult', JSON.stringify(response));
        
        
        const analysisType = response.analysis_type || 'basic';
        const message = analysisType === 'enhanced_with_timer' 
            ? 'Enhanced avatar generated successfully with timer photos!' 
            : 'Avatar generated successfully!';
        
        showToast(message, 'success');
        
        
        setTimeout(() => {
            window.location.href = '/report';
        }, 500);
    } else {
        throw new Error(response.message || 'Avatar generation failed');
    }
}

/* Calculate Timer Consistency */
function calculateTimerConsistency(photos) {
    const timers = photos.map(p => p.timerUsed);
    const uniqueTimers = [...new Set(timers)];
    return uniqueTimers.length === 1 ? 'consistent' : 'mixed';
}

/* Validate Avatar Form */
function validateAvatarForm() {
    let isValid = true;
    
    
    const height = document.getElementById('height');
    if (!height.value || height.value < 120 || height.value > 220) {
        height.classList.add('is-invalid');
        isValid = false;
    }
    
    
    const weight = document.getElementById('weight');
    if (!weight.value || weight.value < 30 || weight.value > 200) {
        weight.classList.add('is-invalid');
        isValid = false;
    }
    
    
    const gender = document.querySelector('input[name="gender"]:checked');
    if (!gender) {
        document.querySelectorAll('.gender-label').forEach(label => {
            label.classList.add('error');
        });
        isValid = false;
    }
    
    return isValid;
}

/* Collect Form Data */
function collectFormData() {
    const formData = {
        height: parseFloat(document.getElementById('height').value),
        weight: parseFloat(document.getElementById('weight').value),
        gender: document.querySelector('input[name="gender"]:checked').value,
    };
    
    
    const heightInMeters = formData.height / 100;
    formData.bmi = (formData.weight / (heightInMeters * heightInMeters)).toFixed(1);
    
    
    formData.timestamp = new Date().toISOString();
    
    return formData;
}

/* Update Submit Button State */
function updateSubmitButtonState() {
    const submitButton = document.getElementById('generateBtn');
    if (!submitButton) return;
    
    const hasPhotos = window.cameraController && window.cameraController.hasAllPhotos();
    
    if (hasPhotos) {
        submitButton.innerHTML = '🚀 Generate Enhanced 3D Avatar';
        submitButton.classList.add('enhanced');
        submitButton.title = 'Generate avatar with enhanced accuracy using timer photos';
    } else {
        submitButton.innerHTML = '📊 Generate 3D Avatar';
        submitButton.classList.remove('enhanced');
        submitButton.title = 'Generate basic avatar using measurements only';
    }
}

/* Update UI Based on Gender Selection */
function updateGenderSpecificUI(gender) {
    
    const formContainer = document.querySelector('.avatar-form');
    if (formContainer) {
        formContainer.dataset.gender = gender;
    }
}

// Progress indicator as user fills the form
function updateFormProgress() {
    const requiredFields = document.querySelectorAll('[required]');
    const filledFields = Array.from(requiredFields).filter(field => {
        if (field.type === 'radio') {
            return document.querySelector(`input[name="${field.name}"]:checked`);
        }
        return field.value.trim() !== '';
    });
    
    const progress = (filledFields.length / requiredFields.length) * 100;
    
    
    const progressBar = document.querySelector('.form-progress-bar');
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
    }
    
    
    const steps = document.querySelectorAll('.progress-step');
    const stepsCompleted = Math.floor((progress / 100) * steps.length);
    
    steps.forEach((step, index) => {
        if (index < stepsCompleted) {
            step.classList.add('active');
        } else {
            step.classList.remove('active');
        }
    });
    
    
    updateSubmitButtonState();
}


document.addEventListener('input', updateFormProgress);
document.addEventListener('change', updateFormProgress);


document.addEventListener('DOMContentLoaded', function() {
    updateFormProgress();
    updateSubmitButtonState();
});