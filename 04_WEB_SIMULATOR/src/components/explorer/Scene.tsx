"use client";
/**
 * The 3D scene: hybrid look (realistic at the top level, stylised technical blocks with glowing links in the
 * fronthaul view). All geometry is drawn from src/lib/sceneLayout.ts; what each part says comes from
 * content/architecture.json. Packet particles are ILLUSTRATIVE and are labelled so in the UI.
 */
import { Canvas, useFrame, useThree, type ThreeEvent } from "@react-three/fiber";
import { Edges, Html, Line, OrbitControls, PerformanceMonitor } from "@react-three/drei";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { getElement, type Element, type Tier } from "@/lib/architecture";
import { DOWN, PALETTES, QUALITY, type QualityLevel, type ScenePalette, type ThemeName } from "@/lib/explorerTheme";
import type { ViewState } from "@/lib/explorerState";
import { AZIMUTH_LIMIT, POLAR_MAX, POLAR_MIN, SHORT, level2, partsAt, linksAt, poseFor, type LinkSpec, type PartSpec, type V3 } from "@/lib/sceneLayout";

export interface HoverInfo {
  id: string;
  x: number;
  y: number;
}
export interface SceneProps {
  view: ViewState;
  theme: ThemeName;
  quality: QualityLevel;
  autoQuality: boolean;
  onQuality: (q: QualityLevel) => void;
  reducedMotion: boolean;
  hoveredId: string | null;
  onHover: (h: HoverInfo | null) => void;
  onSelect: (id: string) => void;
}

function tierColor(tier: Tier, p: ScenePalette): string {
  return tier === 1 ? p.tier1 : tier === 2 ? p.tier2 : tier === 3 ? p.tier3 : p.dimmed;
}

// ------------------------------------------------------------------ interactive wrapper
interface PartProps {
  spec: PartSpec;
  el: Element;
  p: ScenePalette;
  selected: boolean;
  hovered: boolean;
  onHover: (h: HoverInfo | null) => void;
  onSelect: (id: string) => void;
  animate: boolean;
  segments: number;
  centered?: boolean; // level 2: spec.pos is the centre of the block, not its base
}

