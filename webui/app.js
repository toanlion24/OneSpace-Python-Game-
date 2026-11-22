/* Điều khiển chính của giao diện web: menu, chọn nhân vật, cửa hàng, nhạc, màn chơi.
   Mọi việc chấm code / lưu tiến độ / mua bán do Python làm, gọi qua api(...). */

const TOKEN = new URLSearchParams(location.hash.slice(1)).get("token") ?? "";
const SPEEDS = [1, 2, 4];
const SAVE_DELAY_MILLISECONDS = 600;
const VOLUME_STEP = 10;
const AUTO_TRACK = -1;
const STAGE_COLORS = { 1: "#22d3ee", 2: "#34d399", 3: "#fb923c", 4: "#a78bfa", 5: "#f472b6" };
const EVENT_SOUNDS = {
  move: "step", gem: "gem", hurt: "hurt", door_open: "door", unlock: "door", shield: "shield",
  chest_open: "chest", key: "coin", box_break: "hit", fail: "fail", die: "fail",
};

const ICONS = {
  star: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.6l2.9 6 6.5.8-4.8 4.5 1.2 6.5L12 17.3l-5.8 3.1 1.2-6.5L2.6 9.4l6.5-.8z"/></svg>',
  coin: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="#ffc94a"/><circle cx="12" cy="12" r="6.2" fill="none" stroke="#b7791f" stroke-width="1.6"/><path d="M12 8.5v7" stroke="#b7791f" stroke-width="2" stroke-linecap="round"/></svg>',
  play: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15l12.5-7.5z"/></svg>',
  back: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>',
  next: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>',
  book: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2z"/><path d="M4 19V5"/><path d="M9 7h6"/></svg>',
  bulb: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 00-3.6 10.8c.7.6 1.1 1.3 1.1 2.2h5c0-.9.4-1.6 1.1-2.2A6 6 0 0012 3z"/></svg>',
  reset: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 109-9 9.7 9.7 0 00-6.7 2.8L3 8"/><path d="M3 3v5h5"/></svg>',
  copy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a1 1 0 01-1-1V4a1 1 0 011-1h10a1 1 0 011 1v1"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
  close: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>',
  skip: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M5 5v14l9-7zM14 5v14l9-7z"/></svg>',
  gem: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 3h10l4 6-9 12L3 9z"/></svg>',
  key: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="8" cy="12" r="4"/><path d="M12 12h9M18 12v3M21 12v2"/></svg>',
  music: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l11-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="17" cy="16" r="3"/></svg>',
  mute: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 5L6 9H2v6h4l5 4z"/><path d="M23 9l-6 6M17 9l6 6"/></svg>',
  shop: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l1.5-5h15L21 9"/><path d="M4 9v11h16V9"/><path d="M3 9h18"/><path d="M9 20v-6h6v6"/></svg>',
  user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0116 0"/></svg>',
  save: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M7 10l5 5 5-5"/><path d="M4 17v3h16v-3"/></svg>',
  upload: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V3M7 8l5-5 5 5"/><path d="M4 17v3h16v-3"/></svg>',
  heart: '<svg viewBox="0 0 24 24" fill="#fb7185"><path d="M12 21s-7.5-4.6-9.6-9.3C.8 8 3 4 6.8 4c2.2 0 3.6 1.2 5.2 3 1.6-1.8 3-3 5.2-3C21 4 23.2 8 21.6 11.7 19.5 16.4 12 21 12 21z"/></svg>',
  shield: '<svg viewBox="0 0 24 24"><path d="M12 2l8 3v6c0 5-3.4 9.4-8 11-4.6-1.6-8-6-8-11V5z" fill="#b7793f" stroke="#fde68a" stroke-width="1.5"/><path d="M12 5v14" stroke="#fde68a" stroke-width="1.5"/></svg>',
  lock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 018 0v4"/></svg>',
};

const appRoot = document.getElementById("app");
const audio = window.audioBoard;
const state = {
  data: null,
  completions: null,
  stage: 1,
  level: null,
  editor: null,
  map: null,
  running: false,
  speedIndex: 0,
  hintIndex: 0,
  saveTimer: null,
  settingsTimer: null,
  resizeObserver: null,
  spriteLoop: null,
};

