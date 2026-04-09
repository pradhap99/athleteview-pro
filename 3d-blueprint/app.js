import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

// ============================================================
// CONSTANTS & CONFIG
// ============================================================
const TEAL = 0x0A6E75;
const TEAL_BRIGHT = 0x0FABB5;
const AMBER = 0xF59E0B;
const BLUE = 0x3B82F6;
const GREEN = 0x22C55E;
const RED = 0xEF4444;
const BG_COLOR = 0x0D0D15;

const CATEGORY_COLORS = {
  processing: '#22C55E',
  connectivity: '#3B82F6',
  biometrics: '#EF4444',
  power: '#F59E0B',
  mechanical: '#6B7280',
};

// Explode spacing per layer (mm offset when fully exploded)
const EXPLODE_OFFSETS = {
  adhesive: -30,
  bottomHousing: -18,
  battery: -6,
  pcb: 0,
  components: 8, // components ride on pcb + small offset
  topHousing: 22,
  lensWindow: 34,
};

// ============================================================
// COMPONENT DATA
// ============================================================
const COMPONENT_DATA = {
  adhesive: {
    name: '3M Medical Adhesive',
    part: '3M 4076 Series',
    category: 'mechanical',
    dims: '70 × 46 × 0.2mm',
    layer: 'Layer 1 — Bottom (skin contact)',
    specs: ['Medical-grade acrylic adhesive', 'Hypoallergenic, latex-free', '72-hour continuous wear rated'],
  },
  bottomHousing: {
    name: 'Silicone Housing (Bottom)',
    part: 'Custom LSR Molded',
    category: 'mechanical',
    dims: '72 × 48 × 0.5mm',
    layer: 'Layer 2 — Bottom enclosure',
    specs: ['Medical-grade LSR silicone', 'PPG sensor window cutout', 'Shore A 40 durometer'],
  },
  battery: {
    name: 'Enovix Si-Anode Battery',
    part: 'EN-1100-3D',
    category: 'power',
    dims: '28.9 × 17.3 × 2.0mm',
    layer: 'Layer 3 — Center-left of stack',
    specs: ['1,100 mAh capacity', 'Silicon-anode 3D cell architecture', '800+ cycle life, <1% swelling'],
  },
  pcb: {
    name: '8-Layer LCP Rigid-Flex PCB',
    part: 'Custom 8L LCP',
    category: 'mechanical',
    dims: '70 × 46 × 0.8mm',
    layer: 'Layer 4 — Main board',
    specs: ['8-layer LCP substrate', 'Rigid-flex with antenna extensions', 'Immersion gold (ENIG) finish'],
  },
  soc: {
    name: 'RV1106G3 SoC',
    part: 'RV1106G3',
    category: 'processing',
    dims: '12.3 × 12.3 × 1.5mm',
    layer: 'Layer 4 — PCB center',
    specs: ['ARM Cortex-A7 + RISC-V', '1.0 TOPS NPU (INT8)', 'Hardware ISP + H.265 encoder'],
  },
  camera: {
    name: 'Sony IMX415 Camera',
    part: 'IMX415-AAQR',
    category: 'processing',
    dims: '12 × 9.3 × 3mm (+lens)',
    layer: 'Layer 4 — PCB top-right',
    specs: ['8.29MP, 4K@60fps', '1/2.8" CMOS, 1.45μm pixel', 'HDR, PDAF capable'],
  },
  modem5g: {
    name: 'Quectel RG255C-GL (5G RedCap)',
    part: 'RG255C-GL',
    category: 'connectivity',
    dims: '29 × 32 × 2.4mm',
    layer: 'Layer 4 — PCB right half',
    specs: ['3GPP Rel-17 5G NR RedCap', 'DL 220 Mbps / UL 120 Mbps', 'GNSS: GPS+GLONASS+Galileo'],
  },
  wifi: {
    name: 'CYW55913 WiFi 6E + BLE 5.4',
    part: 'CYW55913',
    category: 'connectivity',
    dims: '3.57 × 5.32 × 0.8mm',
    layer: 'Layer 4 — PCB top-left',
    specs: ['Wi-Fi 6E tri-band (2.4/5/6 GHz)', 'Bluetooth 5.4 + LE Audio', '1×1 MIMO, 20 MHz channels'],
  },
  ble: {
    name: 'nRF54L15 BLE 6.0',
    part: 'nRF54L15',
    category: 'connectivity',
    dims: '2.4 × 2.2 × 0.5mm',
    layer: 'Layer 4 — Near CYW55913',
    specs: ['Bluetooth 6.0 w/ Channel Sounding', '128 MHz Cortex-M33', 'Ultra-low-power: 3.2 μA sleep'],
  },
  uwb: {
    name: 'Qorvo QM35825 UWB',
    part: 'QM35825',
    category: 'connectivity',
    dims: '4.08 × 3.38 × 0.8mm',
    layer: 'Layer 4 — PCB bottom-left',
    specs: ['IEEE 802.15.4z HRP UWB', '±5 cm ranging accuracy', 'FiRa 2.0 + CCC Digital Key'],
  },
  ppg: {
    name: 'MAX86178 PPG+ECG+BioZ',
    part: 'MAX86178',
    category: 'biometrics',
    dims: '2.77 × 2.57 × 0.8mm',
    layer: 'Layer 4 — PCB bottom-center',
    specs: ['Optical PPG (Green+Red+IR)', 'Single-lead ECG', 'Bio-impedance (BioZ) for hydration'],
  },
  imu: {
    name: 'ICM-45686 IMU',
    part: 'ICM-45686',
    category: 'biometrics',
    dims: '3 × 2.5 × 0.8mm',
    layer: 'Layer 4 — Near SoC',
    specs: ['6-axis (3-axis accel + 3-axis gyro)', '±32g / ±4000 dps range', '0.7 mA low-power mode'],
  },
  envSensors: {
    name: 'Environmental Sensors',
    part: 'SHT45 + BMP585 + AS6221',
    category: 'biometrics',
    dims: '~6 × 3 × 0.8mm cluster',
    layer: 'Layer 4 — PCB edge',
    specs: ['SHT45: ±1% RH, ±0.1°C', 'BMP585: barometric pressure', 'AS6221: ±0.09°C skin temp'],
  },
  mic: {
    name: 'IM73A135 MEMS Mic',
    part: 'IM73A135V01',
    category: 'biometrics',
    dims: '3 × 2 × 0.8mm',
    layer: 'Layer 4 — PCB edge',
    specs: ['71 dB SNR, IP57 rated', 'PDM digital output', 'Flat response 28Hz—20kHz'],
  },
  pmic: {
    name: 'RK809-2 PMIC',
    part: 'RK809-2',
    category: 'power',
    dims: '4 × 4 × 0.8mm',
    layer: 'Layer 4 — Near battery',
    specs: ['Multi-rail power management', '4× buck + 9× LDO regulators', 'I2C programmable sequencing'],
  },
  topHousing: {
    name: 'Silicone Housing (Top) — IP68',
    part: 'Custom LSR Molded',
    category: 'mechanical',
    dims: '72 × 48 × 0.5mm',
    layer: 'Layer 5 — Top enclosure',
    specs: ['IP68 water/dust sealed', 'Camera lens window cutout', 'AthleteView logo embossed'],
  },
  lensWindow: {
    name: 'Optical Window',
    part: 'Gorilla Glass DX',
    category: 'mechanical',
    dims: '5mm Ø × 0.3mm',
    layer: 'Layer 6 — Top surface',
    specs: ['Corning Gorilla Glass DX', 'AR coated, oleophobic', '98.5% light transmission'],
  },
};

