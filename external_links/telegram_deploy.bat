@echo off
cd /d "R:\Repos\Roboto-SAI-2026\external_links"
pip install pyTelegramBotAPI
echo "Launching RobotoEmpireBot..."
python external_links/omni_bot.py
pause
