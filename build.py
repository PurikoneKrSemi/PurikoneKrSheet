import os
import glob
import shutil
import json
from html import escape as html_escape
from bs4 import BeautifulSoup

# ===== 일본 서버 선행 업데이트 페이지 (jp_news.html) =====
JP_NEWS_DIR = "jp_news"

# 월별 아카이브 아래에 보여 줄 링크 (label, url).  필요 없으면 SIDE_LINKS = [] 로 비우면 된다.
SIDE_LINKS = [
    ("미래시 시트",
     "https://docs.google.com/spreadsheets/d/1i4NJeBFWgVYayfRrNZl_-CxhN5unesAp5m33S_cEMiY/edit?gid=293652162#gid=293652162"),
]

JP_NEWS_STYLE = """
<style>
  /* 카드 폭 고정: 내용 길이에 따라 박스 폭이 변하지 않게 한다 */
  html { scrollbar-gutter: stable; }
  #page-content { width: 100%; max-width: 100%; min-width: 0; }
  /* 월별 아카이브 아래의 외부 링크 (index_template 의 .inline-timeline-panel 자리를 그대로 이용) */
  .jpn-sheetlink a {
    display: flex; align-items: center; justify-content: center; gap: 6px; width: 100%;
    padding: 10px 14px; border-radius: 999px; background: #ec4899; color: #fff;
    font-size: 15px; font-weight: 600; text-decoration: none; text-align: center;
  }
  .jpn-sheetlink a:hover { background: #db2777; }
  .jpn-wrap { width: 100%; max-width: 980px; min-width: 0; margin: 0 auto; box-sizing: border-box; }
  .jpn-item { min-width: 0; }
  .jpn-head-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin: 0 0 14px; }
  .jpn-title { margin: 0; font-size: 22px; font-weight: 700; color: #334155; }
  .jpn-note { margin: 0 0 14px; font-size: 13px; color: #64748b; }

  .jpn-chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 16px; padding: 0; list-style: none; }
  .jpn-chip {
    padding: 8px 18px; border: 0; border-radius: 999px; background: #fff; color: #334155;
    font-size: 15px; cursor: pointer; box-shadow: 0 1px 4px rgba(15, 23, 42, .06);
  }
  .jpn-chip[aria-pressed="true"] { background: #ec4899; color: #fff; }

  .jpn-list { display: flex; flex-direction: column; gap: 12px; margin: 0; padding: 0; list-style: none; }
  .jpn-item { background: #fff; border-radius: 12px; box-shadow: 0 2px 8px rgba(15, 23, 42, .07); overflow: hidden; }
  .jpn-item[hidden] { display: none; }

  .jpn-head {
    width: 100%; display: flex; align-items: center; gap: 14px; padding: 14px 18px;
    border: 0; background: transparent; text-align: left; cursor: pointer; font: inherit; color: inherit;
  }
  .jpn-head:hover { background: #fff7fb; }
  .jpn-thumb { flex: 0 0 auto; width: 120px; height: 68px; object-fit: cover; border-radius: 8px; background: #fce7f3; }
  .jpn-meta { flex: 1 1 auto; min-width: 0; }
  .jpn-line { display: flex; align-items: center; flex-wrap: wrap; gap: 4px 8px; margin-bottom: 4px; }
  .jpn-date { font-size: 15px; font-weight: 600; color: #ec4899; }
  .jpn-badge { padding: 2px 9px; border-radius: 999px; background: #6b7280; color: #fff; font-size: 12px; line-height: 1.5; }
  /* 긴 제목은 한 줄로 줄이고 …로 생략, 카드를 펼치면 전체 제목을 보여 준다 */
  .jpn-name { display: block; font-size: 16px; line-height: 1.5; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .jpn-item.is-open .jpn-name { white-space: normal; overflow: visible; word-break: break-word; }
  .jpn-chev { flex: 0 0 auto; width: 22px; height: 22px; border-radius: 50%; background: #e5e7eb; position: relative; transition: transform .2s ease; }
  .jpn-chev::before {
    content: ''; position: absolute; left: 7px; top: 6px; width: 6px; height: 6px;
    border-right: 2px solid #475569; border-bottom: 2px solid #475569; transform: rotate(45deg);
  }
  .jpn-item.is-open .jpn-chev { transform: rotate(180deg); }

  .jpn-body { display: none; padding: 4px 18px 18px; border-top: 1px solid #f1f5f9; color: #1e293b; line-height: 1.7; font-size: 15px; word-break: break-word; }
  .jpn-item.is-open .jpn-body { display: block; }
  .jpn-body { min-width: 0; max-width: 100%; overflow-x: auto; }
  .jpn-body pre, .jpn-body code { white-space: pre-wrap; overflow-wrap: anywhere; }
  .jpn-body img { max-width: 100%; height: auto; border-radius: 6px; }
  .jpn-body h1, .jpn-body h2, .jpn-body h3, .jpn-body h4 { margin: 18px 0 8px; color: #be185d; line-height: 1.4; }
  .jpn-body h1 { font-size: 20px; } .jpn-body h2 { font-size: 18px; } .jpn-body h3, .jpn-body h4 { font-size: 16px; }
  .jpn-body table { width: 100% !important; max-width: 100%; border-collapse: collapse; margin: 10px 0; display: block; overflow-x: auto; }
  .jpn-body th, .jpn-body td { border: 1px solid #e2e8f0; padding: 6px 10px; }
  .jpn-body a { color: #4f46e5; }
  .jpn-source { margin-top: 16px; font-size: 13px; }
  .jpn-source a { color: #64748b; }

  .jpn-tools { display: flex; align-items: center; gap: 8px; margin-left: auto; flex-wrap: wrap; }
  .jpn-allbtn { padding: 6px 14px; border: 1px solid #f9a8d4; border-radius: 999px; background: #fff; color: #be185d; font-size: 13px; cursor: pointer; font-family: inherit; }
  .jpn-allbtn[aria-pressed="true"] { background: #be185d; border-color: #be185d; color: #fff; }
  .jpn-tag { padding: 2px 9px; border-radius: 999px; background: #fce7f3; color: #be185d; font-size: 12px; line-height: 1.5; }
  .jpn-lang { display: inline-flex; padding: 3px; border-radius: 999px; background: #fff; box-shadow: 0 1px 4px rgba(15, 23, 42, .06); }
  .jpn-lang button { padding: 5px 14px; border: 0; border-radius: 999px; background: transparent; color: #64748b; font-size: 13px; cursor: pointer; font-family: inherit; }
  .jpn-lang button[aria-pressed="true"] { background: #ec4899; color: #fff; }
  .jpn-orig { display: block; margin-top: 2px; font-size: 12px; line-height: 1.4; color: #94a3b8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .jpn-item.is-open .jpn-orig { white-space: normal; overflow: visible; word-break: break-word; }
  .jpn-untr { margin: 10px 0 0; padding: 6px 10px; border-radius: 8px; background: #f8fafc; color: #64748b; font-size: 12px; }

  .jpn-empty, .jpn-error { padding: 40px 12px; text-align: center; color: #64748b; background: #fff; border-radius: 12px; }
  .jpn-error { color: #dc2626; }

  @media (max-width: 900px) {
    .jpn-wrap { margin-top: 16px; }
  }

  @media (max-width: 600px) {
    .jpn-head { padding: 12px 12px; gap: 10px; }
    .jpn-thumb { width: 84px; height: 48px; }
    .jpn-name { font-size: 15px; white-space: normal; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; word-break: break-word; }
    .jpn-item.is-open .jpn-name { display: block; -webkit-line-clamp: unset; }
    .jpn-orig { white-space: normal; display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; }
    .jpn-item.is-open .jpn-orig { display: block; -webkit-line-clamp: unset; }
    .jpn-body { padding: 4px 12px 14px; font-size: 14px; }
    .jpn-chip { padding: 7px 14px; font-size: 14px; }
  }
</style>
"""