// ============================================================
// SCENE SETUP
// ============================================================
const canvas = document.getElementById('three-canvas');
const scene = new THREE.Scene();
scene.background = new THREE.Color(BG_COLOR);

const camera = new THREE.PerspectiveCamera(40, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(90, 65, 90);

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  alpha: false,
});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.1;

// Post-processing
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));

const bloomPass = new UnrealBloomPass(
  new THREE.Vector2(window.innerWidth, window.innerHeight),
  0.3, // strength
  0.4, // radius
  0.85 // threshold
);
composer.addPass(bloomPass);
composer.addPass(new OutputPass());

// Controls
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 30;
controls.maxDistance = 250;
controls.target.set(0, 4, 0);
controls.update();

// ============================================================
// LIGHTING
// ============================================================
const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
scene.add(ambientLight);

const mainLight = new THREE.DirectionalLight(0xffffff, 1.2);
mainLight.position.set(40, 60, 30);
mainLight.castShadow = false;
scene.add(mainLight);

const fillLight = new THREE.DirectionalLight(0x8ecae6, 0.3);
fillLight.position.set(-30, 20, -20);
scene.add(fillLight);

const rimLight = new THREE.DirectionalLight(0x0FABB5, 0.2);
rimLight.position.set(0, -10, -40);
scene.add(rimLight);

// Environment map (simple gradient)
const pmremGenerator = new THREE.PMREMGenerator(renderer);
const envScene = new THREE.Scene();
const envGeo = new THREE.SphereGeometry(100, 32, 16);
const envMat = new THREE.MeshBasicMaterial({
  color: 0x111122,
  side: THREE.BackSide,
});
envScene.add(new THREE.Mesh(envGeo, envMat));
// Add a bright spot
const spotGeo = new THREE.SphereGeometry(15, 16, 8);
const spotMat = new THREE.MeshBasicMaterial({ color: 0x445566 });
const spotMesh = new THREE.Mesh(spotGeo, spotMat);
spotMesh.position.set(40, 60, 30);
envScene.add(spotMesh);
const envMap = pmremGenerator.fromScene(envScene, 0.04).texture;
scene.environment = envMap;
pmremGenerator.dispose();

