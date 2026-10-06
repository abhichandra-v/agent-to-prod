# agent-to-prod — the 15-minute path from clone to running in prod.
IMAGE ?= ghcr.io/abhichandra-v/agent-to-prod
TAG   ?= latest

.PHONY: help test run build scan deploy secret clean
help:                 ## show this help
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n",$$1,$$2}'

test:                 ## run the app tests
	cd app && python -m pytest -q

run:                  ## run locally on :8080 (no key needed — uses the stub)
	cd app && uvicorn main:app --reload --port 8080

build:                ## build the hardened image
	docker build -t $(IMAGE):$(TAG) .

scan:                 ## scan the image for HIGH/CRITICAL vulns (needs trivy)
	trivy image --severity HIGH,CRITICAL --ignore-unfixed $(IMAGE):$(TAG)

secret:               ## create the LLM API key secret (set LLM_API_KEY first)
	kubectl create namespace agent --dry-run=client -o yaml | kubectl apply -f -
	kubectl create secret generic agent-secrets -n agent \
	  --from-literal=llm-api-key=$(LLM_API_KEY) \
	  --dry-run=client -o yaml | kubectl apply -f -

deploy:               ## apply the hardened manifests
	kubectl apply -k deploy/base
	kubectl rollout status deployment/agent -n agent --timeout=120s

clean:                ## delete the deployed resources
	kubectl delete -k deploy/base --ignore-not-found
