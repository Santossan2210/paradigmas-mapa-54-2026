@echo off
rem Inicia o sistema de telemetria e abre o navegador. Autor: Antonio Santos
cd /d "%~dp0"
python -m telemetria
if errorlevel 1 pause
