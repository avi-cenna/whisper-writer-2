fmt:
    poetry run black .
    poetry run isort .

run:
    sudo poetry run python run.py

test:
    sudo poetry run python src/main_z.py

