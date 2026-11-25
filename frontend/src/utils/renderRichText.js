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

/** 行内格式：粗体 / 斜体 / 行内代码 / 箭头 */
function formatInline(line) {
  let s = escapeHtml(line);
  s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/__(.+?)__/g, "<strong>$1</strong>");
  // 斜体：避免吃掉 ** 已经处理过的内容
  s = s.replace(/(^|[^*<])\*([^*\n<][^*\n]*?)\*(?!\*)/g, "$1<em>$2</em>");
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  s = s.replace(/-&gt;/g, "→").replace(/→/g, '<span class="md-arrow">→</span>');
  // 兜底：清掉没配对的强调符号，避免把 ** / __ 直接露给用户
  s = s.replace(/\*\*/g, "");
  s = s.replace(/__/g, "");
  return s;
}

function splitTableRow(line) {
  const raw = line.trim().replace(/^\|/, "").replace(/\|$/, "");
  return raw.split("|").map((c) => c.trim());
}

/** 表格分隔行：| --- | :---: | 之类 */
function isTableSep(line) {
  return /^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$/.test(String(line).trim());
}

/** 可能是表格行：含竖线且不是纯分隔符噪声 */
function looksLikeTableRow(line) {
  const t = String(line).trim();
  return t.includes("|") && t.replace(/[|\s:-]/g, "").length > 0;
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

/**
 * 统一的块级 Markdown 渲染（讲义正文与答疑气泡共用，保证两边都能处理表格/各级标题）。
 *
 * @param {string} text
 * @param {{ headingAs?: "p"|"h", dropLeadingHeading?: boolean }} opts
 *   headingAs: "p" 用于聊天气泡（避免 h 标签字号过大）；"h" 用于讲义正文
 *   dropLeadingHeading: 去掉首行标题（讲义页已有 section.title）
 */
function renderBlocks(text, { headingAs = "p", dropLeadingHeading = false } = {}) {
  let s = String(text).replace(/\r\n/g, "\n");
  if (dropLeadingHeading) s = s.replace(/^#{1,6}[^\n]*\n+/, "");

  const lines = s.split("\n");
  const out = [];
  let listType = null;

  const closeList = () => {
    if (listType) {
      out.push(listType === "ol" ? "</ol>" : "</ul>");
      listType = null;
    }
  };
  const openList = (type) => {
    if (listType === type) return;
    closeList();
    out.push(type === "ol" ? '<ol class="md-ol">' : '<ul class="md-ul">');
    listType = type;
  };

  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // ---- 代码块（内部不解析）----
    if (trimmed.startsWith("```")) {
      closeList();
      const lang = trimmed.slice(3).trim();
      const buf = [];
      i += 1;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        buf.push(lines[i]);
        i += 1;
      }
      i += 1; // 跳过结束的 ```
      out.push(
        `<pre class="md-pre"><code${lang ? ` class="lang-${escapeHtml(lang)}"` : ""}>${escapeHtml(buf.join("\n"))}</code></pre>`
      );
      continue;
    }

    // ---- 表格：当前行像表格行，且下一行是分隔行 ----
    if (looksLikeTableRow(line) && i + 1 < lines.length && isTableSep(lines[i + 1])) {
      closeList();
      const rows = [splitTableRow(line)];
      i += 2;
      while (i < lines.length && looksLikeTableRow(lines[i])) {
        if (!isTableSep(lines[i])) rows.push(splitTableRow(lines[i]));
        i += 1;
      }
      out.push(renderMdTable(rows));
      continue;
    }

    if (!trimmed) {
      closeList();
      out.push("<br>");
      i += 1;
      continue;
    }

    // ---- 标题 1~6 级（必须 # 后有空格，避免把 #标签 当标题）----
    const h = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (h) {
      closeList();
      const level = h[1].length;
      const inner = formatInline(h[2]);
      if (headingAs === "h") {
        const tag = `h${Math.min(level + 2, 6)}`;
        out.push(`<${tag} class="md-h">${inner}</${tag}>`);
      } else {
        out.push(`<p class="md-h md-h${level}">${inner}</p>`);
      }
      i += 1;
      continue;
    }

    // ---- 分隔线 ----
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      closeList();
      out.push('<hr class="md-hr" />');
      i += 1;
      continue;
    }

    // ---- 有序列表 ----
    const ol = trimmed.match(/^\d+[.)]\s+(.+)$/);
    if (ol) {
      openList("ol");
      out.push(`<li>${formatInline(ol[1])}</li>`);
      i += 1;
      continue;
    }

    // ---- 无序列表 ----
    const ul = trimmed.match(/^[-*+]\s+(.+)$/);
    if (ul) {
      openList("ul");
      out.push(`<li>${formatInline(ul[1])}</li>`);
      i += 1;
      continue;
    }

    // ---- 引用 ----
    const bq = trimmed.match(/^>\s?(.*)$/);
    if (bq) {
      closeList();
      out.push(`<blockquote class="md-quote">${formatInline(bq[1])}</blockquote>`);
      i += 1;
      continue;
    }

    closeList();
    out.push(`<p class="md-p">${formatInline(line)}</p>`);
    i += 1;
  }
  closeList();
  return out.join("");
}

/** 抽出公式为占位符，交给块级渲染，最后回填 */
function withMath(text, render) {
  const slots = [];
  const push = (html) => {
    const key = `\u0000MATH${slots.length}\u0000`;
    slots.push(html);
    return key;
  };
  let s = String(text);
  s = s.replace(/\$\$([\s\S]+?)\$\$/g, (_, tex) => push(renderKatex(tex.trim(), true)));
  s = s.replace(/\$([^$\n]+?)\$/g, (_, tex) => push(renderKatex(tex.trim(), false)));
  s = s.replace(/\\\[([\s\S]+?)\\\]/g, (_, tex) => push(renderKatex(tex.trim(), true)));
  s = s.replace(/\\\((.+?)\\\)/g, (_, tex) => push(renderKatex(tex.trim(), false)));
  let html = render(s);
  html = html.replace(/\u0000MATH(\d+)\u0000/g, (_, idx) => slots[Number(idx)] || "");
  return html;
}

/**
 * 聊天 / 答疑气泡：公式 + 完整 Markdown（表格、1~6 级标题、列表、代码块、分隔线、引用）。
 * 学生消息只转义 + 换行。
 */
export function renderRichText(text, { math = true } = {}) {
  if (text == null || text === "") return "";
  if (!math) return escapeHtml(String(text)).replace(/\n/g, "<br>");
  return withMath(text, (s) => renderBlocks(s, { headingAs: "p", dropLeadingHeading: false }));
}

/** 讲义正文：同一套渲染，标题用真实 h 标签、丢掉首行标题（页面已有 section.title） */
export function renderLessonMarkdown(text) {
  if (text == null || text === "") return "";
  return withMath(text, (s) => renderBlocks(s, { headingAs: "h", dropLeadingHeading: true }));
}