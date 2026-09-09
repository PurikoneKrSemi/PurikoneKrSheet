import os
import glob
from bs4 import BeautifulSoup

def process_semi_auto_merge(files):
    """세미오토 전용 병합 로직 (타임라인 컨트롤 포함)"""
    if not files:
        return ""
    
    # 1. 첫 번째 파일 기반으로 기본 문서 생성
    with open(files[0], 'r', encoding='utf-8') as f:
        base_soup = BeautifulSoup(f.read(), 'html.parser')

    # 2. 월별 파일 파싱
    parsed_contents = []
    for filepath in files:
        tab_name = os.path.splitext(os.path.basename(filepath))[0]
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            container = soup.find(id="content-container")
            html_content = container.decode_contents() if container else soup.decode_contents()
            parsed_contents.append((tab_name, html_content))

    # 3. CSS 주입
    style_tag = base_soup.find('style')
    if not style_tag:
        style_tag = base_soup.new_tag('style')
        if base_soup.head:
            base_soup.head.append(style_tag)
    
    style_tag.string = (style_tag.string or "") + """
        body { padding-bottom: 120px !important; display: flex; flex-direction: column; align-items: center; }
        #content-container { width: 100%; max-width: 1000px; margin: 0 auto; display: flex; flex-direction: column; align-items: center; }
        .tab-content { display: none; width: 100%; margin: 0 auto; }
        .tab-content.active { display: flex; flex-direction: column; align-items: center; }
        .tab-content table { margin-left: auto; margin-right: auto; }
        .bottom-fixed-panel { position: fixed; bottom: 0; left: 0; right: 0; width: 100%; background: #ffffff; border-top: 1px solid #cbd5e1; box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.1); padding: 10px 16px; z-index: 9999; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; box-sizing: border-box; }
        .timeline-control-panel { display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 0.85rem; width: 100%; }
        .timeline-control-panel input { width: 60px; padding: 4px 8px; border: 1px solid #cbd5e1; border-radius: 4px; text-align: center; }
        .tab-scroll-container { width: 100%; margin: 0 auto; overflow-x: auto; white-space: nowrap; padding-bottom: 4px; cursor: grab; user-select: none; text-align: center; -ms-overflow-style: none; scrollbar-width: none; }
        .tab-scroll-container::-webkit-scrollbar { display: none; }
        .tab-scroll-container.active { cursor: grabbing; }
        .tab-nav { display: inline-flex; justify-content: center; gap: 6px; }
        .tab-btn { flex: 0 0 auto; padding: 6px 14px; background: #e2e8f0; border: none; border-radius: 6px; color: #475569; font-weight: 600; font-size: 0.8rem; cursor: pointer; transition: background 0.2s; }
        .tab-btn:hover { background: #cbd5e1; }
        .tab-btn.active { background: var(--primary-color, #4f46e5); color: #fff; }
        tr.timeline-past { text-decoration: line-through !important; opacity: 0.45 !important; color: #888888 !important; }
    """

    # 4. 스크립트 주입
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
                isDown = true; window.isTabDragging = false; dragDistance = 0;
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

    # 5. HTML 동적 재구성
    btns, contents = "", ""
    for idx, (tab_name, html) in enumerate(parsed_contents):
        tab_id = f"tab-page-{idx + 1}"
        is_active = "active" if idx == 0 else ""
        btns += f'<button class="tab-btn {is_active}" onclick="openTab(event, \'{tab_id}\')">{tab_name}</button>'
        contents += f'<div id="{tab_id}" class="tab-content {is_active}">{html}</div>'

    panel_html = f'''
        <div class="bottom-fixed-panel">
            <div class="timeline-control-panel">
                <strong>⏱️ 남은 시간 설정:</strong>
                <input type="number" id="user-timeline-input" value="90" min="20" max="90"> 초
                <button class="card-btn add-space-btn" style="padding: 4px 12px; cursor: pointer;" onclick="applyCustomTimeline()">적용</button>
            </div>
            <div class="tab-scroll-container"><div class="tab-nav">{btns}</div></div>
        </div>
    '''
    
    container = base_soup.find(id="content-container")
    if container:
        container.string = ""
        container.append(BeautifulSoup(contents + panel_html, 'html.parser'))

    return str(base_soup)


