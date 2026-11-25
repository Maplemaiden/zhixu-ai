/** 在讲义 DOM 中按原文片段包裹高亮（尽量不破坏已有标签）。 */

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
      // 渲染时要跳过旧高亮，避免重复包裹；提取 quote 时**不能跳过**，
      // 否则在已有高亮上再划词，提取出的文字会缺失 → 被判为太短 → 浮层不出现。
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

/**
 * 把文本节点拼成一整串，并建立两套索引：
 *   chars[i]  → joined 第 i 个字符来自哪个 {node, offset}（块级边界的虚拟空格为 null）
 *   map[k]    → norm 第 k 个字符对应 joined 的下标
 * norm 是 joined 做「连续空白压成一个空格」之后的版本，用于和 quote 比对。
 */
function buildIndex(nodes) {
  let joined = "";
  const chars = [];
  let lastBlock = null;

  for (const node of nodes) {
    const block = node.parentElement?.closest(BLOCK_SEL) || node.parentElement;
    if (lastBlock && block !== lastBlock) {
      // 跨块级元素：补一个虚拟空格，避免 "上一段末尾下一段开头" 粘在一起
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

function wrapRangeInTextNode(textNode, start, end, note, part = "only") {
  const text = textNode.nodeValue;
  const before = text.slice(0, start);
  const mid = text.slice(start, end);
  const after = text.slice(end);
  if (!mid) return;

  const mark = document.createElement("mark");
  mark.className = `zhixu-hl ${COLOR_CLASS[note.color] || COLOR_CLASS.amber} hl-part-${part}`;
  mark.dataset.noteId = note.id;
  // 只有末尾那一片带标签，否则一次标注会在同一段里渲染出好几个「重点」徽章
  if (note.tag && (part === "last" || part === "only")) mark.dataset.tag = note.tag;
  mark.title = [note.tag, note.remark].filter(Boolean).join(" · ") || "我的高亮";
  mark.textContent = mid;

  const parent = textNode.parentNode;
  const frag = document.createDocumentFragment();
  if (before) frag.appendChild(document.createTextNode(before));
  frag.appendChild(mark);
  if (after) frag.appendChild(document.createTextNode(after));
  parent.replaceChild(frag, textNode);
}

/** 把 [startJoined, endJoined) 这个区间切成「同一文本节点内的连续段」 */
function groupByNode(chars, startJoined, endJoined) {
  const groups = [];
  for (let i = startJoined; i < endJoined; i++) {
    const c = chars[i];
    if (!c) continue; // 块级边界的虚拟空格
    const last = groups[groups.length - 1];
    if (last && last.node === c.node && c.offset === last.end) {
      last.end = c.offset + 1;
    } else {
      groups.push({ node: c.node, start: c.offset, end: c.offset + 1 });
    }
  }
  return groups;
}

/**
 * 从任意节点（元素或 DocumentFragment 包成的容器）提取「归一化文本」。
 * 归一化规则与 buildIndex 完全一致：块级边界补空格、连续空白压成单空格。
 * 保存标注时用它生成 quote，保证与渲染时的匹配逻辑同源，不会一边有空格一边没有。
 */
export function extractText(node) {
  if (!node) return "";
  // 提取 quote 时把已高亮的文字也算进来（skipMarks: false）
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

  for (const note of list) {
    // 与保存时的归一化保持一致：连续空白压成一个空格
    const quoteNorm = note.quote.replace(/\s+/g, " ").trim();
    if (!quoteNorm) continue;

    // 不跳过 mark：unwrapMarks 已清掉旧高亮，这里遇到的 mark 是同一次循环里
    // 刚包上的。允许在其内部再包一层，重叠标注才能都显示出来
    // （否则长的那条先包，短的那条文字被跳过 → 保存了却看不到）。
    const nodes = collectTextNodes(root, { skipMarks: false });
    if (!nodes.length) continue;

    const { chars, norm, map } = buildIndex(nodes);
    let idx = norm.indexOf(quoteNorm);
    if (idx < 0) continue;

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
