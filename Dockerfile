FROM public.ecr.aws/lambda/python:3.12

WORKDIR /app

RUN pip install --upgrade pip

COPY src/ ${LAMBDA_TASK_ROOT}

CMD [ "lambda_function.lambda_handler" ]