JP_NEWS_SCRIPT = r"""
<script>
(function () {
  var MONTHS = __MONTHS__;               // 오름차순 (과거 -> 최신)
  var root = document.getElementById('jpn-root');
  var cache = {};
  var tagOrder = [];                      // jp_news/index.json 의 tags (칩 표시 순서)
  var state = { month: null, all: false, cat: 'all', lang: 'ko', open: {}, view: null };

  try { if (localStorage.getItem('jpn_lang') === 'ja') state.lang = 'ja'; } catch (e) {}

  function labelOf(key) {
    var p = String(key).split('-');
    return p[0] + '년 ' + parseInt(p[1], 10) + '월';
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  /* 방어용: 본문 HTML에서 스크립트/이벤트 속성을 한 번 더 제거 */
  function clean(html) {
    var t = document.createElement('template');
    t.innerHTML = html || '';
    t.content.querySelectorAll('script,iframe,object,embed,style,link,meta,form').forEach(function (n) { n.remove(); });
    t.content.querySelectorAll('*').forEach(function (n) {
      Array.prototype.slice.call(n.attributes).forEach(function (a) {
        var name = a.name.toLowerCase(), val = (a.value || '').trim().toLowerCase();
        if (name.indexOf('on') === 0) n.removeAttribute(a.name);
        if ((name === 'href' || name === 'src') && val.indexOf('javascript:') === 0) n.removeAttribute(a.name);
      });
    });
    return t.innerHTML;
  }

  async function loadMonth(key) {
    if (cache[key]) return cache[key];
    var res = await fetch('jp_news/' + key + '.json', { cache: 'no-cache' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    cache[key] = await res.json();
    return cache[key];
  }

  async function loadTagOrder() {
    try {
      var r = await fetch('jp_news/index.json', { cache: 'no-cache' });
      if (r.ok) { var j = await r.json(); if (Array.isArray(j.tags)) tagOrder = j.tags; }
    } catch (e) {}
  }

  function prep(items) {
    /* '숨김' 처리한 공지는 사이트에 내보내지 않는다 */
    return items.filter(function (it) { return !it.hidden; }).map(function (it) {
      it.cats = Array.isArray(it.cats) ? it.cats : (it.cat ? [it.cat] : []);
      it.tags = Array.isArray(it.tags) ? it.tags : [];
      return it;
    }).sort(function (a, b) {
      return (b.date || '').localeCompare(a.date || '') || String(b.id).localeCompare(String(a.id));
    });
  }

  async function buildView() {
    if (state.all) {
      var list = await Promise.all(MONTHS.map(function (k) { return loadMonth(k).catch(function () { return { items: [] }; }); }));
      var all = [];
      list.forEach(function (d) { all = all.concat(d.items || []); });
      return { title: '전체 월 모아보기', items: prep(all), empty: '표시할 공지가 없습니다.' };
    }
    var data = await loadMonth(state.month);
    return { title: (data.label || labelOf(data.month)) + ' 일본 서버 업데이트', items: prep(data.items || []), empty: '이 달에 표시할 공지가 없습니다.' };
  }

  function keysOf(it) { return it.cats.concat(it.tags); }

  function render(view) {
    state.view = view;
    var items = view.items;
    var cats = [], tags = [], hasKo = false;
    items.forEach(function (it) {
      it.cats.forEach(function (c) { if (cats.indexOf(c) < 0) cats.push(c); });
      it.tags.forEach(function (t) { if (tags.indexOf(t) < 0) tags.push(t); });
      if (it.title_ko || it.html_ko) hasKo = true;
    });
    tags.sort(function (a, b) {                 // 태그는 편집기에서 정한 순서대로
      var i = tagOrder.indexOf(a), j = tagOrder.indexOf(b);
      return (i < 0 ? 999 : i) - (j < 0 ? 999 : j);
    });
    var chips = cats.concat(tags.filter(function (t) { return cats.indexOf(t) < 0; }));
    if (state.cat !== 'all' && chips.indexOf(state.cat) < 0) state.cat = 'all';
    var ko = hasKo && state.lang === 'ko';

    var html = '<div class="jpn-wrap">';
    html += '<div class="jpn-head-row"><h2 class="jpn-title">' + esc(view.title) + '</h2><div class="jpn-tools">';
    html += '<button type="button" class="jpn-allbtn" aria-pressed="' + state.all + '" title="모든 달의 공지를 한 번에 모아 봅니다">전체 월 모아보기</button>';
    if (hasKo) {
      html += '<div class="jpn-lang" role="group" aria-label="언어">' +
        '<button type="button" data-lang="ko" aria-pressed="' + (ko) + '">한국어</button>' +
        '<button type="button" data-lang="ja" aria-pressed="' + (!ko) + '">日本語</button></div>';
    }
    html += '</div></div>';
    html += '<p class="jpn-note">일본 서버 공식 홈페이지의 공지를 모아 둔 페이지입니다.<br>월별 아카이브는 한국 서버 적용 시기(일본 서버 +13개월) 기준이며, 공지 속 날짜는 일본 서버 기준 그대로입니다.<br>항목을 누르면 자세한 내용이 펼쳐집니다.</p>';

    if (chips.length > 0) {
      html += '<ul class="jpn-chips">';
      html += '<li><button type="button" class="jpn-chip" data-cat="all" aria-pressed="' + (state.cat === 'all') + '">모든 것</button></li>';
      chips.forEach(function (c) {
        html += '<li><button type="button" class="jpn-chip" data-cat="' + esc(c) + '" aria-pressed="' + (state.cat === c) + '">' + esc(c) + '</button></li>';
      });
      html += '</ul>';
    }

    if (!items.length) {
      html += '<div class="jpn-empty">' + esc(view.empty) + '</div>';
    } else {
      html += '<ul class="jpn-list">';
      items.forEach(function (it, i) {
        var keys = keysOf(it);
        var show = state.cat === 'all' || keys.indexOf(state.cat) >= 0;
        var key = String(it.id);
        var isOpen = !!state.open[key];
        var useKo = ko && !!it.title_ko;
        var bodyKo = ko && !!it.html_ko;
        html += '<li class="jpn-item' + (isOpen ? ' is-open' : '') + '" data-id="' + esc(key) + '" data-keys="' + esc(keys.join('|')) + '"' + (show ? '' : ' hidden') + '>';
        html += '<button type="button" class="jpn-head" aria-expanded="' + isOpen + '" aria-controls="jpn-b-' + i + '">';
        if (it.thumb) html += '<img class="jpn-thumb" loading="lazy" referrerpolicy="no-referrer" alt="" src="' + esc(it.thumb) + '">';
        html += '<span class="jpn-meta"><span class="jpn-line"><span class="jpn-date">' + esc((it.date || '').replace(/-/g, '/')) + '</span>';
        it.cats.forEach(function (c) { html += '<span class="jpn-badge">' + esc(c) + '</span>'; });
        it.tags.forEach(function (t) { html += '<span class="jpn-tag">' + esc(t) + '</span>'; });
        html += '</span><span class="jpn-name" lang="' + (useKo ? 'ko' : 'ja') + '">' + esc(useKo ? it.title_ko : it.title);
        if (useKo && it.title) html += '<span class="jpn-orig" lang="ja">' + esc(it.title) + '</span>';
        html += '</span></span><span class="jpn-chev" aria-hidden="true"></span></button>';
        html += '<div class="jpn-body" id="jpn-b-' + i + '" lang="' + (bodyKo ? 'ko' : 'ja') + '">' + clean(bodyKo ? it.html_ko : it.html);
        if (ko && !bodyKo) html += '<p class="jpn-untr">아직 번역되지 않은 공지입니다. (일본어 원문)</p>';
        if (it.url) html += '<div class="jpn-source"><a href="' + esc(it.url) + '" target="_blank" rel="noopener noreferrer">공식 홈페이지 원문 보기 ↗</a></div>';
        html += '</div></li>';
      });
      html += '</ul>';
    }
    html += '</div>';
    root.innerHTML = html;
  }

  async function refresh() {
    root.innerHTML = '<div class="jpn-empty">불러오는 중…</div>';
    try {
      render(await buildView());
    } catch (e) {
      root.innerHTML = '<div class="jpn-error">데이터를 불러오지 못했습니다: ' + esc(e.message) + '</div>';
    }
  }

  async function show(key) {
    state.month = key;
    state.all = false;
    state.cat = 'all';
    state.open = {};
    await refresh();
  }

  root.addEventListener('click', function (e) {
    var lang = e.target.closest('.jpn-lang button');
    if (lang) {
      state.lang = lang.getAttribute('data-lang');
      try { localStorage.setItem('jpn_lang', state.lang); } catch (err) {}
      if (state.view) render(state.view);
      return;
    }
    if (e.target.closest('.jpn-allbtn')) {
      state.all = !state.all;
      state.open = {};
      refresh();
      return;
    }
    var chip = e.target.closest('.jpn-chip');
    if (chip) {
      state.cat = chip.getAttribute('data-cat');
      root.querySelectorAll('.jpn-chip').forEach(function (b) {
        b.setAttribute('aria-pressed', String(b === chip));
      });
      root.querySelectorAll('.jpn-item').forEach(function (li) {
        li.hidden = !(state.cat === 'all' || li.getAttribute('data-keys').split('|').indexOf(state.cat) >= 0);
      });
      return;
    }
    var head = e.target.closest('.jpn-head');
    if (head) {
      var li = head.parentNode;
      var open = li.classList.toggle('is-open');
      state.open[li.getAttribute('data-id')] = open;
      head.setAttribute('aria-expanded', String(open));
    }
  });

  /* index_template.html 의 월별 아카이브(사이드바/모바일 드롭다운)가 호출하는 함수 */
  window.toggleCustomDropdown = function (e) {
    e.stopPropagation();
    var w = document.querySelector('.top-tab-dropdown-wrapper');
    if (w) w.classList.toggle('open');
  };

  window.selectCustomOption = function (el, key) {
    document.querySelectorAll('.custom-option').forEach(function (o) { o.classList.remove('selected'); });
    el.classList.add('selected');
    var label = document.getElementById('selected-subtab-label');
    if (label) label.textContent = el.getAttribute('data-archive-label') || el.textContent;
    var w = document.querySelector('.top-tab-dropdown-wrapper');
    if (w) w.classList.remove('open');
    show(key);
  };

  if (MONTHS.length) loadTagOrder().then(function () { show(MONTHS[0]); });   // 처음에는 첫 번째 달 (다른 탭과 동일)
})();
</script>
"""


