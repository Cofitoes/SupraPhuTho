@echo off
title AutoUpdateSupra
:LOOP
echo ========================================================
echo   DONG BO BOOKING, GIO XUAT VA BIEN SO XE TREN DASHBOARD
echo ========================================================
echo.
echo Dang tu dong dong bo tu Email va cac file Booking (CHAY NGAM)...
powershell -ExecutionPolicy Bypass -File "%~dp0run_pipeline.ps1"
echo.
echo ========================================================
echo KET THUC DONG BO LOKAL.
echo ========================================================
echo.
call "%~dp0Dong_Bo_Github.bat"

echo Dang doi 60 giay de cap nhat tiep theo...
timeout /t 60 /nobreak >nul
goto LOOP
