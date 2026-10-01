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
            .subtab-header-panel {
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
        tr.timeline-past { text-decoration: line-through !important; opacity: 0.45 !important; color: #888888 !important; }
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

            // 상위 탭바가 가로 스크롤 컨테이너(overflow-x:auto)라 position:absolute로는
            // 세로로 잘려서 안 보이므로, position:fixed로 두고 트리거 기준 좌표를 직접 계산해서 배치
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

def _add_mobile_full_auto_view(document_soup, root_soup):
    """풀오토/심연토벌전용 모바일 뷰를 원본 테이블 옆에 생성한다.

    - 하나의 table 안에 thead/tbody가 여러 번 반복되는 심연토벌전 구조 대응
    - 심연토벌전 헤더는 '전초퀘스트 / 노말·하드 / 베하·익스'만 표시
    - 심연토벌전 전초퀘스트는 이미지 1열을 빈칸으로 유지
    - CR 2행 구조 대응
    - 세미오토에서는 이 함수가 호출되지 않는다.
    """
    tables = root_soup.select('table.output-table')

    def append_fragment(target, html):
        """HTML fragment의 자식 노드만 안전하게 target에 추가."""
        fragment = BeautifulSoup(html, 'html.parser')
        for child in list(fragment.contents):
            target.append(child)

    def append_column_header(mobile_view, row):
        """심연토벌전의 섹션 헤더를 모바일용으로 추가."""
        cells = row.find_all(['th', 'td'], recursive=False)

        if not cells:
            return

        row_classes = row.get('class') or []
        link = row.find('a')

        # ---------------------------------
        # 최상단 링크 행
        # ---------------------------------
        if (
            'guide-link-row' in row_classes
            or (link is not None and len(cells) == 1)
        ):
            title_box = document_soup.new_tag('div')
            title_box['class'] = ['mobile-full-auto-title']

            if link:
                append_fragment(title_box, str(link))
            else:
                title_box.string = row.get_text(
                    ' ',
                    strip=True
                )

            mobile_view.append(title_box)
            return

        # ---------------------------------
        # 심연토벌전 섹션 헤더
        #
        # 원본:
        # 전초퀘스트 | 캐릭터 | 딜량 | 조작
        # 노말/하드   | 캐릭터 | 딜량 | 조작
        # 베하/익스   | 캐릭터 | 딜량 | 조작
        #
        # 모바일:
        # 전초퀘스트
        # 노말/하드
        # 베하/익스
        # ---------------------------------
        if (
            len(cells) >= 4
            and cells[1].get_text(
                ' ',
                strip=True
            ) == '캐릭터'
            and cells[2].get_text(
                ' ',
                strip=True
            ) == '딜량'
            and cells[3].get_text(
                ' ',
                strip=True
            ) == '조작'
        ):
            header_text = cells[0].get_text(
                ' ',
                strip=True
            )

            header_box = document_soup.new_tag('div')
            header_box['class'] = [
                'mobile-full-auto-section-header'
            ]
            header_box.string = header_text

            mobile_view.append(header_box)

    for table in tables:

        mobile_view = document_soup.new_tag('div')
        mobile_view['class'] = [
            'mobile-full-auto-view'
        ]

        # 현재 tbody가 어느 섹션에 속하는지 기억
        current_section_name = None

        # ---------------------------------
        # 하나의 table 안에 있는
        # 모든 thead / tbody를 순서대로 처리
        # ---------------------------------
        sections = table.find_all(
            ['thead', 'tbody'],
            recursive=False
        )

        for section in sections:

            rows = section.find_all(
                'tr',
                recursive=False
            )

            # =================================
            # THEAD
            # =================================
            if section.name == 'thead':

                for row in rows:

                    cells = row.find_all(
                        ['th', 'td'],
                        recursive=False
                    )

                    if not cells:
                        continue

                    # 현재 섹션 이름 기억
                    #
                    # 전초퀘스트
                    # 노말/하드
                    # 베하/익스
                    if (
                        len(cells) >= 4
                        and cells[1].get_text(
                            ' ',
                            strip=True
                        ) == '캐릭터'
                        and cells[2].get_text(
                            ' ',
                            strip=True
                        ) == '딜량'
                        and cells[3].get_text(
                            ' ',
                            strip=True
                        ) == '조작'
                    ):
                        current_section_name = cells[0].get_text(
                            ' ',
                            strip=True
                        )

                    append_column_header(
                        mobile_view,
                        row
                    )

                continue

            # =================================
            # TBODY
            # =================================
            i = 0

            while i < len(rows):

                row = rows[i]

                cells = row.find_all(
                    ['td', 'th'],
                    recursive=False
                )

                if not cells:
                    i += 1
                    continue

                # ---------------------------------
                # 혹시 tbody 안에 헤더가 들어있는
                # 변형 HTML도 대응
                # ---------------------------------
                if (
                    len(cells) >= 4
                    and cells[1].get_text(
                        ' ',
                        strip=True
                    ) == '캐릭터'
                    and cells[2].get_text(
                        ' ',
                        strip=True
                    ) == '딜량'
                    and cells[3].get_text(
                        ' ',
                        strip=True
                    ) == '조작'
                    and not row.find('img')
                ):
                    current_section_name = cells[0].get_text(
                        ' ',
                        strip=True
                    )

                    append_column_header(
                        mobile_view,
                        row
                    )

                    i += 1
                    continue

                # =================================
                # 이미지가 있는 행 = 1개 편성
                # =================================
                if row.find('img'):

                    team_box = document_soup.new_tag('div')
                    team_box['class'] = [
                        'mobile-full-auto-team'
                    ]

                    # ---------------------------------
                    # 이미지 영역
                    # ---------------------------------
                    image_grid = document_soup.new_tag('div')
                    image_grid['class'] = [
                        'mobile-full-auto-images'
                    ]

                    # =================================
                    # 심연토벌전 전초퀘스트
                    #
                    # 원본 구조:
                    # [빈칸] [캐릭터] [캐릭터] [캐릭터]
                    # [캐릭터] [캐릭터]
                    #
                    # 모바일에서도 첫 번째 칸을
                    # 빈칸으로 유지
                    # =================================
                    if current_section_name == '전초퀘스트':

                        empty_item = document_soup.new_tag(
                            'div'
                        )
                        empty_item['class'] = [
                            'mobile-full-auto-image-cell'
                        ]

                        image_grid.append(
                            empty_item
                        )

                        # 실제 이미지는 5개
                        image_cells = [
                            c
                            for c in cells
                            if c.find('img')
                        ][:5]

                    else:

                        # ---------------------------------
                        # 일반 풀오토 / 심연토벌전
                        # ---------------------------------
                        image_cells = [
                            c
                            for c in cells
                            if c.find('img')
                        ][:6]

                    # ---------------------------------
                    # 이미지 추가
                    # ---------------------------------
                    for cell in image_cells:

                        item = document_soup.new_tag(
                            'div'
                        )
                        item['class'] = [
                            'mobile-full-auto-image-cell'
                        ]

                        img = cell.find('img')

                        if img:
                            item.append(
                                BeautifulSoup(
                                    str(img),
                                    'html.parser'
                                )
                            )

                        image_grid.append(
                            item
                        )

                    team_box.append(
                        image_grid
                    )

                    # =================================
                    # 딜량 / 조작 셀 찾기
                    # =================================
                    damage_cell = None
                    operation_cell = None

                    for cell in cells:

                        rowspan = cell.get(
                            'rowspan'
                        )

                        if rowspan == '2':

                            if damage_cell is None:
                                damage_cell = cell

                            elif operation_cell is None:
                                operation_cell = cell

                    # rowspan이 없는 기존 구조 대응
                    if (
                        damage_cell is None
                        and len(cells) >= 8
                    ):
                        damage_cell = cells[6]

                    if (
                        operation_cell is None
                        and len(cells) >= 8
                    ):
                        operation_cell = cells[7]

                    # =================================
                    # 다음 행이 CR 행인지 확인
                    # =================================
                    cr_row = None

                    if i + 1 < len(rows):

                        next_row = rows[i + 1]

                        next_cells = next_row.find_all(
                            ['td', 'th'],
                            recursive=False
                        )

                        if next_cells:

                            first_text = next_cells[0].get_text(
                                ' ',
                                strip=True
                            ).upper()

                            first_classes = (
                                next_cells[0].get(
                                    'class'
                                ) or []
                            )

                            if (
                                first_text == 'CR'
                                or 'th-label'
                                in first_classes
                            ):
                                cr_row = next_row

                    # =================================
                    # CR 행
                    # =================================
                    if cr_row is not None:

                        cr_box = document_soup.new_tag(
                            'div'
                        )
                        cr_box['class'] = [
                            'mobile-full-auto-cr'
                        ]

                        cr_cells = cr_row.find_all(
                            ['td', 'th'],
                            recursive=False
                        )

                        for cell in cr_cells[:6]:

                            item = document_soup.new_tag(
                                'div'
                            )
                            item['class'] = [
                                'mobile-full-auto-cr-cell'
                            ]

                            append_fragment(
                                item,
                                cell.decode_contents()
                            )

                            cr_box.append(
                                item
                            )

                        team_box.append(
                            cr_box
                        )

                    # =================================
                    # 딜량 / 조작 정보
                    # =================================
                    if (
                        damage_cell is not None
                        or operation_cell is not None
                    ):

                        info_box = document_soup.new_tag(
                            'div'
                        )
                        info_box['class'] = [
                            'mobile-full-auto-info'
                        ]

                        # ---------------------------------
                        # 딜량 라벨
                        # ---------------------------------
                        damage_label = document_soup.new_tag(
                            'div'
                        )
                        damage_label['class'] = [
                            'mobile-full-auto-info-label',
                            'damage-label'
                        ]
                        damage_label.string = '딜량'

                        info_box.append(
                            damage_label
                        )

                        # ---------------------------------
                        # 딜량 값
                        # ---------------------------------
                        damage_value = document_soup.new_tag(
                            'div'
                        )
                        damage_value['class'] = [
                            'mobile-full-auto-info-value',
                            'damage-value'
                        ]

                        if damage_cell is not None:

                            append_fragment(
                                damage_value,
                                damage_cell.decode_contents()
                            )

                        info_box.append(
                            damage_value
                        )

                        # ---------------------------------
                        # 조작 라벨
                        # ---------------------------------
                        operation_label = document_soup.new_tag(
                            'div'
                        )
                        operation_label['class'] = [
                            'mobile-full-auto-info-label',
                            'operation-label'
                        ]
                        operation_label.string = '조작'

                        info_box.append(
                            operation_label
                        )

                        # ---------------------------------
                        # 조작 값
                        # ---------------------------------
                        operation_value = document_soup.new_tag(
                            'div'
                        )
                        operation_value['class'] = [
                            'mobile-full-auto-info-value',
                            'operation-value'
                        ]

                        if operation_cell is not None:

                            append_fragment(
                                operation_value,
                                operation_cell.decode_contents()
                            )

                        info_box.append(
                            operation_value
                        )

                        team_box.append(
                            info_box
                        )

                    # =================================
                    # 편성 추가
                    # =================================
                    mobile_view.append(
                        team_box
                    )

                    # CR 행은 이미 처리했으므로
                    # 다음 편성으로 이동
                    if cr_row is not None:
                        i += 2
                    else:
                        i += 1

                    continue

                i += 1

        # =================================
        # 원본 테이블 바로 뒤에
        # 모바일 전용 뷰 삽입
        # =================================
        table.insert_after(
            mobile_view
        )



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

            # 풀오토/심연토벌전만 모바일 전용 뷰를 추가한다.
            # 세미오토에는 process_full_auto_merge() 자체를 사용하지 않는다.
            target_root = container if container else soup
            _add_mobile_full_auto_view(soup, target_root)

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

        /* 모바일 전용 뷰는 PC에서는 숨김 */
        .mobile-full-auto-view {
            display: none !important;
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

        /* 📱 모바일 전용: 풀오토/심연토벌전만 별도 구조로 표시 */
        @media (max-width: 768px) {
            /* 원본 고정폭 테이블은 모바일에서 숨기고,
               바로 뒤에 생성한 모바일 전용 뷰를 사용 */
            .tab-content table.output-table {
                display: none !important;
            }

            .mobile-full-auto-view {
                display: block !important;
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
                overflow: hidden !important;
            }

            /* 1️⃣ 제목 */
            /* 📱 심연토벌전 최상단 링크 */
            .mobile-full-auto-title {
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;

                padding: 7px 10px !important;

                background: #f1f5f9 !important;
                border-bottom: 1px solid #cbd5e1 !important;

                text-align: left !important;
                font-weight: 600 !important;

                /* 한 줄 고정 + 말줄임 */
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
            }

            .mobile-full-auto-title a {
                display: block !important;
                width: 100% !important;
                max-width: 100% !important;

                color: #2563eb !important;
                text-decoration: none !important;

                /* 줄바꿈 금지 */
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
            }

            /* 2️⃣ 심연토벌전의 반복 컬럼 헤더 */
            .mobile-full-auto-column-header {
                display: grid !important;
                grid-template-columns: 2fr 2fr 1fr 1fr !important;
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
                background: #f1f5f9 !important;
                border-bottom: 1px solid #cbd5e1 !important;
            }

            .mobile-full-auto-column-item {
                min-width: 0 !important;
                padding: 7px 4px !important;
                text-align: center !important;
                overflow: hidden !important;
                white-space: nowrap !important;
                text-overflow: ellipsis !important;
                border-right: 1px solid #e2e8f0 !important;
            }

            .mobile-full-auto-column-item:last-child {
                border-right: none !important;
            }

            /* 📱 심연토벌전 구간 헤더 */
            .mobile-full-auto-section-header {
                display: block !important;
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;

                padding: 8px 10px !important;

                background: #f1f5f9 !important;
                border-bottom: 1px solid #cbd5e1 !important;

                font-weight: 600 !important;
                text-align: left !important;

                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
            }
            /* 3️⃣ 편성 하나 */
            .mobile-full-auto-team {
                width: 100% !important;
                max-width: 100% !important;
                box-sizing: border-box !important;
                margin: 0 0 12px 0 !important;
                padding: 0 0 12px 0 !important;
                border-bottom: 2px solid #e2e8f0 !important;
            }

            /* 4️⃣ 이미지 6열 */
            .mobile-full-auto-images {
                display: grid !important;
                grid-template-columns: repeat(6, minmax(0, 1fr)) !important;
                width: 100% !important;
                box-sizing: border-box !important;
            }

            .mobile-full-auto-image-cell {
                min-width: 0 !important;
                padding: 2px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                overflow: hidden !important;
            }

            .mobile-full-auto-image-cell img {
                display: block !important;
                width: 100% !important;
                max-width: 55px !important;
                height: auto !important;
                object-fit: cover !important;
            }

            /* 5️⃣ CR 6열 */
            .mobile-full-auto-cr {
                display: grid !important;
                grid-template-columns: repeat(6, minmax(0, 1fr)) !important;
                width: 100% !important;
                box-sizing: border-box !important;
                margin-top: 2px !important;
            }

            .mobile-full-auto-cr-cell {
                min-width: 0 !important;
                padding: 4px 2px !important;
                text-align: center !important;
                color: #334155 !important;
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
            }

            /* 6️⃣ 딜량 / 수치 / 조작 / 데이터 = 1 / 1 / 1 / 3 */
            .mobile-full-auto-info {
                display: grid !important;
                grid-template-columns: repeat(6, minmax(0, 1fr)) !important;
                width: 100% !important;
                box-sizing: border-box !important;
                margin-top: 6px !important;
                gap: 0 !important;
            }

            .mobile-full-auto-info-label,
            .mobile-full-auto-info-value {
                min-width: 0 !important;
                min-height: 34px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                box-sizing: border-box !important;
                padding: 6px 4px !important;
            }

            .mobile-full-auto-info-label {
                color: #64748b !important;
                font-weight: 500 !important;
                background: #f8fafc !important;
            }

            .mobile-full-auto-info-value {
                font-weight: 600 !important;
            }

            .damage-label {
                grid-column: 1 / span 1 !important;
                background: #fff1f2 !important;
            }

            .damage-value {
                grid-column: 2 / span 1 !important;
                background: #fff1f2 !important;
                color: #e11d48 !important;
                font-family: 'Roboto Mono', monospace !important;
                white-space: nowrap !important;
            }

            .operation-label {
                grid-column: 3 / span 1 !important;
                background: #f8fafc !important;
            }

            .operation-value {
                grid-column: 4 / span 3 !important;
                background: #f8fafc !important;
                white-space: pre-line !important;
                word-break: break-word !important;
                overflow-wrap: anywhere !important;
                text-align: center !important;
            }

            .mobile-full-auto-info-label:first-child {
                border-radius: 6px 0 0 6px !important;
            }

            .mobile-full-auto-info-value:last-child {
                border-radius: 0 6px 6px 0 !important;
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