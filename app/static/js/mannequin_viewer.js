

class MannequinViewer {
    constructor(containerId, mannequinPath) {
        this.container = document.getElementById(containerId);
        this.mannequinPath = mannequinPath;
        
        
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.mannequin = null;
        this.lights = [];
        
        
        this.controls = {
            isRotating: false,
            isZooming: false,
            previousMouseX: 0,
            previousMouseY: 0,
            rotationSpeed: 0.005,
            zoomSpeed: 0.1,
            minZoom: 1,
            maxZoom: 5,
            currentZoom: 2.5
        };
        
        
        this.animationId = null;
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error('Container element not found');
            return;
        }
        
        this.createScene();
        this.createCamera();
        this.createRenderer();
        this.setupLighting();
        this.loadMannequin();
        this.setupControls();
        this.handleResize();
        this.animate();
    }
    
    createScene() {
        this.scene = new THREE.Scene();
        
        
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = 512;
        canvas.height = 512;
        
        const gradient = context.createLinearGradient(0, 0, 0, canvas.height);
        gradient.addColorStop(0, '#f8f9fa');
        gradient.addColorStop(0.5, '#e9ecef');
        gradient.addColorStop(1, '#dee2e6');
        
        context.fillStyle = gradient;
        context.fillRect(0, 0, canvas.width, canvas.height);
        
        const texture = new THREE.CanvasTexture(canvas);
        this.scene.background = texture;
        
        
        this.scene.fog = new THREE.Fog(0xf8f9fa, 5, 15);
    }
    
    createCamera() {
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 100);
        this.camera.position.set(0, 0, this.controls.currentZoom);
        this.camera.lookAt(0, 0, 0);
    }
    
    createRenderer() {
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true,
            alpha: false,
            powerPreference: "high-performance"
        });
        
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        
        
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.outputEncoding = THREE.sRGBEncoding;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.2;
        
        
        this.container.innerHTML = '';
        this.container.appendChild(this.renderer.domElement);
    }
    
    setupLighting() {
        
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);
        this.lights.push(ambientLight);
        
        
        const keyLight = new THREE.DirectionalLight(0xffffff, 0.8);
        keyLight.position.set(3, 4, 5);
        keyLight.castShadow = true;
        
        
        keyLight.shadow.mapSize.width = 2048;
        keyLight.shadow.mapSize.height = 2048;
        keyLight.shadow.camera.near = 0.5;
        keyLight.shadow.camera.far = 15;
        keyLight.shadow.camera.left = -3;
        keyLight.shadow.camera.right = 3;
        keyLight.shadow.camera.top = 3;
        keyLight.shadow.camera.bottom = -3;
        keyLight.shadow.bias = -0.0001;
        
        this.scene.add(keyLight);
        this.lights.push(keyLight);
        
        
        const fillLight = new THREE.DirectionalLight(0xffffff, 0.4);
        fillLight.position.set(-2, 2, -3);
        this.scene.add(fillLight);
        this.lights.push(fillLight);
        
        
        const rimLight = new THREE.DirectionalLight(0xffffff, 0.3);
        rimLight.position.set(-1, -1, -2);
        this.scene.add(rimLight);
        this.lights.push(rimLight);
        
        
        const groundGeometry = new THREE.PlaneGeometry(10, 10);
        const groundMaterial = new THREE.ShadowMaterial({ opacity: 0.2 });
        const groundPlane = new THREE.Mesh(groundGeometry, groundMaterial);
        groundPlane.rotation.x = -Math.PI / 2;
        groundPlane.position.y = -1;
        groundPlane.receiveShadow = true;
        this.scene.add(groundPlane);
    }
    
    loadMannequin() {
        const loader = new THREE.GLTFLoader();
        
        
        console.log('Loading mannequin from:', this.mannequinPath);
        
        loader.load(
            this.mannequinPath,
            (gltf) => this.onMannequinLoaded(gltf),
            (progress) => this.onLoadProgress(progress),
            (error) => this.onLoadError(error)
        );
    }
    
    onMannequinLoaded(gltf) {
        console.log('Mannequin loaded successfully');
        
        this.mannequin = gltf.scene;
        
        
        this.processMannequin();
        
        
        this.scene.add(this.mannequin);
        
        
        this.container.dispatchEvent(new CustomEvent('mannequinLoaded'));
    }
    
    processMannequin() {
        
        const box = new THREE.Box3().setFromObject(this.mannequin);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        
        
        this.mannequin.position.sub(center);
        
        
        const targetHeight = 1.8;
        const currentHeight = size.y;
        if (currentHeight > 0) {
            const scale = targetHeight / currentHeight;
            this.mannequin.scale.setScalar(scale);
        }
        
        
        this.mannequin.traverse((child) => {
            if (child.isMesh) {
                
                child.castShadow = true;
                child.receiveShadow = true;
                
                
                if (child.material) {
                    
                    if (child.material.isMeshStandardMaterial) {
                        child.material.roughness = 0.8;
                        child.material.metalness = 0.1;
                    } else {
                        
                        const newMaterial = new THREE.MeshStandardMaterial({
                            color: child.material.color || 0xcccccc,
                            roughness: 0.8,
                            metalness: 0.1,
                            flatShading: false
                        });
                        child.material = newMaterial;
                    }
                } else {
                    
                    child.material = new THREE.MeshStandardMaterial({
                        color: 0xcccccc,
                        roughness: 0.8,
                        metalness: 0.1
                    });
                }
                
                
                if (child.geometry) {
                    child.geometry.computeVertexNormals();
                }
            }
        });
        
        
        this.mannequin.position.y = -0.2;
    }
    
    onLoadProgress(progress) {
        const percentComplete = (progress.loaded / progress.total) * 100;
        console.log('Loading progress:', Math.round(percentComplete) + '%');
    }
    
    onLoadError(error) {
        console.error('Error loading mannequin:', error);
        this.showErrorMessage();
    }
    
    showErrorMessage() {
        this.container.innerHTML = `
            <div style="
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100%;
                color: #dc3545;
                text-align: center;
                padding: 2rem;
            ">
                <svg width="60" height="60" fill="currentColor" viewBox="0 0 24 24" style="margin-bottom: 1rem;">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                <h4>Unable to load 3D model</h4>
                <p style="color: #6c757d; margin: 0;">The mannequin file may still be processing</p>
            </div>
        `;
    }
    
    setupControls() {
        const canvas = this.renderer.domElement;
        
        
        canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
        canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
        canvas.addEventListener('mouseup', () => this.onMouseUp());
        canvas.addEventListener('wheel', (e) => this.onWheel(e));
        
        
        canvas.addEventListener('touchstart', (e) => this.onTouchStart(e));
        canvas.addEventListener('touchmove', (e) => this.onTouchMove(e));
        canvas.addEventListener('touchend', () => this.onTouchEnd());
        
        
        canvas.addEventListener('contextmenu', (e) => e.preventDefault());
        
        
        canvas.addEventListener('mouseleave', () => this.onMouseUp());
        
        
        canvas.style.cursor = 'grab';
    }
    
    onMouseDown(event) {
        this.controls.isRotating = true;
        this.controls.previousMouseX = event.clientX;
        this.controls.previousMouseY = event.clientY;
        this.container.style.cursor = 'grabbing';
    }
    
    onMouseMove(event) {
        if (this.controls.isRotating && this.mannequin) {
            const deltaX = event.clientX - this.controls.previousMouseX;
            const deltaY = event.clientY - this.controls.previousMouseY;
            
            
            this.mannequin.rotation.y += deltaX * this.controls.rotationSpeed;
            
            
            this.mannequin.rotation.x += deltaY * this.controls.rotationSpeed * 0.5;
            
            
            this.mannequin.rotation.x = Math.max(-Math.PI/4, Math.min(Math.PI/4, this.mannequin.rotation.x));
            
            this.controls.previousMouseX = event.clientX;
            this.controls.previousMouseY = event.clientY;
        }
    }
    
    onMouseUp() {
        this.controls.isRotating = false;
        this.container.style.cursor = 'grab';
    }
    
    onWheel(event) {
        event.preventDefault();
        
        const delta = event.deltaY > 0 ? 1 : -1;
        this.controls.currentZoom += delta * this.controls.zoomSpeed;
        this.controls.currentZoom = Math.max(
            this.controls.minZoom, 
            Math.min(this.controls.maxZoom, this.controls.currentZoom)
        );
        
        this.camera.position.z = this.controls.currentZoom;
    }
    
    onTouchStart(event) {
        if (event.touches.length === 1) {
            
            this.controls.isRotating = true;
            this.controls.previousMouseX = event.touches[0].clientX;
            this.controls.previousMouseY = event.touches[0].clientY;
        } else if (event.touches.length === 2) {
            
            this.controls.isZooming = true;
            const touch1 = event.touches[0];
            const touch2 = event.touches[1];
            const distance = Math.sqrt(
                Math.pow(touch2.clientX - touch1.clientX, 2) + 
                Math.pow(touch2.clientY - touch1.clientY, 2)
            );
            this.controls.initialTouchDistance = distance;
            this.controls.initialZoom = this.controls.currentZoom;
        }
    }
    
    onTouchMove(event) {
        event.preventDefault();
        
        if (event.touches.length === 1 && this.controls.isRotating && this.mannequin) {
            
            const deltaX = event.touches[0].clientX - this.controls.previousMouseX;
            const deltaY = event.touches[0].clientY - this.controls.previousMouseY;
            
            this.mannequin.rotation.y += deltaX * this.controls.rotationSpeed;
            this.mannequin.rotation.x += deltaY * this.controls.rotationSpeed * 0.5;
            this.mannequin.rotation.x = Math.max(-Math.PI/4, Math.min(Math.PI/4, this.mannequin.rotation.x));
            
            this.controls.previousMouseX = event.touches[0].clientX;
            this.controls.previousMouseY = event.touches[0].clientY;
        } else if (event.touches.length === 2 && this.controls.isZooming) {
            
            const touch1 = event.touches[0];
            const touch2 = event.touches[1];
            const distance = Math.sqrt(
                Math.pow(touch2.clientX - touch1.clientX, 2) + 
                Math.pow(touch2.clientY - touch1.clientY, 2)
            );
            
            const scale = distance / this.controls.initialTouchDistance;
            this.controls.currentZoom = this.controls.initialZoom / scale;
            this.controls.currentZoom = Math.max(
                this.controls.minZoom, 
                Math.min(this.controls.maxZoom, this.controls.currentZoom)
            );
            
            this.camera.position.z = this.controls.currentZoom;
        }
    }
    
    onTouchEnd() {
        this.controls.isRotating = false;
        this.controls.isZooming = false;
    }
    
    handleResize() {
        window.addEventListener('resize', () => {
            if (!this.container) return;
            
            const width = this.container.clientWidth;
            const height = this.container.clientHeight;
            
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            
            this.renderer.setSize(width, height);
        });
    }
    
    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        
        
        if (!this.controls.isRotating && this.mannequin) {
            
            
        }
        
        this.renderer.render(this.scene, this.camera);
    }
    
    dispose() {
        
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        if (this.renderer) {
            this.renderer.dispose();
        }
        
        if (this.mannequin) {
            this.scene.remove(this.mannequin);
        }
        
        
        const canvas = this.renderer?.domElement;
        if (canvas) {
            canvas.removeEventListener('mousedown', this.onMouseDown);
            canvas.removeEventListener('mousemove', this.onMouseMove);
            canvas.removeEventListener('mouseup', this.onMouseUp);
            canvas.removeEventListener('wheel', this.onWheel);
            canvas.removeEventListener('touchstart', this.onTouchStart);
            canvas.removeEventListener('touchmove', this.onTouchMove);
            canvas.removeEventListener('touchend', this.onTouchEnd);
        }
    }
}


if (typeof module !== 'undefined' && module.exports) {
    module.exports = MannequinViewer;
}