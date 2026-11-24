/** 在讲义 DOM 中按原文片段包裹高亮（尽量不破坏已有标签）。 */

const COLOR_CLASS = {
  amber: "hl-amber",
  mint: "hl-mint",
  rose: "hl-rose",
  sky: "hl-sky",
};

function unwrapMarks(root) {
  root.querySelectorAll("mark.zhixu-hl").forEach((mark) => {
    const parent = mark.parentNode;
    if (!parent) return;
    while (mark.firstChild) parent.insertBefore(mark.firstChild, mark);
    parent.removeChild(mark);
    parent.normalize();
  });
}

function collectTextNodes(root) {
  const nodes = [];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
      if (node.parentElement?.closest("mark.zhixu-hl")) return NodeFilter.FILTER_REJECT;
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

function wrapRangeInTextNode(textNode, start, end, note) {
  const text = textNode.nodeValue;
  const before = text.slice(0, start);
  const mid = text.slice(start, end);
  const after = text.slice(end);
  const mark = document.createElement("mark");
  mark.className = `zhixu-hl ${COLOR_CLASS[note.color] || COLOR_CLASS.amber}`;
  mark.dataset.noteId = note.id;
  if (note.tag) mark.dataset.tag = note.tag;
  mark.title = [note.tag, note.remark].filter(Boolean).join(" · ") || "我的高亮";
  mark.textContent = mid;

  const parent = textNode.parentNode;
  const frag = document.createDocumentFragment();
  if (before) frag.appendChild(document.createTextNode(before));
  frag.appendChild(mark);
  if (after) frag.appendChild(document.createTextNode(after));
  parent.replaceChild(frag, textNode);
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

  for (const note of list) {
    const quote = note.quote.trim();
    const nodes = collectTextNodes(root);
    let joined = "";
    const map = [];
    for (const node of nodes) {
      const start = joined.length;
      joined += node.nodeValue;
      map.push({ node, start, end: joined.length });
    }
    const idx = joined.indexOf(quote);
    if (idx < 0) continue;
    const endIdx = idx + quote.length;

    // 只处理落在单个 text node 内的情况；跨节点则退化为逐段包裹
    const spans = map.filter((m) => m.end > idx && m.start < endIdx);
    for (const span of spans) {
      const localStart = Math.max(0, idx - span.start);
      const localEnd = Math.min(span.node.nodeValue.length, endIdx - span.start);
      if (localEnd > localStart) {
        wrapRangeInTextNode(span.node, localStart, localEnd, note);
      }
    }
  }
}
