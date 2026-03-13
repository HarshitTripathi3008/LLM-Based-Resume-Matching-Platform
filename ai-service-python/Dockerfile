# Use the AWS Lambda Python base image
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.9

# Install system dependencies (needed for scikit-learn and other potential C-extensions)
RUN yum install -y gcc gcc-c++ python3-devel

# Update pip, setuptools, and wheel
RUN pip install --upgrade pip setuptools wheel

# Copy requirements.txt
COPY requirements.txt ./

# Install dependencies from requirements.txt
RUN pip install -r requirements.txt

# Copy the application code
COPY ./app ./app

# Set the handler to Mangum handler in main.py
CMD ["app.main.handler"]
