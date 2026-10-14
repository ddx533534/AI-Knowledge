#!/usr/bin/env node
/**
 * 把仓库根目录下的 NN-* 内容目录生成一个多页静态站点，输出到 site/dist。
 *
 * 零依赖，只用 Node 内置模块。用法：
 *   node site/build.mjs          # 从任意目录执行都可以
 *
 * 自动发现：仓库根下所有匹配 /^\d\d-(.+)$/ 的目录都会成为一个栏目，
 * 目录名（去编号）在 CAT_META 里查中文名，查不到就用原名。新增目录/类别
 * 不需要改脚本，直接生效。
 *
 * 每个栏目下顶层的 *.md 成为一篇文章（README.md / index.md 除外）；
 * 文件名以 YYYY-MM-DD 开头时用文件名的日期，否则取该文件最后一次 git
 * 提交日期。栏目下的 assets/ 整体复制到 dist/assets/<栏目>/。
 */
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const SITE_DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.dirname(SITE_DIR);
const DIST = path.join(SITE_DIR, 'dist');

const SITE = {
  title: 'Moting 技术笔记',
  sub: '跨端渲染 · AI 工作流编排 · 工程实践',
  desc: '跨端渲染与 AI 工作流编排方向的调研、复盘与日报。',
};

/** 目录名（去编号）→ 中文栏目名；未登记的目录用目录名本身，不用改脚本。 */
const CAT_META = {
  Knowledge: {
    title: '技术知识',
    nav: '知识',
    intro: '一个主题一份文档，写清结论、依据与边界，不重复建文件。',
  },
  'Work-Practice': {
    title: '工作实践',
    nav: '实践',
    intro: '工作中真实遇到的问题：怎么撞上的、比过哪些路、最后怎么落地、留下什么没解决。',
  },
  Daily: {
    title: 'AI 日报',
    nav: '日报',
    intro: '每天的 AI 行业简报与一个 GitHub 仓库深析。',
  },
  Interview: {
    title: '面试知识体系',
    nav: '面试',
    intro: '计算机基础面试的成体系整理：结论先行、有图有据，覆盖网络、操作系统、数据结构、组成原理与数据库缓存。',
  },
  Board: {
    title: '备考看板',
    nav: '看板',
    pageDir: true,
    intro: '自己用的工具页：逐日勾选任务、记录耗时与卡点、错题到期复习。数据只存在你自己的浏览器里，不会上传。',
  },
};

/* ------------------------------------------------------------------ 工具 */

const esc = (s) =>
  String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

const enc = (s) => encodeURIComponent(String(s)).replace(/%2F/gi, '/');

const relPrefix = (depth) => '../'.repeat(depth);

