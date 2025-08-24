python3 -m venv venv && \
source venv/bin/activate && \
pip install --upgrade pip boto3 && \
python test_deployed_lambda.py
