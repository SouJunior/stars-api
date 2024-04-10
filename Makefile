start:
	docker compose  -f .docker/docker-compose.yml up 

down:
	docker compose  -f .docker/docker-compose.yml down 

build:
	docker compose  -f .docker/docker-compose.yml up  --build
