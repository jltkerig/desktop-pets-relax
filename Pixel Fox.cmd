@echo off
rem Double-click to start Pixel Fox. Works even where PowerShell scripts are blocked by policy.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
