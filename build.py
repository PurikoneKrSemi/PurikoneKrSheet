import os
import glob
import shutil
import json
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

    bg_folder = "images/bg"
    bg_files = []
    if os.path.exists(bg_folder):
        exts = ('*.jpg', '*.jpeg', '*.png', '*.webp', '*.gif')
        for ext in exts:
            for f in glob.glob(os.path.join(bg_folder, ext)):
                bg_files.append(f.replace("\\", "/"))

    if os.path.exists("templates/index_template.html"):
        with open("templates/index_template.html", "r", encoding="utf-8") as f:
            template_content = f.read()
        
        json_bg_files = json.dumps(bg_files, ensure_ascii=False)
        final_index = template_content.replace('"{{BG_IMAGES_PLACEHOLDER}}"', json_bg_files)
        
        with open("index.html", "w", encoding="utf-8") as f_out:
            f_out.write(final_index)

if __name__ == "__main__":
    build_site()