// ============================================================
// GRID
// ============================================================
function createGrid() {
  const gridGroup = new THREE.Group();
  const gridMat = new THREE.LineBasicMaterial({ color: 0x1a1a2e, transparent: true, opacity: 0.4 });
  const size = 200;
  const step = 10;
  const points = [];
  
  for (let i = -size; i <= size; i += step) {
    points.push(new THREE.Vector3(i, -8, -size), new THREE.Vector3(i, -8, size));
    points.push(new THREE.Vector3(-size, -8, i), new THREE.Vector3(size, -8, i));
  }
  
  const geo = new THREE.BufferGeometry().setFromPoints(points);
  const grid = new THREE.LineSegments(geo, gridMat);
  gridGroup.add(grid);
  
  // Subtle glow ring around origin
  const ringGeo = new THREE.RingGeometry(50, 51, 64);
  const ringMat = new THREE.MeshBasicMaterial({
    color: TEAL,
    transparent: true,
    opacity: 0.06,
    side: THREE.DoubleSide,
  });
  const ring = new THREE.Mesh(ringGeo, ringMat);
  ring.rotation.x = -Math.PI / 2;
  ring.position.y = -7.9;
  gridGroup.add(ring);
  
  return gridGroup;
}
scene.add(createGrid());

// ============================================================
// HELPER: Rounded Box
// ============================================================
function createRoundedBox(w, h, d, radius, segments = 4) {
  const shape = new THREE.Shape();
  const hw = w / 2, hh = h / 2;
  const r = Math.min(radius, hw, hh);
  
  shape.moveTo(-hw + r, -hh);
  shape.lineTo(hw - r, -hh);
  shape.quadraticCurveTo(hw, -hh, hw, -hh + r);
  shape.lineTo(hw, hh - r);
  shape.quadraticCurveTo(hw, hh, hw - r, hh);
  shape.lineTo(-hw + r, hh);
  shape.quadraticCurveTo(-hw, hh, -hw, hh - r);
  shape.lineTo(-hw, -hh + r);
  shape.quadraticCurveTo(-hw, -hh, -hw + r, -hh);
  
  const extrudeSettings = {
    depth: d,
    bevelEnabled: false,
    steps: 1,
  };
  
  const geometry = new THREE.ExtrudeGeometry(shape, extrudeSettings);
  // Rotate so extrusion goes along Y axis
  geometry.rotateX(-Math.PI / 2);
  // Center vertically
  geometry.translate(0, d / 2, 0);
  
  return geometry;
}

// ============================================================
// BUILD COMPONENTS
// ============================================================
const allMeshes = {}; // name -> mesh
const interactiveMeshes = []; // for raycasting
const layerGroups = {}; // layerName -> Group
const originalPositions = {}; // name -> Vector3
const componentMaterials = {}; // name -> original material

// Helper to make a mesh interactive
function makeInteractive(mesh, dataKey) {
  mesh.userData.dataKey = dataKey;
  interactiveMeshes.push(mesh);
}

// Layer 1: Medical Adhesive
function buildAdhesive() {
  const group = new THREE.Group();
  const geo = createRoundedBox(70, 46, 0.2, 3);
  const mat = new THREE.MeshStandardMaterial({
    color: 0xF5F0E8,
    transparent: true,
    opacity: 0.6,
    roughness: 0.8,
    metalness: 0.0,
  });
  const mesh = new THREE.Mesh(geo, mat);
  componentMaterials['adhesive'] = mat;
  makeInteractive(mesh, 'adhesive');
  allMeshes['adhesive'] = mesh;
  group.add(mesh);
  group.position.y = 0;
  layerGroups['adhesive'] = group;
  originalPositions['adhesive'] = new THREE.Vector3(0, 0, 0);
  scene.add(group);
}

// Layer 2: Bottom Housing
function buildBottomHousing() {
  const group = new THREE.Group();
  const geo = createRoundedBox(72, 48, 0.5, 4);
  const mat = new THREE.MeshStandardMaterial({
    color: 0x2A2A35,
    roughness: 0.65,
    metalness: 0.1,
  });
  const mesh = new THREE.Mesh(geo, mat);
  componentMaterials['bottomHousing'] = mat;
  makeInteractive(mesh, 'bottomHousing');
  allMeshes['bottomHousing'] = mesh;
  
  // PPG sensor cutout (visual)
  const cutoutGeo = new THREE.BoxGeometry(6, 0.6, 5);
  const cutoutMat = new THREE.MeshStandardMaterial({
    color: 0x0D0D15,
    roughness: 0.9,
  });
  const cutout = new THREE.Mesh(cutoutGeo, cutoutMat);
  cutout.position.set(0, 0, 8);
  group.add(cutout);
  
  group.add(mesh);
  group.position.y = 0.2;
  layerGroups['bottomHousing'] = group;
  originalPositions['bottomHousing'] = new THREE.Vector3(0, 0.2, 0);
  scene.add(group);
}

