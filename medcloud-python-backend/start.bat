@echo off
echo ====================================================
echo Instalando Bibliotecas Python Necessarias...
echo ====================================================
pip install -r requirements.txt
echo.
echo ====================================================
echo Iniciando o Servidor Leitor de PDF do MedCloud...
echo ====================================================
python main.py
pause
