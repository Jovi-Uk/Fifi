/* Camera Controller */

class CameraController {
    constructor() {
        this.currentPoseIndex = 0;
        this.capturedPhotos = [];
        this.stream = null;
        this.isCapturing = false;
        this.timerActive = false;
        this.timerInterval = null;
        this.selectedTimer = 5; 
        
        // Analytics tracking
        this.retakeCount = 0;
        this.timerCancellationCount = 0;
        this.sessionStartTime = Date.now();
        
        
        this.audioContext = null;
        this.enableAudio = true;
        
        // Pose configurations
        this.poses = [
            {
                name: 'front',
                instruction: 'Stand facing the camera',
                description: 'Position yourself within the guide outline. Stand naturally with arms slightly away from your body. Make sure your full body is visible.',
                guideClass: 'front',
                guideText: 'Face Forward'
            },
            {
                name: 'left',
                instruction: 'Turn to show your left side',
                description: 'Turn 90° to your left. Keep arms slightly away from your body. Stand straight and ensure your full profile is visible.',
                guideClass: 'left',
                guideText: 'Left Side'
            },
            {
                name: 'right',
                instruction: 'Turn to show your right side',
                description: 'Turn 90° to your right. Keep arms slightly away from your body. Stand straight and ensure your full profile is visible.',
                guideClass: 'right',
                guideText: 'Right Side'
            },
            {
                name: 'back',
                instruction: 'Turn to show your back',
                description: 'Turn around completely. Keep arms slightly away from your body. Look straight ahead and ensure your full back view is visible.',
                guideClass: 'back',
                guideText: 'Face Away'
            }
        ];
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updatePhotoStatus();
        this.initializeAudio();
    }
    
