FROM python:3.8.0
EXPOSE 8000
ADD . /home/user/email_notifier
WORKDIR /home/user/email_notifier
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
CMD [ "python", "main.py"]
