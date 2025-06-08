FROM --platform=linux/amd64 python:3.12
EXPOSE 8501
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN  pip3 install --upgrade pip && pip3 install -r requirements.txt
COPY . .

# Command overriden by docker-compose
CMD streamlit run app.py