function Part({ spec, el, p, selected, hovered, onHover, onSelect, animate, segments, centered }: PartProps) {
  const dim = el.tier === "dimmed";
  const ghost = !!spec.ghost;
  const color = tierColor(el.tier, p);
  const opacity = dim ? 0.38 : ghost ? 0.4 : 1;
  const emissive = dim || ghost ? 0 : (selected ? 0.9 : hovered ? 0.7 : 0.4) * p.glow;
  const [sx, sy, sz] = spec.size ?? [2, 2, 2];
  const group = useRef<THREE.Group>(null);
  useFrame((st) => {
    if (!group.current || !animate) return;
    if (spec.shape === "sat") group.current.rotation.y = st.clock.elapsedTime * 0.25;
    if (spec.shape === "injector") {
      const s = 1 + 0.15 * Math.sin(st.clock.elapsedTime * 4);
      group.current.scale.setScalar(s);
    }
  });
  const mat = (c = color, e = emissive) => (
    <meshStandardMaterial color={c} emissive={c} emissiveIntensity={e} transparent={opacity < 1} opacity={opacity} roughness={0.55} metalness={0.25} />
  );
  const edge = selected ? p.edge : hovered && !dim ? p.edge : undefined;
  const handlers = {
    onPointerOver: (e: ThreeEvent<PointerEvent>) => {
      e.stopPropagation();
      onHover({ id: el.id, x: e.nativeEvent.clientX, y: e.nativeEvent.clientY });
      document.body.style.cursor = dim ? "default" : "pointer";
    },
    onPointerMove: (e: ThreeEvent<PointerEvent>) => {
      e.stopPropagation();
      onHover({ id: el.id, x: e.nativeEvent.clientX, y: e.nativeEvent.clientY });
    },
    onPointerOut: () => {
      onHover(null);
      document.body.style.cursor = "";
    },
    onClick: (e: ThreeEvent<MouseEvent>) => {
      e.stopPropagation();
      if (!dim) onSelect(el.id);
    },
  };
  let body: React.ReactNode;
  switch (spec.shape) {
    case "rack":
      body = (
        <>
          <mesh position={[0, sy / 2, 0]}>
            <boxGeometry args={[sx, sy, sz]} />
            {mat()}
            {edge && <Edges color={edge} />}
          </mesh>
          {[0.25, 0.5, 0.75].map((f) => (
            <mesh key={f} position={[0, sy * f, sz / 2 + 0.02]}>
              <boxGeometry args={[sx * 0.8, 0.08, 0.04]} />
              <meshStandardMaterial color={dim ? p.dimmed : p.edge} emissive={dim ? "#000" : p.edge} emissiveIntensity={dim ? 0 : 0.6 * p.glow} transparent={opacity < 1} opacity={opacity} />
            </mesh>
          ))}
        </>
      );
      break;
    case "block":
    case "standby":
      body = (
        <mesh position={[0, sy / 2, 0]}>
          <boxGeometry args={[sx, sy, sz]} />
          {spec.shape === "standby" ? <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.15 * p.glow} transparent opacity={0.45} wireframe={false} /> : mat()}
          <Edges color={edge ?? color} />
        </mesh>
      );
      break;
    case "oru":
      body = (
        <>
          <mesh position={[0, 0, 0]}>
            <boxGeometry args={[sx, sy, sz]} />
            {mat()}
            {edge && <Edges color={edge} />}
          </mesh>
          <mesh position={[0, 0, sz / 2 + 0.03]}>
            <boxGeometry args={[sx * 0.82, sy * 0.86, 0.06]} />
            <meshStandardMaterial color={p.edge} emissive={p.edge} emissiveIntensity={0.18 * p.glow} transparent={opacity < 1} opacity={opacity * 0.9} />
          </mesh>
        </>
      );
      break;
    case "cloud":
      body = (
        <>
          {([[0, 0, 0, 2.2], [2.4, -0.4, 0.4, 1.7], [-2.3, -0.5, -0.3, 1.6], [0.6, 1.2, 0.2, 1.5]] as number[][]).map(([x, y, z, r], i) => (
            <mesh key={i} position={[x, y, z]}>
              <sphereGeometry args={[r, segments, segments]} />
              {mat()}
            </mesh>
          ))}
        </>
      );
      break;
    case "sat":
      body = (
        <>
          <mesh>
            <boxGeometry args={[1.4, 1.4, 1.4]} />
            {mat()}
            {edge && <Edges color={edge} />}
          </mesh>
          {[-1, 1].map((s) => (
            <mesh key={s} position={[s * 2.2, 0, 0]}>
              <boxGeometry args={[2.6, 0.06, 1.2]} />
              <meshStandardMaterial color={p.tier2} emissive={p.tier2} emissiveIntensity={0.25 * p.glow} transparent={opacity < 1} opacity={opacity} />
            </mesh>
          ))}
        </>
      );
      break;
    case "slab":
      body = (
        <mesh>
          <boxGeometry args={[sx, sy, sz]} />
          {mat()}
          {edge && <Edges color={edge} />}
        </mesh>
      );
      break;
    case "phone":
      body = (
        <mesh>
          <boxGeometry args={[sx, sy, sz]} />
          {mat()}
          {edge && <Edges color={edge} />}
        </mesh>
      );
      break;
    case "chip":
      body = (
        <mesh>
          <boxGeometry args={[sx, sy, sz]} />
          {mat()}
          <Edges color={edge ?? color} />
        </mesh>
      );
      break;
    case "injector":
      body = (
        <mesh>
          <octahedronGeometry args={[0.7, 0]} />
          <meshStandardMaterial color={p.attack} emissive={p.attack} emissiveIntensity={0.9 * p.glow} />
          {edge && <Edges color={edge} />}
        </mesh>
      );
      break;
    case "rings":
      body = (
        <>
          {[1.2, 2.2, 3.2].map((r, i) => (
            <mesh key={i} rotation={[0, Math.PI / 2, 0]}>
              <torusGeometry args={[r, 0.04, 6, segments * 2]} />
              <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.5 * p.glow} transparent opacity={0.5 - i * 0.1} />
            </mesh>
          ))}
          <mesh visible={true}>
            <sphereGeometry args={[3.3, 8, 8]} />
            <meshBasicMaterial transparent opacity={0} depthWrite={false} />
          </mesh>
        </>
      );
      break;
  }
  const h = spec.shape === "rack" || spec.shape === "block" || spec.shape === "standby" ? sy : spec.shape === "oru" ? sy / 2 : spec.shape === "cloud" ? 3.6 : spec.shape === "rings" ? 3.8 : spec.shape === "slab" ? 1.2 : 1.6;
  return (
    <group ref={group} position={spec.pos} {...handlers} name={`part-${el.id}`}>
      <group position={[0, centered && (spec.shape === "rack" || spec.shape === "block" || spec.shape === "standby") ? -sy / 2 : 0, 0]}>{body}</group>
      <Html position={[0, h + 0.55, 0]} center style={{ pointerEvents: "none" }} zIndexRange={[20, 0]}>
        <div
          data-testid={`label-${el.id}${spec.label ? `-${spec.label.replace(/\W+/g, "")}` : ""}`}
          className={`whitespace-nowrap rounded px-1.5 py-0.5 text-[11px] font-semibold leading-tight shadow ${dim || ghost ? "opacity-70" : ""}`}
          style={{ background: p.bg + "e6", color: dim ? p.dimmed : p.ink, border: `1px solid ${color}` }}
        >
          {spec.label ?? SHORT[el.id] ?? el.name}
        </div>
      </Html>
    </group>
  );
}

