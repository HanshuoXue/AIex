#!/usr/bin/env bash

# Create Azure OpenAI connection for Prompt Flow
cd flows/program_match
pf connection create --file azure_openai_connection.yaml --set api_key="$AZURE_OPENAI_API_KEY" api_base="$AZURE_OPENAI_ENDPOINT" || true
cd ../..

# Start the FastAPI application
uvicorn main:app --host 0.0.0.0 --port 8000