function gitDate(relPath) {
  try {
    const out = execFileSync('git', ['log', '-1', '--format=%cs', '--', relPath], {
      cwd: REPO,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim();
    return out || null;
  } catch {
    return null;
  }
}

function mtimeDate(abs) {
  try {
    return fs.statSync(abs).mtime.toISOString().slice(0, 10);
  } catch {
    return null;
  }
}

const stripInline = (s) =>
  s
    .replace(/`([^`]+)`/g, '$1')
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\[[^\]]*\]/g, '$1')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .trim();

/** 页面类栏目的 title 标记会被原样嵌进 <head>，做一次转义防护。 */
const escAttr = (s) => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');

/* ------------------------------------------------------- markdown 渲染 */

const RE_DEF = /^\[([^\]]+)\]:\s*(\S+)\s*$/;

function splitRefs(src) {
  const refs = {};
  const lines = [];
  for (const line of src.split('\n')) {
    const m = line.match(RE_DEF);
    if (m) refs[m[1].trim()] = m[2].replace(/^<|>$/g, '');
    else lines.push(line);
  }
  return { refs, text: lines.join('\n') };
}

function renderBlock(src, ctx) {
  const lines = src.split('\n');
  const out = [];
  let i = 0;

  const para = [];

  const flush = () => {
    if (!para.length) return;
    const joined = para.join('\n');
    const html = inline(joined, ctx);
    out.push(para.length === 1 && isLoneImage(joined) ? html : `<p>${html}</p>`);
    para.length = 0;
  };

  while (i < lines.length) {
    const line = lines[i];

    if (!line.trim()) {
      flush();
      i += 1;
      continue;
    }

    // 围栏代码
    const fence = line.match(/^```\s*([\w+-]*)\s*$/);
    if (fence) {
      flush();
      const body = [];
      i += 1;
      while (i < lines.length && !/^```\s*$/.test(lines[i])) {
        body.push(lines[i]);
        i += 1;
      }
      i += 1;
      const lang = fence[1] ? ` class="lang-${esc(fence[1])}"` : '';
      out.push(`<pre><code${lang}>${esc(body.join('\n'))}</code></pre>`);
      continue;
    }

    // 标题
    const head = line.match(/^(#{1,6})\s+(.*)$/);
    if (head) {
      flush();
      const lv = head[1].length;
      const text = inline(head[2].trim(), ctx);
      const id = slugId(stripInline(head[2]));
      out.push(`<h${lv} id="${esc(id)}">${text}</h${lv}>`);
      i += 1;
      continue;
    }

    // 分隔线
    if (/^(-{3,}|\*{3,}|_{3,})\s*$/.test(line.trim())) {
      flush();
      out.push('<hr>');
      i += 1;
      continue;
    }

    // 表格
    if (line.includes('|') && i + 1 < lines.length && /^\s*\|?[\s:\-|]+\|[\s:\-|]*$/.test(lines[i + 1])) {
      flush();
      const cells = (r) =>
        r
          .replace(/^\s*\|/, '')
          .replace(/\|\s*$/, '')
          .split('|')
          .map((c) => c.trim());
      const head = cells(line);
      const rows = [];
      i += 2;
      while (i < lines.length && lines[i].includes('|') && lines[i].trim()) {
        rows.push(cells(lines[i]));
        i += 1;
      }
      const th = head.map((c) => `<th>${inline(c, ctx)}</th>`).join('');
      const tb = rows
        .map((r) => `<tr>${r.map((c) => `<td>${inline(c, ctx)}</td>`).join('')}</tr>`)
        .join('');
      out.push(`<div class="table-wrap"><table><thead><tr>${th}</tr></thead><tbody>${tb}</tbody></table></div>`);
      continue;
    }

    // 引用
    if (/^\s*>/.test(line)) {
      flush();
      const body = [];
      while (i < lines.length && /^\s*>/.test(lines[i])) {
        body.push(lines[i].replace(/^\s*>\s?/, ''));
        i += 1;
      }
      out.push(`<blockquote><p>${inline(body.join('\n'), ctx)}</p></blockquote>`);
      continue;
    }

    // 列表
    if (/^\s*([-*+]|\d+\.)\s+/.test(line)) {
      flush();
      const items = [];
      while (i < lines.length && /^\s*([-*+]|\d+\.)\s+/.test(lines[i])) {
        const m = lines[i].match(/^(\s*)([-*+]|\d+\.)\s+(.*)$/);
        items.push({
          level: Math.floor(m[1].length / 2),
          ordered: /\d/.test(m[2]),
          text: m[3],
        });
        i += 1;
      }
      out.push(renderItems(listTree(items), ctx));
      continue;
    }

    para.push(line);
    i += 1;
  }

  flush();
  return out.join('\n');
}

/** 整段只有一张图时不要套 <p>，否则 figure 会被塞进段落里（非法嵌套）。 */
const isLoneImage = (s) => /^\s*!\[[^\]]*\]\(\s*[^)\s]+(?:\s+"[^"]*")?\s*\)\s*$/.test(s);

function listTree(items) {
  const root = { children: [] };
  const stack = [{ node: root, level: -1 }];
  for (const it of items) {
    while (stack.length > 1 && it.level <= stack[stack.length - 1].level) stack.pop();
    const node = { text: it.text, ordered: it.ordered, children: [] };
    stack[stack.length - 1].node.children.push(node);
    stack.push({ node, level: it.level });
  }
  return root.children;
}

function renderItems(nodes, ctx) {
  if (!nodes.length) return '';
  const tag = nodes[0].ordered ? 'ol' : 'ul';
  const body = nodes
    .map((n) => {
      const sub = n.children.length ? renderItems(n.children, ctx) : '';
      return `<li>${inline(n.text, ctx)}${sub}</li>`;
    })
    .join('');
  return `<${tag}>${body}</${tag}>`;
}

const RE_CODE = /`([^`]+)`/g;
const RE_IMG = /!\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+"([^"]*)")?\s*\)/g;
const RE_REF_NAMED = /\[([^\]]+)\]\[([^\]]*)\]/g;
const RE_LINK = /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g;
const RE_REF_SHORT = /\[([A-Za-z][A-Za-z0-9_-]{0,11})\]/g;

