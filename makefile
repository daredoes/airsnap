DOCKER_IMAGE=airsnap
DOCKER_REPO=daredoes
TAG_NAME=develop

run:
	docker run -d \
    -p 8080:8080 \
    --network=host \
    -v /Users/dare/Git/airsnap/tmp:/home \
    $(DOCKER_REPO)/$(DOCKER_IMAGE)


build:
	docker build --platform=linux/amd64 -t $(DOCKER_REPO)/$(DOCKER_IMAGE) .
	# docker build --platform=linux/arm64 -t $(DOCKER_REPO)/$(DOCKER_IMAGE) .

push:
	docker tag $(DOCKER_REPO)/$(DOCKER_IMAGE) $(DOCKER_REPO)/$(DOCKER_IMAGE):$(TAG_NAME)
	docker push $(DOCKER_REPO)/$(DOCKER_IMAGE):$(TAG_NAME)

.PHONY: build push 
