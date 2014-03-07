test:
	python tests.py

flake8:
	flake8 classsettings tests.py

coverage:
	coverage erase
	coverage run --branch --source=classsettings tests.py
	coverage html
