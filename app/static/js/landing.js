// static/js/landing.js - Landing Page Specific JavaScript





document.addEventListener('DOMContentLoaded', function() {
    const heroVideo = document.getElementById('heroVideo');
    if (heroVideo) {
        
        heroVideo.removeAttribute('controls');
        
        
        heroVideo.muted = true;
        heroVideo.autoplay = true;
        heroVideo.loop = true;
        heroVideo.playsInline = true;
        
        
        heroVideo.load();
        
        
        const attemptPlay = () => {
            heroVideo.play().then(() => {
                console.log('Video playing successfully');
            }).catch((error) => {
                console.log('Video autoplay attempt failed:', error);
                
                setTimeout(attemptPlay, 100);
            });
        };
        
        
        attemptPlay();
        
        
        const playOnInteraction = () => {
            heroVideo.play();
            document.removeEventListener('click', playOnInteraction);
            document.removeEventListener('scroll', playOnInteraction);
            document.removeEventListener('touchstart', playOnInteraction);
        };
        
        document.addEventListener('click', playOnInteraction);
        document.addEventListener('scroll', playOnInteraction);
        document.addEventListener('touchstart', playOnInteraction);
    }
    
    
    initialiseAppleProblemSection();
    
    
    initializePanoramicCarousel();

    
    setupProblemSectionStats();
});
 document.addEventListener("DOMContentLoaded", () => {
    const track = document.getElementById("panoramicTrack");

    let speed = 2; 
    let position = 0;
    let paused = false;

    function animate() {
        if (!paused) {
            position -= speed;
            
            if (Math.abs(position) >= track.scrollWidth / 2) {
                position = 0;
            }
            track.style.transform = `translateX(${position}px)`;
        }
        requestAnimationFrame(animate);
    }

    
    track.addEventListener("mouseenter", () => paused = true);
    track.addEventListener("mouseleave", () => paused = false);

    animate();
});
// Enhanced Navigation Scroll Effect
window.addEventListener('scroll', () => {
    const navbar = document.getElementById('navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// Smooth Scrolling for Navigation Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start',
                inline: 'nearest'
            });
        }
    });
});


const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            
            const sectionContent = entry.target.querySelector('.section-content');
            if (sectionContent) {
                sectionContent.classList.add('visible');
            } else {
                
                entry.target.classList.add('visible');
            }
        }
    });
}, observerOptions);


document.querySelectorAll('.section').forEach(section => {
    observer.observe(section);
});


function openPartnerModal() {
    document.getElementById('partnerModal').style.display = 'flex';
    document.getElementById('partnerModal').style.alignItems = 'center';
    document.getElementById('partnerModal').style.justifyContent = 'center';
}

function closePartnerModal() {
    document.getElementById('partnerModal').style.display = 'none';
}

window.onclick = function(event) {
    const modal = document.getElementById('partnerModal');
    if (event.target == modal) {
        closePartnerModal();
    }
}


const messageTextarea = document.getElementById('partnerMessage');
const charCountSpan = document.querySelector('.char-count');
if(messageTextarea) {
    messageTextarea.addEventListener('input', () => {
        const currentLength = messageTextarea.value.length;
        charCountSpan.textContent = `${currentLength} / 1000`;
    });
}


function handlePartnerSubmit(event) {
    event.preventDefault();
    console.log('Form submitted');
    alert('Thank you! Your message has been sent.');
    closePartnerModal();
}


function animateNumberOnce(el, totalDurationMs = 1500) {
    if (!el || el.dataset.animated === 'true') return;

    const original = (el.textContent || '').trim();
    const isPercentage = original.includes('%');
    const isCurrency = original.includes('$');
    const hasB = original.toUpperCase().includes('B');
    const numeric = parseInt(original.replace(/[^\d]/g, ''), 10) || 0;
    if (numeric === 0) { el.dataset.animated = 'true'; return; }

    const steps = 50;
    const increment = numeric / steps;
    const interval = Math.max(10, Math.floor(totalDurationMs / steps));
    let current = 0;

    el.dataset.animated = 'true';
    const timer = setInterval(() => {
        current += increment;
        if (current >= numeric) {
            current = numeric;
            clearInterval(timer);
        }
        const v = Math.floor(current);
        if (isCurrency) {
            el.textContent = '$' + v + (hasB ? 'B' : '');
        } else if (isPercentage) {
            el.textContent = v + '%';
        } else {
            el.textContent = String(v);
        }
    }, interval);
}

function setupProblemSectionStats() {
    const grid = document.querySelector('.problem-visual');
    if (!grid) return;

    const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                grid.querySelectorAll('.stat-number').forEach(el => animateNumberOnce(el));
                obs.disconnect();
            }
        });
    }, { threshold: 0.3 });

    observer.observe(grid);
}

