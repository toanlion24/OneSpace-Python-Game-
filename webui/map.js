/* Vẽ bản đồ và phát lại các sự kiện mà engine Python ghi lại (đi, đánh, nhặt ngọc...).
   Bản đồ vẽ bằng canvas với hình pixel-art trong gamekit/, có hoạt ảnh, bóng đổ,
   hạt hiệu ứng và không khí riêng cho từng kiểu bản đồ. */

const TILE = 48;
const TOP_PAD = 46;
const KIT = "../gamekit/";
const MAX_MAP_SCALE = 2.2;

const ENEMY_CHARS = { r: "robot", b: "barrel", c: "cannon", x: "spikebox", B: "duck" };
const ENEMY_HP = { duck: 3 };
const ENEMY_SPRITES = {
  robot: ["4 Enemies/1", 48, 1.7],
  barrel: ["4 Enemies/3", 48, 1.7],
  cannon: ["4 Enemies/4", 48, 1.7],
  spikebox: ["4 Enemies/5", 48, 1.7],
  duck: ["4 Enemies/6 (48x72)", 72, 2.0],
};
const GEM_GLOW = { 1: "#fb7185", 2: "#34d399", 3: "#60a5fa", 4: "#facc15", 5: "#c084fc", 6: "#22d3ee" };
const EVENT_DURATIONS = {
  move: 170, bump: 220, attack: 260, hurt: 380, shield: 320, gem: 70, key: 70, box_break: 260,
  gem_reveal: 140, door_open: 260, unlock: 260, chest_open: 340, heal: 320, jam: 260, say: 900,
  fail: 520, die: 520, print: 0, info: 60,
};

const imageCache = new Map();

function loadImage(path) {
  if (!imageCache.has(path)) {
    imageCache.set(path, new Promise((resolve, reject) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = () => reject(new Error(`Không tải được hình ${path}`));
      image.src = KIT + path.split("/").map(encodeURIComponent).join("/");
    }));
  }
  return imageCache.get(path);
}

function recolorImage(image, pairs) {
  const canvas = document.createElement("canvas");
  canvas.width = image.width;
  canvas.height = image.height;
  const context = canvas.getContext("2d");
  context.drawImage(image, 0, 0);
  if (!pairs || pairs.length === 0) return canvas;
  const pixels = context.getImageData(0, 0, canvas.width, canvas.height);
  const data = pixels.data;
  for (let index = 0; index < data.length; index += 4) {
    for (const [oldColor, newColor] of pairs) {
      if (data[index] === oldColor[0] && data[index + 1] === oldColor[1] && data[index + 2] === oldColor[2]) {
        data[index] = newColor[0];
        data[index + 1] = newColor[1];
        data[index + 2] = newColor[2];
        break;
      }
    }
  }
  context.putImageData(pixels, 0, 0);
  return canvas;
}

function frameStrip(source, frameWidth) {
  const count = Math.max(1, Math.floor(source.width / frameWidth));
  return { source, frameWidth, frameHeight: source.height, count };
}

function tintedTile(tileset, column, row, multiply, add) {
  const canvas = document.createElement("canvas");
  canvas.width = TILE;
  canvas.height = TILE;
  const context = canvas.getContext("2d");
  context.imageSmoothingEnabled = false;
  context.drawImage(tileset, column * 16, row * 16, 16, 16, 0, 0, TILE, TILE);
  const isTinted = multiply.some((channel) => channel !== 255);
  const isBrightened = add.some((channel) => channel !== 0);
  if (isTinted) {
    context.globalCompositeOperation = "multiply";
    context.fillStyle = `rgb(${multiply.join(",")})`;
    context.fillRect(0, 0, TILE, TILE);
  }
  if (isBrightened) {
    context.globalCompositeOperation = "lighter";
    context.fillStyle = `rgb(${add.join(",")})`;
    context.fillRect(0, 0, TILE, TILE);
  }
  context.globalCompositeOperation = "destination-in";
  context.drawImage(tileset, column * 16, row * 16, 16, 16, 0, 0, TILE, TILE);
  return canvas;
}

function plainTile(tileset, column, row) {
  return tintedTile(tileset, column, row, [255, 255, 255], [0, 0, 0]);
}