// Layer 3: Battery
function buildBattery() {
  const group = new THREE.Group();
  const geo = createRoundedBox(28.9, 17.3, 2.0, 1.5);
  const mat = new THREE.MeshStandardMaterial({
    color: 0x1a2744,
    roughness: 0.3,
    metalness: 0.7,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(-14, 0, 0);
  componentMaterials['battery'] = mat;
  makeInteractive(mesh, 'battery');
  allMeshes['battery'] = mesh;
  
  // Silver terminal strip
  const termGeo = new THREE.BoxGeometry(28.9, 0.3, 2);
  const termMat = new THREE.MeshStandardMaterial({
    color: 0xAAAAAA,
    roughness: 0.2,
    metalness: 0.9,
  });
  const term = new THREE.Mesh(termGeo, termMat);
  term.position.set(-14, 1.15, -8.5);
  group.add(term);
  
  group.add(mesh);
  group.position.y = 0.7;
  layerGroups['battery'] = group;
  originalPositions['battery'] = new THREE.Vector3(0, 0.7, 0);
  scene.add(group);
}

// Layer 4: PCB
function buildPCB() {
  const group = new THREE.Group();
  
  // Main PCB body
  const pcbGeo = createRoundedBox(70, 46, 0.8, 2);
  const pcbMat = new THREE.MeshStandardMaterial({
    color: 0x1B5E20,
    roughness: 0.6,
    metalness: 0.15,
  });
  const pcbMesh = new THREE.Mesh(pcbGeo, pcbMat);
  componentMaterials['pcb'] = pcbMat;
  makeInteractive(pcbMesh, 'pcb');
  allMeshes['pcb'] = pcbMesh;
  group.add(pcbMesh);
  
  // PCB traces (golden lines on surface)
  const traceMat = new THREE.MeshStandardMaterial({
    color: 0xC8A84E,
    roughness: 0.3,
    metalness: 0.8,
    transparent: true,
    opacity: 0.4,
  });
  
  // Horizontal traces
  for (let i = -18; i <= 18; i += 3) {
    const traceGeo = new THREE.BoxGeometry(60 + Math.random() * 8, 0.05, 0.3);
    const trace = new THREE.Mesh(traceGeo, traceMat);
    trace.position.set(Math.random() * 4 - 2, 0.43, i);
    group.add(trace);
  }
  // Vertical traces
  for (let i = -28; i <= 28; i += 4) {
    const traceGeo = new THREE.BoxGeometry(0.3, 0.05, 36 + Math.random() * 8);
    const trace = new THREE.Mesh(traceGeo, traceMat);
    trace.position.set(i, 0.43, Math.random() * 4 - 2);
    group.add(trace);
  }
  
  // Flex extensions
  const flexMat = new THREE.MeshStandardMaterial({
    color: 0xB8860B,
    roughness: 0.5,
    metalness: 0.3,
    transparent: true,
    opacity: 0.7,
  });
  const flex1Geo = new THREE.BoxGeometry(8, 0.3, 20);
  const flex1 = new THREE.Mesh(flex1Geo, flexMat);
  flex1.position.set(39, 0.15, 0);
  group.add(flex1);
  
  const flex2Geo = new THREE.BoxGeometry(8, 0.3, 16);
  const flex2 = new THREE.Mesh(flex2Geo, flexMat);
  flex2.position.set(-39, 0.15, -5);
  group.add(flex2);
  
  // === PCB Components ===
  
  // a) SoC - RV1106G3
  const socGeo = new THREE.BoxGeometry(12.3, 1.5, 12.3);
  const socMat = new THREE.MeshStandardMaterial({
    color: 0x1a1a1a,
    roughness: 0.7,
    metalness: 0.2,
  });
  const socMesh = new THREE.Mesh(socGeo, socMat);
  socMesh.position.set(-2, 1.15, -2);
  componentMaterials['soc'] = socMat;
  makeInteractive(socMesh, 'soc');
  allMeshes['soc'] = socMesh;
  group.add(socMesh);
  
  // SoC gold pads
  const padMat = new THREE.MeshStandardMaterial({ color: 0xD4A843, roughness: 0.2, metalness: 0.9 });
  for (let side = 0; side < 4; side++) {
    for (let i = 0; i < 8; i++) {
      const padGeo = new THREE.BoxGeometry(side < 2 ? 0.3 : 1.0, 0.3, side < 2 ? 1.0 : 0.3);
      const pad = new THREE.Mesh(padGeo, padMat);
      const offset = -4.2 + i * 1.2;
      if (side === 0) pad.position.set(-2 - 6.3, 0.85, -2 + offset);
      else if (side === 1) pad.position.set(-2 + 6.3, 0.85, -2 + offset);
      else if (side === 2) pad.position.set(-2 + offset, 0.85, -2 - 6.3);
      else pad.position.set(-2 + offset, 0.85, -2 + 6.3);
      group.add(pad);
    }
  }
  
  // b) Camera IMX415
  const camBaseGeo = new THREE.BoxGeometry(12, 1, 9.3);
  const camBaseMat = new THREE.MeshStandardMaterial({ color: 0x1B4332, roughness: 0.6, metalness: 0.2 });
  const camBase = new THREE.Mesh(camBaseGeo, camBaseMat);
  camBase.position.set(22, 0.9, -14);
  group.add(camBase);
  
  const lensGeo = new THREE.CylinderGeometry(2, 2, 2, 24);
  const lensMat = new THREE.MeshStandardMaterial({ color: 0x888899, roughness: 0.1, metalness: 0.9 });
  const lens = new THREE.Mesh(lensGeo, lensMat);
  lens.position.set(22, 2.4, -14);
  group.add(lens);
  
  // Lens glass
  const lensGlassGeo = new THREE.CylinderGeometry(1.6, 1.6, 0.2, 24);
  const lensGlassMat = new THREE.MeshStandardMaterial({
    color: 0x112244,
    roughness: 0.0,
    metalness: 0.3,
    transparent: true,
    opacity: 0.5,
  });
  const lensGlass = new THREE.Mesh(lensGlassGeo, lensGlassMat);
  lensGlass.position.set(22, 3.45, -14);
  group.add(lensGlass);
  
  // Camera group for interaction
  const camGroup = new THREE.Group();
  const camHitbox = new THREE.Mesh(
    new THREE.BoxGeometry(12, 3, 9.3),
    new THREE.MeshBasicMaterial({ visible: false })
  );
  camHitbox.position.set(22, 1.9, -14);
  componentMaterials['camera'] = camBaseMat;
  makeInteractive(camHitbox, 'camera');
  allMeshes['camera'] = camHitbox;
  group.add(camHitbox);
  
  // c) 5G Modem RG255C-GL
  const modemGeo = new THREE.BoxGeometry(29, 2.4, 32);
  const modemMat = new THREE.MeshStandardMaterial({
    color: 0x999999,
    roughness: 0.25,
    metalness: 0.8,
  });
  const modemMesh = new THREE.Mesh(modemGeo, modemMat);
  modemMesh.position.set(18, 1.6, 6);
  componentMaterials['modem5g'] = modemMat;
  makeInteractive(modemMesh, 'modem5g');
  allMeshes['modem5g'] = modemMesh;
  group.add(modemMesh);
  
  // RF shield edges
  const shieldMat = new THREE.MeshStandardMaterial({ color: 0xBBBBBB, roughness: 0.15, metalness: 0.95 });
  const shieldEdges = [
    [29, 0.3, 0.4, 18, 2.85, -9.8],
    [29, 0.3, 0.4, 18, 2.85, 21.8],
    [0.4, 0.3, 32, 3.3, 2.85, 6],
    [0.4, 0.3, 32, 32.7, 2.85, 6],
  ];
  shieldEdges.forEach(([w, h, d, x, y, z]) => {
    const geo = new THREE.BoxGeometry(w, h, d);
    const m = new THREE.Mesh(geo, shieldMat);
    m.position.set(x, y, z);
    group.add(m);
  });
  
  // d) WiFi CYW55913
  const wifiGeo = new THREE.BoxGeometry(3.57, 0.8, 5.32);
  const wifiMat = new THREE.MeshStandardMaterial({ color: 0x1a1a22, roughness: 0.6, metalness: 0.3 });
  const wifiMesh = new THREE.Mesh(wifiGeo, wifiMat);
  wifiMesh.position.set(-18, 0.8, -12);
  componentMaterials['wifi'] = wifiMat;
  makeInteractive(wifiMesh, 'wifi');
  allMeshes['wifi'] = wifiMesh;
  group.add(wifiMesh);
  
  // Gold bumps on WiFi
  for (let r = 0; r < 2; r++) {
    for (let c = 0; c < 3; c++) {
      const bumpGeo = new THREE.SphereGeometry(0.2, 8, 6);
      const bump = new THREE.Mesh(bumpGeo, padMat);
      bump.position.set(-18 - 0.8 + c * 0.8, 1.25, -12 - 1.2 + r * 2.4);
      group.add(bump);
    }
  }
  
  // e) BLE nRF54L15
  const bleGeo = new THREE.BoxGeometry(2.4, 0.5, 2.2);
  const bleMat = new THREE.MeshStandardMaterial({ color: 0x4488CC, roughness: 0.5, metalness: 0.2 });
  const bleMesh = new THREE.Mesh(bleGeo, bleMat);
  bleMesh.position.set(-14, 0.65, -14);
  componentMaterials['ble'] = bleMat;
  makeInteractive(bleMesh, 'ble');
  allMeshes['ble'] = bleMesh;
  group.add(bleMesh);
  
  // f) UWB QM35825
  const uwbGeo = new THREE.BoxGeometry(4.08, 0.8, 3.38);
  const uwbMat = new THREE.MeshStandardMaterial({ color: 0x1B4332, roughness: 0.6, metalness: 0.2 });
  const uwbMesh = new THREE.Mesh(uwbGeo, uwbMat);
  uwbMesh.position.set(-22, 0.8, 14);
  componentMaterials['uwb'] = uwbMat;
  makeInteractive(uwbMesh, 'uwb');
  allMeshes['uwb'] = uwbMesh;
  group.add(uwbMesh);
  
  // UWB gold pads
  for (let i = 0; i < 4; i++) {
    const padGeo2 = new THREE.BoxGeometry(0.6, 0.1, 0.3);
    const pad2 = new THREE.Mesh(padGeo2, padMat);
    pad2.position.set(-22 - 1.5 + i * 1, 0.45, 14 + 1.8);
    group.add(pad2);
  }
  
  // g) PPG MAX86178
  const ppgGeo = new THREE.BoxGeometry(2.77, 0.8, 2.57);
  const ppgMat = new THREE.MeshStandardMaterial({ color: 0x222222, roughness: 0.5, metalness: 0.3 });
  const ppgMesh = new THREE.Mesh(ppgGeo, ppgMat);
  ppgMesh.position.set(0, 0.8, 16);
  componentMaterials['ppg'] = ppgMat;
  makeInteractive(ppgMesh, 'ppg');
  allMeshes['ppg'] = ppgMesh;
  group.add(ppgMesh);
  
  // Red LED dot
  const ledGeo = new THREE.SphereGeometry(0.3, 12, 8);
  const ledRedMat = new THREE.MeshStandardMaterial({ color: 0xFF2222, emissive: 0xFF0000, emissiveIntensity: 0.5, roughness: 0.3 });
  const ledRed = new THREE.Mesh(ledGeo, ledRedMat);
  ledRed.position.set(-0.5, 1.25, 16);
  group.add(ledRed);
  
  // IR dot
  const ledIRMat = new THREE.MeshStandardMaterial({ color: 0x330011, emissive: 0x440022, emissiveIntensity: 0.3, roughness: 0.3 });
  const ledIR = new THREE.Mesh(ledGeo, ledIRMat);
  ledIR.position.set(0.5, 1.25, 16);
  group.add(ledIR);
  
  // h) IMU ICM-45686
  const imuGeo = new THREE.BoxGeometry(3, 0.8, 2.5);
  const imuMat = new THREE.MeshStandardMaterial({ color: 0x555566, roughness: 0.5, metalness: 0.3 });
  const imuMesh = new THREE.Mesh(imuGeo, imuMat);
  imuMesh.position.set(-6, 0.8, 4);
  componentMaterials['imu'] = imuMat;
  makeInteractive(imuMesh, 'imu');
  allMeshes['imu'] = imuMesh;
  group.add(imuMesh);
  
  // i) Environmental sensors cluster
  const envGroup = new THREE.Group();
  const envMat = new THREE.MeshStandardMaterial({ color: 0xDDDDDD, roughness: 0.6, metalness: 0.1 });
  const envChips = [
    [2, 0.6, 2, -28, 0.7, -6],
    [1.8, 0.5, 1.8, -28, 0.65, -3],
    [1.5, 0.4, 1.5, -28, 0.6, -0.5],
  ];
  envChips.forEach(([w, h, d, x, y, z]) => {
    const geo = new THREE.BoxGeometry(w, h, d);
    const m = new THREE.Mesh(geo, envMat);
    m.position.set(x, y, z);
    envGroup.add(m);
  });
  componentMaterials['envSensors'] = envMat;
  const envHitbox = new THREE.Mesh(
    new THREE.BoxGeometry(4, 1, 8),
    new THREE.MeshBasicMaterial({ visible: false })
  );
  envHitbox.position.set(-28, 0.7, -3);
  makeInteractive(envHitbox, 'envSensors');
  allMeshes['envSensors'] = envHitbox;
  envGroup.add(envHitbox);
  group.add(envGroup);
  
  // j) Mic IM73A135
  const micGeo = new THREE.BoxGeometry(3, 0.8, 2);
  const micMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.7, metalness: 0.2 });
  const micMesh = new THREE.Mesh(micGeo, micMat);
  micMesh.position.set(-28, 0.8, 8);
  componentMaterials['mic'] = micMat;
  makeInteractive(micMesh, 'mic');
  allMeshes['mic'] = micMesh;
  group.add(micMesh);
  
  // Mic port hole
  const portGeo = new THREE.CylinderGeometry(0.3, 0.3, 0.2, 12);
  const portMat = new THREE.MeshStandardMaterial({ color: 0x050505, roughness: 0.9 });
  const port = new THREE.Mesh(portGeo, portMat);
  port.position.set(-28, 1.25, 8);
  group.add(port);
  
  // k) PMIC RK809-2
  const pmicGeo = new THREE.BoxGeometry(4, 0.8, 4);
  const pmicMat = new THREE.MeshStandardMaterial({ color: 0x1a1a22, roughness: 0.6, metalness: 0.3 });
  const pmicMesh = new THREE.Mesh(pmicGeo, pmicMat);
  pmicMesh.position.set(-20, 0.8, 4);
  componentMaterials['pmic'] = pmicMat;
  makeInteractive(pmicMesh, 'pmic');
  allMeshes['pmic'] = pmicMesh;
  group.add(pmicMesh);
  
  group.position.y = 0.7;
  layerGroups['pcb'] = group;
  originalPositions['pcb'] = new THREE.Vector3(0, 0.7, 0);
  scene.add(group);
}

