/**
 * Star-map route: fetches places from the live backend and renders them as
 * glowing points in a Three.js scene. This module contains no simulation
 * logic — only fetching and rendering.
 */
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { ApiError, type Place, getPlaces } from "./api";

/** Wiki coordinates are divided by this to fit the scene. */
const COORD_SCALE = 10;

/** Accent colors per place type (sci-fi HUD palette). */
const TYPE_COLORS: Record<Place["meta"]["type"], number> = {
  region: 0x3b82f6,
  system: 0x22d3ee,
  "colony-site": 0xa3e635,
  station: 0xf8fafc,
  anomaly: 0xef4444,
};

const TYPE_FALLBACK_COLOR = 0x94a3b8;

function typeColor(type: Place["meta"]["type"]): THREE.Color {
  return new THREE.Color(TYPE_COLORS[type] ?? TYPE_FALLBACK_COLOR);
}

/** Soft radial glow sprite, generated procedurally on a canvas. */
function makeGlowTexture(): THREE.Texture {
  const size = 128;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    throw new Error("Canvas 2D context unavailable.");
  }
  const gradient = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  gradient.addColorStop(0, "rgba(255,255,255,1)");
  gradient.addColorStop(0.25, "rgba(255,255,255,0.85)");
  gradient.addColorStop(0.6, "rgba(255,255,255,0.18)");
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, size);
  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  return texture;
}

