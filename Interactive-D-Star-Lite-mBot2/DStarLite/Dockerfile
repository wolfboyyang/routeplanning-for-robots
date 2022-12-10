FROM python:3-alpine

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

EXPOSE 8550

CMD ["python", "./d_star_lite_main.py"]