    initializeAudio() {
    // Initialize Web Audio API for countdown sounds    
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.warn('Web Audio API not supported, countdown will be silent');
            this.enableAudio = false;
        }
    }
    
    bindEvents() {
        // Open camera button
        document.getElementById('openCameraBtn').addEventListener('click', () => {
            this.openCamera();
        });
        
        // Timer selection
        document.getElementById('timer5s').addEventListener('change', (e) => {
            if (e.target.checked) {
                this.selectedTimer = 5;
                this.updateTimerDisplay();
            }
        });
        
        document.getElementById('timer10s').addEventListener('change', (e) => {
            if (e.target.checked) {
                this.selectedTimer = 10;
                this.updateTimerDisplay();
            }
        });
        
        // Camera modal controls
        document.getElementById('captureBtn').addEventListener('click', () => {
            this.startCaptureTimer();
        });
        
        document.getElementById('cancelTimerBtn').addEventListener('click', () => {
            this.cancelTimer();
        });
        
        document.getElementById('retakeBtn').addEventListener('click', () => {
            this.retakeCurrentPhoto();
        });
        
        document.getElementById('closeCameraBtn').addEventListener('click', () => {
            this.closeCamera();
        });
        
         // Close modal on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (this.timerActive) {
                    this.cancelTimer();
                } else if (this.stream) {
                    this.closeCamera();
                }
            }
        });
    }
    
    async openCamera() {
        try {
            
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user' 
                },
                audio: false
            });
            
            // Setup video stream
            const video = document.getElementById('cameraVideo');
            video.srcObject = this.stream;
            
            // Show modal
            document.getElementById('cameraModal').style.display = 'flex';
            
            // Reset to first pose if starting over
            if (this.capturedPhotos.length === 0) {
                this.currentPoseIndex = 0;
            }
            
            this.updatePoseGuide();
            this.updateProgressIndicator();
            this.updateTimerDisplay();
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.showCameraError(error);
        }
    }
    
    closeCamera() {
        
        this.cancelTimer();
        
        // Stop camera stream
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        // Hide modal
        document.getElementById('cameraModal').style.display = 'none';
        
         // Update photo status
        this.updatePhotoStatus();
    }
    
    updateTimerDisplay() {
        const timerDisplay = document.getElementById('timerDisplay');
        const captureBtn = document.getElementById('captureBtn');
        
        timerDisplay.textContent = `${this.selectedTimer}s timer selected`;
        
        if (this.currentPoseIndex === this.poses.length - 1) {
            captureBtn.innerHTML = `📸 Final Photo (${this.selectedTimer}s timer)`;
        } else {
            captureBtn.innerHTML = `📸 Capture Photo ${this.currentPoseIndex + 1}/4 (${this.selectedTimer}s timer)`;
        }
    }
    
    startCaptureTimer() {
        if (this.isCapturing || this.timerActive) return;
        
        this.timerActive = true;
        let countdown = this.selectedTimer;
        
         // Update UI for timer mode
        this.showTimerCountdown();
        
        // Update countdown display
        this.updateCountdownDisplay(countdown);
        
        // Play start sound
        this.playCountdownSound('start');
        
        // Start countdown
        this.timerInterval = setInterval(() => {
            countdown--;
            
            this.updateCountdownDisplay(countdown);
            
            // Play countdown sounds
            if (countdown <= 3 && countdown > 0) {
                this.playCountdownSound('tick');
            } else if (countdown === 0) {
                this.playCountdownSound('capture');
            }
            
            // Capture when countdown reaches 0
            if (countdown <= 0) {
                this.timerInterval = null;
                this.timerActive = false;
                this.hideTimerCountdown();
                this.capturePhoto();
            }
        }, 1000);
    }
    
    cancelTimer() {
        if (!this.timerActive) return;
        
        
        this.timerCancellationCount++;
        
         // Clear timer
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        
        this.timerActive = false;
        this.hideTimerCountdown();
        this.playCountdownSound('cancel');
        
        
        this.updateTimerDisplay();
    }
    
    showTimerCountdown() {
        // Hide normal controls, show timer interface    
        document.getElementById('captureBtn').style.display = 'none';
        document.getElementById('retakeBtn').style.display = 'none';
        document.getElementById('timerControls').style.display = 'none';
        
        // Show timer countdown interface
        document.getElementById('timerCountdown').style.display = 'flex';
        document.getElementById('cancelTimerBtn').style.display = 'inline-block';
        
        // Show positioning instruction
        const instruction = document.getElementById('poseInstruction');
        const originalInstruction = instruction.textContent;
        instruction.textContent = `Get ready! Position yourself for ${this.poses[this.currentPoseIndex].name} pose`;
        instruction.setAttribute('data-original', originalInstruction);
    }
    
    hideTimerCountdown() {
        // Show normal controls
        document.getElementById('captureBtn').style.display = 'inline-block';
        document.getElementById('retakeBtn').style.display = 'inline-block';
        document.getElementById('timerControls').style.display = 'flex';
        
        // Hide timer countdown interface
        document.getElementById('timerCountdown').style.display = 'none';
        document.getElementById('cancelTimerBtn').style.display = 'none';
        
        // Restore original instruction
        const instruction = document.getElementById('poseInstruction');
        const originalInstruction = instruction.getAttribute('data-original');
        if (originalInstruction) {
            instruction.textContent = originalInstruction;
            instruction.removeAttribute('data-original');
        }
    }
    
    updateCountdownDisplay(countdown) {
        const countdownNumber = document.getElementById('countdownNumber');
        const countdownCircle = document.getElementById('countdownCircle');
        const progressRing = document.getElementById('progressRing');
        
        if (countdown > 0) {
            countdownNumber.textContent = countdown;
            countdownNumber.className = 'countdown-number active';
            
             // Update progress ring
            const circumference = 2 * Math.PI * 45; 
            const progress = ((this.selectedTimer - countdown) / this.selectedTimer) * circumference;
            progressRing.style.strokeDasharray = `${progress} ${circumference}`;
            
            // Add pulse animation for last 3 seconds
            if (countdown <= 3) {
                countdownCircle.classList.add('pulse');
                countdownNumber.classList.add('urgent');
            }
        } else {
            countdownNumber.textContent = '📸';
            countdownNumber.className = 'countdown-number capture';
            countdownCircle.classList.remove('pulse');
            countdownCircle.classList.add('capture-flash');
        }
    }
    
    playCountdownSound(type) {
        if (!this.enableAudio || !this.audioContext) return;
        
        try {
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            // Different sounds for different events
            switch (type) {
                case 'start':
                    oscillator.frequency.setValueAtTime(800, this.audioContext.currentTime);
                    gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
                    break;
                case 'tick':
                    oscillator.frequency.setValueAtTime(600, this.audioContext.currentTime);
                    gainNode.gain.setValueAtTime(0.15, this.audioContext.currentTime);
                    break;
                case 'capture':
                    oscillator.frequency.setValueAtTime(1000, this.audioContext.currentTime);
                    gainNode.gain.setValueAtTime(0.2, this.audioContext.currentTime);
                    break;
                case 'cancel':
                    oscillator.frequency.setValueAtTime(400, this.audioContext.currentTime);
                    gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
                    break;
            }
            
            oscillator.start();
            oscillator.stop(this.audioContext.currentTime + 0.1);
        } catch (e) {
            
        }
    }
    
    updatePoseGuide() {
        const pose = this.poses[this.currentPoseIndex];
        
        // Update instructions
        document.getElementById('poseInstruction').textContent = pose.instruction;
        document.getElementById('poseDescription').textContent = pose.description;
        
        // Update pose guide
        const poseGuide = document.getElementById('poseGuide');
        poseGuide.className = `pose-guide ${pose.guideClass}`;
        poseGuide.textContent = pose.guideText;
        
        // Update timer display
        this.updateTimerDisplay();
    }
    
    updateProgressIndicator() {
        // Update progress steps
        for (let i = 0; i < this.poses.length; i++) {
            const step = document.getElementById(`step-${i}`);
            
            if (i < this.capturedPhotos.length) {
                step.className = 'progress-step completed';
            } else if (i === this.currentPoseIndex) {
                step.className = 'progress-step active';
            } else {
                step.className = 'progress-step';
            }
        }
    }
    
    async capturePhoto() {
        if (this.isCapturing) return;
        
        this.isCapturing = true;
        
        try {
            // Create canvas to capture frame
            const video = document.getElementById('cameraVideo');
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Set canvas size to match video
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            // Draw current video frame to canvas
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // Validate canvas content
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const pixels = imageData.data;
            
            // Check if image has content
            let hasContent = false;
            for (let i = 0; i < pixels.length; i += 4) {
                const r = pixels[i], g = pixels[i+1], b = pixels[i+2];
                if (r > 10 && g > 10 && b > 10 && (r < 245 || g < 245 || b < 245)) {
                    hasContent = true;
                    break;
                }
            }
            
            if (!hasContent) {
                throw new Error('Captured image appears to be empty or corrupted');
            }
            
            // Convert to blob with higher quality for full-body shots
            const blob = await new Promise((resolve, reject) => {
                canvas.toBlob(blob => {
                    if (blob && blob.size > 1000) {
                        resolve(blob);
                    } else {
                        reject(new Error('Failed to create valid image blob'));
                    }
                }, 'image/jpeg', 0.9); 
            });
            
            
            const photoData = {
                pose: this.poses[this.currentPoseIndex].name,
                blob: blob,
                dataUrl: canvas.toDataURL('image/jpeg', 0.9),
                timestamp: Date.now(),
                timerUsed: this.selectedTimer
            };
            
            
            if (this.capturedPhotos.length <= this.currentPoseIndex) {
                this.capturedPhotos.push(photoData);
            } else {
                this.capturedPhotos[this.currentPoseIndex] = photoData;
            }
            
            this.updateCapturedPhotosDisplay();
            this.updateProgressIndicator();
            this.showCaptureSuccess();
            this.dispatchPhotoUpdateEvent();
            
            
            if (this.currentPoseIndex < this.poses.length - 1) {
                setTimeout(() => {
                    this.currentPoseIndex++;
                    this.updatePoseGuide();
                }, 1500); 
            } else {
                
                setTimeout(() => {
                    this.showCompletionMessage();
                }, 1500);
            }
            
        } catch (error) {
            console.error('Error capturing photo:', error);
            this.showCaptureError();
        } finally {
            this.isCapturing = false;
        }
    }
    
    retakeCurrentPhoto() {
        
        this.retakeCount++;
        
        
        if (this.capturedPhotos[this.currentPoseIndex]) {
            this.capturedPhotos.splice(this.currentPoseIndex, 1);
        }
        
        
        this.updateCapturedPhotosDisplay();
        this.updateProgressIndicator();
        this.updatePoseGuide();
        
        
        document.getElementById('retakeBtn').style.display = 'none';
        
        
        this.dispatchPhotoUpdateEvent();
    }
    
    updateCapturedPhotosDisplay() {
        const container = document.getElementById('capturedPhotos');
        container.innerHTML = '';
        
        this.capturedPhotos.forEach((photo, index) => {
            const photoContainer = document.createElement('div');
            photoContainer.className = 'captured-photo-container';
            
            const img = document.createElement('img');
            img.src = photo.dataUrl;
            img.className = 'captured-photo';
            img.title = `${this.poses[index]?.name || 'Unknown'} pose (${photo.timerUsed}s timer)`;
            
            const timerBadge = document.createElement('div');
            timerBadge.className = 'timer-badge';
            timerBadge.textContent = `${photo.timerUsed}s`;
            
            photoContainer.appendChild(img);
            photoContainer.appendChild(timerBadge);
            container.appendChild(photoContainer);
        });
        
        
        if (this.capturedPhotos.length > 0) {
            document.getElementById('retakeBtn').style.display = 'inline-block';
        }
    }
    
    updatePhotoStatus() {
        const photoCount = document.getElementById('photoCount');
        const photoStatus = document.getElementById('photoStatus');
        
        photoCount.textContent = this.capturedPhotos.length;
        
        if (this.capturedPhotos.length === 4) {
            photoStatus.className = 'photo-status photos-captured';
            photoStatus.innerHTML = '✅ All photos captured! Enhanced accuracy enabled.';
        } else if (this.capturedPhotos.length > 0) {
            photoStatus.className = 'photo-status';
            photoStatus.innerHTML = `${this.capturedPhotos.length}/4 photos captured`;
        } else {
            photoStatus.className = 'photo-status';
            photoStatus.innerHTML = '0/4 photos captured';
        }
        
        
        this.dispatchPhotoUpdateEvent();
    }
    
    dispatchPhotoUpdateEvent() {
        
        const event = new CustomEvent('photosUpdated', {
            detail: {
                photoCount: this.capturedPhotos.length,
                hasAllPhotos: this.hasAllPhotos(),
                currentPose: this.currentPoseIndex,
                timerUsage: this.getTimerUsageStats()
            }
        });
        document.dispatchEvent(event);
    }
    
    getTimerUsageStats() {
        if (this.capturedPhotos.length === 0) return null;
        
        return {
            timer5sCount: this.capturedPhotos.filter(p => p.timerUsed === 5).length,
            timer10sCount: this.capturedPhotos.filter(p => p.timerUsed === 10).length,
            averageTimer: this.capturedPhotos.reduce((sum, p) => sum + p.timerUsed, 0) / this.capturedPhotos.length,
            retakeCount: this.retakeCount,
            cancellationCount: this.timerCancellationCount
        };
    }
    
    showCaptureSuccess() {
        
        const viewport = document.querySelector('.camera-viewport');
        viewport.style.border = '3px solid #28a745';
        
        
        const flash = document.createElement('div');
        flash.className = 'capture-flash-overlay';
        viewport.appendChild(flash);
        
        setTimeout(() => {
            viewport.style.border = 'none';
            if (flash.parentNode) {
                flash.parentNode.removeChild(flash);
            }
        }, 800);
    }
    
    showCaptureError() {
        
        const viewport = document.querySelector('.camera-viewport');
        viewport.style.border = '3px solid #dc3545';
        
        setTimeout(() => {
            viewport.style.border = 'none';
        }, 1000);
    }
    
    showCompletionMessage() {
        const instruction = document.getElementById('poseInstruction');
        const description = document.getElementById('poseDescription');
        
        instruction.textContent = '🎉 All photos captured successfully!';
        description.textContent = 'Excellent work! You can now close the camera and generate your 3D avatar with enhanced accuracy.';
        
        
        const captureBtn = document.getElementById('captureBtn');
        captureBtn.innerHTML = '✅ Photos Complete';
        captureBtn.disabled = true;
        captureBtn.style.background = '#28a745';
        
        
        document.getElementById('timerControls').style.display = 'none';
    }
    
    showCameraError(error) {
        let message = 'Unable to access camera. ';
        
        if (error.name === 'NotAllowedError') {
            message += 'Please allow camera permissions and try again.';
        } else if (error.name === 'NotFoundError') {
            message += 'No camera found on this device.';
        } else {
            message += 'Please check your camera and try again.';
        }
        
        alert(message);
    }
    
    
    getCapturedPhotos() {
        return this.capturedPhotos;
    }
    
    
    hasAllPhotos() {
        return this.capturedPhotos.length === 4;
    }
    
    
    clearPhotos() {
        this.capturedPhotos = [];
        this.currentPoseIndex = 0;
        this.retakeCount = 0;
        this.timerCancellationCount = 0;
        this.updatePhotoStatus();
        this.updateCapturedPhotosDisplay();
        this.dispatchPhotoUpdateEvent();
    }
    
    
    getPhotosAsFormData() {
        const formData = new FormData();
        
        this.capturedPhotos.forEach((photo, index) => {
            formData.append(`photo_${photo.pose}`, photo.blob, `${photo.pose}.jpg`);
        });
        
        
        const timerMetadata = {
            timers_used: this.capturedPhotos.map(p => p.timerUsed),
            average_timer: this.capturedPhotos.reduce((sum, p) => sum + p.timerUsed, 0) / this.capturedPhotos.length
        };
        formData.append('timer_metadata', JSON.stringify(timerMetadata));
        
        return formData;
    }
}


let cameraController;
document.addEventListener('DOMContentLoaded', () => {
    cameraController = new CameraController();
});