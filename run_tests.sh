python3 -m venv venv && \
source venv/bin/activate && \
pip install --upgrade pip boto3 && \
poetry run pytest  tests -s