/* Khung soạn code Python: tô màu cú pháp, số dòng, tự thụt lề, đánh dấu dòng lỗi.
   Dùng một <textarea> trong suốt đặt chồng lên bản tô màu (<pre>), nên gõ tiếng Việt
   bằng Unikey / bộ gõ của Windows hoạt động bình thường. */

const PYTHON_KEYWORDS = new Set([
  "False", "None", "True", "and", "as", "assert", "break", "class", "continue", "def", "del", "elif",
  "else", "except", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda",
  "nonlocal", "not", "or", "pass", "raise", "return", "try", "while", "with", "yield",
]);

const PYTHON_BUILTINS = new Set([
  "print", "range", "len", "int", "str", "float", "bool", "list", "dict", "set", "tuple", "sum", "min",
  "max", "abs", "round", "sorted", "reversed", "enumerate", "zip", "map", "filter", "any", "all",
  "isinstance", "type", "iter", "next", "super", "input", "open", "repr", "ord", "chr",
]);

const TOKEN_PATTERN =
  /(#.*)|([rRfFbB]{0,2}"(?:\\.|[^"\\])*"?|[rRfFbB]{0,2}'(?:\\.|[^'\\])*'?)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_]\w*)/g;

const INDENT = "    ";
const LINE_HEIGHT = 24;
const EDITOR_PADDING = { left: 16, top: 14 };
const IDENTIFIER_BEFORE = /[A-Za-z_][A-Za-z0-9_]*$/;
const IMPORT_AS = /^\s*import\s+([\w.]+)(?:\s+as\s+(\w+))?/;
const FROM_IMPORT = /^\s*from\s+([\w.]+)\s+import\s+(.+)/;

/* ------------------------------------------------------------ gợi ý lệnh (giống completion.py) */
function isInsideTextOrComment(line, column) {
  let quote = null;
  for (const character of line.slice(0, column)) {
    if (quote) {
      if (character === quote) quote = null;
    } else if (character === '"' || character === "'") {
      quote = character;
    } else if (character === "#") {
      return true;
    }
  }
  return quote !== null;
}

function moduleAliases(lines, modules) {
  const aliases = {};
  for (const line of lines) {
    const importMatch = line.match(IMPORT_AS);
    if (importMatch) {
      aliases[importMatch[2] ?? importMatch[1].split(".")[0]] = importMatch[1];
      continue;
    }
    const fromMatch = line.match(FROM_IMPORT);
    if (!fromMatch) continue;
    for (const part of fromMatch[2].split(",")) {
      const name = part.trim().split(" as ").pop().trim();
      if (name) aliases[name] = modules[name] ? name : fromMatch[1];
    }
  }
  return aliases;
}

function namesInCode(lines, skipRow) {
  const names = new Set();
  lines.forEach((line, index) => {
    if (index === skipRow) return;
    const code = line.split("#")[0].replace(/"[^"]*"|'[^']*'/g, "");
    for (const name of code.match(/[A-Za-z_][A-Za-z0-9_]*/g) ?? []) {
      if (name.length >= 2 && !PYTHON_KEYWORDS.has(name)) names.add(name);
    }
  });
  return names;
}

function filterSuggestions(pool, prefix, maxSuggestions, allowEmpty = false) {
  if (!prefix && !allowEmpty) return [];
  const lowered = prefix.toLowerCase();
  const result = pool.filter((item) =>
    item.insert.toLowerCase().startsWith(lowered) && item.insert.replace(/[():]+$/, "").trim() !== prefix);
  return result.slice(0, prefix ? maxSuggestions : maxSuggestions + 3);
}

function suggestCompletions(data, text, caret, extraNames = []) {
  const lines = text.split("\n");
  const row = text.slice(0, caret).split("\n").length - 1;
  const line = lines[row];
  const column = caret - text.slice(0, caret).lastIndexOf("\n") - 1;
  const before = line.slice(0, column);
  if (isInsideTextOrComment(line, column)) return null;
  const prefix = before.match(IDENTIFIER_BEFORE)?.[0] ?? "";
  const start = column - prefix.length;
  if (prefix && /^\d/.test(prefix)) return null;
  const startOffset = caret - prefix.length;

  if (start > 0 && before[start - 1] === ".") {
    const owner = before.slice(0, start - 1).match(IDENTIFIER_BEFORE)?.[0] ?? "";
    let pool;
    if (owner === "hero") pool = data.hero;
    else {
      const module = moduleAliases(lines, data.modules)[owner] ?? owner;
      pool = data.modules[module] ?? data.methods;
    }
    return { start: startOffset, items: filterSuggestions(pool, prefix, data.maxSuggestions, true) };
  }
  if (!prefix) return null;

  const stripped = before.trimStart();
  if ((stripped.startsWith("import ") || stripped.startsWith("from ")) && !stripped.includes(" import ")) {
    const pool = data.importable.map((name) => ({ label: name, insert: name, hint: "Thư viện được phép dùng", cursorBack: 0 }));
    return { start: startOffset, items: filterSuggestions(pool, prefix, data.maxSuggestions) };
  }
  if (/\b(def|class)\s+\w*$/.test(before)) return null;

  const keywordNames = new Set(data.keywords.map((item) => item.label));
  const known = new Set([...data.builtins.map((item) => item.label.split("(")[0]), "hero"]);
  const userNames = [...new Set([...namesInCode(lines, row), ...extraNames])]
    .filter((name) => !keywordNames.has(name) && !known.has(name))
    .sort();
  const pool = [
    { label: "hero", insert: "hero", hint: "Nhân vật của bạn - gõ dấu . để xem lệnh", cursorBack: 0 },
    ...userNames.map((name) => ({ label: name, insert: name, hint: "Tên trong code / dữ liệu có sẵn", cursorBack: 0 })),
    ...data.keywords,
    ...data.builtins,
  ];
  return { start: startOffset, items: filterSuggestions(pool, prefix, data.maxSuggestions) };
}

function escapeHtml(text) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function highlightPythonLine(line) {
  let html = "";
  let lastIndex = 0;
  for (const match of line.matchAll(TOKEN_PATTERN)) {
    html += escapeHtml(line.slice(lastIndex, match.index));
    const [token, comment, string, number, name] = match;
    let className = "";
    if (comment) className = "tok-comment";
    else if (string) className = "tok-string";
    else if (number) className = "tok-number";
    else if (name) {
      const previousCharacter = line[match.index - 1];
      if (PYTHON_KEYWORDS.has(name)) className = "tok-keyword";
      else if (name === "hero") className = "tok-hero";
      else if (name === "self") className = "tok-self";
      else if (previousCharacter === ".") className = "tok-method";
      else if (PYTHON_BUILTINS.has(name)) className = "tok-builtin";
    }
    html += className ? `<span class="${className}">${escapeHtml(token)}</span>` : escapeHtml(token);
    lastIndex = match.index + token.length;
  }
  return html + escapeHtml(line.slice(lastIndex));
}

class CodeEditor {
  constructor(container, { onRun, onChange, completionData = null, extraNames = [] }) {
    this.onRun = onRun;
    this.onChange = onChange;
    this.completionData = completionData;
    this.extraNames = extraNames;
    this.errorLine = null;
    this.suggestion = null;
    this.selectedSuggestion = 0;
    container.innerHTML = `
      <div class="code-editor">
        <div class="code-gutter"></div>
        <div class="code-area">
          <pre aria-hidden="true"></pre>
          <textarea spellcheck="false" autocapitalize="off" autocomplete="off" wrap="off"></textarea>
          <div class="suggest-box" hidden></div>
        </div>
      </div>`;
    this.gutter = container.querySelector(".code-gutter");
    this.highlightLayer = container.querySelector("pre");
    this.textarea = container.querySelector("textarea");
    this.suggestBox = container.querySelector(".suggest-box");
    this.textarea.addEventListener("input", (event) => {
      this.errorLine = null;
      this.render();
      this.onChange?.(this.getValue());
      const typedWord = event.inputType === "insertText" && /[\w.]/.test(event.data ?? "");
      if (typedWord) this.updateSuggestions();
      else this.closeSuggestions();
    });
    this.textarea.addEventListener("scroll", () => {
      this.syncScroll();
      this.closeSuggestions();
    });
    this.textarea.addEventListener("keydown", (event) => this.handleKey(event));
    this.textarea.addEventListener("blur", () => setTimeout(() => this.closeSuggestions(), 150));
    this.textarea.addEventListener("mousedown", () => this.closeSuggestions());
    this.suggestBox.addEventListener("mousedown", (event) => {
      const option = event.target.closest("[data-index]");
      if (!option) return;
      event.preventDefault();
      this.acceptSuggestion(Number(option.dataset.index));
    });
    for (const eventName of ["click", "keyup", "select"]) {
      this.textarea.addEventListener(eventName, () => this.renderActiveLine());
    }
  }

  // ------------------------------------------------------------ suggestions
  characterWidth() {
    if (!this.measuredCharacterWidth) {
      const context = document.createElement("canvas").getContext("2d");
      context.font = getComputedStyle(this.textarea).font;
      this.measuredCharacterWidth = context.measureText("M".repeat(20)).width / 20;
    }
    return this.measuredCharacterWidth;
  }

  updateSuggestions(force = false) {
    if (!this.completionData) return;
    const caret = this.textarea.selectionStart;
    const result = suggestCompletions(this.completionData, this.textarea.value, caret, this.extraNames);
    if (!result || result.items.length === 0 || (!force && result.start === caret && !this.textarea.value[caret - 1]?.match(/\./))) {
      this.closeSuggestions();
      return;
    }
    this.suggestion = result;
    this.selectedSuggestion = 0;
    this.renderSuggestions();
  }

  renderSuggestions() {
    const { items, start } = this.suggestion;
    const textBefore = this.textarea.value.slice(0, start);
    const row = textBefore.split("\n").length - 1;
    const column = start - textBefore.lastIndexOf("\n") - 1;
    const left = EDITOR_PADDING.left + column * this.characterWidth() - this.textarea.scrollLeft;
    const top = EDITOR_PADDING.top + (row + 1) * LINE_HEIGHT - this.textarea.scrollTop + 2;
    this.suggestBox.innerHTML = items.map((item, index) => `
      <div class="suggest-item ${index === this.selectedSuggestion ? "selected" : ""}" data-index="${index}">
        <span class="label">${escapeHtml(item.label)}</span><span class="hint">${escapeHtml(item.hint)}</span>
      </div>`).join("");
    this.suggestBox.hidden = false;
    const areaHeight = this.textarea.clientHeight;
    const boxHeight = this.suggestBox.offsetHeight;
    const placeAbove = top + boxHeight > areaHeight && top - LINE_HEIGHT - boxHeight > 0;
    this.suggestBox.style.left = `${Math.max(4, left - 8)}px`;
    this.suggestBox.style.top = `${placeAbove ? top - LINE_HEIGHT - boxHeight - 4 : top}px`;
  }

  closeSuggestions() {
    this.suggestion = null;
    this.suggestBox.hidden = true;
  }

  acceptSuggestion(index = this.selectedSuggestion) {
    const item = this.suggestion?.items[index];
    if (!item) return;
    this.textarea.setSelectionRange(this.suggestion.start, this.textarea.selectionStart);
    this.closeSuggestions();
    this.insertText(item.insert);
    if (item.cursorBack) {
      const caret = this.textarea.selectionStart - item.cursorBack;
      this.textarea.setSelectionRange(caret, caret);
    }
    this.textarea.focus();
  }

  handleSuggestionKey(event) {
    if (!this.suggestion) return false;
    const count = this.suggestion.items.length;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      const step = event.key === "ArrowDown" ? 1 : -1;
      this.selectedSuggestion = (this.selectedSuggestion + step + count) % count;
      this.renderSuggestions();
    } else if ((event.key === "Tab" || event.key === "Enter") && !event.ctrlKey) {
      this.acceptSuggestion();
    } else if (event.key === "Escape") {
      this.closeSuggestions();
      event.stopPropagation();
    } else {
      return false;
    }
    event.preventDefault();
    return true;
  }

  getValue() {
    return this.textarea.value;
  }

  setValue(text) {
    this.textarea.value = text;
    this.errorLine = null;
    this.render();
  }

  focus() {
    this.textarea.focus();
  }

  setErrorLine(lineNumber) {
    this.errorLine = lineNumber;
    this.render();
    if (lineNumber) {
      this.textarea.scrollTop = Math.max(0, (lineNumber - 4) * LINE_HEIGHT);
    }
  }

  currentLineNumber() {
    return this.textarea.value.slice(0, this.textarea.selectionStart).split("\n").length;
  }

  render() {
    const lines = this.textarea.value.split("\n");
    const activeLine = this.currentLineNumber();
    this.highlightLayer.innerHTML = lines
      .map((line, index) => {
        const number = index + 1;
        const classes = ["code-line"];
        if (number === this.errorLine) classes.push("error");
        else if (number === activeLine) classes.push("active");
        return `<span class="${classes.join(" ")}">${highlightPythonLine(line) || " "}</span>`;
      })
      .join("");
    this.gutter.innerHTML = lines
      .map((_line, index) => {
        const number = index + 1;
        let className = "";
        if (number === this.errorLine) className = "error";
        else if (number === activeLine) className = "active";
        return `<div class="${className}">${number}</div>`;
      })
      .join("");
    this.syncScroll();
  }

  renderActiveLine() {
    const activeLine = this.currentLineNumber();
    if (activeLine !== this.lastActiveLine) {
      this.lastActiveLine = activeLine;
      this.render();
    }
  }

  syncScroll() {
    this.highlightLayer.scrollTop = this.textarea.scrollTop;
    this.highlightLayer.scrollLeft = this.textarea.scrollLeft;
    this.gutter.scrollTop = this.textarea.scrollTop;
  }

  insertText(text) {
    // execCommand giữ được lịch sử Ctrl+Z của trình duyệt.
    document.execCommand("insertText", false, text);
  }

  handleKey(event) {
    if (this.handleSuggestionKey(event)) return;
    if (event.key === " " && event.ctrlKey) {
      event.preventDefault();
      this.updateSuggestions(true);
      return;
    }
    if (event.key === "Escape") {
      // Esc trong khung code chỉ bỏ chọn chữ, không thoát ra menu.
      event.stopPropagation();
      return;
    }
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      this.onRun?.();
      return;
    }
    if (event.key === "Tab") {
      event.preventDefault();
      if (event.shiftKey) this.changeIndent(-1);
      else if (this.textarea.selectionStart !== this.textarea.selectionEnd) this.changeIndent(1);
      else this.insertText(INDENT);
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      this.insertNewLine();
      return;
    }
    if (event.key === "Backspace") {
      this.handleBackspace(event);
      return;
    }
    if (event.key === "/" && event.ctrlKey) {
      event.preventDefault();
      this.toggleComment();
    }
  }

  insertNewLine() {
    const value = this.textarea.value;
    const lineStart = value.lastIndexOf("\n", this.textarea.selectionStart - 1) + 1;
    const currentLine = value.slice(lineStart, this.textarea.selectionStart);
    let indent = currentLine.match(/^\s*/)[0];
    if (currentLine.trimEnd().endsWith(":")) indent += INDENT;
    this.insertText("\n" + indent);
  }

  handleBackspace(event) {
    const { selectionStart, selectionEnd, value } = this.textarea;
    if (selectionStart !== selectionEnd) return;
    const lineStart = value.lastIndexOf("\n", selectionStart - 1) + 1;
    const beforeCaret = value.slice(lineStart, selectionStart);
    if (beforeCaret.length === 0 || beforeCaret.trim() !== "") return;
    const removeCount = beforeCaret.length % 4 || 4;
    event.preventDefault();
    this.textarea.setSelectionRange(selectionStart - removeCount, selectionStart);
    this.insertText("");
  }

  selectedLineRange() {
    const { selectionStart, selectionEnd, value } = this.textarea;
    const start = value.lastIndexOf("\n", selectionStart - 1) + 1;
    let end = value.indexOf("\n", selectionEnd - (selectionEnd > selectionStart ? 1 : 0));
    if (end === -1) end = value.length;
    return [start, end];
  }

  replaceLines(transform) {
    const [start, end] = this.selectedLineRange();
    const original = this.textarea.value.slice(start, end);
    const replaced = original.split("\n").map(transform).join("\n");
    this.textarea.setSelectionRange(start, end);
    this.insertText(replaced);
    this.textarea.setSelectionRange(start, start + replaced.length);
  }

  changeIndent(direction) {
    if (direction > 0) {
      this.replaceLines((line) => INDENT + line);
      return;
    }
    this.replaceLines((line) => line.replace(/^ {1,4}/, ""));
  }

  toggleComment() {
    const [start, end] = this.selectedLineRange();
    const lines = this.textarea.value.slice(start, end).split("\n");
    const allCommented = lines.every((line) => line.trim() === "" || line.trimStart().startsWith("#"));
    this.replaceLines((line) => {
      if (line.trim() === "") return line;
      if (allCommented) return line.replace(/^(\s*)# ?/, "$1");
      return line.replace(/^(\s*)/, "$1# ");
    });
  }
}

window.CodeEditor = CodeEditor;
window.highlightPythonLine = highlightPythonLine;
window.escapeHtml = escapeHtml;
