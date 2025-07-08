#!/bin/bash

# NYT RSS Feed Docker Management Script

set -e

case "$1" in
    "build")
        echo "Building NYT RSS Docker image..."
        docker build -t nyt-rss-feed .
        echo "Build complete!"
        ;;
    "run")
        echo "Running NYT RSS container..."
        docker run -d --name nyt-rss -p 8080:8080 --restart unless-stopped nyt-rss-feed
        echo "Container started! RSS feed available at http://localhost:8080"
        ;;
    "stop")
        echo "Stopping NYT RSS container..."
        docker stop nyt-rss || true
        docker rm nyt-rss || true
        echo "Container stopped!"
        ;;
    "logs")
        echo "Showing container logs..."
        docker logs -f nyt-rss
        ;;
    "compose-up")
        echo "Starting with docker-compose..."
        docker-compose up -d
        echo "Service started! RSS feed available at http://localhost:8080"
        ;;
    "compose-down")
        echo "Stopping docker-compose services..."
        docker-compose down
        echo "Services stopped!"
        ;;
    "test")
        echo "Testing RSS feed..."
        curl -I http://localhost:8080/health
        echo "Testing RSS content..."
        curl -s http://localhost:8080/rss | head -20
        ;;
    *)
        echo "Usage: $0 {build|run|stop|logs|compose-up|compose-down|test}"
        echo ""
        echo "Commands:"
        echo "  build       - Build the Docker image"
        echo "  run         - Run the container"
        echo "  stop        - Stop and remove the container"
        echo "  logs        - Show container logs"
        echo "  compose-up  - Start with docker-compose"
        echo "  compose-down - Stop docker-compose services"
        echo "  test        - Test the RSS feed"
        exit 1
        ;;
esac
