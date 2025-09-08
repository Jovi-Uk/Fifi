


class ReportPage {
    constructor() {
        this.avatarData = null;
        this.mannequinViewer = null;
        this.init();
    }

    init() {
        console.log('ReportPage: Initializing');
        
        
        this.loadAvatarData();

        if (this.avatarData) {
            this.populateInfo();
            this.initializeViewer();
            this.initializeInteractions();
        } else {
            this.showError();
        }
    }

    loadAvatarData() {
        
        const sessionData = sessionStorage.getItem('avatarResult');
        
        if (sessionData) {
            try {
                this.avatarData = JSON.parse(sessionData);
                console.log('ReportPage: Avatar data loaded successfully', this.avatarData);
            } catch (e) {
                console.error('ReportPage: Failed to parse avatar data', e);
                this.avatarData = null;
            }
        } else {
            console.warn('ReportPage: No avatar data found in session storage');
        }
    }

    populateInfo() {
        console.log('ReportPage: Populating user information');
        
        
        const userMeasurements = this.avatarData.user_measurements || {};
        const mannequin = this.avatarData.mannequin || {};
        const similarityScore = mannequin.similarity_score || this.avatarData.similarity_score || 0;
        
        
        this.setElementText('userHeight', `${userMeasurements.height_cm || '--'} cm`);
        this.setElementText('userWeight', `${userMeasurements.weight_kg || '--'} kg`);
        this.setElementText('userBMI', userMeasurements.bmi || '--');
        this.setElementText('userGender', this.capitalizeFirst(userMeasurements.gender || '--'));
        
        
        this.setElementText('modelHeight', `${mannequin.estimated_height || '--'} cm`);
        this.setElementText('modelWeight', `${mannequin.estimated_weight || '--'} kg`);
        this.setElementText('modelBMI', mannequin.estimated_bmi || '--');
        this.setElementText('modelId', mannequin.mannequin_id ? `#${mannequin.mannequin_id}` : '--');
        
        
        this.animateSimilarityScore(similarityScore);
        
        
        if (this.avatarData.analysis_type === 'enhanced_with_timer' && this.avatarData.photo_analysis) {
            this.displayEnhancedAnalysis();
        }
    }

