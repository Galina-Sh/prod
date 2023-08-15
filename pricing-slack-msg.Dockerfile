FROM python:3.7

RUN mkdir /pricing-slack-msg

WORKDIR /pricing-slack-msg

COPY requirements-pricing-slack-msg.txt ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install -r requirements-pricing-slack-msg.txt

COPY pricing-slack-msg ./

CMD ["python","main.py"]
