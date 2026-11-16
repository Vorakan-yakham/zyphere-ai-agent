@echo off
title ZYP HERE - เปิด Zyphere
 echo กำลังเปิด Zyphere...
 start cmd /k "ollama serve"
 timeout /t 3 /nobreak >nul
 streamlit run app.py
 pause
