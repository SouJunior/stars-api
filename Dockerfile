FROM python:3.12

WORKDIR /code

# Instala as dependências primeiro para aproveitar o cache do Docker
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copia o restante dos arquivos do projeto
COPY . /code

# Garante que o diretório /code esteja no PATH do Python para encontrar o módulo 'app'
ENV PYTHONPATH=/code

EXPOSE 80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
