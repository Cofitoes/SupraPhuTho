@echo off
title AUTO CHECK EMAIL - Cap nhat Booking moi 30 phut
echo ========================================================
echo   TU DONG QUET EMAIL VA CAP NHAT BOOKING MOI 30 PHUT
echo   Nhan Ctrl+C de dung
echo ========================================================
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0auto_check_email.ps1"
pause