// Problem Section Functionality with Scrollytelling
function initialiseAppleProblemSection() {
    const problemSection = document.querySelector('#problem') || document.querySelector('.apple-problem-section') || document.querySelector('.problem-section-immersive');
    const problemStatements = document.querySelectorAll('.problem-statement');
    const problemVideo = document.getElementById('problemVideo');
    const playButton = document.getElementById('problemVideoPlayBtn');
    const contentWrapper = document.querySelector('.problem-content-wrapper');
    
    if (!problemSection) {
        console.log('Problem section not found');
        return;
    }
    
    
    function setupIntersectionScrollytelling() {
        
        const observerOptions = {
            root: null,
            threshold: [0, 0.15, 0.3, 0.45, 0.6, 0.75],
            rootMargin: '-20% 0px -20% 0px' 
        };
        
    const statementObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
        if (entry.intersectionRatio > 0.3) {
                    
                    entry.target.classList.add('visible');
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
            
            const statEl = entry.target.querySelector('.problem-stat-number');
            if (statEl) animateNumberOnce(statEl);
                } else if (entry.intersectionRatio < 0.15) {
                    
                    entry.target.classList.remove('visible');
                    entry.target.style.opacity = '0';
                    entry.target.style.transform = 'translateY(100px)';
                }
            });
        }, observerOptions);
        
        
        problemStatements.forEach((statement, index) => {
            
            statement.style.opacity = '0';
            statement.style.transform = 'translateY(100px)';
            statement.style.transition = `all ${1.2 + index * 0.2}s cubic-bezier(0.4, 0, 0.2, 1)`;
            
            
            statementObserver.observe(statement);
        });
        
        
        if (problemStatements[0]) {
            problemStatements[0].classList.add('visible');
            problemStatements[0].style.opacity = '1';
            problemStatements[0].style.transform = 'translateY(0)';
        }

        
        const sectionObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    problemSection.classList.add('in-view');
                } else {
                    problemSection.classList.remove('in-view');
                }
            });
        }, { threshold: 0.1 });
        
        sectionObserver.observe(problemSection);
    }
    
    /* Set up video playback controls */
    function setupVideoControls() {
        if (!playButton || !problemVideo) {
            console.log('Video or play button not found');
            return;
        }
        
        
        let isPlaying = false;
        
        
        problemVideo.muted = true;
        problemVideo.loop = true;
        problemVideo.playsInline = true;
        
        
        function togglePlayback() {
            if (isPlaying) {
                problemVideo.pause();
                updatePlayButton(false);
            } else {
                problemVideo.play()
                    .then(() => {
                        updatePlayButton(true);
                    })
                    .catch(err => {
                        console.error('Video play failed:', err);
                        updatePlayButton(false);
                    });
            }
        }
        
        
        function updatePlayButton(playing) {
            isPlaying = playing;
            
            if (playing) {
                
                playButton.innerHTML = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <rect x="6" y="4" width="4" height="16" fill="currentColor"/>
                        <rect x="14" y="4" width="4" height="16" fill="currentColor"/>
                    </svg>
                `;
                playButton.setAttribute('aria-label', 'Pause video');
            } else {
                
                playButton.innerHTML = `
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M8 5v14l11-7z" fill="currentColor"/>
                    </svg>
                `;
                playButton.setAttribute('aria-label', 'Play video');
            }
        }
        
        
        playButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            togglePlayback();
        });
        
        
        problemVideo.addEventListener('play', () => updatePlayButton(true));
        problemVideo.addEventListener('pause', () => updatePlayButton(false));
        problemVideo.addEventListener('ended', () => updatePlayButton(false));
        
        
        problemVideo.play()
            .then(() => {
                console.log('Video autoplaying');
                updatePlayButton(true);
            })
            .catch(err => {
                console.log('Autoplay prevented, user interaction required');
                updatePlayButton(false);
            });

        
        setTimeout(() => {
            if (problemVideo.clientHeight === 0) {
                problemVideo.load();
                problemVideo.play().catch(()=>{});
            }
        }, 500);
    }
    
    
    setupIntersectionScrollytelling(); 
    setupVideoControls();              

    
    
    console.log('Apple-style problem section initialized');
}


function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}



/* PANORAMIC CAROUSEL */
function initializePanoramicCarousel() {
    const panoramicSection = document.getElementById('panoramicCarousel');
    const panoramicTrack = document.getElementById('panoramicTrack');
    
    if (!panoramicSection || !panoramicTrack) return;
    
    
    let isDragging = false;          
    let startX = 0;                  
    let currentTranslateX = 0;       
    let lastTranslateX = 0;          
    let velocity = 0;                
    let animationFrame = null;       
    
    
    const items = panoramicTrack.querySelectorAll('.panoramic-item');
    if (items.length === 0) return;
    
    
    let totalOriginalWidth = 0;      
    let singleSetWidth = 0;          
    
    
    function calculateDimensions() {
        totalOriginalWidth = 0;
        
        
        const originalItemCount = 6; 
        
        for (let i = 0; i < originalItemCount; i++) {
            if (items[i]) {
                
                totalOriginalWidth += items[i].offsetWidth + 40;
            }
        }
        
        
        singleSetWidth = totalOriginalWidth;
        
        console.log('Carousel dimensions calculated:', {
            totalWidth: totalOriginalWidth,
            itemCount: items.length,
            originalCount: originalItemCount
        });
    }
    
    
    function applyTranslation(x) {
        
        panoramicTrack.style.transform = `translateX(${x}px)`;
        currentTranslateX = x;
        
        
        if (currentTranslateX < -singleSetWidth) {
            
            currentTranslateX += singleSetWidth;
            panoramicTrack.style.transition = 'none'; 
            panoramicTrack.style.transform = `translateX(${currentTranslateX}px)`;
        }
        
        else if (currentTranslateX > 0) {
            
            currentTranslateX -= singleSetWidth;
            panoramicTrack.style.transition = 'none';
            panoramicTrack.style.transform = `translateX(${currentTranslateX}px)`;
        }
    }


    
    function handleMouseDown(e) {
        
        if (e.button !== 0) return;
        
        isDragging = true;
        startX = e.clientX;              
        lastTranslateX = currentTranslateX;  
        
        
        panoramicSection.style.cursor = 'grabbing';
        panoramicSection.style.userSelect = 'none'; 
        
        
        panoramicTrack.style.transition = 'none';
        
        
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
            animationFrame = null;
        }
        
        e.preventDefault(); 
    }
    
    
    function handleMouseMove(e) {
        if (!isDragging) return;
        
        
        const deltaX = e.clientX - startX;
        
        
        velocity = deltaX - (currentTranslateX - lastTranslateX);
        
        
        
        const newTranslateX = lastTranslateX + deltaX;
        applyTranslation(newTranslateX);
        
        e.preventDefault();
    }
    
    
    function handleMouseUp(e) {
        if (!isDragging) return;
        
        isDragging = false;
        
        
        panoramicSection.style.cursor = 'grab';
        panoramicSection.style.userSelect = '';
        
        
        applyMomentum();
        
        e.preventDefault();
    }
    
    
    function applyMomentum() {
        const friction = 0.95;        
        const minVelocity = 0.5;      
        
        function animate() {
            if (Math.abs(velocity) > minVelocity) {
                velocity *= friction;  
                
                
                applyTranslation(currentTranslateX + velocity * 0.1);
                
                
                animationFrame = requestAnimationFrame(animate);
            } else {
                
                velocity = 0;
                animationFrame = null;
            }
        }
        
        
        if (Math.abs(velocity) > minVelocity) {
            animate();
        }
    }
    
    
    function handleMouseLeave(e) {
        if (isDragging) {
            handleMouseUp(e);
        }
    }
    
    
    function handleWheel(e) {
        
        if (Math.abs(e.deltaX) > Math.abs(e.deltaY) || e.shiftKey) {
            e.preventDefault();
            
            const scrollAmount = e.shiftKey ? e.deltaY : e.deltaX;
            const newTranslateX = currentTranslateX - scrollAmount;
            
            
            panoramicTrack.style.transition = 'transform 0.3s ease-out';
            applyTranslation(newTranslateX);
        }
    }
    
    
    calculateDimensions();
    
    
    panoramicSection.style.cursor = 'grab';
    
    
    
    document.addEventListener('mousemove', handleMouseMove);  
    document.addEventListener('mouseup', handleMouseUp);      
    
    
    
    
    window.addEventListener('resize', () => {
        calculateDimensions();
    });
    
    
    const images = panoramicTrack.querySelectorAll('img');
    images.forEach(img => {
        img.addEventListener('dragstart', e => e.preventDefault());
        img.style.userSelect = 'none';  
        img.style.pointerEvents = 'none'; 
    });
    
    console.log('Panoramic carousel initialized with drag interaction');
}


window.openPartnerModal = openPartnerModal;
window.closePartnerModal = closePartnerModal;
window.handlePartnerSubmit = handlePartnerSubmit;
window.initialiseAppleProblemSection = initialiseAppleProblemSection;
window.initializePanoramicCarousel = initializePanoramicCarousel;