// Layer 5: Top Housing
function buildTopHousing() {
  const group = new THREE.Group();
  const geo = createRoundedBox(72, 48, 0.5, 4);
  const mat = new THREE.MeshStandardMaterial({
    color: 0x2A2A35,
    roughness: 0.6,
    metalness: 0.15,
  });
  const mesh = new THREE.Mesh(geo, mat);
  componentMaterials['topHousing'] = mat;
  makeInteractive(mesh, 'topHousing');
  allMeshes['topHousing'] = mesh;
  group.add(mesh);
  
  // Camera window cutout
  const windowGeo = new THREE.CylinderGeometry(3, 3, 0.6, 24);
  const windowMat = new THREE.MeshStandardMaterial({ color: 0x0D0D15, roughness: 0.9 });
  const windowMesh = new THREE.Mesh(windowGeo, windowMat);
  windowMesh.position.set(22, 0, -14);
  group.add(windowMesh);
  
  // Logo text (embossed effect)
  const logoMat = new THREE.MeshStandardMaterial({
    color: 0x3A3A48,
    roughness: 0.4,
    metalness: 0.3,
  });
  const logoGeo = new THREE.BoxGeometry(22, 0.1, 3);
  const logo = new THREE.Mesh(logoGeo, logoMat);
  logo.position.set(-5, 0.3, 4);
  group.add(logo);
  
  // Small "AV" mark
  const markGeo = new THREE.BoxGeometry(4, 0.12, 2);
  const mark = new THREE.Mesh(markGeo, logoMat);
  mark.position.set(-5, 0.32, 8);
  group.add(mark);
  
  group.position.y = 3.8;
  layerGroups['topHousing'] = group;
  originalPositions['topHousing'] = new THREE.Vector3(0, 3.8, 0);
  scene.add(group);
}