async function loadHeroStrips(hero) {
  const folder = `1 Main Characters/${hero.base}`;
  const strips = {};
  for (const [state, fileName] of [["idle", "Idle"], ["run", "Run"], ["hit", "Hit"], ["jump", "Jump"]]) {
    const image = await loadImage(`${folder}/${fileName}.png`);
    strips[state] = frameStrip(recolorImage(image, hero.recolor), 32);
  }
  return strips;
}

async function drawHeroAvatar(canvas, hero) {
  const strips = await loadHeroStrips(hero);
  const context = canvas.getContext("2d");
  canvas.width = 32;
  canvas.height = 32;
  context.imageSmoothingEnabled = false;
  context.drawImage(strips.idle.source, 0, 0, 32, 32, 0, 2, 32, 32);
}

function keyOf(x, y) {
  return `${x},${y}`;
}

class MapView {
  constructor(canvas) {
    this.canvas = canvas;
    this.context = canvas.getContext("2d");
    this.speed = 1;
    this.time = 0;
    this.lastFrame = performance.now();
    this.sprites = null;
    this.state = null;
    this.queue = [];
    this.current = null;
    this.particles = [];
    this.floaters = [];
    this.ambient = [];
    this.shake = 0;
    this.callbacks = {};
    this.running = true;
    requestAnimationFrame((now) => this.frame(now));
  }

  destroy() {
    this.running = false;
  }

  async setup({ rows, theme, hero, hp, maxHp }) {
    this.theme = theme;
    this.startHp = hp;
    this.maxHp = maxHp;
    const tileset = await loadImage("2 Locations/Tiles/Tileset.png");
    const enemies = {};
    for (const [kind, [folder, frameWidth, scale]] of Object.entries(ENEMY_SPRITES)) {
      enemies[kind] = {
        idle: frameStrip(await loadImage(`${folder}/Idle.png`), frameWidth),
        hit: frameStrip(await loadImage(`${folder}/Hit.png`), frameWidth),
        scale,
      };
    }
    const gems = {};
    for (let color = 1; color <= 6; color += 1) {
      gems[color] = frameStrip(await loadImage(`3 Objects/Gems/${color}.png`), 16);
    }
    this.sprites = {
      floor: tintedTile(tileset, theme.floor[0], theme.floor[1], theme.floorMultiply, theme.add),
      wall: tintedTile(tileset, theme.wall[0], theme.wall[1], theme.wallMultiply, theme.add),
      doorLocked: plainTile(tileset, 13, 5),
      doorJammed: plainTile(tileset, 6, 8),
      hero: await loadHeroStrips(hero),
      enemies,
      gems,
      crates: {
        1: await loadImage("3 Objects/Boxes/1_Idle.png"),
        2: await loadImage("3 Objects/Boxes/2_Idle.png"),
      },
      trophy: frameStrip(await loadImage("3 Objects/Checkpoints/End_Idle.png"), 64),
      spikes: await loadImage("6 Traps/4.png"),
    };
    this.setRows(rows);
  }

  setRows(rows) {
    this.rows = rows;
    this.columns = Math.max(...rows.map((row) => row.length));
    this.canvas.width = this.columns * TILE;
    this.canvas.height = rows.length * TILE + TOP_PAD;
    this.context.imageSmoothingEnabled = false;
    this.createAmbient();
    this.reset();
    this.fit();
  }

  fit() {
    const container = this.canvas.parentElement;
    if (!container || !this.canvas.width) return;
    const availableWidth = container.clientWidth - 24;
    const availableHeight = container.clientHeight - 24;
    const scale = Math.min(availableWidth / this.canvas.width, availableHeight / this.canvas.height, MAX_MAP_SCALE);
    this.canvas.style.width = `${Math.floor(this.canvas.width * scale)}px`;
    this.canvas.style.height = `${Math.floor(this.canvas.height * scale)}px`;
  }

