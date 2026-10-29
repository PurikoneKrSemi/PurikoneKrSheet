@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 번역 도우미를 시작합니다. 이 창을 켜 둔 동안 편집기의 번역 버튼이 동작합니다.
python translate_news.py --serve
pause
