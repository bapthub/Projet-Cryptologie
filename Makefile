all:
	docker compose up -d --build
run:
	docker build -t myflaskapp .
	docker run -d -p 5000:5000 -p 27017:27017 --name myflaskapp myflaskapp
kill:
	docker stop myflaskapp
	docker rm myflaskapp
portainer:
	 docker run -d -p 9000:9000 --name=portainer --restart=unless-stopped -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce
down:
	docker compose down