  reset() {
    const state = {
      gems: new Map(), enemies: new Map(), doors: new Map(), crates: new Map(), keys: new Set(),
      locks: new Set(), chests: new Map(), spikes: new Set(), walls: new Set(), floors: new Set(),
      exit: null,
      hero: { x: 0, y: 0, fromX: 0, fromY: 0, toX: 0, toY: 0, facing: "right", animation: "idle", lunge: 0 },
      hp: this.startHp ?? 3,
      keyCount: 0,
      gemCount: 0,
      bubble: null,
    };
    this.rows.forEach((row, y) => {
      for (let x = 0; x < this.columns; x += 1) {
        const character = row[x] ?? " ";
        const key = keyOf(x, y);
        if (character === " ") continue;
        if (character === "#") {
          state.walls.add(key);
          continue;
        }
        state.floors.add(key);
        if (character === "@") Object.assign(state.hero, { x, y, fromX: x, fromY: y, toX: x, toY: y });
        else if (character === "E") state.exit = { x, y };
        else if (character === "^") state.spikes.add(key);
        else if (character === "G") state.gems.set(key, 1);
        else if ("123456".includes(character)) state.gems.set(key, Number(character));
        else if (character === "D") state.doors.set(key, { type: "locked", shakeUntil: 0 });
        else if (character === "J") state.doors.set(key, { type: "jammed", shakeUntil: 0 });
        else if (ENEMY_CHARS[character]) {
          const kind = ENEMY_CHARS[character];
          state.enemies.set(key, { kind, hp: ENEMY_HP[kind] ?? 1, hitUntil: 0, dyingSince: null });
        } else if (character === "O") state.crates.set(key, 1);
        else if (character === "Q") state.crates.set(key, 2);
        else if (character === "k") state.keys.add(key);
        else if (character === "L") state.locks.add(key);
        else if (character === "C") state.chests.set(key, { opened: false });
      }
    });
    this.state = state;
    this.queue = [];
    this.current = null;
    this.particles = [];
    this.floaters = [];
    this.callbacks.onState?.(this.state);
  }

  play(events, callbacks) {
    this.reset();
    this.callbacks = callbacks;
    this.queue = [...events];
    this.callbacks.onState?.(this.state);
  }

  get isPlaying() {
    return this.current !== null || this.queue.length > 0;
  }

  skip() {
    while (this.isPlaying) this.advance(10_000);
  }

  // ------------------------------------------------------------ playback
  advance(milliseconds) {
    let remaining = milliseconds;
    while (remaining > 0) {
      if (!this.current) {
        if (this.queue.length === 0) {
          if (this.callbacks.onDone) {
            const onDone = this.callbacks.onDone;
            this.callbacks.onDone = null;
            onDone();
          }
          return;
        }
        const event = this.queue.shift();
        const duration = (EVENT_DURATIONS[event.type] ?? 120) / this.speed;
        this.current = { event, elapsed: 0, duration };
        this.startEvent(event);
      }
      const step = Math.min(remaining, this.current.duration - this.current.elapsed);
      this.current.elapsed += step;
      remaining -= step;
      this.updateEvent(this.current);
      if (this.current.elapsed >= this.current.duration) {
        this.finishEvent(this.current.event);
        this.current = null;
      }
      if (step === 0 && this.current) remaining = 0;
    }
  }

  cellCenter(x, y) {
    return [x * TILE + TILE / 2, TOP_PAD + y * TILE + TILE / 2];
  }

  burst(x, y, color, count = 14, speed = 1) {
    const [centerX, centerY] = this.cellCenter(x, y);
    for (let index = 0; index < count; index += 1) {
      const angle = Math.random() * Math.PI * 2;
      const velocity = (40 + Math.random() * 110) * speed;
      this.particles.push({
        x: centerX, y: centerY,
        velocityX: Math.cos(angle) * velocity, velocityY: Math.sin(angle) * velocity - 60,
        life: 0.6 + Math.random() * 0.4, age: 0, color, size: 2 + Math.random() * 3,
      });
    }
  }

  floatText(x, y, text, color) {
    const [centerX, centerY] = this.cellCenter(x, y);
    this.floaters.push({ x: centerX, y: centerY - 30, text, color, age: 0, life: 1.1 });
  }

  log(text, kind) {
    this.callbacks.onLog?.(text, kind);
  }