def process_full_auto_merge(files):
    """풀오토 전용 병합 로직 (테이블 스케일링 포함)"""
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
        body { padding-bottom: 80px !important; display: flex; flex-direction: column; align-items: center; }
        #content-container { width: 100% !important; max-width: 100% !important; display: flex; flex-direction: column; align-items: center; box-sizing: border-box !important; }
        .tab-content { display: none; transform-origin: top center; margin: 0 auto; max-width: 100% !important; box-sizing: border-box !important; }
        .tab-content.active { display: flex; flex-direction: column; align-items: center; }
        .tab-content table { max-width: 100% !important; box-sizing: border-box !important; table-layout: fixed !important; }
        .tab-content tr { max-width: 100% !important; }
        .tab-content td, .tab-content th { white-space: normal !important; word-break: break-all !important; overflow-wrap: break-word !important; max-width: 100% !important; box-sizing: border-box !important; }
        .tab-content img { max-width: 100% !important; height: auto !important; }
        .bottom-fixed-panel { position: fixed; bottom: 0; left: 0; right: 0; width: 100%; background: #ffffff; border-top: 1px solid #cbd5e1; box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.1); padding: 8px 16px; z-index: 9999; display: flex; align-items: center; justify-content: center; box-sizing: border-box; }
        .tab-scroll-container { width: 100%; margin: 0 auto; overflow-x: auto; white-space: nowrap; padding: 2px 0; cursor: grab; user-select: none; text-align: center; -ms-overflow-style: none; scrollbar-width: none; }
        .tab-scroll-container::-webkit-scrollbar { display: none; }
        .tab-scroll-container.active { cursor: grabbing; }
        .tab-nav { display: inline-flex; justify-content: center; gap: 6px; }
        .tab-btn { flex: 0 0 auto; padding: 8px 16px; background: #e2e8f0; border: none; border-radius: 6px; color: #475569; font-weight: 600; font-size: 0.85rem; cursor: pointer; transition: background 0.2s; }
        .tab-btn:hover { background: #cbd5e1; }
        .tab-btn.active { background: var(--primary-color, #4f46e5); color: #fff; }
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
                isDown = true; window.isTabDragging = false; dragDistance = 0;
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

    panel_html = f'''
        <div class="bottom-fixed-panel">
            <div class="tab-scroll-container"><div class="tab-nav">{btns}</div></div>
        </div>
    '''
    
    container = base_soup.find(id="content-container")
    if container:
        container.string = ""
        container.append(BeautifulSoup(contents + panel_html, 'html.parser'))

    return str(base_soup)


def build_site():
    # 자연어 정렬(2026-08, 2026-09 순서대로 정렬)
    semi_files = sorted(glob.glob("data/semi_auto/*.html"))
    full_files = sorted(glob.glob("data/full_auto/*.html"))

    # 각각에 맞는 스크립트로 독립 병합 수행
    merged_semi_auto = process_semi_auto_merge(semi_files)
    merged_full_auto = process_full_auto_merge(full_files)

    recruits_html = ""
    if os.path.exists("data/recruits.html"):
        with open("data/recruits.html", "r", encoding="utf-8") as f:
            recruits_html = f.read()

    # index 템플릿 치환
    with open("templates/index_template.html", "r", encoding="utf-8") as f:
        template = f.read()

    final_index = template.replace("<!-- SEMI_AUTO_PLACEHOLDER -->", merged_semi_auto)\
                           .replace("<!-- FULL_AUTO_PLACEHOLDER -->", merged_full_auto)\
                           .replace("<!-- RECRUITS_PLACEHOLDER -->", recruits_html)

    os.makedirs("dist", exist_ok=True)
    with open("dist/index.html", "w", encoding="utf-8") as f:
        f.write(final_index)

if __name__ == "__main__":
    build_site()