/* Sổ tay lý thuyết: tra cứu toàn bộ kiến thức của game ở một chỗ.
   - Mục lục theo Giai đoạn / World, từ điển thuật ngữ, bảng tra lệnh.
   - Ô tìm kiếm không phân biệt dấu ("vong lap" cũng ra "vòng lặp") và tô sáng chữ tìm thấy.
   - Nút "In / Lưu PDF" in cả cuốn sổ ra giấy hoặc file PDF. */

const handbookState = { data: null, searchTimer: null };
const HANDBOOK_STAGE_COLORS = { 1: "#22d3ee", 2: "#34d399", 3: "#fb923c", 4: "#a78bfa", 5: "#f472b6" };

function stripMarks(text) {
  return text.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase();
}

function handbookRichText(text) {
  return escapeHtml(text).replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
}

function handbookCodePairs(pairs, color) {
  return `<div class="code-pairs" style="--section-color:${color}">${pairs.map(([code, note]) => `
    <div class="code-pair hb-entry">
      <pre data-code="${escapeHtml(code)}">${highlightPythonLine(code)}<button class="copy-button" title="Chép dòng code">${ICONS.copy}</button></pre>
      ${note ? `<div class="note">${handbookRichText(note)}</div>` : ""}
    </div>`).join("")}</div>`;
}

function handbookList(items) {
  return `<ul>${items.map((item) => `<li class="hb-entry">${handbookRichText(item)}</li>`).join("")}</ul>`;
}

function renderHandbookWorld(world) {
  const color = HANDBOOK_STAGE_COLORS[world.stage];
  const lesson = world.lesson;
  const lessonHtml = lesson ? `
    <div class="hb-group">
      <h3>Hiểu kỹ hơn</h3>
      <h4>Hình dung đời thường</h4>
      <div class="card hb-entry">${handbookRichText(lesson.analogy)}</div>
      <h4>Mẫu câu lệnh - từng phần nghĩa là gì</h4>
      ${handbookCodePairs(lesson.syntax, color)}
      <h4>Chạy thử trong đầu - Python làm gì ở từng dòng</h4>
      ${handbookCodePairs(lesson.walkthrough, color)}
      <h4>Mẹo nhớ</h4>
      <div class="card">${handbookList(lesson.tips)}</div>
    </div>` : "";
  const levelsHtml = world.levels.map((level) => `
    <div class="hb-group hb-level">
      <h3><span class="hb-level-id">${level.id}</span>${escapeHtml(level.title)}</h3>
      ${handbookList(level.concept)}
      ${level.example.length ? `<h4>Ví dụ</h4>${handbookCodePairs(level.example, color)}` : ""}
      ${level.mistakes.length ? `<h4 class="hb-warning">Lỗi hay gặp</h4>${handbookList(level.mistakes)}` : ""}
    </div>`).join("");
  return `
    <section class="hb-chapter section" id="hb-world-${world.number}" style="--section-color:${color}" data-title="${escapeHtml(`${world.title} ${world.concept} ${world.skill}`)}">
      <div class="hb-chapter-head">
        <div class="hb-number">${world.number}</div>
        <div>
          <div class="eyebrow">Giai đoạn ${world.stage} · World ${world.number}</div>
          <h2>${escapeHtml(world.title)} — ${escapeHtml(world.concept)}</h2>
          <div class="hb-skill">Kỹ năng: ${escapeHtml(world.skill)}</div>
        </div>
      </div>
      ${lessonHtml}
      ${levelsHtml}
    </section>`;
}

function renderCommandTable(title, items) {
  return `
    <div class="hb-group">
      <h3>${escapeHtml(title)}</h3>
      <div class="hb-commands">
        ${items.map((item) => `
          <div class="hb-command hb-entry">
            <code>${escapeHtml(item.label)}</code>
            <span>${escapeHtml(item.hint)}</span>
          </div>`).join("")}
      </div>
    </div>`;
}