  startEvent(event) {
    const state = this.state;
    const hero = state.hero;
    this.callbacks.onEvent?.(event);
    switch (event.type) {
      case "move":
        Object.assign(hero, {
          fromX: event.src[0], fromY: event.src[1], toX: event.dst[0], toY: event.dst[1],
          facing: event.direction, animation: "run",
        });
        break;
      case "bump":
        hero.facing = event.direction;
        hero.animation = "idle";
        break;
      case "attack": {
        hero.facing = event.direction ?? hero.facing;
        const [targetX, targetY] = event.target;
        const enemy = state.enemies.get(keyOf(targetX, targetY));
        if (event.hit && enemy) {
          enemy.hitUntil = this.time + 0.35;
          this.burst(targetX, targetY, "#fde68a", 10);
          if (event.killed) enemy.dyingSince = this.time;
        }
        break;
      }
      case "hurt":
        hero.animation = "hit";
        state.hp = event.hp;
        this.shake = 0.35;
        this.floatText(hero.x, hero.y, "-1 ♥", "#fb7185");
        this.log(event.text, "bad");
        break;
      case "shield":
        state.shieldUsed = true;
        this.floatText(hero.x, hero.y, "Khiên!", "#93c5fd");
        this.log(event.text, "info");
        break;
      case "gem": {
        const [gemX, gemY] = event.pos;
        state.gems.delete(keyOf(gemX, gemY));
        state.gemCount += 1;
        this.burst(gemX, gemY, GEM_GLOW[event.color] ?? "#fff", 16);
        this.floatText(gemX, gemY, "+1", GEM_GLOW[event.color] ?? "#fff");
        break;
      }
      case "key": {
        const [keyX, keyY] = event.pos;
        state.keys.delete(keyOf(keyX, keyY));
        state.keyCount = event.keys;
        this.burst(keyX, keyY, "#facc15", 12);
        this.floatText(keyX, keyY, "+1 chìa", "#facc15");
        break;
      }
      case "box_break": {
        const [boxX, boxY] = event.pos;
        state.crates.delete(keyOf(boxX, boxY));
        this.burst(boxX, boxY, "#b7793f", 18, 1.2);
        break;
      }
      case "gem_reveal": {
        const [gemX, gemY] = event.pos;
        state.gems.set(keyOf(gemX, gemY), event.color);
        break;
      }
      case "door_open": {
        const [doorX, doorY] = event.pos;
        state.doors.delete(keyOf(doorX, doorY));
        this.burst(doorX, doorY, "#a5b4fc", 16);
        this.log("Cửa đã mở!", "good");
        break;
      }
      case "unlock": {
        const [lockX, lockY] = event.pos;
        state.locks.delete(keyOf(lockX, lockY));
        state.keyCount = event.keys;
        this.burst(lockX, lockY, "#facc15", 16);
        break;
      }
      case "chest_open": {
        const [chestX, chestY] = event.pos;
        const chest = state.chests.get(keyOf(chestX, chestY));
        if (chest) chest.opened = true;
        this.burst(chestX, chestY, "#ffc94a", 24, 1.3);
        this.floatText(chestX, chestY, "+xu", "#ffc94a");
        break;
      }
      case "heal":
        state.hp = event.hp;
        this.floatText(hero.x, hero.y, `+${event.amount} ♥`, "#34d399");
        break;
      case "jam": {
        const [doorX, doorY] = event.pos;
        const door = state.doors.get(keyOf(doorX, doorY));
        if (door) door.shakeUntil = this.time + 0.3;
        this.log("Cửa bị kẹt! Thử lại...", "info");
        break;
      }
      case "say":
        state.bubble = { text: String(event.text), until: this.time + 2.2 };
        this.log(`Hero nói: ${event.text}`, "accent");
        break;
      case "print":
        this.log(event.text, "print");
        break;
      case "info":
        this.log(event.text, "info");
        break;
      case "fail":
      case "die":
        hero.animation = "hit";
        this.shake = 0.4;
        break;
      default:
        break;
    }
    this.callbacks.onState?.(state);
  }

  updateEvent(current) {
    const hero = this.state.hero;
    const progress = Math.min(1, current.elapsed / current.duration);
    const type = current.event.type;
    if (type === "move") {
      const eased = progress < 0.5 ? 2 * progress * progress : 1 - (-2 * progress + 2) ** 2 / 2;
      hero.x = hero.fromX + (hero.toX - hero.fromX) * eased;
      hero.y = hero.fromY + (hero.toY - hero.fromY) * eased;
    } else if (type === "bump" || type === "attack") {
      hero.lunge = Math.sin(progress * Math.PI) * (type === "attack" ? 0.35 : 0.18);
    }
  }