# 한국 서버는 일본 서버보다 13개월 늦게 업데이트된다. 월별 아카이브 '표시'에만 적용한다.
KR_OFFSET_MONTHS = 13


def _shift_month(key, delta):
    y, m = key.split("-")
    t = int(y) * 12 + (int(m) - 1) + delta
    return "%04d-%02d" % (t // 12, t % 12 + 1)


def _month_label(key):
    """일본 서버 '2025-10' -> 아카이브 표시용 '26년11월' (한국 서버 적용 월).
    index_template.html 의 연도 그룹 파서가 읽는 형식이다."""
    kr = _shift_month(key, KR_OFFSET_MONTHS)
    return "%s년%d월" % (kr[2:4], int(kr[5:7]))


def process_jp_news():
    """jp_news/index.json 을 읽어 jp_news.html 을 만든다."""
    index_path = os.path.join(JP_NEWS_DIR, "index.json")
    months = []
    if os.path.exists(index_path):
        try:
            with open(index_path, "r", encoding="utf-8-sig") as f:
                months = sorted(json.load(f).get("months", []))  # 다른 탭과 같은 오름차순
        except Exception as e:
            print("[jp_news] index.json 을 읽지 못했습니다: %s (%s)" % (os.path.abspath(index_path), e))
    else:
        print("[jp_news] index.json 이 없습니다: %s  (build.py 를 저장소 최상위 폴더에서 실행했는지 확인하세요)" % os.path.abspath(index_path))
    print("[jp_news] 월 %d개 -> jp_news.html" % len(months))

    if not months:
        html = (
            '<div id="page-content"><div class="jpn-wrap">'
            '<div style="padding:40px 12px;text-align:center;color:#64748b;background:#fff;border-radius:12px">'
            '아직 수집된 일본 서버 공지가 없습니다.</div></div></div>'
        )
    else:
        first = 0                                                 # 기본 선택: 첫 번째(가장 오래된) 달 - 다른 탭과 동일
        links = "".join(
            '<div class="inline-timeline-panel jpn-sheetlink"><a href="%s" target="_blank" rel="noopener noreferrer">%s ↗</a></div>'
            % (html_escape(url, quote=True), html_escape(label))
            for label, url in SIDE_LINKS
        )
        options = "".join(
            '<div class="custom-option%s" onclick="selectCustomOption(this, \'%s\', \'%s\')">%s</div>'
            % (" selected" if i == first else "", key, _month_label(key), _month_label(key))
            for i, key in enumerate(months)
        )
        nav = (
            '<div class="subtab-header-panel">'
            '<div class="top-tab-dropdown-wrapper">'
            '<div class="custom-select-trigger" onclick="toggleCustomDropdown(event)">'
            '<span id="selected-subtab-label">%s</span>'
            '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2.5" '
            'stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>'
            '</div>'
            '<div class="custom-select-options">%s</div>'
            '</div>%s</div>'
        ) % (_month_label(months[first]), options, links)
        script = JP_NEWS_SCRIPT.replace("__MONTHS__", json.dumps(months))
        html = (
            JP_NEWS_STYLE
            + '<div id="page-content">' + nav
            + '<div id="jpn-root"></div></div>'
            + script
        )

    with open("jp_news.html", "w", encoding="utf-8") as f:
        f.write(html)


def process_semi_auto_merge(files):
    if not files:
        return ""
    
    with open(files[0], 'r', encoding='utf-8') as f:
        base_soup = BeautifulSoup(f.read(), 'html.parser')

    parsed_contents = []
    for filepath in files:
        tab_name = os.path.splitext(os.path.basename(filepath))[0]
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            container = soup.find(id="content-container")
            html_content = container.decode_contents() if container else soup.decode_contents()
            parsed_contents.append((tab_name, html_content))

    style_tag = base_soup.find('style')
    if not style_tag:
        style_tag = base_soup.new_tag('style')
        if base_soup.head:
            base_soup.head.append(style_tag)
    
    style_tag.string = (style_tag.string or "") + """
        body { padding-bottom: 16px !important; }

        /* 원본 HTML의 본문 크기를 유지하고 가운데 정렬 */
        #page-content {
            margin-left: auto !important;
            margin-right: auto !important;
            box-sizing: border-box;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        /* 하위탭 + 이월시간 패널 레이아웃 */
        .subtab-header-panel {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        /* 모던 커스텀 드롭다운 스타일 (밝은 배경 적용) */
        .top-tab-dropdown-wrapper {
            position: relative !important;
            display: inline-block !important;
            user-select: none;
        }
        .custom-select-trigger {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            padding: 8px 18px;
            font-size: 0.95rem;
            font-weight: 500;
            color: #475569;
            background: rgba(255, 255, 255, 0.85);
            border: none;
            border-radius: 10px 10px 0 0;
            cursor: pointer;
            transition: all 0.2s ease;
            min-width: 110px;
            box-sizing: border-box;
            box-shadow: 0 -2px 6px rgba(0, 0, 0, 0.03);
        }
        .custom-select-trigger:hover {
            background: #ffffff;
            color: #0f172a;
        }
        .custom-select-trigger svg {
            transition: transform 0.2s ease;
        }
        .top-tab-dropdown-wrapper.open .custom-select-trigger {
            background: #ffffff;
            color: #4f46e5;
            font-weight: 600;
        }
        .top-tab-dropdown-wrapper.open .custom-select-trigger svg {
            transform: rotate(180deg);
            stroke: #4f46e5;
        }

        .custom-select-options {
            display: none;
            position: fixed;
            min-width: 140px;
            max-height: 260px;
            overflow-y: auto;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
            z-index: 999999;
            padding: 6px 0;
        }
        .top-tab-dropdown-wrapper.open .custom-select-options {
            display: block;
        }
        .custom-option {
            padding: 8px 14px;
            font-size: 0.88rem;
            color: #334155;
            cursor: pointer;
            transition: background 0.15s ease, color 0.15s ease;
            text-align: left;
        }
        .custom-option:hover {
            background-color: #f1f5f9;
            color: #0f172a;
        }
        .custom-option.selected {
            background-color: #eff6ff;
            color: #4f46e5;
            font-weight: 600;
        }

        /* ⏱️ 이월 시간 박스 (밝은 배경 적용) */
        .inline-timeline-panel {
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(255, 255, 255, 0.85);
            padding: 5px 12px;
            border-radius: 10px 10px 0 0;
            font-size: 0.85rem;
            color: #475569;
            font-weight: 500;
            box-sizing: border-box;
            box-shadow: 0 -2px 6px rgba(0, 0, 0, 0.03);
        }
        .inline-timeline-panel input {
            width: 45px;
            padding: 3px 6px;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            text-align: center;
            font-size: 0.85rem;
            outline: none;
            background: #ffffff;
        }
        .inline-timeline-panel input:focus {
            border-color: #4f46e5;
        }
        .timeline-apply-btn {
            padding: 4px 10px;
            background: #4f46e5;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        tr.timeline-past {
            text-decoration: line-through !important;
            opacity: 0.45 !important;
            color: #888888 !important;
        }
        .timeline-apply-btn:hover { background: #4338ca; }
    """

    script_tag = base_soup.new_tag('script')
    script_tag.string = """
        const BASE_SECONDS = 90;
        
        function toggleCustomDropdown(e) {
            e.stopPropagation();
            const wrapper = document.querySelector('.top-tab-dropdown-wrapper');
            if (!wrapper) return;

            if (wrapper.classList.contains('open')) {
                wrapper.classList.remove('open');
                return;
            }

            const trigger = wrapper.querySelector('.custom-select-trigger');
            const options = wrapper.querySelector('.custom-select-options');
            if (trigger && options) {
                const rect = trigger.getBoundingClientRect();
                options.style.top = rect.bottom + 'px';
                options.style.left = rect.left + 'px';
                options.style.minWidth = rect.width + 'px';
            }
            wrapper.classList.add('open');
        }

        function selectCustomOption(el, tabId, tabName) {
            document.querySelectorAll('.custom-option').forEach(opt => opt.classList.remove('selected'));
            el.classList.add('selected');
            
            const label = document.getElementById('selected-subtab-label');
            if (label) label.textContent = tabName;
            
            const wrapper = document.querySelector('.top-tab-dropdown-wrapper');
            if (wrapper) wrapper.classList.remove('open');

            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            const target = document.getElementById(tabId);
            if (target) target.classList.add('active');
        }

        document.addEventListener('click', (e) => {
            const wrapper = document.querySelector('.top-tab-dropdown-wrapper');
            if (wrapper && !wrapper.contains(e.target)) {
                wrapper.classList.remove('open');
            }
        });

        function timeToSeconds(str) {
            if (!str) return null;
            const m = str.trim().match(/^(\\d{1,2}):([0-5]\\d)/);
            return m ? parseInt(m[1], 10) * 60 + parseInt(m[2], 10) : null;
        }
        function secondsToTime(sec) {
            const sign = sec < 0 ? "-" : ""; sec = Math.abs(sec);
            return sign + Math.floor(sec / 60) + ":" + String(sec % 60).padStart(2, "0");
        }

        function applyCustomTimeline() {
            const input = document.getElementById('user-timeline-input');
            let remainSec = parseInt(input.value, 10);
            if (isNaN(remainSec)) return;
            remainSec = Math.max(20, Math.min(90, remainSec));
            input.value = remainSec;
            const diff = BASE_SECONDS - remainSec;
            const activeTab = document.querySelector('.tab-content.active');
            if (!activeTab) return;
            activeTab.querySelectorAll('table').forEach(table => {
                let lastKnownSec = null;
                table.querySelectorAll('tbody tr').forEach(tr => {
                    const tds = tr.querySelectorAll('td');
                    if (!tds.length) return;
                    const timeCell = tr.querySelector('td.time') || tds[0];
                    if (!timeCell) return;
                    if (!timeCell.hasAttribute('data-orig-text')) {
                        timeCell.setAttribute('data-orig-text', timeCell.textContent.trim());
                    }
                    const origText = timeCell.getAttribute('data-orig-text');
                    const sec = timeToSeconds(origText);
                    let checkSec = null;
                    if (sec !== null) {
                        lastKnownSec = sec;
                        checkSec = sec - diff;
                        const actionText = origText.replace(/^(\\d{1,2}):([0-5]\\d)\\s*/, "");
                        timeCell.textContent = secondsToTime(checkSec) + (actionText ? " " + actionText : "");
                    } else if (lastKnownSec !== null) {
                        checkSec = lastKnownSec - diff;
                    }
                    if (checkSec !== null && checkSec <= 0) {
                        tr.classList.add('timeline-past');

                        tr.querySelectorAll('td').forEach(td => {
                            td.style.setProperty('text-decoration', 'line-through', 'important');
                            td.style.setProperty('opacity', '0.45', 'important');
                            td.style.setProperty('color', '#888888', 'important');
                        });
                    } else {
                        tr.classList.remove('timeline-past');

                        tr.querySelectorAll('td').forEach(td => {
                            td.style.removeProperty('text-decoration');
                            td.style.removeProperty('opacity');
                            td.style.removeProperty('color');
                        });
                    }
                });
            });
        }
    """
    if base_soup.body:
        base_soup.body.append(script_tag)

    options_html, contents = "", ""
    first_tab_name = parsed_contents[0][0] if parsed_contents else ""

    for idx, (tab_name, html) in enumerate(parsed_contents):
        tab_id = f"tab-page-{idx + 1}"
        is_active = "active" if idx == 0 else ""
        selected_cls = "selected" if idx == 0 else ""
        options_html += f'<div class="custom-option {selected_cls}" onclick="selectCustomOption(this, \'{tab_id}\', \'{tab_name}\')">{tab_name}</div>'
        contents += f'<div id="{tab_id}" class="tab-content {is_active}">{html}</div>'

    top_nav_html = f'''
        <div class="subtab-header-panel">
            <div class="top-tab-dropdown-wrapper">
                <div class="custom-select-trigger" onclick="toggleCustomDropdown(event)">
                    <span id="selected-subtab-label">{first_tab_name}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </div>
                <div class="custom-select-options">
                    {options_html}
                </div>
            </div>
            <div class="inline-timeline-panel">
                <span>이월 계산기</span>
                <input type="number" id="user-timeline-input" value="90" min="20" max="90"> 초
                <button type="button" class="timeline-apply-btn" onclick="applyCustomTimeline()">적용</button>
            </div>
        </div>
    '''

    container = base_soup.find(id="content-container")
    if container:
        container["id"] = "page-content"
        container.string = ""
        container.append(BeautifulSoup(top_nav_html + contents, 'html.parser'))

    return str(base_soup)


def process_full_auto_merge(files, is_abyss=False):
    if not files:
        return ""
    
    with open(files[0], 'r', encoding='utf-8') as f:
        base_soup = BeautifulSoup(f.read(), 'html.parser')

    parsed_contents = []
    for filepath in files:
        tab_name = os.path.splitext(os.path.basename(filepath))[0]
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            container = soup.find(id="content-container")

            target_root = container if container else soup

            html_content = target_root.decode_contents() if container else soup.decode_contents()
            parsed_contents.append((tab_name, html_content))

    style_tag = base_soup.find('style')
    if not style_tag:
        style_tag = base_soup.new_tag('style')
        if base_soup.head:
            base_soup.head.append(style_tag)

    style_tag.string = (style_tag.string or "") + """
        html, body {
            overflow-x: hidden !important;
            margin: 0;
            padding: 0;
        }

        body {
            padding-bottom: 16px !important;
        }

        #page-content {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }

        .tab-content {
            display: none;
            width: 100% !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
        }

        .tab-content.active {
            display: block;
        }

        .tab-content table:not(.output-table) { 
            max-width: 100% !important; 
            box-sizing: border-box !important; 
            margin: 0 !important;
        }

        .tab-content table.output-table {
            max-width: 100% !important;
            width: 868px !important;
            table-layout: fixed !important;
        }

        .tab-content tr { 
            max-width: 100% !important; 
        }

        .tab-content table,
        .tab-content table *,
        .tab-content td,
        .tab-content th,
        .tab-content td *,
        .tab-content th * { 
            font-size: 14px !important;
            line-height: 1.4 !important;
        }

        .tab-content td, .tab-content th {
            padding: 8px 12px !important;
            white-space: nowrap !important;
            max-width: 100% !important; 
            box-sizing: border-box !important; 
        }

        .tab-content img { 
            max-width: 100% !important; 
            height: auto !important; 
        }

        .top-tab-dropdown-wrapper {
            position: relative !important;
            display: inline-block !important;
            user-select: none;
        }
        .custom-select-trigger {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            padding: 8px 18px;
            font-size: 0.95rem;
            font-weight: 500;
            color: #475569;
            background: rgba(255, 255, 255, 0.85);
            border: none;
            border-radius: 10px 10px 0 0;
            cursor: pointer;
            transition: all 0.2s ease;
            min-width: 110px;
            box-sizing: border-box;
            box-shadow: 0 -2px 6px rgba(0, 0, 0, 0.03);
        }
        .custom-select-trigger:hover {
            background: #ffffff;
            color: #0f172a;
        }
        .custom-select-trigger svg {
            transition: transform 0.2s ease;
        }
        .top-tab-dropdown-wrapper.open .custom-select-trigger {
            background: #ffffff;
            color: #4f46e5;
            font-weight: 600;
        }
        .top-tab-dropdown-wrapper.open .custom-select-trigger svg {
            transform: rotate(180deg);
            stroke: #4f46e5;
        }

        .custom-select-options {
            display: none;
            position: fixed;
            min-width: 140px;
            max-height: 260px;
            overflow-y: auto;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
            z-index: 999999;
            padding: 6px 0;
        }
        .top-tab-dropdown-wrapper.open .custom-select-options {
            display: block;
        }
        .custom-option {
            padding: 8px 14px;
            font-size: 0.88rem;
            color: #334155;
            cursor: pointer;
            transition: background 0.15s ease, color 0.15s ease;
            text-align: left;
        }
        .custom-option:hover {
            background-color: #f1f5f9;
            color: #0f172a;
        }
        .custom-option.selected {
            background-color: #eff6ff;
            color: #4f46e5;
            font-weight: 600;
        }

        /* 📱 모바일(767px 이하) 가로 스크롤 방지 및 강제 반응형 스타일 추가 */
        @media (max-width: 767px) {
            .tab-content table.output-table {
                width: 100% !important;
                max-width: 100% !important;
                table-layout: auto !important;
            }

            .tab-content table.output-table td,
            .tab-content table.output-table th {
                white-space: normal !important;
                word-break: break-word !important;
                overflow-wrap: anywhere !important;
                padding: 4px 2px !important;
            }

            .tab-content table.output-table td.img-td,
            .tab-content table.output-table th.img-td {
                width: auto !important;
                min-width: 0 !important;
                max-width: none !important;
                height: auto !important;
            }

            .tab-content table.output-table td.img-td img,
            .tab-content table.output-table th.img-td img {
                width: 100% !important;
                max-width: 45px !important;
                height: auto !important;
                min-width: 0 !important;
                min-height: 0 !important;
                object-fit: contain !important;
            }
        }
    """

    script_tag = base_soup.new_tag('script')
    script_tag.string = """
        function toggleCustomDropdown(e) {
            e.stopPropagation();
            const wrapper = document.querySelector('.top-tab-dropdown-wrapper');
            if (!wrapper) return;

            if (wrapper.classList.contains('open')) {
                wrapper.classList.remove('open');
                return;
            }

            const trigger = wrapper.querySelector('.custom-select-trigger');
            const options = wrapper.querySelector('.custom-select-options');
            if (trigger && options) {
                const rect = trigger.getBoundingClientRect();
                options.style.top = rect.bottom + 'px';
                options.style.left = rect.left + 'px';
                options.style.minWidth = rect.width + 'px';
            }
            wrapper.classList.add('open');
        }

        function selectCustomOption(el, tabId, tabName) {
            document.querySelectorAll('.custom-option').forEach(opt => opt.classList.remove('selected'));
            el.classList.add('selected');
            
            const label = document.getElementById('selected-subtab-label');
            if (label) label.textContent = tabName;
            
            const wrapper = document.querySelector('.top-tab-dropdown-wrapper');
            if (wrapper) wrapper.classList.remove('open');

            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            const target = document.getElementById(tabId);
            if (target) target.classList.add('active');
            fitActiveTab();
        }

        document.addEventListener('click', (e) => {
            const wrapper = document.querySelector('.top-tab-dropdown-wrapper');
            if (wrapper && !wrapper.contains(e.target)) {
                wrapper.classList.remove('open');
            }
        });

        function fitActiveTab() {
            const activeTab = document.querySelector('.tab-content.active');
            if (!activeTab) return;
            activeTab.style.transform = 'none';
            activeTab.style.marginBottom = '0px';
        }
        window.addEventListener('resize', fitActiveTab);
        document.addEventListener('DOMContentLoaded', fitActiveTab);
        setTimeout(fitActiveTab, 100);
    """
    if base_soup.body:
        base_soup.body.append(script_tag)

    options_html, contents = "", ""
    first_tab_name = parsed_contents[0][0] if parsed_contents else ""

    for idx, (tab_name, html) in enumerate(parsed_contents):
        tab_id = f"tab-page-{idx + 1}"
        is_active = "active" if idx == 0 else ""
        selected_cls = "selected" if idx == 0 else ""
        options_html += f'<div class="custom-option {selected_cls}" onclick="selectCustomOption(this, \'{tab_id}\', \'{tab_name}\')">{tab_name}</div>'
        contents += f'<div id="{tab_id}" class="tab-content {is_active}">{html}</div>'

    top_nav_html = f"""
        <div class="subtab-header-panel">
            <div class="top-tab-dropdown-wrapper">
                <div class="custom-select-trigger" onclick="toggleCustomDropdown(event)">
                    <span id="selected-subtab-label">{first_tab_name}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
                        stroke="#64748b" stroke-width="2.5"
                        stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </div>
                <div class="custom-select-options">
                    {options_html}
                </div>
            </div>
        </div>
    """

    container = base_soup.find(id="content-container")
    if container:
        container["id"] = "page-content"
        container.string = ""
        container.append(BeautifulSoup(top_nav_html + contents, 'html.parser'))

    return str(base_soup)

def build_site():
    semi_files = sorted(glob.glob("data/semi_auto/*.html"))
    merged_semi = process_semi_auto_merge(semi_files)
    if merged_semi:
        with open("semi_auto.html", "w", encoding="utf-8") as f:
            f.write(merged_semi)

    full_files = sorted(glob.glob("data/full_auto/*.html"))
    merged_full = process_full_auto_merge(full_files)
    if merged_full:
        with open("full_auto.html", "w", encoding="utf-8") as f:
            f.write(merged_full)

    abyss_files = sorted(glob.glob("data/abyss/*.html"))
    merged_abyss = process_full_auto_merge(abyss_files, is_abyss=True)
    if merged_abyss:
        with open("abyss.html", "w", encoding="utf-8") as f:
            f.write(merged_abyss)

    if os.path.exists("data/recruits.html"):
        with open("data/recruits.html", "r", encoding="utf-8") as f:
            with open("recruits.html", "w", encoding="utf-8") as f_out:
                f_out.write(f.read())

    # 일본 서버 선행 업데이트 (crawl_news.py 가 만든 jp_news/*.json 이 있을 때)
    process_jp_news()

    if os.path.exists("templates/index_template.html"):
        with open("templates/index_template.html", "r", encoding="utf-8") as f:
            template_content = f.read()
        
        with open("index.html", "w", encoding="utf-8") as f_out:
            f_out.write(template_content)

if __name__ == "__main__":
    build_site()