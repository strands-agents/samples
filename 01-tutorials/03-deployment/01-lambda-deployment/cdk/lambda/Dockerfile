FROM public.ecr.aws/lambda/python:3.13

# Copy requirements and install
COPY requirements.txt .
RUN pip install -r requirements.txt --target .

# Copy function code
COPY app.py ./
COPY create_booking.py ./
COPY delete_booking.py ./
COPY get_booking.py ./

# Command to run the handler
CMD ["app.handler"]