  finishEvent(event) {
    const hero = this.state.hero;
    hero.lunge = 0;
    if (event.type === "move") {
      hero.x = hero.toX;
      hero.y = hero.toY;
    }
    if (event.type === "attack" && event.killed) {
      const [targetX, targetY] = event.target;
      this.state.enemies.delete(keyOf(targetX, targetY));
      this.burst(targetX, targetY, "#e5e7eb", 22, 1.3);
    }
    if (!this.queue.length || this.queue[0].type !== "move") {
      if (hero.animation === "run") hero.animation = "idle";
    }
    if (event.type === "hurt") hero.animation = "idle";
  }

  // ------------------------------------------------------------ ambient
  createAmbient() {
    const count = { snow: 70, dust: 40, fireflies: 26, sparkle: 34, leaves: 22 }[this.theme?.ambient] ?? 0;
    this.ambient = Array.from({ length: count }, () => ({
      x: Math.random() * this.canvas.width,
      y: Math.random() * this.canvas.height,
      phase: Math.random() * Math.PI * 2,
      speed: 0.4 + Math.random() * 0.8,
      size: 1 + Math.random() * 2.2,
    }));
  }

  updateAmbient(deltaSeconds) {
    const kind = this.theme?.ambient;
    for (const particle of this.ambient) {
      particle.phase += deltaSeconds * particle.speed;
      if (kind === "snow") {
        particle.y += 22 * particle.speed * deltaSeconds;
        particle.x += Math.sin(particle.phase) * 10 * deltaSeconds;
      } else if (kind === "leaves") {
        particle.y += 16 * particle.speed * deltaSeconds;
        particle.x += 18 * deltaSeconds + Math.sin(particle.phase * 2) * 12 * deltaSeconds;
      } else if (kind === "dust") {
        particle.x += 14 * particle.speed * deltaSeconds;
        particle.y += Math.sin(particle.phase) * 4 * deltaSeconds;
      } else {
        particle.x += Math.cos(particle.phase) * 10 * deltaSeconds;
        particle.y += Math.sin(particle.phase * 1.3) * 8 * deltaSeconds;
      }
      if (particle.y > this.canvas.height) particle.y = -4;
      if (particle.x > this.canvas.width) particle.x = -4;
      if (particle.x < -6) particle.x = this.canvas.width;
    }
  }

  // ------------------------------------------------------------ frame loop
  frame(now) {
    if (!this.running) return;
    const deltaSeconds = Math.min(0.05, (now - this.lastFrame) / 1000);
    this.lastFrame = now;
    this.time += deltaSeconds;
    if (this.state) {
      this.advance(deltaSeconds * 1000);
      this.updateEffects(deltaSeconds);
      this.updateAmbient(deltaSeconds);
      this.draw();
    }
    requestAnimationFrame((next) => this.frame(next));
  }

  updateEffects(deltaSeconds) {
    for (const particle of this.particles) {
      particle.age += deltaSeconds;
      particle.x += particle.velocityX * deltaSeconds;
      particle.y += particle.velocityY * deltaSeconds;
      particle.velocityY += 260 * deltaSeconds;
    }
    this.particles = this.particles.filter((particle) => particle.age < particle.life);
    for (const floater of this.floaters) floater.age += deltaSeconds;
    this.floaters = this.floaters.filter((floater) => floater.age < floater.life);
    this.shake = Math.max(0, this.shake - deltaSeconds);
  }