// ------------------------------------------------------------------ links and packets
function useCurve(points: V3[]) {
  return useMemo(() => new THREE.CatmullRomCurve3(points.map((q) => new THREE.Vector3(...q)), false, "catmullrom", 0.15), [points]);
}
const ROLE_COLOR = (r: LinkSpec["role"], p: ScenePalette) => (r === "splane" ? p.splane : r === "mplane" ? p.mplane : r === "cplane" ? p.cplane : r === "uplane" ? p.uplane : r === "synce" ? p.synce : p.dimmed);

function PacketFlow({ curve, color, count, speed }: { curve: THREE.CatmullRomCurve3; color: string; count: number; speed: number }) {
  const ref = useRef<THREE.InstancedMesh>(null);
  const tmp = useMemo(() => new THREE.Object3D(), []);
  useFrame((st) => {
    const m = ref.current;
    if (!m) return;
    for (let i = 0; i < count; i++) {
      const u = (st.clock.elapsedTime * speed + i / count) % 1;
      tmp.position.copy(curve.getPointAt(u));
      m.setMatrixAt(i, tmp.matrix.identity().setPosition(tmp.position));
    }
    m.instanceMatrix.needsUpdate = true;
  });
  if (count <= 0) return null;
  return (
    <instancedMesh ref={ref} args={[undefined, undefined, count]} frustumCulled={false}>
      <sphereGeometry args={[0.22, 8, 8]} />
      <meshBasicMaterial color={color} />
    </instancedMesh>
  );
}