function inline(raw, ctx) {
  const slot = [];
  const put = (html) => {
    slot.push(html);
    return `\u0000${slot.length - 1}\u0000`;
  };
  const a = (label, url) =>
    `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(label)}</a>`;

  let t = String(raw);
  t = t.replace(RE_CODE, (m, c) => put(`<code>${esc(c)}</code>`));
  t = t.replace(RE_IMG, (m, alt, src, hint) => put(ctx.figure(alt, src, hint)));
  t = t.replace(RE_REF_NAMED, (m, label, ref) => {
    const url = ctx.refs[(ref || label).trim()];
    return url ? put(a(label, url)) : esc(m);
  });
  t = t.replace(RE_LINK, (m, label, url) => put(a(label, url)));
  t = t.replace(RE_REF_SHORT, (m, ref) => {
    const url = ctx.refs[ref];
    return url ? put(a(ref, url)) : esc(m);
  });

  t = esc(t);
  t = t.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  t = t.replace(/(^|[^*\w])\*([^*\n]+)\*/g, '$1<em>$2</em>');
  t = t.replace(/\u0000(\d+)\u0000/g, (m, n) => slot[Number(n)]);
  return t;
}

function slugId(s) {
  return String(s)
    .trim()
    .toLowerCase()
    .replace(/[\s]+/g, '-')
    .replace(/[^\w\u4e00-\u9fa5-]/g, '')
    .slice(0, 60);
}

/* ------------------------------------------------------------- 站点结构 */

function discover() {
  const cats = [];
  // 内容栏目按名字排序；页面类栏目（看板等工具页）排在导航最后，避免插在日报和面试中间
  const catOrder = [];
  for (const name of fs.readdirSync(REPO).sort()) {
    const m = name.match(/^(\d\d)-(.+)$/);
    if (!m) continue;
    const abs = path.join(REPO, name);
    if (!fs.statSync(abs).isDirectory()) continue;
    const suffix = m[2];
    const meta = CAT_META[suffix] || {};
    const pageDir = !!meta.pageDir;
    if (!pageDir) catOrder.push(suffix.toLowerCase());
    cats.push({
      id: suffix.toLowerCase(),
      dir: abs,
      dirName: name,
      pageDir,
      exts: pageDir ? ['.html'] : ['.md'],
      title: meta.title || suffix,
      nav: meta.nav || suffix,
      intro: meta.intro || '',
      posts: [],
    });
  }

  const isIndex = (f) => /^(readme|index)\.(md|html)$/i.test(f);
  for (const cat of cats) {
    for (const f of fs.readdirSync(cat.dir).sort()) {
      if (!cat.exts.some((e) => f.toLowerCase().endsWith(e))) continue;
      if (isIndex(f)) continue;
      const abs = path.join(cat.dir, f);
      if (!fs.statSync(abs).isFile()) continue;
      const slug = f.replace(/\.[a-z0-9]+$/i, '');
      const rel = path.relative(REPO, abs);
      const dm = slug.match(/^(\d{4}-\d{2}-\d{2})/);
      const date = dm ? dm[1] : gitDate(rel) || mtimeDate(abs);
      cat.posts.push({ cat, slug, file: abs, rel, date, title: '', summary: '', body: '' });
    }
    cat.posts.sort((a, b) => String(b.date).localeCompare(String(a.date)) || a.slug.localeCompare(b.slug));
  }
  return cats.filter((c) => c.posts.length).sort((a, b) => {
    const ka = catOrder.includes(a.id) ? catOrder.indexOf(a.id) : catOrder.length + cats.indexOf(a);
    const kb = catOrder.includes(b.id) ? catOrder.indexOf(b.id) : catOrder.length + cats.indexOf(b);
    return ka - kb;
  });
}