// Layer 6: Lens Window
function buildLensWindow() {
  const group = new THREE.Group();
  const geo = new THREE.CylinderGeometry(2.5, 2.5, 0.3, 32);
  const mat = new THREE.MeshStandardMaterial({
    color: 0x334466,
    roughness: 0.0,
    metalness: 0.2,
    transparent: true,
    opacity: 0.4,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(22, 0, -14);
  componentMaterials['lensWindow'] = mat;
  makeInteractive(mesh, 'lensWindow');
  allMeshes['lensWindow'] = mesh;
  group.add(mesh);
  
  group.position.y = 4.3;
  layerGroups['lensWindow'] = group;
  originalPositions['lensWindow'] = new THREE.Vector3(0, 4.3, 0);
  scene.add(group);
}

// Build all
buildAdhesive();
buildBottomHousing();
buildBattery();
buildPCB();
buildTopHousing();
buildLensWindow();

// ============================================================
// RAYCASTING & INTERACTION
// ============================================================
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
const tooltip = document.getElementById('tooltip');
const tooltipName = document.getElementById('tooltip-name');
const tooltipSpec = document.getElementById('tooltip-spec');

let hoveredKey = null;
let selectedKey = null;

// Glow material for hover
function setGlow(dataKey, on) {
  const mat = componentMaterials[dataKey];
  if (!mat) return;
  if (on) {
    mat._origEmissive = mat.emissive.getHex();
    mat._origEmissiveIntensity = mat.emissiveIntensity;
    mat.emissive.setHex(TEAL_BRIGHT);
    mat.emissiveIntensity = 0.35;
  } else {
    if (mat._origEmissive !== undefined) {
      mat.emissive.setHex(mat._origEmissive);
      mat.emissiveIntensity = mat._origEmissiveIntensity || 0;
    }
  }
}

function onPointerMove(e) {
  mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
  
  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObjects(interactiveMeshes, false);
  
  if (intersects.length > 0) {
    const key = intersects[0].object.userData.dataKey;
    if (key !== hoveredKey) {
      if (hoveredKey && hoveredKey !== selectedKey) setGlow(hoveredKey, false);
      hoveredKey = key;
      if (key !== selectedKey) setGlow(key, true);
      canvas.style.cursor = 'pointer';
    }
    // Tooltip
    const data = COMPONENT_DATA[key];
    tooltipName.textContent = data.name;
    tooltipSpec.textContent = data.dims;
    tooltip.classList.remove('hidden');
    tooltip.style.left = (e.clientX + 16) + 'px';
    tooltip.style.top = (e.clientY - 10) + 'px';
  } else {
    if (hoveredKey && hoveredKey !== selectedKey) setGlow(hoveredKey, false);
    hoveredKey = null;
    canvas.style.cursor = 'grab';
    tooltip.classList.add('hidden');
  }
}

function onPointerDown(e) {
  // Quick raycast to check if we clicked a component
  mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObjects(interactiveMeshes, false);
  
  if (intersects.length > 0) {
    const key = intersects[0].object.userData.dataKey;
    selectComponent(key);
  }
}

function selectComponent(key) {
  // Deselect previous
  if (selectedKey) setGlow(selectedKey, false);
  selectedKey = key;
  setGlow(key, true);
  showInfoPanel(key);
}

function showInfoPanel(key) {
  const data = COMPONENT_DATA[key];
  if (!data) return;
  
  const panel = document.getElementById('info-panel');
  document.getElementById('info-name').textContent = data.name;
  document.getElementById('info-part').textContent = data.part;
  document.getElementById('info-dimensions').textContent = data.dims;
  document.getElementById('info-layer').textContent = data.layer;
  
  const catDot = document.getElementById('info-category-dot');
  catDot.style.background = CATEGORY_COLORS[data.category] || '#6B7280';
  document.getElementById('info-category-name').textContent = data.category;
  
  const specsList = document.getElementById('info-specs');
  specsList.innerHTML = '';
  data.specs.forEach(s => {
    const li = document.createElement('li');
    li.textContent = s;
    specsList.appendChild(li);
  });
  
  panel.classList.remove('hidden');
  panel.classList.add('visible');
}

document.getElementById('info-close').addEventListener('click', () => {
  const panel = document.getElementById('info-panel');
  panel.classList.remove('visible');
  panel.classList.add('hidden');
  if (selectedKey) {
    setGlow(selectedKey, false);
    selectedKey = null;
  }
});

canvas.addEventListener('pointermove', onPointerMove);
canvas.addEventListener('pointerdown', onPointerDown);

// ============================================================
// EXPLODE ANIMATION
// ============================================================
let explodeProgress = 0; // 0 = assembled, 1 = fully exploded
let targetExplode = 0;
let isExploded = false;

const explodeSlider = document.getElementById('explode-slider');
const sliderVal = document.getElementById('slider-val');
const explodeBtn = document.getElementById('explode-btn');

function updateExplode(progress) {
  explodeProgress = progress;
  
  // Layer positions
  const layers = [
    { key: 'adhesive', offset: -30 },
    { key: 'bottomHousing', offset: -18 },
    { key: 'battery', offset: -8 },
    { key: 'pcb', offset: 0 },
    { key: 'topHousing', offset: 20 },
    { key: 'lensWindow', offset: 34 },
  ];
  
  layers.forEach(({ key, offset }) => {
    const group = layerGroups[key];
    const orig = originalPositions[key];
    if (group && orig) {
      group.position.y = orig.y + offset * progress;
    }
  });
}

explodeSlider.addEventListener('input', (e) => {
  const val = parseInt(e.target.value);
  sliderVal.textContent = val;
  targetExplode = val / 100;
  isExploded = val > 50;
  updateExplodeBtnState();
});

explodeBtn.addEventListener('click', () => {
  isExploded = !isExploded;
  targetExplode = isExploded ? 1 : 0;
  updateExplodeBtnState();
});

function updateExplodeBtnState() {
  const btn = explodeBtn;
  if (isExploded) {
    btn.classList.add('active');
    btn.querySelector('span').textContent = 'Assemble';
  } else {
    btn.classList.remove('active');
    btn.querySelector('span').textContent = 'Explode';
  }
}

document.getElementById('reset-btn').addEventListener('click', () => {
  targetExplode = 0;
  isExploded = false;
  updateExplodeBtnState();
  animateCamera(90, 65, 90, 0, 4, 0);
  
  // Reset camera preset buttons
  presetButtons.forEach(b => b.classList.remove('active'));
  document.querySelector('[data-view="isometric"]').classList.add('active');
  
  // Close info panel
  const panel = document.getElementById('info-panel');
  panel.classList.remove('visible');
  panel.classList.add('hidden');
  if (selectedKey) {
    setGlow(selectedKey, false);
    selectedKey = null;
  }
});

// ============================================================
// CAMERA PRESETS
// ============================================================
const presetButtons = document.querySelectorAll('.preset-btn');

const cameraPresets = {
  isometric: { pos: [90, 65, 90], target: [0, 4, 0] },
  top: { pos: [0, 120, 0.1], target: [0, 4, 0] },
  side: { pos: [130, 15, 0], target: [0, 4, 0] },
  bottom: { pos: [0, -100, 0.1], target: [0, 4, 0] },
};

presetButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    const view = btn.dataset.view;
    const preset = cameraPresets[view];
    if (preset) {
      animateCamera(...preset.pos, ...preset.target);
      presetButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    }
  });
});

