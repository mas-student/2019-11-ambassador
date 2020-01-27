FROM python:3.8.0
EXPOSE 5000
ADD . /home/user/web_notifier
WORKDIR /home/user/web_notifier
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
CMD [ "python", "main.py"]