/** Procedural background starfield — decoration only, not game data. */
function makeStarfield(count: number): THREE.Points {
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const color = new THREE.Color();
  for (let i = 0; i < count; i += 1) {
    // Points on a distant sphere.
    const radius = 400 + Math.random() * 200;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
    positions[i * 3 + 1] = radius * Math.cos(phi);
    positions[i * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta);
    const shade = 0.25 + Math.random() * 0.5;
    color.setHSL(0.6, 0.3, shade * 0.5);
    colors[i * 3] = color.r;
    colors[i * 3 + 1] = color.g;
    colors[i * 3 + 2] = color.b;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  const material = new THREE.PointsMaterial({
    size: 1.4,
    sizeAttenuation: false,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
    depthWrite: false,
  });
  return new THREE.Points(geometry, material);
}

/** Faint 3D grid for spatial orientation. */
function makeGrid(): THREE.Group {
  const group = new THREE.Group();
  const grid = new THREE.GridHelper(240, 24, 0x1e293b, 0x141922);
  const material = grid.material as THREE.Material;
  material.transparent = true;
  material.opacity = 0.55;
  group.add(grid);
  return group;
}

function placePosition(place: Place): THREE.Vector3 {
  const [x, y, z] = place.meta.coordinates;
  return new THREE.Vector3(x / COORD_SCALE, y / COORD_SCALE, z / COORD_SCALE);
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/**
 * Mount the star-map view into `container`.
 * Returns an unmount function that disposes the Three.js scene.
 */
export function mountMapView(container: HTMLElement): () => void {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  container.classList.add("hud-view");
  container.innerHTML = "";

  const stage = document.createElement("div");
  stage.className = "map-stage";
  container.appendChild(stage);

  const infoPanel = document.createElement("aside");
  infoPanel.className = "hud-panel map-info hidden";
  infoPanel.setAttribute("aria-live", "polite");
  stage.appendChild(infoPanel);

  const statusOverlay = document.createElement("div");
  statusOverlay.className = "map-status";
  statusOverlay.innerHTML =
    '<div class="hud-panel">' +
    '<div class="status-title">Linking to backend</div>' +
    '<div class="status-body">Fetching star-map data from the API…</div>' +
    "</div>";
  stage.appendChild(statusOverlay);

  // --- Three.js setup ---
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  stage.prepend(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0b0b10);

  const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 2000);
  camera.position.set(0, 60, 140);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = !reducedMotion;
  controls.dampingFactor = 0.08;
  controls.minDistance = 10;
  controls.maxDistance = 700;
  controls.autoRotate = !reducedMotion;
  controls.autoRotateSpeed = 0.5;

  scene.add(makeStarfield(2000));
  scene.add(makeGrid());

  // Selection highlight ring (billboarded to face the camera).
  const ring = new THREE.Mesh(
    new THREE.RingGeometry(2.2, 2.6, 48),
    new THREE.MeshBasicMaterial({
      color: 0x3b82f6,
      transparent: true,
      opacity: 0.9,
      side: THREE.DoubleSide,
      depthWrite: false,
    }),
  );
  ring.visible = false;
  scene.add(ring);

  const glowTexture = makeGlowTexture();

  let places: Place[] = [];
  let points: THREE.Points | null = null;
  let hovered: number | null = null;
  let selected: number | null = null;
  let disposed = false;
  let animationId = 0;

  function setStatus(title: string, bodyHtml: string): void {
    statusOverlay.innerHTML = `<div class="hud-panel"><div class="status-title">${escapeHtml(title)}</div><div class="status-body">${bodyHtml}</div><button type="button" class="retry-button">Retry link</button></div>`;
    const retry = statusOverlay.querySelector<HTMLButtonElement>(".retry-button");
    retry?.addEventListener("click", () => {
      void loadPlaces();
    });
  }

  function hideStatus(): void {
    statusOverlay.style.display = "none";
  }

  function showStatus(): void {
    statusOverlay.style.display = "flex";
  }

  function renderFrame(): void {
    ring.quaternion.copy(camera.quaternion);
    renderer.render(scene, camera);
  }

  function updateRing(): void {
    const index = selected ?? hovered;
    if (index === null || !points) {
      ring.visible = false;
      return;
    }
    ring.visible = true;
    ring.position.copy(placePosition(places[index]));
    const material = ring.material as THREE.MeshBasicMaterial;
    material.color.set(selected !== null ? 0x3b82f6 : 0x94a3b8);
    if (!reducedMotion) {
      renderFrame();
    }
  }

  function showPlaceInfo(place: Place): void {
    const meta = place.meta;
    const coords = meta.coordinates.map((n) => n.toFixed(1)).join(", ");
    const tags = (items: string[], warn: boolean): string =>
      items.length > 0
        ? items
            .map((item) => `<span class="tag${warn ? " warn" : ""}">${escapeHtml(item)}</span>`)
            .join("")
        : '<span class="tag">none</span>';
    infoPanel.innerHTML =
      `<h2>${escapeHtml(meta.name)}</h2>` +
      `<div class="row"><span class="k">type</span> · <span class="v">${escapeHtml(meta.type)}</span></div>` +
      `<div class="row"><span class="k">coords</span> · <span class="v">[${escapeHtml(coords)}]</span></div>` +
      `<div class="row"><span class="k">resources</span><br>${tags(meta.resources, false)}</div>` +
      `<div class="row"><span class="k">hazards</span><br>${tags(meta.hazards, true)}</div>`;
    infoPanel.classList.remove("hidden");
  }

  function select(index: number | null): void {
    selected = index;
    if (index !== null) {
      showPlaceInfo(places[index]);
    } else {
      infoPanel.classList.add("hidden");
    }
    updateRing();
  }

  // --- Pointer interaction (hover highlight + click select) ---
  const raycaster = new THREE.Raycaster();
  raycaster.params.Points = { threshold: 2.5 };
  const pointer = new THREE.Vector2();
  let downX = 0;
  let downY = 0;

  function pickPlace(event: PointerEvent): number | null {
    if (!points) {
      return null;
    }
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObject(points);
    return hits.length > 0 && hits[0].index !== undefined ? hits[0].index : null;
  }

  function onPointerMove(event: PointerEvent): void {
    const index = pickPlace(event);
    if (index !== hovered) {
      hovered = index;
      renderer.domElement.style.cursor = index !== null ? "pointer" : "";
      updateRing();
    }
  }

  function onPointerDown(event: PointerEvent): void {
    downX = event.clientX;
    downY = event.clientY;
  }

  function onPointerUp(event: PointerEvent): void {
    // Ignore drags — only treat near-stationary presses as clicks.
    if (Math.hypot(event.clientX - downX, event.clientY - downY) > 5) {
      return;
    }
    select(pickPlace(event));
  }

  renderer.domElement.addEventListener("pointermove", onPointerMove);
  renderer.domElement.addEventListener("pointerdown", onPointerDown);
  renderer.domElement.addEventListener("pointerup", onPointerUp);

  function buildPoints(): void {
    if (points) {
      scene.remove(points);
      points.geometry.dispose();
      (points.material as THREE.Material).dispose();
    }
    const count = places.length;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    const sizes = new Float32Array(count);
    for (const [i, place] of places.entries()) {
      const pos = placePosition(place);
      positions[i * 3] = pos.x;
      positions[i * 3 + 1] = pos.y;
      positions[i * 3 + 2] = pos.z;
      const color = typeColor(place.meta.type);
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
      sizes[i] = place.meta.type === "region" ? 26 : 18;
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute("size", new THREE.BufferAttribute(sizes, 1));
    const material = new THREE.ShaderMaterial({
      uniforms: { glow: { value: glowTexture } },
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      vertexShader: `
				attribute float size;
				varying vec3 vColor;
				void main() {
					vColor = color;
					vec4 mv = modelViewMatrix * vec4(position, 1.0);
					gl_PointSize = size * (220.0 / -mv.z);
					gl_Position = projectionMatrix * mv;
				}
			`,
      fragmentShader: `
				uniform sampler2D glow;
				varying vec3 vColor;
				void main() {
					vec4 tex = texture2D(glow, gl_PointCoord);
					gl_FragColor = vec4(vColor * tex.rgb, tex.a);
				}
			`,
      vertexColors: true,
    });
    points = new THREE.Points(geometry, material);
    scene.add(points);
  }

  async function loadPlaces(): Promise<void> {
    if (disposed) {
      return;
    }
    showStatus();
    statusOverlay.innerHTML =
      '<div class="hud-panel">' +
      '<div class="status-title">Linking to backend</div>' +
      '<div class="status-body">Fetching star-map data from the API…</div>' +
      "</div>";
    try {
      places = await getPlaces();
    } catch (error) {
      const detail =
        error instanceof ApiError ? error.message : "Unexpected error while fetching places.";
      setStatus(
        "API offline",
        `<span class="danger">${escapeHtml(detail)}</span><br>Start the backend on port 8000 to load the star map.<br>No place data is shown because none could be verified.`,
      );
      return;
    }
    if (places.length === 0) {
      setStatus(
        "No places found",
        "The backend responded but returned zero places.<br>" +
          'Check that <span class="value">wiki/places/</span> has content on the API side.',
      );
      return;
    }
    hideStatus();
    buildPoints();
    renderFrame();
  }

  function resize(): void {
    const width = stage.clientWidth;
    const height = stage.clientHeight;
    if (width === 0 || height === 0) {
      return;
    }
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    if (reducedMotion) {
      renderFrame();
    }
  }

  const resizeObserver = new ResizeObserver(resize);
  resizeObserver.observe(stage);

  function animate(): void {
    if (disposed) {
      return;
    }
    animationId = requestAnimationFrame(animate);
    controls.update();
    renderFrame();
  }

  // Kick off.
  resize();
  void loadPlaces();
  if (reducedMotion) {
    controls.addEventListener("change", renderFrame);
    renderFrame();
  } else {
    animate();
  }

  // --- Teardown ---
  return () => {
    disposed = true;
    cancelAnimationFrame(animationId);
    resizeObserver.disconnect();
    controls.dispose();
    renderer.domElement.removeEventListener("pointermove", onPointerMove);
    renderer.domElement.removeEventListener("pointerdown", onPointerDown);
    renderer.domElement.removeEventListener("pointerup", onPointerUp);
    scene.traverse((object) => {
      if (object instanceof THREE.Mesh || object instanceof THREE.Points) {
        object.geometry.dispose();
        const material = object.material as THREE.Material | THREE.Material[];
        if (Array.isArray(material)) {
          for (const m of material) {
            m.dispose();
          }
        } else {
          material.dispose();
        }
      }
    });
    glowTexture.dispose();
    renderer.dispose();
    renderer.domElement.remove();
  };
}