function renderHandbook(data) {
  const commands = data.commands;
  const moduleTables = Object.entries(commands.modules)
    .map(([name, items]) => renderCommandTable(`Thư viện ${name}`, items)).join("");
  return `
    <div class="handbook" id="handbook">
      <aside class="hb-side">
        <div class="hb-brand">${ICONS.book}<div><b>Sổ tay Python</b><span>OneSpace CodeQuest</span></div></div>
        <label class="hb-search">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>
          <input id="hb-search" type="search" placeholder="Tìm: vòng lặp, append, KeyError..." autocomplete="off" spellcheck="false">
        </label>
        <nav class="hb-nav">
          <button data-goto="hb-intro">Cách dùng sổ tay</button>
          <button data-goto="hb-glossary">Từ điển thuật ngữ</button>
          <button data-goto="hb-commands">Bảng tra lệnh</button>
          ${data.stages.map((stage) => `
            <div class="hb-stage" style="--stage-color:${HANDBOOK_STAGE_COLORS[stage.number]}">Giai đoạn ${stage.number} · ${escapeHtml(stage.title)}</div>
            ${data.worlds.filter((world) => world.stage === stage.number).map((world) => `
              <button data-goto="hb-world-${world.number}"><span>${world.number}</span>${escapeHtml(world.title)}</button>`).join("")}`).join("")}
        </nav>
      </aside>
      <div class="hb-main">
        <header class="hb-head">
          <div class="hb-result" id="hb-result">23 World · ${data.glossary.length} thuật ngữ</div>
          <div class="spacer"></div>
          <button class="button small" id="hb-print">${ICONS.save} In / Lưu PDF</button>
          <button class="button small icon" id="hb-close" title="Đóng (Esc)">${ICONS.close}</button>
        </header>
        <div class="hb-content" id="hb-content">
          <section class="hb-chapter section hb-intro" id="hb-intro" style="--section-color:var(--accent-2)" data-title="cách dùng sổ tay">
            <h1>Sổ tay lý thuyết Python</h1>
            <p class="hb-entry">Toàn bộ kiến thức của 138 màn CodeQuest, xếp theo 5 giai đoạn và 23 World. Mỗi World có phần <b>Hiểu kỹ hơn</b> (hình dung đời thường, mẫu câu lệnh, chạy thử từng dòng, mẹo nhớ) và lý thuyết của từng bài.</p>
            <p class="hb-entry">Gõ vào ô <b>Tìm</b> bên trái để tra nhanh - gõ không dấu cũng được. Bấm vào dòng code để thấy nút chép; bôi đen chữ rồi <span class="kbd">Ctrl</span> + <span class="kbd">C</span> để chép.</p>
            <p class="hb-entry">Ví dụ trong sổ tay khác lời giải của màn - hãy hiểu rồi tự áp dụng.</p>
          </section>
          <section class="hb-chapter section" id="hb-glossary" style="--section-color:var(--pink)" data-title="từ điển thuật ngữ">
            <h2>Từ điển thuật ngữ</h2>
            <div class="terms hb-terms">
              ${data.glossary.map((entry) => `<div class="term hb-entry"><b>${escapeHtml(entry.term)}</b>${handbookRichText(entry.meaning)}</div>`).join("")}
            </div>
          </section>
          <section class="hb-chapter section" id="hb-commands" style="--section-color:var(--gold)" data-title="bảng tra lệnh hero hàm python">
            <h2>Bảng tra lệnh</h2>
            ${renderCommandTable("Lệnh của hero (gõ hero. rồi tên lệnh)", commands.hero)}
            ${renderCommandTable("Hàm có sẵn của Python", commands.builtins)}
            ${renderCommandTable("Từ khoá Python", commands.keywords)}
            ${renderCommandTable("Phương thức hay dùng (gõ sau dấu chấm)", commands.methods)}
            ${moduleTables}
          </section>
          ${data.worlds.map(renderHandbookWorld).join("")}
          <div class="hb-empty" id="hb-empty" hidden>Không tìm thấy. Thử từ khác, ví dụ "list", "vòng lặp", "lỗi".</div>
        </div>
      </div>
    </div>`;
}

function highlightMatches(element, words) {
  const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
  const textNodes = [];
  while (walker.nextNode()) textNodes.push(walker.currentNode);
  for (const node of textNodes) {
    const original = node.nodeValue;
    let normalized = "";
    const originalIndex = [];
    for (let index = 0; index < original.length; index += 1) {
      const stripped = stripMarks(original[index]);
      for (const character of stripped) {
        normalized += character;
        originalIndex.push(index);
      }
    }
    const ranges = [];
    for (const word of words) {
      let position = normalized.indexOf(word);
      while (position !== -1) {
        ranges.push([originalIndex[position], originalIndex[position + word.length - 1] + 1]);
        position = normalized.indexOf(word, position + word.length);
      }
    }
    if (!ranges.length) continue;
    ranges.sort((first, second) => first[0] - second[0]);
    const fragment = document.createDocumentFragment();
    let cursor = 0;
    for (const [start, end] of ranges) {
      if (start < cursor) continue;
      fragment.append(original.slice(cursor, start));
      const mark = document.createElement("mark");
      mark.textContent = original.slice(start, end);
      fragment.append(mark);
      cursor = end;
    }
    fragment.append(original.slice(cursor));
    node.replaceWith(fragment);
  }
}

