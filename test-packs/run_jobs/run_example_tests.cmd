@echo off
SET MARKER="example"
SET SEARCHPATH=%~dp0%..\tests\

cd %USERPROFILE%\TAF
call venv\Scripts\activate
cd %SEARCHPATH%
pytest -m %MARKER%

