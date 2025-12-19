/**
 * STAC-CAPS Three.js 3D Scene
 * Real-time visualization of tracked objects and rail corridor
 */

// Scene globals
let scene, camera, renderer, controls;
let trainMesh, railsMesh;
let objectMeshes = {};

// Initialize on load
document.addEventListener('DOMContentLoaded', initThreeScene);

function initThreeScene() {
    const container = document.getElementById('three-container');
    if (!container) return;

    // Scene setup
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0f);
    scene.fog = new THREE.Fog(0x0a0a0f, 50, 200);

    // Camera
    const aspect = container.clientWidth / container.clientHeight;
    camera = new THREE.PerspectiveCamera(60, aspect, 0.1, 1000);
    camera.position.set(0, 30, 50);
    camera.lookAt(0, 0, 0);

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // Lights
    const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 50, 30);
    directionalLight.castShadow = true;
    scene.add(directionalLight);

    // Grid helper
    const gridHelper = new THREE.GridHelper(100, 50, 0x2a2a3a, 0x1a1a24);
    scene.add(gridHelper);

    // Rails
    createRails();

    // Train (camera position indicator)
    createTrain();

    // Handle resize
    window.addEventListener('resize', onWindowResize);

    // Reset camera button
    document.getElementById('reset-camera-btn')?.addEventListener('click', resetCamera);

    // Animation loop
    animate();
}

function createRails() {
    const railGeometry = new THREE.BoxGeometry(1.435, 0.1, 100);
    const railMaterial = new THREE.MeshStandardMaterial({
        color: 0x888888,
        metalness: 0.8,
        roughness: 0.3
    });

    // Left rail
    const leftRail = new THREE.Mesh(
        new THREE.BoxGeometry(0.1, 0.15, 100),
        railMaterial
    );
    leftRail.position.set(-0.7175, 0.075, 0);
    scene.add(leftRail);

    // Right rail
    const rightRail = new THREE.Mesh(
        new THREE.BoxGeometry(0.1, 0.15, 100),
        railMaterial
    );
    rightRail.position.set(0.7175, 0.075, 0);
    scene.add(rightRail);

    // Sleepers
    const sleeperMaterial = new THREE.MeshStandardMaterial({ color: 0x4a3728 });
    for (let z = -50; z <= 50; z += 2) {
        const sleeper = new THREE.Mesh(
            new THREE.BoxGeometry(2.5, 0.1, 0.3),
            sleeperMaterial
        );
        sleeper.position.set(0, 0.05, z);
        scene.add(sleeper);
    }

    // Ground plane
    const groundGeometry = new THREE.PlaneGeometry(20, 100);
    const groundMaterial = new THREE.MeshStandardMaterial({
        color: 0x1a1a24,
        side: THREE.DoubleSide
    });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.01;
    ground.receiveShadow = true;
    scene.add(ground);
}

function createTrain() {
    // Simple train representation at origin
    const trainGeometry = new THREE.BoxGeometry(2, 3, 8);
    const trainMaterial = new THREE.MeshStandardMaterial({
        color: 0x3b82f6,
        metalness: 0.5,
        roughness: 0.5
    });
    trainMesh = new THREE.Mesh(trainGeometry, trainMaterial);
    trainMesh.position.set(0, 1.5, -40);
    trainMesh.castShadow = true;
    scene.add(trainMesh);

    // Direction indicator
    const arrowHelper = new THREE.ArrowHelper(
        new THREE.Vector3(0, 0, 1),
        new THREE.Vector3(0, 3, -40),
        5,
        0x22c55e
    );
    scene.add(arrowHelper);
}

function createObjectMesh(id, category) {
    let geometry, material;

    switch (category) {
        case 'PERSON':
            // Cylinder for person
            geometry = new THREE.CylinderGeometry(0.3, 0.3, 1.8, 8);
            material = new THREE.MeshStandardMaterial({
                color: 0xef4444,
                emissive: 0x440000,
                emissiveIntensity: 0.3
            });
            break;
        case 'KNOWN':
            // Box for known object
            geometry = new THREE.BoxGeometry(1, 1, 1);
            material = new THREE.MeshStandardMaterial({
                color: 0x22c55e,
                emissive: 0x004400,
                emissiveIntensity: 0.3
            });
            break;
        default:
            // Sphere for unknown
            geometry = new THREE.SphereGeometry(0.5, 16, 16);
            material = new THREE.MeshStandardMaterial({
                color: 0xf97316,
                emissive: 0x441100,
                emissiveIntensity: 0.3
            });
    }

    const mesh = new THREE.Mesh(geometry, material);
    mesh.castShadow = true;
    scene.add(mesh);
    objectMeshes[id] = mesh;

    // Add ID label
    const labelSprite = createLabel(`ID: ${id}`);
    mesh.add(labelSprite);
    labelSprite.position.y = 2;

    return mesh;
}

function createLabel(text) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 128;
    canvas.height = 32;

    context.fillStyle = 'rgba(0, 0, 0, 0.7)';
    context.fillRect(0, 0, canvas.width, canvas.height);

    context.font = '16px Arial';
    context.fillStyle = 'white';
    context.textAlign = 'center';
    context.fillText(text, canvas.width / 2, 22);

    const texture = new THREE.CanvasTexture(canvas);
    const spriteMaterial = new THREE.SpriteMaterial({ map: texture });
    const sprite = new THREE.Sprite(spriteMaterial);
    sprite.scale.set(2, 0.5, 1);

    return sprite;
}

// Called from app.js when new frame data arrives
window.updateThreeScene = function (objects3D) {
    if (!scene) return;

    const currentIds = new Set();

    // Update or create meshes
    objects3D.forEach(obj => {
        const id = obj.track_id;
        currentIds.add(id);

        let mesh = objectMeshes[id];
        if (!mesh) {
            mesh = createObjectMesh(id, obj.category || 'UNKNOWN');
        }

        // Update position
        const [x, y, z] = obj.position || [0, 0, 10];
        mesh.position.set(x, y > 0 ? y : 1, z);

        // Pulse effect for close objects
        if (z < 20) {
            const scale = 1 + Math.sin(Date.now() / 100) * 0.1;
            mesh.scale.set(scale, scale, scale);
        } else {
            mesh.scale.set(1, 1, 1);
        }
    });

    // Remove old meshes
    Object.keys(objectMeshes).forEach(id => {
        if (!currentIds.has(parseInt(id))) {
            scene.remove(objectMeshes[id]);
            delete objectMeshes[id];
        }
    });
};

function onWindowResize() {
    const container = document.getElementById('three-container');
    if (!container) return;

    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

function resetCamera() {
    camera.position.set(0, 30, 50);
    camera.lookAt(0, 0, 0);
}

function animate() {
    requestAnimationFrame(animate);

    // Slight camera orbit for dynamic feel
    // camera.position.x = Math.sin(Date.now() * 0.0001) * 10;

    renderer.render(scene, camera);
}
