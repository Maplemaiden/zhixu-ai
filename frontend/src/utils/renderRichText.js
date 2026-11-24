import katex from "katex";

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderKatex(tex, displayMode) {
  try {
    return katex.renderToString(tex, {
      throwOnError: false,
      displayMode,
      strict: "ignore",
    });
  } catch {
    return escapeHtml(tex);
  }
}

function formatInline(line) {
  let s = escapeHtml(line);
  s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  // 过程箭头更易读
  s = s.replace(/-&gt;/g, "→").replace(/→/g, '<span class="md-arrow">→</span>');
  return s;
}

/** 聊天/答疑用：标题、列表、加粗（公式已抽成占位符） */
function renderChatMarkdownBlocks(text) {
  const lines = String(text).replace(/\r\n/g, "\n").split("\n");
  const out = [];
  let listType = null; // "ul" | "ol" | null

  const closeList = () => {
    if (listType === "ul") out.push("</ul>");
    if (listType === "ol") out.push("</ol>");
    listType = null;
  };

  const openList = (type) => {
    if (listType === type) return;
    closeList();
    out.push(type === "ol" ? '<ol class="md-ol">' : '<ul class="md-ul">');
    listType = type;
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      closeList();
      out.push("<br>");
      continue;
    }

    const h = trimmed.match(/^#{1,3}\s+(.+)$/);
    if (h) {
      closeList();
      out.push(`<p class="md-h">${formatInline(`**${h[1]}**`)}</p>`);
      continue;
    }

    const ol = trimmed.match(/^\d+\.\s+(.+)$/);
    if (ol) {
      openList("ol");
      out.push(`<li>${formatInline(ol[1])}</li>`);
      continue;
    }

    const ul = trimmed.match(/^[-*]\s+(.+)$/);
    if (ul) {
      openList("ul");
      out.push(`<li>${formatInline(ul[1])}</li>`);
      continue;
    }

    closeList();
    out.push(`<p class="md-p">${formatInline(line)}</p>`);
  }
  closeList();
  return out.join("");
}

/**
 * 轻量富文本：转义 HTML；助教消息渲染公式 + 基础 Markdown（**加粗**、列表、标题）。
 * 学生消息只转义+换行。
 */
export function renderRichText(text, { math = true } = {}) {
  if (text == null || text === "") return "";
  let s = String(text);

  if (!math) {
    return escapeHtml(s).replace(/\n/g, "<br>");
  }

  // 先抽出公式，避免转义破坏 LaTeX
  const slots = [];
  const push = (html) => {
    const key = `\u0000MATH${slots.length}\u0000`;
    slots.push(html);
    return key;
  };

  s = s.replace(/\$\$([\s\S]+?)\$\$/g, (_, tex) => push(renderKatex(tex.trim(), true)));
  s = s.replace(/\$([^\$\n]+?)\$/g, (_, tex) => push(renderKatex(tex.trim(), false)));
  // 兼容偶尔输出的 \( ... \) / \[ ... \]
  s = s.replace(/\\\((.+?)\\\)/g, (_, tex) => push(renderKatex(tex.trim(), false)));
  s = s.replace(/\\\[([\s\S]+?)\\\]/g, (_, tex) => push(renderKatex(tex.trim(), true)));

  let html = renderChatMarkdownBlocks(s);
  html = html.replace(/\u0000MATH(\d+)\u0000/g, (_, i) => slots[Number(i)] || "");
  return html;
}

function splitTableRow(line) {
  const raw = line.trim().replace(/^\|/, "").replace(/\|$/, "");
  return raw.split("|").map((c) => c.trim());
}

function isTableSep(line) {
  return /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line.trim());
}

function renderMdTable(rows) {
  if (!rows.length) return "";
  const head = rows[0];
  const body = rows.slice(1);
  const th = head.map((c) => `<th>${formatInline(c)}</th>`).join("");
  const trs = body
    .map((r) => `<tr>${r.map((c) => `<td>${formatInline(c)}</td>`).join("")}</tr>`)
    .join("");
  return `<div class="md-table-wrap"><table class="md-table"><thead><tr>${th}</tr></thead><tbody>${trs}</tbody></table></div>`;
}

/** 讲解正文：Markdown 标题/加粗/列表/表格，便于展示知识库讲义 */
export function renderLessonMarkdown(text) {
  if (text == null || text === "") return "";
  let s = String(text).replace(/\r\n/g, "\n");
  // 去掉切片自带的首行标题（页面上已有 section.title）
  s = s.replace(/^#{1,3}[^\n]*\n+/, "");
  const slots = [];
  const push = (html) => {
    const key = `\u0000MATH${slots.length}\u0000`;
    slots.push(html);
    return key;
  };
  s = s.replace(/\$\$([\s\S]+?)\$\$/g, (_, tex) => push(renderKatex(tex.trim(), true)));
  s = s.replace(/\$([^\$\n]+?)\$/g, (_, tex) => push(renderKatex(tex.trim(), false)));

  const lines = s.split("\n");
  const out = [];
  let inUl = false;
  const closeUl = () => {
    if (inUl) {
      out.push("</ul>");
      inUl = false;
    }
  };

  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // Markdown 表格：连续 | 行，中间可含分隔行
    if (trimmed.startsWith("|") && i + 1 < lines.length && isTableSep(lines[i + 1])) {
      closeUl();
      const rows = [splitTableRow(lines[i])];
      i += 2; // skip header + separator
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        if (!isTableSep(lines[i])) rows.push(splitTableRow(lines[i]));
        i += 1;
      }
      out.push(renderMdTable(rows));
      continue;
    }

    const h3 = line.match(/^###\s+(.+)$/);
    const h2 = line.match(/^##\s+(.+)$/);
    const h1 = line.match(/^#\s+(.+)$/);
    const li = line.match(/^[-*]\s+(.+)$/);
    if (h1 || h2 || h3) {
      closeUl();
      const t = escapeHtml((h1 || h2 || h3)[1]);
      out.push(h1 ? `<h3 class="md-h">${t}</h3>` : `<h4 class="md-h">${t}</h4>`);
      i += 1;
      continue;
    }
    if (li) {
      if (!inUl) {
        out.push('<ul class="md-ul">');
        inUl = true;
      }
      out.push(`<li>${formatInline(li[1])}</li>`);
      i += 1;
      continue;
    }
    closeUl();
    if (!trimmed) {
      out.push("<br>");
      i += 1;
      continue;
    }
    if (/^---+$/.test(trimmed)) {
      out.push('<hr class="md-hr" />');
      i += 1;
      continue;
    }
    out.push(`<p class="md-p">${formatInline(line)}</p>`);
    i += 1;
  }
  closeUl();
  let html = out.join("");
  html = html.replace(/\u0000MATH(\d+)\u0000/g, (_, idx) => slots[Number(idx)] || "");
  return html;
}
