start:
	docker compose  -f .docker/docker-compose.yml up 

down:
	docker compose  -f .docker/docker-compose.yml down 

stop:
	docker compose  -f .docker/docker-compose.yml down -v

build:
	docker compose  -f .docker/docker-compose.yml up  --build
