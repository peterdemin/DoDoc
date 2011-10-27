rmdir /S /Q release
mkdir release
mkdir release\DoDoc
copy setup.py release\setup.py
copy *.py release\DoDoc\
cd release
python setup.py bdist_wininst
cd ..
Pause