function LinkMesh({ link, el, p, selected, hovered, onHover, onSelect, particles, animate }: {
  link: LinkSpec; el: Element | undefined; p: ScenePalette; selected: boolean; hovered: boolean;
  onHover: (h: HoverInfo | null) => void; onSelect: (id: string) => void; particles: number; animate: boolean;
}) {
  const curve = useCurve(link.points);
  const pts = useMemo(() => curve.getPoints(48), [curve]);
  const color = ROLE_COLOR(link.role, p);
  const ghost = !!link.ghost;
  const clickable = !!el && el.tier !== "dimmed";
  return (
    <group name={`link-${link.id}`}>
      <Line points={pts} color={color} lineWidth={(selected ? 1.8 : hovered ? 1.4 : 1) * p.lineWidth * (ghost ? 0.6 : 1)} transparent opacity={ghost ? 0.4 : 1} dashed={link.role === "synce" || ghost} dashSize={0.6} gapSize={0.4} />
      {el && (
        <mesh
          onPointerOver={(e) => {
            e.stopPropagation();
            onHover({ id: el.id, x: e.nativeEvent.clientX, y: e.nativeEvent.clientY });
            document.body.style.cursor = clickable ? "pointer" : "default";
          }}
          onPointerMove={(e) => {
            e.stopPropagation();
            onHover({ id: el.id, x: e.nativeEvent.clientX, y: e.nativeEvent.clientY });
          }}
          onPointerOut={() => {
            onHover(null);
            document.body.style.cursor = "";
          }}
          onClick={(e) => {
            e.stopPropagation();
            if (clickable) onSelect(el.id);
          }}
        >
          <tubeGeometry args={[curve, 40, 0.45, 6, false]} />
          <meshBasicMaterial transparent opacity={0} depthWrite={false} />
        </mesh>
      )}
      {link.flow && animate && !ghost && <PacketFlow curve={curve} color={color} count={particles} speed={0.12} />}
      {link.label && (
        <Html position={pts[Math.floor(pts.length / 2)].toArray() as V3} center style={{ pointerEvents: "none" }} zIndexRange={[10, 0]}>
          <div className="whitespace-nowrap rounded px-1 text-[10px]" style={{ color: p.ink, background: p.bg + "cc" }}>
            {link.label}
          </div>
        </Html>
      )}
    </group>
  );
}

// ------------------------------------------------------------------ static decoration (top level, realistic)
function Mast({ p, segments }: { p: ScenePalette; segments: number }) {
  return (
    <group position={[16, 0, 0]}>
      <mesh position={[0, 4, 0]}>
        <cylinderGeometry args={[0.16, 0.42, 8, Math.max(6, segments / 2)]} />
        <meshStandardMaterial color={p.dimmed} roughness={0.7} metalness={0.4} />
      </mesh>
      {[1.5, 3.5, 5.5, 7.3].map((y) => (
        <mesh key={y} position={[0, y, 0]} rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[0.34 - y * 0.02, 0.03, 6, 12]} />
          <meshStandardMaterial color={p.dimmed} />
        </mesh>
      ))}
    </group>
  );
}

function Ground({ p, size }: { p: ScenePalette; size: number }) {
  return (
    <>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]}>
        <planeGeometry args={[size, size]} />
        <meshStandardMaterial color={p.ground} roughness={1} />
      </mesh>
      <gridHelper args={[size, size / 2, p.grid, p.grid]} position={[0, 0, 0]} />
    </>
  );
}

// ------------------------------------------------------------------ camera
function CameraRig({ view, reduced, controls }: { view: ViewState; reduced: boolean; controls: React.RefObject<OrbitControlsImpl | null> }) {
  const { camera } = useThree();
  const goal = useRef({ pos: new THREE.Vector3(), tgt: new THREE.Vector3(), active: false, elapsed: 0 });
  const pose = useMemo(() => poseFor(view.level, view.lls, view.focus), [view.level, view.lls, view.focus]);
  useEffect(() => {
    goal.current.pos.set(...pose.position);
    goal.current.tgt.set(...pose.target);
    const c = controls.current;
    if (c) {
      c.minDistance = pose.minDistance;
      c.maxDistance = pose.maxDistance;
    }
    if (reduced || !c) {
      camera.position.copy(goal.current.pos);
      if (c) {
        c.target.copy(goal.current.tgt);
        c.update();
      }
      goal.current.active = false;
      (window as unknown as { __oranFlying?: boolean }).__oranFlying = false;
    } else {
      goal.current.active = true;
      goal.current.elapsed = 0;
      (window as unknown as { __oranFlying?: boolean }).__oranFlying = true;
    }
  }, [pose, reduced, camera, controls]);
  useFrame((_, dt) => {
    const g = goal.current;
    const c = controls.current;
    if (!g.active || !c) return;
    g.elapsed += dt;
    const k = 1 - Math.exp(-dt * 4.5);
    camera.position.lerp(g.pos, k);
    c.target.lerp(g.tgt, k);
    c.update();
    // finished when at the goal, or after 3 s (the orbit limits can keep a goal slightly out of reach)
    if ((camera.position.distanceTo(g.pos) < 0.06 && c.target.distanceTo(g.tgt) < 0.06) || g.elapsed > 3) {
      camera.position.copy(g.pos);
      c.target.copy(g.tgt);
      c.update();
      g.active = false;
      (window as unknown as { __oranFlying?: boolean }).__oranFlying = false;
    }
  });
  return null;
}

