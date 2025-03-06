# stars-api

### Adicionando Verificações de Qualidade de Código

1. **Adicionar Verificação de Formatação com Black e Padrão PEP8:**

   O PEP 8 define regras para a indentação, uso de espaços em branco, nomes de variáveis, entre outros aspectos do estilo de código. Ao adicionar a verificação do Black no GitHub Actions, estaremos garantindo que o código esteja formatado de acordo com as recomendações do PEP 8.

   - Para instalar o Black, utilize o comando:
     ```bash
     pip install black
     ```
   - Para executar o Black, utilize:
     ```bash
     black <nome_do_seu_arquivo_ou_diretório>
     ```

2. **Adicionar Verificação do Pytest com 100% de Cobertura:**

   O Pytest é uma biblioteca de testes unitários que permite escrever testes simples e escaláveis em Python. Ele fornece suporte para detecção automática de testes, relatórios detalhados e plugins personalizados.

   **Cobertura:**
   A biblioteca Coverage é usada para medir a cobertura de testes do código-fonte Python. Ela ajuda a identificar áreas do código que não estão sendo testadas, fornecendo relatórios sobre a porcentagem de código coberto pelos testes.

   - Para instalar o Pytest e o pytest-cov, utilize o comando:
     ```bash
     pip install pytest pytest-cov
     ```
   - Para executar os testes com o Pytest e calcular a cobertura de código, utilize o pytest-cov diretamente no comando Pytest:
     ```bash
     pytest --cov=.
     ```
   - Para cobrir todo o código ou
    ```bash
     pytest --cov=app
     ```
   - para cobrir apenas o diretório app.

3. **Adicionar Verificação do Flake8:**

   O Flake8 é uma ferramenta de verificação de código que combina as funcionalidades de outras ferramentas populares. Ele verifica o estilo do código, identifica problemas potenciais e fornece sugestões de melhoria.

   - Para instalar o Flake8, utilize o comando:
     ```bash
     pip install flake8
     ```
   - Para verificar seu código com o Flake8, utilize o seguinte comando:
     ```bash
     flake8
     ```


# Documentação
## Este projeto é um aplicativo Python com FastApi com todo o ambiente de execução encapsulado em Docker.

### ambiente virtual
  python3 -m venv env

### ativação do ambiente
  source env/bin/activate

### install nas dependencias
  pip install -r requirements.txt

#### Atulização nas dependencias
  pip freeze > requirements.txt

#### Comando para criar a imagem docker no projeto
  docker build -t backoffice -f .docker/Dockerfile .

#### Configurações de vulnerabilidade da imagem sugerida pelo docker
  docker scout cves local://backoffice:latest
  docker scout recommendations local://backoffice:latest

### Comando para checar se a imagem foi criada
  docker images

### Executar o container e verificar se esta em execução
  docker run -d -p 80:80 nome_do_container
  docker ps

### Comandos para criar/subir os containers
docker-compose up
docker-compose ps

### Parar containers
docker compose down

### Comandos uteis docker
docker-compose stop
docker-compose start
docker-compose restart

### Porta e swagger
http://localhost:8000/docs

### Parar o servidor
  docker stop <seu id> 65d05c5e44806478fd97914e8ecdb61a3a1b530686b20640da7c68e5717ec7a3

## DevOps

> [!CAUTION]
> WebApp utiliza API disponível em https://qwnh5gcnmp.us-east-1.awsapprunner.com/docs
> Indicando uso do serviço AWS App Runner para deploy da API, sem documentação dessa decisão no README

> [!TIP]
> Configurar Continuous Deployment, garantindo ambiente de produção sempre atualizado

N/A