function prepare(post) {
  let src = fs.readFileSync(post.file, 'utf8');
  src = src.replace(/\r\n/g, '\n');
  src = src.replace(/<!--[\s\S]*?-->/g, '');
  if (/^---\s*\n/.test(src)) {
    const end = src.indexOf('\n---', 3);
    if (end !== -1) src = src.slice(src.indexOf('\n', end + 1) + 1);
  }
  const { refs, text } = splitRefs(src);
  const lines = text.split('\n');

  // 页面类栏目：丢进来的就是现成 HTML，正文原样使用，不套模板（文件名即标题）
  if (post.cat.pageDir) {
    post.title = post.slug;
    post.summary = post.cat.intro;
    post.minutes = 0;
    post.refs = {};
    post.src = '';
    post.html = src;
    return;
  }

  let title = post.slug;
  for (const line of lines) {
    const m = line.match(/^#\s+(.*)$/);
    if (m) {
      title = stripInline(m[1]);
      break;
    }
  }

  let summary = '';
  let seenHead = false;
  let fallback = '';
  for (const raw of lines) {
    const line = raw.trim();
    if (/^#{1,6}\s/.test(line)) {
      seenHead = true;
      continue;
    }
    if (!seenHead || !line) continue;
    if (/^[|>]|^```|^[-*+]\s|^\d+\.\s|^!\[/.test(line)) continue;
    if (/^(-{3,}|_{3,}|\*{3,})\s*$/.test(line)) continue;
    const plain = stripInline(line);
    if (!fallback) fallback = plain;
    // 「整理日期：2026-10-11。」这类元信息行不适合当摘要，往后找一段
    if (plain.length < 40 && /^(整理|核实|更新|校对|创建|发布|撰写|修订|最后编辑)?日期[：:]?\s*\d{4}-\d{2}-\d{2}/.test(plain)) {
      continue;
    }
    summary = plain;
    break;
  }
  if (!summary) summary = fallback;
  // 段落首句就是日期时，去掉这个前缀，让摘要从正文开始
  summary = summary.replace(
    /^(整理|核实|更新|校对|创建|发布|撰写|修订|最后编辑)?日期[：:]?\s*\d{4}-\d{2}-\d{2}\s*[。.；;]?\s*/,
    '',
  );
  if (summary.length > 140) summary = `${summary.slice(0, 138)}…`;

  const html = buildHtml(src, refs, figureFactory(post, 1));

  post.title = title;
  post.summary = summary;
  post.minutes = Math.max(1, Math.round(text.replace(/\s/g, '').length / 400));
  post.refs = refs;
  post.src = text;
  post.html = html;
}

/** 把一份 markdown 正文渲染成 HTML（不含标题行），文章页与工具页共用。 */
function buildHtml(src, refs, figure) {
  const ctx = { refs, figure: figure || (() => '') };
  return renderBlock(src.replace(/^#\s+.*$/m, ''), ctx);
}

const assetIndexCache = new Map();

function assetIndex(catAssetDir) {
  if (assetIndexCache.has(catAssetDir)) return assetIndexCache.get(catAssetDir);
  const idx = new Map();
  const walk = (dir) => {
    let entries = [];
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const e of entries) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) walk(p);
      else if (!idx.has(e.name)) idx.set(e.name, p);
    }
  };
  walk(catAssetDir);
  assetIndexCache.set(catAssetDir, idx);
  return idx;
}

/**
 * 图片先按 md 文件所在目录解析；解析不到再退化成按文件名在
 * <栏目>/assets/ 下递归查找——不少文档里只写了 figN-xxx.svg 这样的裸文件名。
 */
function resolveImage(catDir, clean) {
  if (/^https?:\/\//i.test(clean)) return clean;
  const direct = path.resolve(catDir, clean);
  if (fs.existsSync(direct) && fs.statSync(direct).isFile()) return direct;
  const hit = assetIndex(path.join(catDir, 'assets')).get(path.basename(clean));
  return hit || null;
}

function figureFactory(post, depth) {
  const catAssetDir = path.join(post.cat.dir, 'assets');
  return (alt, src, hint) => {
    const clean = String(src).trim();
    const w = hint && /w=(\d+)/.exec(hint);
    const style = w ? ` style="max-width:${w[1]}px"` : '';
    const cap = stripInline(alt);
    const caption = cap ? `<figcaption>${esc(cap)}</figcaption>` : '';
    if (/^https?:\/\//i.test(clean)) {
      return `<figure class="fig"><img src="${esc(clean)}" alt="${esc(cap)}"${style}>${caption}</figure>`;
    }
    const abs = resolveImage(post.cat.dir, clean);
    if (!abs) {
      return `<figure class="fig missing"><figcaption>图片缺失：${esc(clean)}</figcaption></figure>`;
    }
    // 挪进来的现成 HTML 页面：图片就放在页面旁边，直接引用相对路径即可
    if (path.extname(abs).toLowerCase() === '.html') {
      return `<figure class="fig self"><figcaption>交互页面：<a href="${esc(enc(clean))}">${esc(
        cap || clean,
      )}</a></figcaption></figure>`;
    }
    const relFromAssets = path.relative(catAssetDir, abs).split(path.sep).join('/');
    const url = `${relPrefix(depth)}assets/${post.cat.id}/${enc(relFromAssets)}`;
    return `<figure class="fig"><img src="${esc(url)}" alt="${esc(cap)}" loading="lazy"${style}>${caption}</figure>`;
  };
}

/* -------------------------------------------------------------- 模板 */

/** 栏目名可能在栏目页里被改写（如「备考看板」写成「每日备考看板」），记下来给导航用。 */
const post_titles = new Map();

/** nav 元素的标签名可能带 class（页面类栏目自己也渲染了侧边栏），统一按栏目真实信息重算。 */
function navInner(active, depth, cats, labelOf) {
  const p = relPrefix(depth);
  const items = [
    { id: null, label: '首页', href: `${p}index.html`, n: null },
    ...cats.map((c) => ({
      id: c.id,
      label: post_titles.get(c.id) || (labelOf && labelOf(c)) || c.nav || c.title,
      href: `${p}${c.pageDir ? `${c.id}/index.html` : `${c.id}/`}`,
      n: c.pageDir ? null : c.posts.length,
    })),
  ];
  return items
    .map(
      (it) =>
        `<a href="${it.href}"${active === it.id ? ' class="on"' : ''}>${esc(it.label)}${
          it.n != null ? `<b>${it.n}</b>` : ''
        }</a>`,
    )
    .join('');
}

function navHtml(active, depth, cats, labelOf) {
  return `<nav class="nav">${navInner(active, depth, cats, labelOf)}</nav>`;
}

/** 页面类栏目自带侧边栏，构建时替换成按真实栏目算出来的版本，避免手写链接失效。 */
function freshNav(html, depth, cats, active) {
  if (!/<nav class="nav">[\s\S]*?<\/nav>/i.test(html)) return html;
  return html.replace(/<nav class="nav">[\s\S]*?<\/nav>/i, navHtml(active, depth, cats));
}

function layout({ depth, title, desc, body, cats, active, latest }) {
  const p = relPrefix(depth);
  const items = navInner(active, depth, cats);
  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc || SITE.desc)}">
<link rel="stylesheet" href="${p}style.css">
<link rel="alternate icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%232563eb'/%3E%3Ctext x='16' y='22' font-size='18' font-family='sans-serif' fill='white' text-anchor='middle'%3EM%3C/text%3E%3C/svg%3E">
</head>
<body>
<a class="skip" href="#main">跳到正文</a>
<div class="shell">
<aside class="side">
  <div class="side-in">
    <a class="brand" href="${p}index.html">
      <span class="brand-mark">M</span>
      <span class="brand-txt">
        <span class="brand-name">${esc(SITE.title)}</span>
        <span class="brand-sub">${esc(SITE.sub)}</span>
      </span>
    </a>
    <nav class="nav">${items}</nav>
    <p class="side-foot">${latest ? `更新至 <b>${esc(latest)}</b>` : ''}</p>
  </div>
</aside>
<div class="col">
<main id="main">
${body}
</main>
<footer class="foot">
  <p>${esc(SITE.title)} · ${esc(SITE.sub)}</p>
  <p class="muted">内容来自本地知识库，构建脚本自动生成。</p>
</footer>
</div>
</div>
</body>
</html>
`;
}

/** 列表里的一条：桌面为「日期在上、正文在右」的两列，窄屏收成单列。 */
function postItem(post, depth) {
  const p = relPrefix(depth);
  const href = `${p}${post.cat.id}/${enc(post.slug)}.html`;
  const meta = post.cat.pageDir ? '工具页 · 点开即用' : `约 ${post.minutes} 分钟`;
  return `<article class="item">
  <div class="item-d">
    ${post.date ? `<time>${esc(post.date)}</time>` : ''}
    <span class="tag">${esc(post.cat.title)}</span>
  </div>
  <div class="item-b">
    <a class="item-t" href="${href}">${esc(post.title)}</a>
    ${post.summary ? `<p class="item-s">${esc(post.summary)}</p>` : ''}
    <p class="item-m">${esc(meta)}</p>
  </div>
</article>`;
}

/** 首页每个栏目只展开前几条。 */
const HOME_LIMIT = 5;

/* --------------------------------------------------------------- 生成 */

function main() {
  const cats = discover();
  if (!cats.length) {
    console.error('没有找到任何 NN-* 内容目录');
    process.exit(1);
  }

  for (const cat of cats) cat.posts.forEach(prepare);

  // 先读一遍页面类栏目的手写首页，把自定义标题登记好，免得后面生成的页面还叫目录名
  for (const cat of cats) {
    if (!cat.pageDir) continue;
    const custom = path.join(SITE_DIR, `${cat.id}-index.html`);
    if (!fs.existsSync(custom)) continue;
    const t = fs.readFileSync(custom, 'utf8').match(/<title>([^<]*)<\/title>/i);
    if (t && t[1].trim()) post_titles.set(cat.id, t[1].trim());
  }

  fs.rmSync(DIST, { recursive: true, force: true });
  fs.mkdirSync(DIST, { recursive: true });
  fs.copyFileSync(path.join(SITE_DIR, 'style.css'), path.join(DIST, 'style.css'));

  for (const cat of cats) {
    const from = path.join(cat.dir, 'assets');
    if (fs.existsSync(from)) {
      fs.cpSync(from, path.join(DIST, 'assets', cat.id), { recursive: true });
    }
    if (!cat.pageDir) continue;
    // 页面类栏目：整目录搬过去，另外把项目 README 也带出去供直接下载
    fs.mkdirSync(path.join(DIST, cat.id), { recursive: true });
    fs.cpSync(cat.dir, path.join(DIST, cat.id), { recursive: true });
    const readme = path.join(cat.dir, 'README.md');
    if (fs.existsSync(readme)) fs.copyFileSync(readme, path.join(DIST, cat.id, 'README.md'));
  }

  const all = cats.flatMap((c) => c.posts).sort((a, b) => String(b.date).localeCompare(String(a.date)));
  const latest = all[0] && all[0].date;

  // 首页
  const home = `<section class="intro">
  <h1>${esc(SITE.title)}</h1>
  <p class="lede">${esc(SITE.desc)}</p>
  <p class="stats">共 <b>${all.length}</b> 篇 · ${cats
    .map((c) => `<a href="${c.id}/">${esc(c.title)}</a> <b>${c.posts.length}</b>`)
    .join(' · ')}${latest ? ` · 更新至 <b>${esc(latest)}</b>` : ''}</p>
</section>
${cats
  .map(
    (c) => `<section class="sec">
  <div class="sec-head">
    <h2><a href="${c.id}/">${esc(c.title)}</a></h2>
    <span class="count">${c.posts.length} 篇</span>
  </div>
  ${c.intro ? `<p class="sec-intro">${esc(c.intro)}</p>` : ''}
  <div class="list">${c.posts.slice(0, HOME_LIMIT).map((p) => postItem(p, 0)).join('')}</div>
  ${
    c.posts.length > HOME_LIMIT
      ? `<p class="more"><a href="${c.id}/">全部 ${c.posts.length} 篇 →</a></p>`
      : ''
  }
</section>`,
  )
  .join('')}`;

  fs.writeFileSync(
    path.join(DIST, 'index.html'),
    layout({ depth: 0, title: SITE.title, desc: SITE.desc, body: home, cats, active: null, latest }),
  );

  // 栏目页
  for (const cat of cats) {
    // 页面类栏目：有手写的 site/<id>-index.html 就直接用它，标题靠文件里声明的
    if (cat.pageDir) {
      const custom = path.join(SITE_DIR, `${cat.id}-index.html`);
      const idxPath = path.join(DIST, cat.id, 'index.html');
      if (fs.existsSync(custom)) {
        let html = fs.readFileSync(custom, 'utf8');
        const t = html.match(/<title>([^<]*)<\/title>/i);
        const d = html.match(/<meta name="description" content="([^"]*)"/i);
        const titleOf = (t && t[1].trim()) || cat.title;
        post_titles.set(cat.id, titleOf);
        cat.linkTitle = titleOf;
        const head =
          `<title>${esc(titleOf)} · ${esc(SITE.title)}</title>\n` +
          `<meta name="description" content="${esc(d ? d[1] : cat.intro || SITE.desc)}">`;
        html = /<title>[\s\S]*?<\/title>/i.test(html)
          ? html.replace(/<title>[\s\S]*?<\/title>[\s\S]*?(?=<link rel="stylesheet")/i, `${head}\n`)
          : html;
        html = freshNav(html, `${cat.id}/`, cats, cat.id);
        fs.writeFileSync(idxPath, html);
      } else {
        const body = `<nav class="crumb"><a href="../index.html">首页</a><span>/</span>${esc(cat.title)}</nav>
<h1 class="page-t">${esc(cat.title)}</h1>
${cat.intro ? `<p class="lede">${esc(cat.intro)}</p>` : ''}`;
        fs.writeFileSync(
          idxPath,
          layout({
            depth: 1,
            title: `${cat.title} · ${SITE.title}`,
            desc: cat.intro || SITE.desc,
            body,
            cats,
            active: cat.id,
            latest,
          }),
        );
      }
      continue;
    }
    const body = `<nav class="crumb"><a href="../index.html">首页</a><span>/</span>${esc(cat.title)}</nav>
<h1 class="page-t">${esc(cat.title)}</h1>
${cat.intro ? `<p class="lede">${esc(cat.intro)}</p>` : ''}
<div class="list">${cat.posts.map((p) => postItem(p, 1)).join('')}</div>`;
    fs.mkdirSync(path.join(DIST, cat.id), { recursive: true });
    fs.writeFileSync(
      path.join(DIST, cat.id, 'index.html'),
      layout({
        depth: 1,
        title: `${cat.title} · ${SITE.title}`,
        desc: cat.intro || SITE.desc,
        body,
        cats,
        active: cat.id,
        latest,
      }),
    );
  }

  // 文章页
  let written = 0;
  for (const cat of cats) {
    const idx = cat.posts;
    for (let n = 0; n < idx.length; n += 1) {
      const post = idx[n];
      const ctx = { refs: post.refs, figure: figureFactory(post, 1) };
      const html = post.html != null ? post.html : renderBlock(post.src.replace(/^#\s+.*$/m, ''), ctx);
      fs.mkdirSync(path.join(DIST, cat.id), { recursive: true });

      // 页面类栏目：现成 HTML 直接落盘，用其它栏目拼好的精确侧边栏替掉它自己那份
      if (cat.pageDir) {
        const fixed = cat.exts.includes('.html')
          ? post.html.replace(/<nav class="nav">[\s\S]*?<\/nav>/i, navHtml(cat.id, 1, cats))
          : post.html;
        fs.writeFileSync(path.join(DIST, cat.id, `${post.slug}.html`), fixed);
        written += 1;
        continue;
      }

      const prev = idx[n - 1];
      const next = idx[n + 1];
      const linkOf = (x) => `../${x.cat.id}/${enc(x.slug)}.html`;
      const body = `<nav class="crumb"><a href="../index.html">首页</a><span>/</span><a href="./">${esc(
        cat.title,
      )}</a></nav>
<article class="post">
  <h1 class="post-t">${esc(post.title)}</h1>
  <p class="post-m"><span class="tag">${esc(cat.title)}</span>${
    post.date ? `<time>${esc(post.date)}</time>` : ''
  }<span>约 ${post.minutes} 分钟</span></p>
  <div class="prose">
${html}
  </div>
</article>
<nav class="pager">
  ${prev ? `<a class="pg" href="${linkOf(prev)}"><span>上一篇</span>${esc(prev.title)}</a>` : '<span class="pg off"></span>'}
  ${next ? `<a class="pg next" href="${linkOf(next)}"><span>下一篇</span>${esc(next.title)}</a>` : '<span class="pg off"></span>'}
</nav>
<p class="back"><a href="./">← 返回${esc(cat.title)}</a></p>`;
      fs.mkdirSync(path.join(DIST, cat.id), { recursive: true });
      fs.writeFileSync(
        path.join(DIST, cat.id, `${post.slug}.html`),
        layout({
          depth: 1,
          title: `${post.title} · ${SITE.title}`,
          desc: post.summary,
          body,
          cats,
          active: cat.id,
          latest,
        }),
      );
      written += 1;
    }
  }

  // 404
  fs.writeFileSync(
    path.join(DIST, '404.html'),
    layout({
      depth: 0,
      title: `页面不存在 · ${SITE.title}`,
      desc: '页面不存在',
      body: `<h1 class="page-t">页面不存在</h1><p class="lede">这个地址没有内容，可能是链接过期或路径写错了。</p><p class="back"><a href="./index.html">← 回首页</a></p>`,
      cats,
      active: null,
      latest,
    }),
  );

  console.log(
    `构建完成：${cats.length} 个栏目、${written} 篇文章 → ${path.relative(REPO, DIST)}`,
  );
  for (const c of cats) console.log(`  - ${c.dirName} → /${c.id}/ （${c.posts.length} 篇）`);
}

main();
