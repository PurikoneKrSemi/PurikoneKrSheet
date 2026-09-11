import os
import glob
import shutil
from bs4 import BeautifulSoup

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
        body { padding-bottom: 16px !important; display: flex; flex-direction: column; align-items: center; }
        #page-content { width: 100%; max-width: 1000px; margin: 0 auto; display: flex; flex-direction: column; align-items: center; }
        .tab-content { display: none; width: 100%; margin: 0 auto; }
        .tab-content.active { display: flex; flex-direction: column; align-items: center; }
        .tab-content table { margin-left: auto; margin-right: auto; }

        /* 하위탭 + 이월 시간 설정: 상단 고정(2단바)에 한 덩어리로 붙임 */
        .top-tab-panel { width: 100%; background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 8px 16px 6px; box-sizing: border-box; }
        .timeline-control-panel { display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 0.8rem; width: 100%; margin-top: 6px; padding-top: 6px; border-top: 1px solid #f1f5f9; }
        .timeline-control-panel input { width: 60px; padding: 4px 8px; border: 1px solid #cbd5e1; border-radius: 4px; text-align: center; }
        
        /* 적용 버튼 스타일 */
        .timeline-apply-btn {
            padding: 5px 14px;
            background: #4f46e5;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s, transform 0.1s;
        }
        .timeline-apply-btn:hover { background: #4338ca; }
        .timeline-apply-btn:active { transform: scale(0.97); }

        /* 상단 하위탭 가로 스크롤 및 스크롤바 강제 표시 */
        .tab-scroll-container { 
            width: 100% !important; 
            max-width: 100% !important; 
            margin: 0 auto !important; 
            overflow-x: auto !important; 
            white-space: nowrap !important; 
            padding-bottom: 4px !important; 
            cursor: grab; 
            user-select: none; 
            text-align: center; 
            box-sizing: border-box !important;
            scrollbar-width: auto !important;
            -ms-overflow-style: auto !important;
        }
        .tab-scroll-container::-webkit-scrollbar { 
            display: block !important; 
            height: 8px !important; 
        }
        .tab-scroll-container::-webkit-scrollbar-track {
            background: #f1f5f9 !important;
            border-radius: 4px !important;
        }
        .tab-scroll-container::-webkit-scrollbar-thumb {
            background: #cbd5e1 !important;
            border-radius: 4px !important;
        }
        .tab-scroll-container::-webkit-scrollbar-thumb:hover {
            background: #94a3b8 !important;
        }
        .tab-scroll-container.active { cursor: grabbing; }
        .tab-nav { 
            display: inline-flex !important; 
            justify-content: center !important; 
            gap: 2px !important; 
            min-width: max-content !important;
            background: #eef1f5 !important;
            border-radius: 8px !important;
            padding: 4px !important;
        }
        .tab-btn { 
            flex: 0 0 auto !important; 
            padding: 8px 16px !important; 
            background: transparent; 
            border: none; 
            border-radius: 8px; 
            color: #64748b; 
            font-weight: 500; 
            font-size: 0.85rem; 
            cursor: pointer; 
            transition: background 0.2s, color 0.2s; 
        }
        .tab-btn { -webkit-user-drag: none; user-select: none; }
        .tab-btn:hover { background: rgba(255,255,255,0.6); color: #334155; }
        .tab-btn.active { background: #4f46e5; color: #fff; font-weight: 600; }
        tr.timeline-past { text-decoration: line-through !important; opacity: 0.45 !important; color: #888888 !important; }
    """

    script_tag = base_soup.new_tag('script')
    script_tag.string = """
        const BASE_SECONDS = 90;
        function openTab(evt, tabId) {
            if (window.isTabDragging) return;
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            evt.currentTarget.classList.add('active');
        }
        function initTabDragScroll() {
            const slider = document.querySelector('.tab-scroll-container');
            if (!slider) return;
            let isDown = false, startX, scrollLeft, dragDistance = 0;
            slider.addEventListener('mousedown', (e) => {
                e.preventDefault(); isDown = true; window.isTabDragging = false; dragDistance = 0;
                slider.classList.add('active'); startX = e.pageX - slider.offsetLeft; scrollLeft = slider.scrollLeft;
            });
            slider.addEventListener('mouseleave', () => { isDown = false; slider.classList.remove('active'); });
            slider.addEventListener('mouseup', () => {
                isDown = false; slider.classList.remove('active');
                if (dragDistance > 5) { window.isTabDragging = true; setTimeout(() => { window.isTabDragging = false; }, 50); }
            });
            slider.addEventListener('mousemove', (e) => {
                if (!isDown) return; e.preventDefault();
                const x = e.pageX - slider.offsetLeft;
                dragDistance = Math.abs(x - startX);
                slider.scrollLeft = scrollLeft - (x - startX) * 1.5;
            });
        }
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
                    if (checkSec !== null && checkSec <= 0) tr.classList.add('timeline-past');
                    else tr.classList.remove('timeline-past');
                });
            });
        }
        document.addEventListener('DOMContentLoaded', initTabDragScroll);
    """
    if base_soup.body:
        base_soup.body.append(script_tag)

    btns, contents = "", ""
    for idx, (tab_name, html) in enumerate(parsed_contents):
        tab_id = f"tab-page-{idx + 1}"
        is_active = "active" if idx == 0 else ""
        btns += f'<button class="tab-btn {is_active}" onclick="openTab(event, \'{tab_id}\')">{tab_name}</button>'
        contents += f'<div id="{tab_id}" class="tab-content {is_active}">{html}</div>'

    top_nav_html = f'''
        <div class="top-tab-panel">
            <div class="tab-scroll-container"><div class="tab-nav">{btns}</div></div>
            <div class="timeline-control-panel">
                <strong>⏱️ 이월 시간 설정:</strong>
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


def process_full_auto_merge(files):
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
        html, body { overflow-x: hidden !important; margin: 0; padding: 0; width: 100% !important; }
        body { padding-bottom: 16px !important; display: flex; flex-direction: column; align-items: center; }
        #page-content { width: 100% !important; max-width: 100% !important; display: flex; flex-direction: column; align-items: center; box-sizing: border-box !important; }
        .tab-content { display: none; transform-origin: top center; margin: 0 auto; max-width: 100% !important; box-sizing: border-box !important; }
        .tab-content.active { display: flex; flex-direction: column; align-items: center; }
        .tab-content table { max-width: 100% !important; box-sizing: border-box !important; table-layout: fixed !important; }
        .tab-content tr { max-width: 100% !important; }
        .tab-content td, .tab-content th { white-space: normal !important; word-break: break-all !important; overflow-wrap: break-word !important; max-width: 100% !important; box-sizing: border-box !important; }
        .tab-content img { max-width: 100% !important; height: auto !important; }

        /* 하위탭: 상단 고정(2단바) */
        .top-tab-panel { width: 100%; background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 8px 16px; box-sizing: border-box; }
        
        /* 상단 하위탭 가로 스크롤 및 스크롤바 강제 표시 */
        .tab-scroll-container { 
            width: 100% !important; 
            max-width: 100% !important; 
            margin: 0 auto !important; 
            overflow-x: auto !important; 
            white-space: nowrap !important; 
            padding: 4px 0 8px 0 !important; 
            cursor: grab; 
            user-select: none; 
            text-align: center; 
            box-sizing: border-box !important;
            scrollbar-width: auto !important;
            -ms-overflow-style: auto !important;
        }
        .tab-scroll-container::-webkit-scrollbar { 
            display: block !important; 
            height: 8px !important; 
        }
        .tab-scroll-container::-webkit-scrollbar-track {
            background: #f1f5f9 !important;
            border-radius: 4px !important;
        }
        .tab-scroll-container::-webkit-scrollbar-thumb {
            background: #cbd5e1 !important;
            border-radius: 4px !important;
        }
        .tab-scroll-container::-webkit-scrollbar-thumb:hover {
            background: #94a3b8 !important;
        }
        .tab-scroll-container.active { cursor: grabbing; }
        .tab-nav { 
            display: inline-flex !important; 
            justify-content: center !important; 
            gap: 2px !important; 
            min-width: max-content !important;
            background: #eef1f5 !important;
            border-radius: 8px !important;
            padding: 4px !important;
        }
        .tab-btn { 
            flex: 0 0 auto !important; 
            padding: 8px 16px !important; 
            background: transparent; 
            border: none; 
            border-radius: 8px; 
            color: #64748b; 
            font-weight: 500; 
            font-size: 0.85rem; 
            cursor: pointer; 
            transition: background 0.2s, color 0.2s; 
        }
        .tab-btn { -webkit-user-drag: none; user-select: none; }
        .tab-btn:hover { background: rgba(255,255,255,0.6); color: #334155; }
        .tab-btn.active { background: #4f46e5; color: #fff; font-weight: 600; }
    """

    script_tag = base_soup.new_tag('script')
    script_tag.string = """
        function openTab(evt, tabId) {
            if (window.isTabDragging) return;
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            evt.currentTarget.classList.add('active');
            fitActiveTab();
        }
        function fitActiveTab() {
            const activeTab = document.querySelector('.tab-content.active');
            if (!activeTab) return;
            activeTab.style.transform = 'none';
            const windowWidth = window.innerWidth - 16;
            const contentWidth = activeTab.scrollWidth;
            if (contentWidth > windowWidth && windowWidth > 0) {
                const scale = windowWidth / contentWidth;
                activeTab.style.transform = 'scale(' + scale + ')';
                activeTab.style.marginBottom = '-' + (activeTab.offsetHeight * (1 - scale)) + 'px';
            } else {
                activeTab.style.transform = 'none';
                activeTab.style.marginBottom = '0px';
            }
        }
        function initTabDragScroll() {
            const slider = document.querySelector('.tab-scroll-container');
            if (!slider) return;
            let isDown = false, startX, scrollLeft, dragDistance = 0;
            slider.addEventListener('mousedown', (e) => {
                e.preventDefault(); isDown = true; window.isTabDragging = false; dragDistance = 0;
                slider.classList.add('active'); startX = e.pageX - slider.offsetLeft; scrollLeft = slider.scrollLeft;
            });
            slider.addEventListener('mouseleave', () => { isDown = false; slider.classList.remove('active'); });
            slider.addEventListener('mouseup', () => {
                isDown = false; slider.classList.remove('active');
                if (dragDistance > 5) { window.isTabDragging = true; setTimeout(() => { window.isTabDragging = false; }, 50); }
            });
            slider.addEventListener('mousemove', (e) => {
                if (!isDown) return; e.preventDefault();
                const x = e.pageX - slider.offsetLeft;
                dragDistance = Math.abs(x - startX);
                slider.scrollLeft = scrollLeft - (x - startX) * 1.5;
            });
        }
        window.addEventListener('resize', fitActiveTab);
        document.addEventListener('DOMContentLoaded', () => { initTabDragScroll(); fitActiveTab(); });
    """
    if base_soup.body:
        base_soup.body.append(script_tag)

    btns, contents = "", ""
    for idx, (tab_name, html) in enumerate(parsed_contents):
        tab_id = f"tab-page-{idx + 1}"
        is_active = "active" if idx == 0 else ""
        btns += f'<button class="tab-btn {is_active}" onclick="openTab(event, \'{tab_id}\')">{tab_name}</button>'
        contents += f'<div id="{tab_id}" class="tab-content {is_active}">{html}</div>'

    top_nav_html = f'''
        <div class="top-tab-panel">
            <div class="tab-scroll-container"><div class="tab-nav">{btns}</div></div>
        </div>
    '''

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
    merged_abyss = process_full_auto_merge(abyss_files)
    if merged_abyss:
        with open("abyss.html", "w", encoding="utf-8") as f:
            f.write(merged_abyss)

    if os.path.exists("data/recruits.html"):
        with open("data/recruits.html", "r", encoding="utf-8") as f:
            with open("recruits.html", "w", encoding="utf-8") as f_out:
                f_out.write(f.read())

    if os.path.exists("templates/index_template.html"):
        shutil.copy("templates/index_template.html", "index.html")
   
if __name__ == "__main__":
    build_site()