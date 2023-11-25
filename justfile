fmt:
    poetry run black .
    poetry run isort .

run:
    sudo poetry run python run.py

test:
    sudo poetry run python src/main_z.py

serve:
    poetry run python src/main_z.py

send:
    poetry run python src/main_client.py