let cameraAnimating = false;
let cameraFrom = { pos: new THREE.Vector3(), target: new THREE.Vector3() };
let cameraTo = { pos: new THREE.Vector3(), target: new THREE.Vector3() };
let cameraAnimT = 0;

function animateCamera(px, py, pz, tx, ty, tz) {
  cameraFrom.pos.copy(camera.position);
  cameraFrom.target.copy(controls.target);
  cameraTo.pos.set(px, py, pz);
  cameraTo.target.set(tx, ty, tz);
  cameraAnimT = 0;
  cameraAnimating = true;
}

function easeInOutCubic(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

// ============================================================
// ANIMATION LOOP
// ============================================================
function animate() {
  requestAnimationFrame(animate);
  
  // Smooth explode
  if (Math.abs(explodeProgress - targetExplode) > 0.001) {
    explodeProgress += (targetExplode - explodeProgress) * 0.08;
    updateExplode(explodeProgress);
    // Update slider
    const sliderValue = Math.round(explodeProgress * 100);
    explodeSlider.value = sliderValue;
    sliderVal.textContent = sliderValue;
  }
  
  // Camera animation
  if (cameraAnimating) {
    cameraAnimT += 0.035;
    if (cameraAnimT >= 1) {
      cameraAnimT = 1;
      cameraAnimating = false;
    }
    const t = easeInOutCubic(cameraAnimT);
    camera.position.lerpVectors(cameraFrom.pos, cameraTo.pos, t);
    controls.target.lerpVectors(cameraFrom.target, cameraTo.target, t);
  }
  
  controls.update();
  composer.render();
}

animate();

// ============================================================
// RESIZE
// ============================================================
window.addEventListener('resize', () => {
  const w = window.innerWidth;
  const h = window.innerHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
  composer.setSize(w, h);
});

// ============================================================
// LOADING
// ============================================================
setTimeout(() => {
  document.getElementById('loading').classList.add('fade-out');
  setTimeout(() => {
    document.getElementById('loading').style.display = 'none';
  }, 600);
}, 800);
