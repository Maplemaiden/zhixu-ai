/** 在讲义 DOM 中按原文片段包裹高亮（兼容 KaTeX 公式节点与重复词多次标注）。 */

const COLOR_CLASS = {
  amber: "hl-amber",
  mint: "hl-mint",
  rose: "hl-rose",
  sky: "hl-sky",
};

/** 这些标签视为「块级边界」，跨过它们时文本间应有一个空格 */
const BLOCK_SEL = "p,li,h1,h2,h3,h4,h5,h6,td,th,tr,div,section,article,blockquote,pre,ul,ol,table";

function unwrapMarks(root) {
  root.querySelectorAll("mark.zhixu-hl").forEach((mark) => {
    const parent = mark.parentNode;
    if (!parent) return;
    while (mark.firstChild) parent.insertBefore(mark.firstChild, mark);
    parent.removeChild(mark);
    parent.normalize();
  });
}

function collectTextNodes(root, { skipMarks = true } = {}) {
  const nodes = [];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
      // 跳过 KaTeX 无障碍隐藏的 MathML 树，防止提取出双份乱码或破坏公式内部结构
      if (node.parentElement?.closest(".katex-mathml")) return NodeFilter.FILTER_REJECT;
      if (skipMarks && node.parentElement?.closest("mark.zhixu-hl")) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  let cur = walker.nextNode();
  while (cur) {
    nodes.push(cur);
    cur = walker.nextNode();
  }
  return nodes;
}

function buildIndex(nodes) {
  let joined = "";
  const chars = [];
  let lastBlock = null;

  for (const node of nodes) {
    const block = node.parentElement?.closest(BLOCK_SEL) || node.parentElement;
    if (lastBlock && block !== lastBlock) {
      joined += " ";
      chars.push(null);
    }
    lastBlock = block;
    const v = node.nodeValue;
    for (let i = 0; i < v.length; i++) {
      joined += v[i];
      chars.push({ node, offset: i });
    }
  }

  let norm = "";
  const map = [];
  let prevWs = false;
  for (let i = 0; i < joined.length; i++) {
    if (/\s/.test(joined[i])) {
      if (!prevWs) {
        norm += " ";
        map.push(i);
        prevWs = true;
      }
    } else {
      norm += joined[i];
      map.push(i);
      prevWs = false;
    }
  }
  return { joined, chars, norm, map };
}

function createMarkEl(note, part = "only") {
  const mark = document.createElement("mark");
  mark.className = `zhixu-hl ${COLOR_CLASS[note.color] || COLOR_CLASS.amber} hl-part-${part}`;
  mark.dataset.noteId = note.id;
  if (note.tag && (part === "last" || part === "only")) mark.dataset.tag = note.tag;
  mark.title = [note.tag, note.remark].filter(Boolean).join(" · ") || "点击可编辑或删除标注";
  return mark;
}

function wrapWholeElement(el, note, part = "only") {
  if (!el?.parentNode) return;
  const existing = el.closest(`mark.zhixu-hl[data-note-id="${note.id}"]`);
  if (existing) {
    if (note.tag && (part === "last" || part === "only")) existing.dataset.tag = note.tag;
    return;
  }
  const mark = createMarkEl(note, part);
  el.parentNode.insertBefore(mark, el);
  mark.appendChild(el);
}

function wrapRangeInTextNode(textNode, start, end, note, part = "only") {
  // 若该文本节点处于 KaTeX 公式内部，整块包裹最外层 .katex 节点，避免切碎公式 DOM 导致高亮不可见
  const katexEl = textNode.parentElement?.closest?.(".katex");
  if (katexEl) {
    wrapWholeElement(katexEl, note, part);
    return;
  }

  const text = textNode.nodeValue;
  const before = text.slice(0, start);
  const mid = text.slice(start, end);
  const after = text.slice(end);
  if (!mid) return;

  const mark = createMarkEl(note, part);
  mark.textContent = mid;

  const parent = textNode.parentNode;
  const frag = document.createDocumentFragment();
  if (before) frag.appendChild(document.createTextNode(before));
  frag.appendChild(mark);
  if (after) frag.appendChild(document.createTextNode(after));
  parent.replaceChild(frag, textNode);
}

function groupByNode(chars, startJoined, endJoined) {
  const groups = [];
  for (let i = startJoined; i < endJoined; i++) {
    const c = chars[i];
    if (!c) continue;
    const last = groups[groups.length - 1];
    if (last && last.node === c.node && c.offset === last.end) {
      last.end = c.offset + 1;
    } else {
      groups.push({ node: c.node, start: c.offset, end: c.offset + 1 });
    }
  }
  return groups;
}

export function extractText(node) {
  if (!node) return "";
  const nodes = collectTextNodes(node, { skipMarks: false });
  if (!nodes.length) return "";
  return buildIndex(nodes).norm.trim();
}

/**
 * @param {HTMLElement} root
 * @param {Array<{id:string,quote:string,color?:string,tag?:string,remark?:string}>} notes
 */
export function applyHighlights(root, notes) {
  if (!root) return;
  unwrapMarks(root);

  const list = (notes || [])
    .filter((n) => n?.quote?.trim())
    .slice()
    .sort((a, b) => (b.quote?.length || 0) - (a.quote?.length || 0));

  const seenCountByQuote = new Map();

  for (const note of list) {
    const quoteNorm = note.quote.replace(/\s+/g, " ").trim();
    if (!quoteNorm) continue;

    const nodes = collectTextNodes(root, { skipMarks: false });
    if (!nodes.length) continue;

    const { chars, norm, map } = buildIndex(nodes);
    const targetNth = seenCountByQuote.get(quoteNorm) || 0;
    let searchFrom = 0;
    let idx = -1;
    for (let k = 0; k <= targetNth; k++) {
      const found = norm.indexOf(quoteNorm, searchFrom);
      if (found < 0) break;
      idx = found;
      searchFrom = found + Math.max(1, quoteNorm.length);
    }
    if (idx < 0) continue;
    seenCountByQuote.set(quoteNorm, targetNth + 1);

    const endIdx = idx + quoteNorm.length;
    const startJoined = map[idx];
    const lastMapped = map[endIdx - 1];
    if (startJoined == null || lastMapped == null) continue;
    const endJoined = lastMapped + 1;

    const groups = groupByNode(chars, startJoined, endJoined);
    groups.forEach((g, i) => {
      const part =
        groups.length === 1 ? "only" : i === 0 ? "first" : i === groups.length - 1 ? "last" : "mid";
      wrapRangeInTextNode(g.node, g.start, g.end, note, part);
    });
  }
}
