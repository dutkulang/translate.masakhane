# Use the official AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# AWS Lambda native execution directory path environment variable
WORKDIR ${LAMBDA_TASK_ROOT}

# Install essential compilation tools and OpenMP required by CTranslate2
RUN yum update -y && yum install -y gcc gcc-c++ make libgomp && yum clean all

# Copy your dependency configurations
COPY requirements.txt .

# Optimize container size by fetching a strict CPU compilation distribution of PyTorch
RUN pip install --upgrade pip && \
    pip install torch --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements.txt

# Copy source tree and model download tool over to the execution root
COPY app/ ./app
COPY download_models.py .

# Execute build-time model quantization download sweeps
RUN python download_models.py && rm download_models.py

# Point the Lambda runtime engine directly to your mangum handler hook
CMD ["app.main.handler"]