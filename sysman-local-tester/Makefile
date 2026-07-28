# Makefile for building and pushing SysMan Docker images
.PHONY: all build push clean

# Load environment variables from .env file if it exists
ifneq (,$(wildcard .env))
    include .env
    export
endif

# Defaults
REGISTRY ?= us-central1-docker.pkg.dev/agentspace-argolis-demo/docker-registry
TAG ?= latest

COMPONENTS = emulator mcp-server ops-agent detection-agent diagnosis-agent

all: build

build:
	@echo "Building SysMan components with tag '$(TAG)'..."
	@for comp in $(COMPONENTS); do \
		echo "Building image for sysman-$$comp..."; \
		docker build -t $(REGISTRY)/sysman-$$comp:$(TAG) ../sysman-$$comp; \
	done

push:
	@echo "Pushing SysMan components to $(REGISTRY)..."
	@for comp in $(COMPONENTS); do \
		echo "Pushing $(REGISTRY)/sysman-$$comp:$(TAG)..."; \
		docker push $(REGISTRY)/sysman-$$comp:$(TAG); \
	done

clean:
	@echo "Removing local built images..."
	@for comp in $(COMPONENTS); do \
		docker rmi $(REGISTRY)/sysman-$$comp:$(TAG) || true; \
	done