    setElementText(elementId, text) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
        } else {
            console.warn(`ReportPage: Element '${elementId}' not found`);
        }
    }

    animateSimilarityScore(targetScore) {
        const scoreElement = document.getElementById('similarityScore');
        if (!scoreElement) return;
        
        let currentScore = 0;
        const increment = targetScore / 50; 
        
        const animationInterval = setInterval(() => {
            currentScore += increment;
            if (currentScore >= targetScore) {
                currentScore = targetScore;
                clearInterval(animationInterval);
            }
            scoreElement.textContent = Math.round(currentScore) + '%';
        }, 20);
    }

    displayEnhancedAnalysis() {
        const photoAnalysis = this.avatarData.photo_analysis;
        const timerAnalytics = this.avatarData.timer_analytics;
        
        
        const infoCard = document.querySelector('.info-card');
        if (!infoCard) return;
        
        
        const enhancedContainer = document.getElementById('enhancedAnalysisContainer');
        if (photoAnalysis && enhancedContainer) {
            const analysisSection = document.createElement('div');
            analysisSection.className = 'enhanced-analysis-section';
            analysisSection.innerHTML = `
                <div class="section-title">Photo Analysis Results</div>
                <div class="analysis-grid">
                    <div class="analysis-item">
                        <span class="analysis-label">Confidence Score</span>
                        <span class="analysis-value">${photoAnalysis.confidence_score}%</span>
                    </div>
                    <div class="analysis-item">
                        <span class="analysis-label">Body Symmetry</span>
                        <span class="analysis-value">${photoAnalysis.symmetry_score}%</span>
                    </div>
                </div>
            `;
            enhancedContainer.appendChild(analysisSection);
        }
        
        
        if (timerAnalytics && enhancedContainer) {
            const timerSection = document.createElement('div');
            timerSection.className = 'timer-analysis-section';
            timerSection.innerHTML = `
                <div class="section-title">Timer Effectiveness</div>
                <div class="timer-info">
                    <p>Timer Setting: ${timerAnalytics.average_timer}s average</p>
                    <p>Quality Impact: ${timerAnalytics.photo_quality_impact}</p>
                    <p>Recommended Timer: ${timerAnalytics.recommended_timer}</p>
                </div>
            `;
            enhancedContainer.appendChild(timerSection);
        }
    }

    initializeViewer() {
        console.log('ReportPage: Initializing 3D viewer');
        
        const viewerContainer = document.getElementById('mannequin-viewer');
        if (!viewerContainer) {
            console.error('ReportPage: Viewer container not found');
            return;
        }
        
        
        const mannequin = this.avatarData.mannequin || {};
        const modelPath = mannequin.file_path || '/static/mannequins/default.glb';
        
        
        this.showLoadingState(true);
        
        
        try {
            this.mannequinViewer = new MannequinViewer('mannequin-viewer', modelPath);
            
            
            viewerContainer.addEventListener('mannequinLoaded', () => {
                console.log('ReportPage: Mannequin loaded successfully');
                this.showLoadingState(false);
                showToast('3D model loaded successfully!', 'success');
            });
        } catch (error) {
            console.error('ReportPage: Error initializing viewer', error);
            this.showViewerError();
        }
    }

    showLoadingState(show) {
        const loadingElement = document.getElementById('loadingState');
        if (loadingElement) {
            loadingElement.style.display = show ? 'flex' : 'none';
        }
    }

    showViewerError() {
        const viewerContainer = document.getElementById('mannequin-viewer');
        if (viewerContainer) {
            viewerContainer.innerHTML = `
                <div class="viewer-error">
                    <svg width="60" height="60" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                    </svg>
                    <h3>Unable to load 3D model</h3>
                    <p>Please try refreshing the page</p>
                    <button onclick="location.reload()" class="btn btn-primary">Refresh</button>
                </div>
            `;
        }
    }

    initializeInteractions() {
        console.log('ReportPage: Setting up interactions');
        
        
        const downloadBtn = document.querySelector('.action-btn');
        if (downloadBtn && downloadBtn.textContent.includes('Download')) {
            downloadBtn.addEventListener('click', () => this.downloadReport());
        }
        
        
        const newAvatarBtn = document.querySelector('.btn-back');
        if (newAvatarBtn) {
            newAvatarBtn.addEventListener('click', (e) => {
                e.preventDefault();
                
                sessionStorage.removeItem('avatarResult');
                window.location.href = newAvatarBtn.href;
            });
        }
        
        
        this.initializeSharing();
    }

    initializeSharing() {
        
        const shareButtons = document.querySelectorAll('.share-btn');
        shareButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const platform = btn.dataset.platform;
                this.shareAvatar(platform);
            });
        });
    }

    downloadReport() {
        console.log('ReportPage: Downloading report');
        
        try {
            
            const reportData = {
                generatedAt: new Date().toISOString(),
                analysisType: this.avatarData.analysis_type,
                userMeasurements: this.avatarData.user_measurements,
                mannequinDetails: this.avatarData.mannequin,
                similarityScore: this.avatarData.mannequin.similarity_score || this.avatarData.similarity_score,
                photoAnalysis: this.avatarData.photo_analysis || null,
                timerAnalytics: this.avatarData.timer_analytics || null
            };
            
            
            const dataStr = JSON.stringify(reportData, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            
            
            const url = URL.createObjectURL(dataBlob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `avatar-report-${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showToast('Report downloaded successfully!', 'success');
        } catch (error) {
            console.error('ReportPage: Error downloading report', error);
            showToast('Failed to download report', 'error');
        }
    }

    shareAvatar(platform) {
        const shareUrl = window.location.href;
        const shareText = 'Check out my 3D avatar created with Fifi!';
        let shareLink;
        
        switch (platform) {
            case 'twitter':
                shareLink = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`;
                break;
            case 'facebook':
                shareLink = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`;
                break;
            case 'linkedin':
                shareLink = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`;
                break;
            default:
                showToast('Sharing not available for this platform', 'info');
                return;
        }
        
        if (shareLink) {
            window.open(shareLink, '_blank', 'width=600,height=400');
        }
    }

    showError() {
        console.error('ReportPage: No avatar data available, redirecting to home');
        
        
        document.body.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100vh; text-align: center; background: #000; color: #fff;">
                <div>
                    <h2>No avatar data found</h2>
                    <p>Redirecting you back to create an avatar...</p>
                </div>
            </div>
        `;
        
        
        setTimeout(() => {
            window.location.href = '/demo';
        }, 2000);
    }

    capitalizeFirst(str) {
        return str ? str.charAt(0).toUpperCase() + str.slice(1) : '';
    }

    dispose() {
        
        if (this.mannequinViewer) {
            this.mannequinViewer.dispose();
        }
    }
}


document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing report page');
    window.reportPage = new ReportPage();
});


window.addEventListener('beforeunload', () => {
    if (window.reportPage) {
        window.reportPage.dispose();
    }
});