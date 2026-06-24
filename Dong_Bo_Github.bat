@echo off
echo ========================================================
echo   DONG BO DU LIEU LEN GITHUB (TRANG WEB ONLINE)
echo ========================================================
echo.

REM Tranh Vim editor bi treo khi rebase conflict
set GIT_EDITOR=true

REM Dong bo demo.html sang index.html truoc khi push
copy /Y "%~dp0demo.html" "%~dp0index.html" >nul 2>&1

echo Dang tu dong day cac thay doi len GitHub...

cd /d "%~dp0"
git add .
git commit -m "Auto update data"

REM Pull truoc de tranh conflict
git pull --rebase origin main
if errorlevel 1 (
    echo Phat hien conflict, dang tu dong xu ly...
    git rebase --abort
    git stash
    git pull origin main
    git stash pop
    git add .
    git commit -m "Auto update data - resolved"
)

git push origin main

echo.
echo ========================================================
echo KET THUC DONG BO GITHUB. Vui long doi khoang 1-2 phut 
echo de trang web online tu dong cap nhat.
echo ========================================================