  // ------------------------------------------------------------ drawing
  draw() {
    const context = this.context;
    const { width, height } = this.canvas;
    context.save();
    const backdrop = this.theme.backdrop;
    const gradient = context.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, `rgb(${backdrop.map((channel) => Math.min(255, channel + 18)).join(",")})`);
    gradient.addColorStop(1, `rgb(${backdrop.join(",")})`);
    context.fillStyle = gradient;
    context.fillRect(0, 0, width, height);
    if (this.shake > 0) {
      context.translate((Math.random() - 0.5) * 8 * this.shake, (Math.random() - 0.5) * 8 * this.shake);
    }
    this.drawTerrain();
    this.drawObjects();
    this.drawHero();
    this.drawEffects();
    this.drawAmbient();
    this.drawBubble();
    context.restore();
  }

  forEachCell(cells, callback) {
    for (const key of cells) {
      const [x, y] = key.split(",").map(Number);
      callback(x, y, key);
    }
  }

  drawTerrain() {
    const context = this.context;
    const state = this.state;
    this.forEachCell(state.floors, (x, y) => {
      context.drawImage(this.sprites.floor, x * TILE, TOP_PAD + y * TILE);
    });
    this.forEachCell(state.floors, (x, y) => {
      if (!state.walls.has(keyOf(x, y - 1))) return;
      const top = TOP_PAD + y * TILE;
      const shadow = context.createLinearGradient(0, top, 0, top + 16);
      shadow.addColorStop(0, "rgba(0,0,0,0.45)");
      shadow.addColorStop(1, "rgba(0,0,0,0)");
      context.fillStyle = shadow;
      context.fillRect(x * TILE, top, TILE, 16);
    });
    this.forEachCell(state.walls, (x, y) => {
      const left = x * TILE;
      const top = TOP_PAD + y * TILE;
      context.drawImage(this.sprites.wall, left, top);
      if (!state.walls.has(keyOf(x, y - 1))) {
        context.fillStyle = "rgba(255,255,255,0.12)";
        context.fillRect(left, top, TILE, 3);
      }
    });
    this.forEachCell(state.spikes, (x, y) => {
      context.drawImage(this.sprites.spikes, 4 * 48, 0, 48, 48, x * TILE, TOP_PAD + y * TILE, TILE, TILE);
    });
  }

  drawShadow(x, y, width = 30) {
    const context = this.context;
    const [centerX] = this.cellCenter(x, y);
    const bottom = TOP_PAD + y * TILE + TILE - 6;
    context.fillStyle = "rgba(0,0,0,0.32)";
    context.beginPath();
    context.ellipse(centerX, bottom, width / 2, 6, 0, 0, Math.PI * 2);
    context.fill();
  }

  drawStripFrame(strip, frameIndex, centerX, bottom, scale, flip = false) {
    const context = this.context;
    const frame = frameIndex % strip.count;
    const drawWidth = strip.frameWidth * scale;
    const drawHeight = strip.frameHeight * scale;
    context.save();
    context.translate(centerX, bottom);
    if (flip) context.scale(-1, 1);
    context.drawImage(
      strip.source, frame * strip.frameWidth, 0, strip.frameWidth, strip.frameHeight,
      -drawWidth / 2, -drawHeight, drawWidth, drawHeight,
    );
    context.restore();
  }

  drawGlow(x, y, color, radius = 26) {
    const context = this.context;
    const [centerX, centerY] = this.cellCenter(x, y);
    const glow = context.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius);
    glow.addColorStop(0, `${color}66`);
    glow.addColorStop(1, `${color}00`);
    context.fillStyle = glow;
    context.fillRect(centerX - radius, centerY - radius, radius * 2, radius * 2);
  }

  drawObjects() {
    const context = this.context;
    const state = this.state;
    const time = this.time;
    if (state.exit) {
      const { x, y } = state.exit;
      this.drawGlow(x, y, "#ffc94a", 34);
      this.drawShadow(x, y, 34);
      const [centerX] = this.cellCenter(x, y);
      this.drawStripFrame(this.sprites.trophy, Math.floor(time * 10), centerX, TOP_PAD + y * TILE + TILE - 2, 0.92);
    }
    this.forEachCell(state.doors.keys(), (x, y, key) => {
      const door = state.doors.get(key);
      const offset = door.shakeUntil > time ? Math.sin(time * 80) * 3 : 0;
      const image = door.type === "jammed" ? this.sprites.doorJammed : this.sprites.doorLocked;
      context.drawImage(image, x * TILE + offset, TOP_PAD + y * TILE);
      context.strokeStyle = door.type === "jammed" ? "rgba(251,146,60,0.8)" : "rgba(165,180,252,0.8)";
      context.lineWidth = 2;
      context.strokeRect(x * TILE + 3 + offset, TOP_PAD + y * TILE + 3, TILE - 6, TILE - 6);
    });
    this.forEachCell(state.locks, (x, y) => this.drawLock(x, y));
    this.forEachCell(state.chests.keys(), (x, y, key) => this.drawChest(x, y, state.chests.get(key).opened));
    this.forEachCell(state.keys, (x, y) => this.drawKey(x, y));
    this.forEachCell(state.crates.keys(), (x, y, key) => {
      this.drawShadow(x, y, 36);
      context.drawImage(this.sprites.crates[state.crates.get(key)], x * TILE, TOP_PAD + y * TILE, TILE, TILE);
    });
    this.forEachCell(state.gems.keys(), (x, y, key) => {
      const color = state.gems.get(key);
      this.drawGlow(x, y, GEM_GLOW[color] ?? "#ffffff");
      const [centerX] = this.cellCenter(x, y);
      const bob = Math.sin(time * 3 + x + y) * 3;
      this.drawShadow(x, y, 20);
      this.drawStripFrame(this.sprites.gems[color], Math.floor(time * 9), centerX, TOP_PAD + y * TILE + TILE - 8 + bob, 2.4);
    });
    const enemies = [...state.enemies.entries()].sort((first, second) => first[0].split(",")[1] - second[0].split(",")[1]);
    for (const [key, enemy] of enemies) {
      const [x, y] = key.split(",").map(Number);
      const sprites = this.sprites.enemies[enemy.kind];
      const isHit = enemy.hitUntil > time;
      const strip = isHit ? sprites.hit : sprites.idle;
      const [centerX] = this.cellCenter(x, y);
      this.drawShadow(x, y, enemy.kind === "duck" ? 56 : 34);
      context.save();
      if (enemy.dyingSince !== null) context.globalAlpha = Math.max(0, 1 - (time - enemy.dyingSince) * 3);
      this.drawStripFrame(strip, Math.floor(time * 12), centerX, TOP_PAD + y * TILE + TILE - 2, sprites.scale, true);
      context.restore();
    }
  }

  drawKey(x, y) {
    const context = this.context;
    const [centerX, centerY] = this.cellCenter(x, y);
    const bob = Math.sin(this.time * 3 + x) * 3;
    this.drawGlow(x, y, "#facc15", 24);
    context.save();
    context.translate(centerX, centerY + bob);
    context.rotate(-0.5);
    context.strokeStyle = "#7c5200";
    context.fillStyle = "#facc15";
    context.lineWidth = 2;
    context.beginPath();
    context.arc(-8, 0, 7, 0, Math.PI * 2);
    context.fill();
    context.stroke();
    context.fillRect(-2, -2.5, 18, 5);
    context.fillRect(10, 2, 3, 6);
    context.fillRect(15, 2, 3, 5);
    context.fillStyle = "#7c5200";
    context.beginPath();
    context.arc(-8, 0, 2.5, 0, Math.PI * 2);
    context.fill();
    context.restore();
  }

  drawLock(x, y) {
    const context = this.context;
    const left = x * TILE;
    const top = TOP_PAD + y * TILE;
    context.fillStyle = "#3b2f5c";
    context.fillRect(left + 2, top + 2, TILE - 4, TILE - 4);
    context.strokeStyle = "#8b7cf6";
    context.lineWidth = 2;
    context.strokeRect(left + 3, top + 3, TILE - 6, TILE - 6);
    const centerX = left + TILE / 2;
    context.strokeStyle = "#cbd5e1";
    context.lineWidth = 4;
    context.beginPath();
    context.arc(centerX, top + 20, 8, Math.PI, 0);
    context.stroke();
    context.fillStyle = "#facc15";
    context.fillRect(centerX - 12, top + 20, 24, 18);
    context.fillStyle = "#3b2f5c";
    context.beginPath();
    context.arc(centerX, top + 27, 3, 0, Math.PI * 2);
    context.fill();
    context.fillRect(centerX - 1.5, top + 28, 3, 6);
  }

  drawChest(x, y, opened) {
    const context = this.context;
    const left = x * TILE + 6;
    const top = TOP_PAD + y * TILE + 14;
    const width = TILE - 12;
    this.drawShadow(x, y, 38);
    if (!opened) this.drawGlow(x, y, "#ffc94a", 22);
    context.fillStyle = "#8a4b22";
    context.fillRect(left, top + 10, width, 20);
    context.fillStyle = opened ? "#5c3216" : "#a65d2b";
    if (opened) context.fillRect(left, top - 6, width, 10);
    else context.fillRect(left, top, width, 12);
    context.fillStyle = "#facc15";
    context.fillRect(left, top + 10, width, 3);
    context.fillRect(left + width / 2 - 3, top + 7, 6, 9);
    if (opened) {
      context.fillStyle = "#ffe08a";
      context.fillRect(left + 4, top + 6, width - 8, 5);
    }
  }

  drawHero() {
    const state = this.state;
    const hero = state.hero;
    const strips = this.sprites.hero;
    const direction = { right: [1, 0], left: [-1, 0], up: [0, -1], down: [0, 1] }[hero.facing] ?? [1, 0];
    const drawX = hero.x + direction[0] * hero.lunge;
    const drawY = hero.y + direction[1] * hero.lunge;
    const [centerX] = this.cellCenter(drawX, drawY);
    this.drawShadow(drawX, drawY, 30);
    const strip = strips[hero.animation] ?? strips.idle;
    const framesPerSecond = hero.animation === "run" ? 20 : 14;
    this.drawStripFrame(
      strip, Math.floor(this.time * framesPerSecond), centerX, TOP_PAD + drawY * TILE + TILE - 3, 1.9,
      hero.facing === "left",
    );
  }

  drawEffects() {
    const context = this.context;
    for (const particle of this.particles) {
      context.globalAlpha = Math.max(0, 1 - particle.age / particle.life);
      context.fillStyle = particle.color;
      context.fillRect(particle.x, particle.y, particle.size, particle.size);
    }
    context.globalAlpha = 1;
    context.textAlign = "center";
    context.font = "bold 16px 'Segoe UI', sans-serif";
    for (const floater of this.floaters) {
      const progress = floater.age / floater.life;
      context.globalAlpha = Math.max(0, 1 - progress);
      const y = floater.y - progress * 30;
      context.lineWidth = 4;
      context.strokeStyle = "rgba(0,0,0,0.65)";
      context.strokeText(floater.text, floater.x, y);
      context.fillStyle = floater.color;
      context.fillText(floater.text, floater.x, y);
    }
    context.globalAlpha = 1;
  }

  drawAmbient() {
    const context = this.context;
    const kind = this.theme?.ambient;
    for (const particle of this.ambient) {
      if (kind === "fireflies" || kind === "sparkle") {
        const glow = (Math.sin(particle.phase * 3) + 1) / 2;
        context.fillStyle = kind === "fireflies" ? `rgba(190,255,140,${0.25 + glow * 0.6})` : `rgba(230,210,255,${glow * 0.8})`;
        context.beginPath();
        context.arc(particle.x, particle.y, particle.size * (kind === "sparkle" ? glow : 1), 0, Math.PI * 2);
        context.fill();
      } else if (kind === "leaves") {
        context.fillStyle = "rgba(170, 220, 120, 0.55)";
        context.fillRect(particle.x, particle.y, particle.size * 2, particle.size);
      } else {
        context.fillStyle = kind === "snow" ? "rgba(255,255,255,0.8)" : "rgba(255, 220, 170, 0.35)";
        context.beginPath();
        context.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        context.fill();
      }
    }
  }

  drawBubble() {
    const bubble = this.state.bubble;
    if (!bubble || bubble.until < this.time) return;
    const context = this.context;
    const hero = this.state.hero;
    const [centerX] = this.cellCenter(hero.x, hero.y);
    const top = TOP_PAD + hero.y * TILE - 50;
    context.font = "600 15px 'Segoe UI', sans-serif";
    const text = bubble.text.length > 40 ? `${bubble.text.slice(0, 39)}…` : bubble.text;
    const width = context.measureText(text).width + 24;
    const left = Math.max(4, Math.min(this.canvas.width - width - 4, centerX - width / 2));
    const boxTop = Math.max(4, top);
    context.fillStyle = "rgba(255,255,255,0.96)";
    context.beginPath();
    context.roundRect(left, boxTop, width, 32, 10);
    context.fill();
    context.beginPath();
    context.moveTo(centerX - 7, boxTop + 31);
    context.lineTo(centerX + 7, boxTop + 31);
    context.lineTo(centerX, boxTop + 40);
    context.fill();
    context.fillStyle = "#1e1b4b";
    context.textAlign = "left";
    context.fillText(text, left + 12, boxTop + 21);
  }
}

window.MapView = MapView;
window.drawHeroAvatar = drawHeroAvatar;