function runHandbookSearch(root, query) {
  const words = stripMarks(query).split(/\s+/).filter(Boolean);
  root.querySelectorAll("mark").forEach((mark) => mark.replaceWith(mark.textContent));
  root.querySelectorAll(".hb-chapter").forEach((chapter) => chapter.normalize());
  let matchCount = 0;
  let chapterCount = 0;
  for (const chapter of root.querySelectorAll(".hb-chapter")) {
    const titleMatches = words.length > 0 && words.every((word) => stripMarks(chapter.dataset.title ?? "").includes(word));
    let chapterHasMatch = false;
    for (const entry of chapter.querySelectorAll(".hb-entry")) {
      const matches = words.length === 0 || titleMatches || words.every((word) => stripMarks(entry.textContent).includes(word));
      entry.classList.toggle("hb-hidden", !matches);
      if (matches) {
        chapterHasMatch = true;
        if (words.length) {
          matchCount += 1;
          highlightMatches(entry, words);
        }
      }
    }
    for (const group of chapter.querySelectorAll(".hb-group, .code-pairs, ul, .card, .hb-commands, h4")) {
      if (group.tagName === "H4") continue;
      const hasVisible = group.querySelector(".hb-entry:not(.hb-hidden)") !== null || (group.classList.contains("hb-entry") && !group.classList.contains("hb-hidden"));
      group.classList.toggle("hb-hidden-group", words.length > 0 && !hasVisible);
    }
    chapter.querySelectorAll("h4").forEach((heading) => {
      const next = heading.nextElementSibling;
      heading.classList.toggle("hb-hidden-group", words.length > 0 && next?.classList.contains("hb-hidden-group"));
    });
    chapter.classList.toggle("hb-hidden", !chapterHasMatch);
    if (chapterHasMatch) chapterCount += 1;
  }
  const result = root.querySelector("#hb-result");
  const data = handbookState.data;
  result.textContent = words.length
    ? `${matchCount} kết quả trong ${chapterCount} mục`
    : `23 World · ${data.glossary.length} thuật ngữ`;
  root.querySelector("#hb-empty").hidden = !(words.length && matchCount === 0);
  root.querySelector("#hb-content").scrollTop = 0;
}

function closeHandbook() {
  document.getElementById("handbook")?.remove();
}

async function openHandbook(worldNumber = null) {
  if (document.getElementById("handbook")) return;
  if (!handbookState.data) handbookState.data = await api("handbook");
  const wrapper = document.createElement("div");
  wrapper.innerHTML = renderHandbook(handbookState.data);
  const root = wrapper.firstElementChild;
  document.body.append(root);
  const content = root.querySelector("#hb-content");
  const search = root.querySelector("#hb-search");
  search.addEventListener("input", () => {
    clearTimeout(handbookState.searchTimer);
    handbookState.searchTimer = setTimeout(() => runHandbookSearch(root, search.value), 180);
  });
  search.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && search.value) {
      event.stopPropagation();
      search.value = "";
      runHandbookSearch(root, "");
    }
  });
  root.querySelectorAll("[data-goto]").forEach((button) => {
    button.addEventListener("click", () => {
      if (search.value) {
        search.value = "";
        runHandbookSearch(root, "");
      }
      document.getElementById(button.dataset.goto)?.scrollIntoView({ block: "start" });
      root.querySelectorAll(".hb-nav button").forEach((item) => item.classList.toggle("active", item === button));
    });
  });
  root.querySelector("#hb-close").addEventListener("click", closeHandbook);
  root.querySelector("#hb-print").addEventListener("click", () => {
    search.value = "";
    runHandbookSearch(root, "");
    window.print();
  });
  root.querySelectorAll(".copy-button").forEach((button) => {
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
  if (worldNumber) {
    document.getElementById(`hb-world-${worldNumber}`)?.scrollIntoView({ block: "start" });
    root.querySelector(`[data-goto="hb-world-${worldNumber}"]`)?.classList.add("active");
  } else {
    content.scrollTop = 0;
  }
  search.focus();
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && document.getElementById("handbook")) {
    event.stopImmediatePropagation();
    closeHandbook();
  }
}, true);
