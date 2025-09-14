# Use the official Ollama image as a base
FROM ollama/ollama:latest

# Set the model to pull
ARG MODEL_TO_PULL=qwen:1.8b

# This command runs when the container starts for the first time.
# It pulls the specified model. The server is started automatically by the base image.
# We run this in the background so it doesn't block the server startup.
RUN /bin/sh -c "ollama pull $MODEL_TO_PULL"
