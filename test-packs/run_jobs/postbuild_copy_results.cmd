mkdir "W:\reports\Platform\%JOB_NAME%"
mkdir "W:\reports\Platform\%JOB_NAME%\%BUILD_DISPLAY_NAME%"
xcopy /E "%WORKSPACE%\test-packs\reports"  "W:\reports\Platform\%JOB_NAME%\%BUILD_DISPLAY_NAME%"