/** Test and diagnostics bridge: projects part positions to screen pixels and reports fps. */
function DebugBridge({ view, quality }: { view: ViewState; quality: QualityLevel }) {
  const { camera, gl, size } = useThree();
  const frames = useRef<number[]>([]);
  const total = useRef(0);
  useFrame((st) => {
    total.current++;
    const t = st.clock.elapsedTime;
    frames.current.push(t);
    while (frames.current.length && frames.current[0] < t - 2) frames.current.shift();
  });
  useEffect(() => {
    const api = {
      ready: true,
      quality,
      level: view.level,
      frames: () => total.current,
      fps: () => {
        const f = frames.current;
        return f.length > 1 ? (f.length - 1) / (f[f.length - 1] - f[0]) : 0;
      },
      project: (id: string) => {
        const part = partsAt(view.level, view.lls).find((q) => q.id === id);
        const link = linksAt(view.level, view.lls).find((l) => l.id === id);
        const pos: V3 | undefined = part ? part.pos : link ? link.points[Math.floor(link.points.length / 2)] : undefined;
        if (!pos) return null;
        const v = new THREE.Vector3(...pos);
        if (part && part.shape !== "oru" && part.shape !== "cloud" && part.shape !== "rings" && part.shape !== "sat" && part.shape !== "injector" && part.shape !== "chip" && part.shape !== "phone" && part.shape !== "slab") v.y += (part.size?.[1] ?? 2) / 2;
        v.project(camera);
        const r = gl.domElement.getBoundingClientRect();
        return { x: r.left + ((v.x + 1) / 2) * size.width, y: r.top + ((1 - v.y) / 2) * size.height, inFront: v.z < 1 };
      },
    };
    (window as unknown as { __oranExplorer?: typeof api }).__oranExplorer = api;
  });
  return null;
}

// ------------------------------------------------------------------ level scenes
function Lights({ p }: { p: ScenePalette }) {
  return (
    <>
      <ambientLight intensity={p.bg === "#ffffff" ? 1.1 : 0.7} />
      <directionalLight position={[10, 20, 14]} intensity={p.bg === "#ffffff" ? 1.0 : 1.2} />
      <pointLight position={[-10, 8, 10]} intensity={p.bg === "#ffffff" ? 0 : 60} color={p.tier2} />
    </>
  );
}