// ------------------------------------------------------------ helpers
async function apiResponse(method, args) {
  const response = await fetch(`/api/${method}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Game-Token": TOKEN },
    body: JSON.stringify(args),
  });
  if (!response.ok) throw new Error(`Lỗi máy chủ game (${response.status})`);
  return response;
}

async function api(method, ...args) {
  return (await apiResponse(method, args)).json();
}

async function apiBytes(method, ...args) {
  return (await apiResponse(method, args)).arrayBuffer();
}

function richText(text) {
  return escapeHtml(text).replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
}

function starIcons(count, total = 3) {
  return Array.from({ length: total }, (_unused, index) =>
    ICONS.star.replace("<svg", `<svg class="star ${index < count ? "on" : ""}"`)).join("");
}

function toast(text, kind = "") {
  const element = document.createElement("div");
  element.className = `toast ${kind}`;
  element.textContent = text;
  document.getElementById("toasts").append(element);
  setTimeout(() => element.remove(), kind.includes("long") ? 6000 : 2800);
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const helper = document.createElement("textarea");
    helper.value = text;
    document.body.append(helper);
    helper.select();
    document.execCommand("copy");
    helper.remove();
  }
}

function worldOfLevel(levelId) {
  return state.data.worlds.find((world) => world.levels.some((level) => level.id === levelId));
}

function stopSpriteLoop() {
  if (state.spriteLoop) cancelAnimationFrame(state.spriteLoop);
  state.spriteLoop = null;
}

function teardownScreen() {
  state.map?.destroy();
  state.map = null;
  state.editor = null;
  state.resizeObserver?.disconnect();
  clearTimeout(state.saveTimer);
  stopSpriteLoop();
  document.querySelectorAll(".modal-backdrop").forEach((element) => element.remove());
}

function bindClicks(root, selector, handler) {
  root.querySelectorAll(selector).forEach((element) => {
    element.addEventListener("click", (event) => {
      audio.play("click");
      handler(element, event);
    });
  });
}

function musicLabel() {
  const volume = state.data.settings.musicVolume;
  return volume === 0 ? "Nhạc: Tắt" : `Nhạc: ${volume}%`;
}

function musicTrackFor(level) {
  const chosen = state.data.settings.musicTrack;
  if (chosen !== AUTO_TRACK) return chosen;
  return level ? level.musicTrack : 0;
}

/* Hoạt ảnh nhân vật cho các thẻ trong menu, màn chọn nhân vật và cửa hàng. */
async function animateHeroCanvases(root) {
  const canvases = [...root.querySelectorAll("canvas[data-hero]")];
  const entries = await Promise.all(canvases.map(async (canvas) => {
    const hero = JSON.parse(decodeURIComponent(canvas.dataset.hero));
    return { canvas, strips: await loadHeroStrips(hero), state: canvas.dataset.state ?? "idle", dim: canvas.dataset.dim === "1" };
  }));
  stopSpriteLoop();
  const start = performance.now();
  const frame = (now) => {
    const time = (now - start) / 1000;
    for (const entry of entries) {
      if (!entry.canvas.isConnected) continue;
      const strip = entry.strips[entry.canvas.dataset.state ?? entry.state] ?? entry.strips.idle;
      const context = entry.canvas.getContext("2d");
      context.imageSmoothingEnabled = false;
      context.clearRect(0, 0, entry.canvas.width, entry.canvas.height);
      const index = Math.floor(time * 12) % strip.count;
      context.filter = entry.dim ? "brightness(0.35) saturate(0.4)" : "none";
      context.drawImage(strip.source, index * 32, 0, 32, 32, 0, 0, entry.canvas.width, entry.canvas.height);
    }
    state.spriteLoop = requestAnimationFrame(frame);
  };
  state.spriteLoop = requestAnimationFrame(frame);
}

function heroCanvas(hero, size, { animationState = "idle", dim = false } = {}) {
  const data = encodeURIComponent(JSON.stringify({ base: hero.base, recolor: hero.recolor }));
  return `<canvas class="pixel" width="${size}" height="${size}" data-hero="${data}" data-state="${animationState}" data-dim="${dim ? 1 : 0}"></canvas>`;
}

// ------------------------------------------------------------ start
async function boot() {
  appRoot.innerHTML = '<div class="loading"><div><div class="spinner"></div>Đang mở CodeQuest...</div></div>';
  const [data, completions] = await Promise.all([api("bootstrap"), api("completions")]);
  state.data = data;
  state.completions = completions;
  audio.fetchTrack = (index) => apiBytes("music", index);
  audio.setEffectVolume(data.settings.sfxVolume);
  audio.setMusicVolume(data.settings.musicVolume);
  audio.selectTrack(musicTrackFor(null));
  if (data.restoredFromBackup) toast("Đã tự khôi phục tiến độ từ bản sao lưu trong Documents.", "long");
  if (!data.player.heroPicked) await showHeroes(true);
  else await showMenu();
}

async function refreshData() {
  state.data = await api("bootstrap");
}

// ------------------------------------------------------------ menu
async function showMenu() {
  teardownScreen();
  await refreshData();
  if (!state.level) state.stage = worldOfLevel(state.data.continueLevel).stage;
  audio.selectTrack(musicTrackFor(null));
  renderMenu();
}

function renderMenu() {
  const { player, stages, worlds, continueLevel } = state.data;
  const continueWorld = worldOfLevel(continueLevel);
  const continueInfo = continueWorld.levels.find((level) => level.id === continueLevel);
  const percent = Math.round((player.stars / player.maxStars) * 100);
  const nextRankText = player.nextRank ? `còn ${player.nextRank - player.stars} sao tới cấp tiếp` : "cấp cao nhất!";
  const stage = stages[state.stage - 1];
  const stageCounts = stages.map((item) => {
    const levels = worlds.filter((world) => world.stage === item.number).flatMap((world) => world.levels);
    return [levels.filter((level) => level.done).length, levels.length];
  });
  appRoot.innerHTML = `
    <div class="menu">
      <div class="menu-inner">
        <header class="topbar">
          <div class="brand">
            <img src="../assets/onespace_logo.png" alt="">
            <div>
              <div class="brand-title">Code<span>Quest</span></div>
              <div class="brand-sub">Học Python qua trò chơi</div>
            </div>
          </div>
          <div class="spacer"></div>
          <div class="tool-row">
            <button class="button small" data-action="shop">${ICONS.shop}<span class="label-text">Cửa hàng &amp; Huy hiệu</span></button>
            <button class="button small" data-action="music">${state.data.settings.musicVolume ? ICONS.music : ICONS.mute}<span class="label-text">${musicLabel()}</span></button>
            <button class="button small" data-action="backup" title="Lưu bản sao tiến độ vào Documents">${ICONS.save}<span class="label-text">Sao lưu</span></button>
            <button class="button small" data-action="restore" title="Lấy lại tiến độ từ bản sao lưu">${ICONS.upload}<span class="label-text">Khôi phục</span></button>
          </div>
          <span class="chip gold">${ICONS.star} ${player.stars}</span>
          <span class="chip gold">${ICONS.coin} ${player.coins} xu</span>
          <button class="hero-avatar" data-action="heroes" title="Đổi nhân vật">
            ${heroCanvas(player.hero, 34)}
            <div><div class="name">${escapeHtml(player.hero.name)}</div><div class="rank">${escapeHtml(player.rank)}</div></div>
          </button>
        </header>

        <section class="continue-card glass">
          <div>
            <div class="eyebrow">Tiếp tục hành trình</div>
            <h1>Màn ${continueLevel} · ${escapeHtml(continueInfo.title)}</h1>
            <p>World ${continueWorld.number}: ${escapeHtml(continueWorld.title)} — ${escapeHtml(continueWorld.concept)}</p>
            <div class="progress-row">
              <div class="progress-bar"><div style="width:${percent}%"></div></div>
              <span class="label">${player.completed}/${state.data.worlds.reduce((sum, world) => sum + world.levels.length, 0)} màn · ${escapeHtml(player.rank)} · ${escapeHtml(nextRankText)}</span>
            </div>
          </div>
          <button class="button primary" data-level="${continueLevel}">${ICONS.play} Chơi tiếp</button>
        </section>

        <nav class="stage-tabs">
          ${stages.map((item, index) => `
            <button class="stage-tab ${item.number === state.stage ? "active" : ""}" data-stage="${item.number}" style="--stage-color:${STAGE_COLORS[item.number]}">
              <span class="number">Giai đoạn ${item.number} · ${stageCounts[index][0]}/${stageCounts[index][1]}</span>
              <span class="title">${escapeHtml(item.title)}</span>
            </button>`).join("")}
        </nav>
        <p class="stage-skills">${escapeHtml(stage.skills)}</p>

        <section class="world-grid">
          ${worlds.filter((world) => world.stage === state.stage).map((world) => renderWorldCard(world, continueLevel)).join("")}
        </section>
      </div>
    </div>`;
  animateHeroCanvases(appRoot);
  bindClicks(appRoot, "[data-level]", (element) => openLevel(element.dataset.level));
  bindClicks(appRoot, "[data-stage]", (element) => {
    state.stage = Number(element.dataset.stage);
    renderMenu();
  });
  bindClicks(appRoot, "[data-action]", (element) => {
    const action = element.dataset.action;
    if (action === "shop") showCollection();
    else if (action === "heroes") showHeroes(false);
    else if (action === "music") openMusicPanel();
    else if (action === "backup") backupProgress();
    else if (action === "restore") restoreProgress();
  });
}

function renderWorldCard(world, continueLevel) {
  const stars = world.levels.reduce((sum, level) => sum + level.stars, 0);
  const backdrop = world.theme.backdrop.join(",");
  return `
    <article class="world-card glass ${world.chestOpened ? "cleared" : ""}">
      <div class="backdrop" style="background: linear-gradient(180deg, rgba(${backdrop},0.95), transparent)"></div>
      <div class="world-head">
        <div class="world-badge" style="--stage-color:${STAGE_COLORS[world.stage]}">${world.number}</div>
        <div>
          <h3>${escapeHtml(world.title)}</h3>
          <div class="concept">${escapeHtml(world.concept)}</div>
        </div>
        <div class="world-stars">${world.chestOpened ? '<span class="medal-mini" title="Đã nhận huy hiệu">🏅</span>' : ""}${ICONS.star} ${stars}/${world.levels.length * 3}</div>
      </div>
      <div class="level-list">
        ${world.levels.map((level) => `
          <button class="level-node ${level.done ? "done" : ""} ${level.challenge ? "challenge" : ""} ${level.id === continueLevel ? "next" : ""}"
                  data-level="${level.id}" title="${escapeHtml(level.title)}${level.challenge ? " (Thử thách)" : ""}">
            <span class="id">${level.id}</span>
            <span class="stars">${starIcons(level.stars)}</span>
          </button>`).join("")}
      </div>
    </article>`;
}

async function backupProgress() {
  saveNow();
  const result = await api("backup");
  toast(result.message, result.ok ? "long good" : "long");
}

async function restoreProgress() {
  const result = await api("restore");
  toast(result.message, result.ok ? "long good" : "long");
  if (result.ok) await showMenu();
}

// ------------------------------------------------------------ heroes
async function showHeroes(firstTime) {
  teardownScreen();
  const collection = await api("collection");
  const current = collection.heroes.find((hero) => hero.selected) ?? collection.heroes[0];
  appRoot.innerHTML = `
    <div class="page">
      <div class="page-inner">
        <header class="page-head">
          ${firstTime ? "" : `<button class="button icon" data-action="back" title="Về menu">${ICONS.back}</button>`}
          <div>
            <h1>Chọn nhân vật của em</h1>
            <p>Bấm vào một nhân vật để chọn. Nhân vật hiếm mở khoá bằng xu kiếm được khi qua màn.</p>
          </div>
          <div class="spacer"></div>
          <span class="chip gold">${ICONS.coin} ${collection.player.coins} xu</span>
        </header>
        <div class="hero-layout">
          <div class="hero-grid">
            ${collection.heroes.map((hero) => `
              <button class="hero-card glass ${hero.selected ? "selected" : ""} ${hero.owned ? "" : "locked"} ${hero.price ? "rare" : ""}" data-hero-number="${hero.number}">
                ${heroCanvas(hero, 96, { animationState: hero.selected ? "run" : "idle", dim: !hero.owned })}
                <span class="hero-name">${escapeHtml(hero.name)}</span>
                <span class="hero-status">${heroStatus(hero)}</span>
              </button>`).join("")}
          </div>
          <aside class="hero-preview glass">
            <canvas id="hero-stage" width="360" height="220" class="pixel"></canvas>
            <h2>${escapeHtml(current.name)}</h2>
            <p>${escapeHtml(current.description)}</p>
            <button class="button primary wide" data-action="done">${firstTime ? "Bắt đầu chơi" : "Xong"} ${ICONS.next}</button>
          </aside>
        </div>
      </div>
    </div>`;
  animateHeroCanvases(appRoot);
  drawHeroStage(document.getElementById("hero-stage"), current);
  bindClicks(appRoot, "[data-hero-number]", async (element) => {
    const result = await api("choose_hero", Number(element.dataset.heroNumber));
    if (result.sound) audio.play(result.sound);
    if (!result.ok) {
      audio.play("fail");
      toast(result.message, "long");
      return;
    }
    if (result.sound === "coin") toast(result.message, "good");
    showHeroes(firstTime);
  });
  bindClicks(appRoot, "[data-action]", async (element) => {
    if (element.dataset.action === "done" || element.dataset.action === "back") {
      await api("finish_hero_pick");
      showMenu();
    }
  });
}

function heroStatus(hero) {
  if (hero.selected) return "Đang dùng";
  if (hero.owned) return hero.price ? "Đã mở khoá" : "Miễn phí";
  return `${ICONS.lock} Hiếm · ${hero.price} xu`;
}

async function drawHeroStage(canvas, hero) {
  const strips = await loadHeroStrips(hero);
  const tileset = await loadImage("2 Locations/Tiles/Tileset.png");
  const themes = state.data.themes;
  const tiles = themes.map((theme) => [
    tintedTile(tileset, theme.floor[0], theme.floor[1], theme.floorMultiply, theme.add),
    tintedTile(tileset, theme.wall[0], theme.wall[1], theme.wallMultiply, theme.add),
  ]);
  const context = canvas.getContext("2d");
  const start = performance.now();
  const draw = (now) => {
    if (!canvas.isConnected) return;
    const time = (now - start) / 1000;
    const themeIndex = Math.floor(time / 3) % themes.length;
    const theme = themes[themeIndex];
    const [floor, wall] = tiles[themeIndex];
    context.imageSmoothingEnabled = false;
    context.fillStyle = `rgb(${theme.backdrop.join(",")})`;
    context.fillRect(0, 0, canvas.width, canvas.height);
    for (let x = 0; x < canvas.width; x += 48) {
      context.drawImage(floor, x, 124);
      context.drawImage(wall, x, 172);
    }
    const running = Math.floor(time) % 4 < 2;
    const strip = running ? strips.run : strips.idle;
    const frame = Math.floor(time * 14) % strip.count;
    context.drawImage(strip.source, frame * 32, 0, 32, 32, canvas.width / 2 - 64, 20, 128, 128);
    context.fillStyle = "rgba(255,255,255,0.75)";
    context.font = "600 13px 'Segoe UI', sans-serif";
    context.fillText(`Bản đồ: ${theme.name}`, 12, 20);
    requestAnimationFrame(draw);
  };
  requestAnimationFrame(draw);
}

// ------------------------------------------------------------ collection and shop
async function showCollection() {
  teardownScreen();
  const collection = await api("collection");
  const player = collection.player;
  const rankSpan = player.nextRank ? player.nextRank - player.rankStart : 1;
  const rankFill = player.nextRank ? ((player.stars - player.rankStart) / rankSpan) * 100 : 100;
  appRoot.innerHTML = `
    <div class="page">
      <div class="page-inner">
        <header class="page-head">
          <button class="button icon" data-action="back" title="Về menu">${ICONS.back}</button>
          <div>
            <h1>Bộ sưu tập &amp; Cửa hàng</h1>
            <p>Qua màn để nhận sao và xu. Qua hết một World để mở rương và nhận huy hiệu.</p>
          </div>
          <div class="spacer"></div>
          <span class="chip gold">${ICONS.star} ${player.stars}/${player.maxStars}</span>
          <span class="chip gold">${ICONS.coin} ${player.coins} xu</span>
        </header>
        <div class="collection-layout">
          <div class="collection-left">
            <section class="rank-card glass">
              <div class="eyebrow">Cấp bậc</div>
              <h2>${escapeHtml(player.rank)}</h2>
              <div class="progress-bar"><div style="width:${rankFill}%"></div></div>
              <p>${player.nextRank ? `Còn ${player.nextRank - player.stars} sao để lên cấp tiếp theo` : "Cấp bậc cao nhất!"}</p>
              <div class="rank-steps">
                ${collection.ranks.map((rank) => `<span class="${player.stars >= rank.stars ? "on" : ""}">${escapeHtml(rank.name)}<small>${rank.stars} sao</small></span>`).join("")}
              </div>
            </section>
            <section class="badges glass">
              <h3>Huy hiệu World <small>${collection.badges.filter((badge) => badge.earned).length}/${collection.badges.length}</small></h3>
              <div class="badge-grid">
                ${collection.badges.map((badge) => `
                  <div class="badge ${badge.earned ? "earned" : ""}" style="--stage-color:${STAGE_COLORS[badge.stage]}" title="World ${badge.number}: ${escapeHtml(badge.title)}">
                    <div class="medal">${badge.number}</div>
                    <span>${escapeHtml(badge.title)}</span>
                  </div>`).join("")}
              </div>
            </section>
          </div>
          <section class="shop glass">
            <h3>Cửa hàng</h3>
            <div class="shop-list">
              ${collection.items.map(renderShopItem).join("")}
            </div>
          </section>
        </div>
      </div>
    </div>`;
  animateHeroCanvases(appRoot);
  bindClicks(appRoot, '[data-action="back"]', () => showMenu());
  bindClicks(appRoot, "[data-buy]", async (element) => {
    const result = await api("buy_item", element.dataset.buy);
    if (!result.ok) {
      audio.play("fail");
      toast(result.message, "long");
      return;
    }
    audio.play("coin");
    toast(result.message, "good");
    showCollection();
  });
  bindClicks(appRoot, "[data-equip]", async (element) => {
    await api("choose_hero", Number(element.dataset.equip));
    showCollection();
  });
}

function renderShopItem(item) {
  let icon = ICONS.shield;
  if (item.kind === "skin") icon = heroCanvas(item.hero, 64);
  else if (item.kind === "heart") icon = ICONS.heart;
  let action;
  if (item.kind === "skin" && item.owned) {
    action = item.selected
      ? '<button class="button small" disabled>Đang dùng</button>'
      : `<button class="button small" data-equip="${item.hero.number}">Dùng</button>`;
  } else if (item.owned) {
    action = `<button class="button small" disabled>${ICONS.check} Đã có</button>`;
  } else {
    action = `<button class="button small ${item.canBuy ? "gold" : ""}" data-buy="${item.id}" title="${escapeHtml(item.reason)}">${ICONS.coin} ${item.price}</button>`;
  }
  return `
    <div class="shop-item">
      <div class="shop-icon">${icon}</div>
      <div class="shop-text">
        <b>${escapeHtml(item.name)}</b>
        <span>${escapeHtml(item.description)}</span>
        ${!item.owned && !item.canBuy ? `<small>${escapeHtml(item.reason)}</small>` : ""}
      </div>
      ${action}
    </div>`;
}

// ------------------------------------------------------------ music panel
function openMusicPanel() {
  document.querySelector(".music-panel")?.closest(".modal-backdrop")?.remove();
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  document.body.append(backdrop);
  const render = () => {
    const settings = state.data.settings;
    const playingIndex = audio.wantedTrack ?? 0;
    const track = state.data.tracks[playingIndex];
    let status = `Đang phát: ${track.name} (${track.genre})`;
    if (settings.musicVolume === 0) status = "Nhạc đang tắt (âm lượng 0%)";
    else if (audio.isLoading) status = `Đang soạn nhạc: ${track.name} (${track.genre})...`;
    backdrop.innerHTML = `
      <div class="modal music-panel glass">
        <div class="music-head">
          <h2>${ICONS.music} Nhạc nền</h2>
          <button class="button small icon" data-music="close" title="Đóng">${ICONS.close}</button>
        </div>
        <p class="music-status ${audio.isLoading ? "loading" : ""}">${escapeHtml(status)}</p>
        ${volumeRow("Âm lượng nhạc", "music", settings.musicVolume)}
        ${volumeRow("Âm lượng hiệu ứng", "sfx", settings.sfxVolume)}
        <h3>Chọn bài</h3>
        <button class="track auto ${settings.musicTrack === AUTO_TRACK ? "selected" : ""}" data-track="${AUTO_TRACK}">
          <b>Tự động</b><span>Menu một bài, mỗi World một bài khác</span>
        </button>
        <div class="track-grid">
          ${state.data.tracks.map((item, index) => `
            <button class="track ${settings.musicTrack === index ? "selected" : ""} ${audio.playingTrack === index ? "playing" : ""}" data-track="${index}">
              <span class="genre">${escapeHtml(item.genre)}</span><b>${escapeHtml(item.name)}</b>
            </button>`).join("")}
        </div>
      </div>`;
    backdrop.querySelectorAll("input[type=range]").forEach((slider) => {
      slider.addEventListener("input", () => setVolume(slider.dataset.volume, Number(slider.value), false));
      slider.addEventListener("change", () => render());
    });
    bindClicks(backdrop, "[data-step]", (element) => {
      const kind = element.dataset.volumeKind;
      const current = kind === "music" ? state.data.settings.musicVolume : state.data.settings.sfxVolume;
      setVolume(kind, current + Number(element.dataset.step), true);
      render();
    });
    bindClicks(backdrop, "[data-track]", (element) => {
      const index = Number(element.dataset.track);
      state.data.settings.musicTrack = index;
      if (state.data.settings.musicVolume === 0) setVolume("music", 40, true);
      audio.selectTrack(musicTrackFor(state.level && state.map ? state.level : null));
      persistSettings();
      render();
    });
    bindClicks(backdrop, '[data-music="close"]', () => closeMusicPanel(backdrop));
  };
  audio.onChange = () => {
    if (backdrop.isConnected && !backdrop.querySelector("input:active")) render();
  };
  backdrop.addEventListener("click", (event) => {
    if (event.target === backdrop) closeMusicPanel(backdrop);
  });
  render();
}

function closeMusicPanel(backdrop) {
  backdrop.remove();
  audio.onChange = null;
  const menuButton = appRoot.querySelector('[data-action="music"]');
  if (menuButton) menuButton.innerHTML = `${state.data.settings.musicVolume ? ICONS.music : ICONS.mute}<span class="label-text">${musicLabel()}</span>`;
}

function volumeRow(label, kind, value) {
  return `
    <div class="volume-row">
      <span class="volume-label">${label}</span>
      <button class="button small icon" data-step="-${VOLUME_STEP}" data-volume-kind="${kind}">−</button>
      <input type="range" min="0" max="100" step="1" value="${value}" data-volume="${kind}" style="--fill:${value}%">
      <button class="button small icon" data-step="${VOLUME_STEP}" data-volume-kind="${kind}">+</button>
      <span class="volume-value" id="volume-${kind}">${value}%</span>
    </div>`;
}

function setVolume(kind, value, playSample) {
  const percent = Math.max(0, Math.min(100, Math.round(value)));
  if (kind === "music") {
    state.data.settings.musicVolume = percent;
    audio.setMusicVolume(percent);
  } else {
    state.data.settings.sfxVolume = percent;
    audio.setEffectVolume(percent);
    if (playSample) audio.play("coin");
  }
  const label = document.getElementById(`volume-${kind}`);
  if (label) label.textContent = `${percent}%`;
  const slider = document.querySelector(`input[data-volume="${kind}"]`);
  if (slider) slider.style.setProperty("--fill", `${percent}%`);
  persistSettings();
}

function persistSettings() {
  clearTimeout(state.settingsTimer);
  state.settingsTimer = setTimeout(() => {
    const { musicVolume, sfxVolume, musicTrack } = state.data.settings;
    api("save_settings", musicVolume, sfxVolume, musicTrack);
  }, 300);
}

// ------------------------------------------------------------ play screen
async function openLevel(levelId) {
  teardownScreen();
  if (!state.data) await refreshData();
  const level = await api("level", levelId);
  state.level = level;
  state.hintIndex = 0;
  state.running = false;
  state.stage = level.stage.number;
  audio.selectTrack(musicTrackFor(level));
  renderPlay(level);
}

function renderPlay(level) {
  appRoot.innerHTML = `
    <div class="play">
      <header class="play-topbar">
        <button class="button icon" id="back" title="Về menu">${ICONS.back}</button>
        <div class="crumbs">
          <div class="path">GIAI ĐOẠN ${level.stage.number} · WORLD ${level.world.number}: ${escapeHtml(level.world.title.toUpperCase())}</div>
          <div class="title">Màn ${level.id} · ${escapeHtml(level.title)}</div>
        </div>
        <div class="star-goals">
          ${level.starGoals.map((goal, index) => `
            <span class="star-goal ${index < level.bestStars ? "on" : ""}">${starIcons(index < level.bestStars ? 1 : 0, 1)}<span class="text">${escapeHtml(goal)}</span></span>`).join("")}
        </div>
        <span class="chip gold" id="coins">${ICONS.coin} ${state.data.player.coins}</span>
        <button class="button icon" id="music" title="Nhạc nền">${state.data.settings.musicVolume ? ICONS.music : ICONS.mute}</button>
        <button class="button" id="theory-toggle">${ICONS.book} Lý thuyết</button>
      </header>

      <div class="play-body">
        <section class="play-left">
          <div class="mission glass">
            <div class="story">${richText(level.story)}</div>
            <div class="actions">
              <button class="button small" id="hint">${ICONS.bulb} Gợi ý</button>
            </div>
            <div class="goal"><b>Nhiệm vụ:</b> ${richText(level.goal)}</div>
          </div>
          <div class="map-stage glass" id="map-stage">
            <canvas id="map"></canvas>
            <div class="vignette"></div>
            <div class="map-hud">
              <span class="chip hearts" id="hearts"></span>
              ${level.shield ? `<span class="chip" id="shield" title="Khiên gỗ đỡ đòn đầu tiên">${ICONS.shield}</span>` : ""}
              <span class="chip" id="gems">${ICONS.gem} 0</span>
              <span class="chip" id="keys" hidden>${ICONS.key} 0</span>
            </div>
            <div class="map-tools">
              <button class="button" id="speed">Tốc độ x${SPEEDS[state.speedIndex]}</button>
              <button class="button" id="skip" title="Tua tới cuối">${ICONS.skip}</button>
            </div>
            <div class="map-banner" id="banner" hidden></div>
          </div>
          <div class="console glass">
            <div class="console-head"><span class="dot"></span>Bảng tin</div>
            <div class="console-body" id="console"></div>
          </div>
          ${renderTheory(level)}
        </section>

        <section class="play-right glass">
          <div class="editor-head">
            <div class="file-tab"><span class="dot"></span>main.py</div>
            <div class="spacer"></div>
            <button class="button small ghost" id="reset">${ICONS.reset} Code ban đầu</button>
          </div>
          <div id="editor" style="flex:1; min-height:0; display:flex; flex-direction:column"></div>
          <div class="editor-foot">
            <button class="button run" id="run">${ICONS.play} Chạy code</button>
            <span class="hint-text"><span class="kbd">Ctrl</span> + <span class="kbd">Enter</span> chạy · <span class="kbd">Ctrl</span> + <span class="kbd">Space</span> gợi ý lệnh · <span class="kbd">Ctrl</span> + <span class="kbd">/</span> ghi chú</span>
          </div>
        </section>
      </div>
    </div>`;

  state.editor = new CodeEditor(document.getElementById("editor"), {
    onRun: runCode,
    onChange: scheduleSave,
    completionData: state.completions,
    extraNames: level.inputNames,
  });
  state.editor.setValue(level.code);

  state.map = new MapView(document.getElementById("map"));
  state.map.speed = SPEEDS[state.speedIndex];
  state.map.setup({ rows: level.rows, theme: level.theme, hero: state.data.player.hero, hp: level.hp, maxHp: level.maxHp })
    .then(() => updateHud(state.map?.state));
  state.resizeObserver = new ResizeObserver(() => state.map?.fit());
  state.resizeObserver.observe(document.getElementById("map-stage"));

  logLine(`Màn ${level.id}: ${level.title}`, "accent");
  logLine("Viết code bên phải rồi bấm Chạy code (Ctrl + Enter). Gõ tiếng Việt bằng Unikey bình thường.", "muted");

  document.getElementById("back").addEventListener("click", goMenu);
  document.getElementById("run").addEventListener("click", runCode);
  document.getElementById("hint").addEventListener("click", showHint);
  document.getElementById("reset").addEventListener("click", resetCode);
  document.getElementById("speed").addEventListener("click", toggleSpeed);
  document.getElementById("skip").addEventListener("click", () => state.map?.skip());
  document.getElementById("music").addEventListener("click", openMusicPanel);
  document.getElementById("theory-toggle").addEventListener("click", () => setTheoryOpen(!isTheoryOpen()));
  bindTheory();
  setTheoryOpen(!level.completed);
  if (level.completed) state.editor.focus();
}

function goMenu() {
  saveNow();
  audio.play("click");
  showMenu();
}

function scheduleSave() {
  clearTimeout(state.saveTimer);
  state.saveTimer = setTimeout(saveNow, SAVE_DELAY_MILLISECONDS);
}

function saveNow() {
  clearTimeout(state.saveTimer);
  if (state.level && state.editor) api("save_code", state.level.id, state.editor.getValue());
}

function logLine(text, kind = "") {
  const consoleBody = document.getElementById("console");
  if (!consoleBody) return;
  const line = document.createElement("div");
  line.className = `log ${kind}`;
  line.textContent = text;
  consoleBody.append(line);
  consoleBody.scrollTop = consoleBody.scrollHeight;
}

function clearLog() {
  const consoleBody = document.getElementById("console");
  if (consoleBody) consoleBody.innerHTML = "";
}

function updateHud(mapState) {
  if (!mapState || !state.level) return;
  const hearts = document.getElementById("hearts");
  if (!hearts) return;
  const maxHp = Math.max(state.level.maxHp, mapState.hp);
  hearts.textContent = "♥".repeat(Math.max(0, mapState.hp)) + "♡".repeat(Math.max(0, maxHp - mapState.hp));
  document.getElementById("gems").innerHTML = `${ICONS.gem} ${mapState.gemCount}`;
  const keys = document.getElementById("keys");
  keys.hidden = mapState.keyCount === 0 && mapState.keys.size === 0;
  keys.innerHTML = `${ICONS.key} ${mapState.keyCount}`;
  const shield = document.getElementById("shield");
  if (shield) shield.classList.toggle("used", Boolean(mapState.shieldUsed));
}

function showHint() {
  const hints = state.level.hints;
  if (!hints.length) return;
  audio.play("click");
  const index = Math.min(state.hintIndex, hints.length - 1);
  logLine(`Gợi ý ${index + 1}/${hints.length}: ${hints[index]}`, "accent");
  state.hintIndex += 1;
}

function resetCode() {
  const textarea = state.editor.textarea;
  textarea.focus();
  textarea.select();
  document.execCommand("insertText", false, state.level.starter);
  toast("Đã khôi phục code ban đầu (Ctrl + Z để hoàn tác)");
}

function toggleSpeed() {
  audio.play("click");
  state.speedIndex = (state.speedIndex + 1) % SPEEDS.length;
  const speed = SPEEDS[state.speedIndex];
  state.map.speed = speed;
  document.getElementById("speed").textContent = `Tốc độ x${speed}`;
}

function showBanner(text) {
  const banner = document.getElementById("banner");
  if (!banner) return;
  banner.hidden = !text;
  banner.textContent = text ?? "";
}

function playEventSound(event) {
  if (event.type === "attack") {
    audio.play(event.hit ? "hit" : "step");
    return;
  }
  const sound = EVENT_SOUNDS[event.type];
  if (sound) audio.play(sound);
}

async function runCode() {
  if (state.running || !state.map) return;
  state.running = true;
  state.editor.closeSuggestions();
  const runButton = document.getElementById("run");
  runButton.disabled = true;
  runButton.innerHTML = `${ICONS.play} Đang chạy...`;
  setTheoryOpen(false);
  clearLog();
  showBanner(null);
  state.editor.setErrorLine(null);
  logLine("Đang chạy...", "muted");
  const level = state.level;
  let result;
  try {
    result = await api("run", level.id, state.editor.getValue());
  } catch (error) {
    logLine(String(error), "bad");
    finishRun();
    return;
  }
  if (state.level !== level || !state.map) return;
  state.map.setRows(level.rows);
  const callbacks = { onLog: logLine, onState: updateHud, onEvent: playEventSound };
  state.map.play(result.events, {
    ...callbacks,
    onDone: () => {
      if (!result.hidden) {
        showResult(result, result.errorLine);
        return;
      }
      logLine("Bản đồ chính: đi đúng!", "good");
      logLine(`Thử tiếp code trên bản đồ kiểm tra ẩn ${result.hidden.index}...`, "info");
      showBanner(`Bản đồ kiểm tra ẩn ${result.hidden.index}`);
      setTimeout(() => {
        if (!state.map) return;
        state.map.setRows(result.hidden.rows);
        state.map.play(result.hidden.events, { ...callbacks, onDone: () => showResult(result, result.hidden.errorLine) });
      }, 700);
    },
  });
}

function finishRun() {
  state.running = false;
  const runButton = document.getElementById("run");
  if (runButton) {
    runButton.disabled = false;
    runButton.innerHTML = `${ICONS.play} Chạy code`;
  }
}

function showResult(result, errorLine) {
  finishRun();
  if (!result.won) {
    audio.play("fail");
    logLine(`✗ ${result.message}`, "bad");
    if (errorLine) state.editor.setErrorLine(errorLine);
    return;
  }
  logLine(`✓ ${result.message}`, "good");
  if (result.hiddenPassed) logLine(`Code còn đúng trên cả ${result.hiddenPassed} bản đồ kiểm tra ẩn!`, "good");
  const reward = result.reward;
  if (!reward.stars[1]) logLine(`Sao 2: thử qua màn mà không mất máu (vừa mất ${result.damageTaken}).`, "info");
  if (!reward.stars[2]) logLine(`Sao 3: code đang có ${result.codeLines} dòng - thử rút gọn còn tối đa ${state.level.par} dòng.`, "info");
  if (reward.coins) logLine(`Nhận ${reward.coins} xu!`, "accent");
  state.data.player.coins = reward.totalCoins;
  document.getElementById("coins").innerHTML = `${ICONS.coin} ${reward.totalCoins}`;
  state.level.completed = true;
  state.level.bestStars = Math.max(state.level.bestStars, reward.stars.filter(Boolean).length);
  audio.play(reward.chestWorld ? "chest" : "win");
  showWin(reward);
}

function launchConfetti(container, count) {
  const colors = ["#ffc94a", "#22d3ee", "#a78bfa", "#34d399", "#fb7185", "#f472b6"];
  for (let index = 0; index < count; index += 1) {
    const piece = document.createElement("i");
    piece.className = "confetti";
    piece.style.left = `${Math.random() * 100}%`;
    piece.style.background = colors[index % colors.length];
    piece.style.animationDelay = `${Math.random() * 0.4}s`;
    piece.style.animationDuration = `${1.6 + Math.random() * 1.4}s`;
    piece.style.setProperty("--drift", `${(Math.random() - 0.5) * 240}px`);
    piece.style.setProperty("--spin", `${(Math.random() - 0.5) * 1440}deg`);
    container.append(piece);
  }
}

function showWin(reward) {
  const level = state.level;
  const earned = reward.stars.filter(Boolean).length;
  const titles = ["Hoàn thành!", "Hoàn thành!", "Tuyệt vời!", "Hoàn hảo!"];
  const notes = [];
  if (reward.lootCoins) notes.push(`Rương trong màn: +${reward.lootCoins} xu`);
  if (reward.chestWorld) notes.push(`Mở rương World ${reward.chestWorld}: huy hiệu + ${reward.chestCoins} xu!`);
  if (reward.rankUp) notes.push(`Lên cấp bậc mới: ${reward.newRank}!`);
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  backdrop.innerHTML = `
    <div class="confetti-layer"></div>
    <div class="modal glass">
      <h2>${titles[earned]}</h2>
      <div class="subtitle">Màn ${level.id} · ${escapeHtml(level.title)}</div>
      <div class="big-stars">${reward.stars.map((on) => ICONS.star.replace("<svg", `<svg class="${on ? "on" : ""}"`)).join("")}</div>
      <div class="goal-list">
        ${level.starGoals.map((goal, index) => `
          <div class="${reward.stars[index] ? "on" : ""}">${starIcons(reward.stars[index] ? 1 : 0, 1)} ${escapeHtml(goal)}</div>`).join("")}
      </div>
      <div class="reward">${ICONS.coin.replace("<svg", '<svg width="22" height="22"')} ${reward.coins ? `+${reward.coins} xu` : "Không có xu mới (đã nhận lần trước)"}</div>
      ${notes.map((note) => `<div class="reward-note">${escapeHtml(note)}</div>`).join("")}
      <div class="modal-actions">
        <button class="button" id="stay">Ở lại</button>
        ${level.nextLevel ? `<button class="button primary" id="next">Màn tiếp ${ICONS.next}</button>` : ""}
      </div>
    </div>`;
  document.body.append(backdrop);
  launchConfetti(backdrop.querySelector(".confetti-layer"), reward.chestWorld ? 140 : 80);
  const close = () => backdrop.remove();
  backdrop.querySelector("#stay").addEventListener("click", close);
  backdrop.querySelector("#next")?.addEventListener("click", () => {
    close();
    openLevel(level.nextLevel);
  });
  backdrop.addEventListener("click", (event) => {
    if (event.target === backdrop) close();
  });
}

// ------------------------------------------------------------ theory
function codePairs(pairs) {
  return `<div class="code-pairs">${pairs.map(([code, note]) => `
    <div class="code-pair">
      <pre data-code="${escapeHtml(code)}">${highlightPythonLine(code)}<button class="copy-button" title="Chép dòng code">${ICONS.copy}</button></pre>
      ${note ? `<div class="note">${richText(note)}</div>` : ""}
    </div>`).join("")}</div>`;
}

function listItems(items) {
  return `<ul>${items.map((item) => `<li>${richText(item)}</li>`).join("")}</ul>`;
}

function renderTheory(level) {
  const theory = level.theory;
  const sections = [];
  sections.push(["concept", "Khái niệm", "var(--gold)", listItems(theory.concept)]);
  if (theory.terms.length) {
    sections.push(["terms", "Từ khó trong bài", "var(--pink)", `<div class="terms">${theory.terms.map((term) =>
      `<div class="term"><b>${escapeHtml(term.term)}</b>${richText(term.meaning)}</div>`).join("")}</div>`]);
  }
  let goalHtml = `<div class="card"><b>Kết quả cần đạt:</b> ${richText(level.goal)}</div>`;
  const inputs = Object.entries(level.inputs);
  if (inputs.length) {
    goalHtml += `<p>Dữ liệu vào (biến có sẵn, dùng ngay được trong code):</p>${codePairs(inputs.map(([name, value]) => [`${name} = ${value}`, ""]))}`;
  }
  sections.push(["goal", "Đề bài", "var(--green)", goalHtml]);
  if (theory.starterNotes.length) {
    sections.push(["starter", "Giải thích code ban đầu", "#6ea8ff", codePairs(theory.starterNotes)]);
  }
  const lesson = theory.lesson;
  if (lesson) {
    sections.push(["lesson", "Hiểu kỹ hơn", "var(--accent-2)", `
      <h4>Hình dung đời thường</h4><div class="card">${richText(lesson.analogy)}</div>
      <h4>Mẫu câu lệnh - từng phần nghĩa là gì</h4>${codePairs(lesson.syntax)}
      <h4>Chạy thử trong đầu - Python làm gì ở từng dòng</h4>${codePairs(lesson.walkthrough)}
      <h4>Mẹo nhớ</h4><div class="card">${listItems(lesson.tips)}</div>`]);
  }
  sections.push(["example", "Ví dụ minh hoạ (khác lời giải)", "#a78bfa", codePairs(theory.example)]);
  if (theory.mistakes.length) {
    sections.push(["mistakes", "Lỗi hay gặp", "var(--red)", `<div class="card">${listItems(theory.mistakes)}</div>`]);
  }
  return `
    <aside class="theory" id="theory">
      <div class="theory-head">
        <div>
          <h2>Lý thuyết · ${escapeHtml(level.world.concept)}</h2>
          <div class="sub">Kỹ năng: ${escapeHtml(level.world.skill)} · Giai đoạn ${level.stage.number}</div>
        </div>
        <div class="spacer"></div>
        <button class="button small" id="copy-theory">${ICONS.copy} Chép cả bài</button>
        <button class="button small icon" id="close-theory" title="Đóng (Esc)">${ICONS.close}</button>
      </div>
      <nav class="theory-nav">
        ${sections.map(([id, title]) => `<button data-jump="${id}">${escapeHtml(title)}</button>`).join("")}
      </nav>
      <div class="theory-tip">Kéo chuột để bôi đen là tự chép · Nhấn 3 lần để chép cả đoạn · Rê chuột vào dòng code để thấy nút chép.</div>
      <div class="theory-body" id="theory-body">
        ${sections.map(([id, title, color, html]) => `
          <section class="section" id="section-${id}" style="--section-color:${color}">
            <h3>${escapeHtml(title)}</h3>${html}
          </section>`).join("")}
      </div>
    </aside>`;
}

function isTheoryOpen() {
  return document.getElementById("theory")?.classList.contains("open") ?? false;
}

function setTheoryOpen(open) {
  document.getElementById("theory")?.classList.toggle("open", open);
  document.getElementById("theory-toggle")?.classList.toggle("active", open);
}

function bindTheory() {
  const theory = document.getElementById("theory");
  const body = document.getElementById("theory-body");
  document.getElementById("close-theory").addEventListener("click", () => setTheoryOpen(false));
  document.getElementById("copy-theory").addEventListener("click", async () => {
    await copyText(body.innerText);
    toast("Đã chép cả bài lý thuyết", "good");
  });
  theory.querySelectorAll("[data-jump]").forEach((button) => {
    button.addEventListener("click", () => {
      document.getElementById(`section-${button.dataset.jump}`).scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
  body.querySelectorAll(".copy-button").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      await copyText(button.parentElement.dataset.code);
      button.classList.add("done");
      button.innerHTML = ICONS.check;
      toast("Đã chép dòng code", "good");
      setTimeout(() => {
        button.classList.remove("done");
        button.innerHTML = ICONS.copy;
      }, 1400);
    });
  });
  // Bôi đen bằng chuột (kéo, nhấn đúp, nhấn 3 lần) là tự chép.
  body.addEventListener("mouseup", async () => {
    const selected = window.getSelection()?.toString().trim();
    if (!selected) return;
    await copyText(selected);
    toast(`Đã chép ${selected.length} ký tự - dán bằng Ctrl + V`, "good");
  });
}

// ------------------------------------------------------------ keyboard
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  const modal = document.querySelector(".modal-backdrop");
  if (modal) {
    modal.remove();
    audio.onChange = null;
    return;
  }
  if (isTheoryOpen()) {
    setTheoryOpen(false);
    return;
  }
  if (state.map) goMenu();
});

window.addEventListener("beforeunload", saveNow);

boot().catch((error) => {
  appRoot.innerHTML = `<div class="loading">Không mở được game: ${escapeHtml(String(error))}</div>`;
});
