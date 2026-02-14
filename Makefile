.DEFAULT_GOAL := help

.PHONY: help install server household merchant dashboard run seed clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

server: ## Start the Flask API server (port 5000)
	python full_server.py

household: ## Launch the Household portal (Flet)
	python flet_household.py

merchant: ## Launch the Merchant portal (Flet)
	python flet_merchant.py

dashboard: ## Launch the Analytics dashboard (Flet)
	python flet_dashboard.py

run: ## Start server + all three clients (backgrounded)
	python full_server.py &
	@sleep 2
	python flet_household.py &
	python flet_merchant.py &
	python flet_dashboard.py &
	@echo "All services started. Use 'make clean' to stop."

seed: ## Copy sample data to project root
	cp data/samples/households.json households.json
	cp data/samples/merchant.csv merchant.csv
	@echo "Sample data copied to project root."

clean: ## Remove generated data files
	rm -f households.json merchant.csv Redeem*.csv
	@echo "Generated data files removed."