function Level({ view, p, quality, reduced, hoveredId, onHover, onSelect }: {
  view: ViewState; p: ScenePalette; quality: QualityLevel; reduced: boolean; hoveredId: string | null;
  onHover: (h: HoverInfo | null) => void; onSelect: (id: string) => void;
}) {
  const q = QUALITY[quality];
  const parts = partsAt(view.level, view.lls);
  const links = linksAt(view.level, view.lls);
  const l2 = view.level === 2 ? level2(view.lls) : null;
  const animate = !reduced;
  const focusEl = view.focus;
  const selectedOf = (id: string) => focusEl === id || (id === "o-ru" && focusEl === "o-ru");
  return (
    <>
      <Lights p={p} />
      {view.level === 1 ? (
        <>
          <Ground p={p} size={90} />
          <Mast p={p} segments={q.segments} />
        </>
      ) : (
        <group position={[0, -10, 0]}>
          <Ground p={p} size={70} />
        </group>
      )}
      {links.map((l, i) => (
        <LinkMesh
          key={`${view.level}-${view.lls}-${l.id}-${i}`}
          link={l}
          el={getElement(l.id)}
          p={p}
          selected={selectedOf(l.id)}
          hovered={hoveredId === l.id}
          onHover={onHover}
          onSelect={onSelect}
          particles={q.particles}
          animate={animate}
        />
      ))}
      {parts.map((s) => {
        const el = getElement(s.id);
        if (!el) return null;
        return (
          <Part
            key={`${view.level}-${view.lls}-${s.id}`}
            spec={s}
            el={el}
            p={p}
            selected={selectedOf(s.id)}
            hovered={hoveredId === s.id}
            onHover={onHover}
            onSelect={onSelect}
            animate={animate}
            segments={q.segments}
            centered={view.level === 2}
          />
        );
      })}
      {l2?.decor?.map((d) => (
        <group key={d.id} position={d.pos}>
          <mesh>
            <boxGeometry args={d.size ?? [3, 1.2, 1]} />
            <meshStandardMaterial color={p.dimmed} transparent opacity={0.4} />
            <Edges color={p.dimmed} />
          </mesh>
          <Html position={[0, 1.4, 0]} center style={{ pointerEvents: "none" }}>
            <div className="whitespace-nowrap rounded px-1 text-[10px]" style={{ color: p.ink, background: p.bg + "cc" }}>
              {d.label}
            </div>
          </Html>
        </group>
      ))}
      {l2 && !l2.testbed && (
        <Html position={[0, -7.5, 0]} center style={{ pointerEvents: "none" }}>
          <div className="whitespace-nowrap rounded px-2 py-1 text-xs font-bold uppercase tracking-wide" style={{ color: p.attack, border: `2px dashed ${p.attack}`, background: p.bg + "e6" }}>
            Not the testbed&apos;s configuration
          </div>
        </Html>
      )}
    </>
  );
}

export function hasWebGL(): boolean {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

export default function Scene(props: SceneProps) {
  const { view, theme, quality, autoQuality, onQuality, reducedMotion, hoveredId, onHover, onSelect } = props;
  const p = PALETTES[theme];
  const q = QUALITY[quality];
  const controls = useRef<OrbitControlsImpl | null>(null);
  return (
    <Canvas
      key={q.antialias ? "aa" : "noaa"}
      dpr={q.dpr}
      gl={{ antialias: q.antialias, powerPreference: "high-performance" }}
      camera={{ position: poseFor(view.level, view.lls, view.focus).position, fov: 42, near: 0.1, far: 500 }}
      onPointerMissed={() => onHover(null)}
      style={{ touchAction: "none" }}
      data-testid="explorer-canvas"
    >
      <color attach="background" args={[p.bg]} />
      <fog attach="fog" args={[p.fog, 110, 260]} />
      {autoQuality && <PerformanceMonitor onDecline={() => onQuality(DOWN[quality])} flipflops={2} />}
      <OrbitControls
        ref={controls as React.Ref<OrbitControlsImpl>}
        makeDefault
        enablePan={false}
        enableDamping
        minPolarAngle={POLAR_MIN}
        maxPolarAngle={POLAR_MAX}
        minAzimuthAngle={-AZIMUTH_LIMIT}
        maxAzimuthAngle={AZIMUTH_LIMIT}
        rotateSpeed={0.6}
      />
      <CameraRig view={view} reduced={reducedMotion} controls={controls} />
      <DebugBridge view={view} quality={quality} />
      <Level view={view} p={p} quality={quality} reduced={reducedMotion} hoveredId={hoveredId} onHover={onHover} onSelect={onSelect} />
    </Canvas>
  );
}
