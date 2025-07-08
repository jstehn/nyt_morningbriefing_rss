# NYT Morning Briefing RSS Feed

A containerized Python service that scrapes The New York Times Morning Briefing using HTTP requests and serves it as an RSS feed over HTTP.

## Features

- **Lightweight**: Uses `requests` and `BeautifulSoup` - no browser automation required
- **Containerized**: Ready-to-deploy Docker container
- **HTTP API**: Serves RSS feed and health check endpoints
- **Robust**: Comprehensive error handling and logging

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd nyt
   ```

2. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

3. **Access the RSS feed:**
   - RSS Feed: http://localhost:8080/rss
   - Health Check: http://localhost:8080/health

### Using Helper Script

The `docker-run.sh` script provides convenient commands:

```bash
# Start the service
./docker-run.sh start

# Stop the service
./docker-run.sh stop

# View logs
./docker-run.sh logs

# Test the service
./docker-run.sh test
```

## 🐳 Docker Deployment

### Building the Image

```bash
docker build -t nyt-rss-feed .
```

### Running the Container

```bash
docker run -d \
  --name nyt-rss-service \
  -p 8080:8080 \
  nyt-rss-feed
```

### Using Docker Compose

```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

## 📡 API Endpoints

- **GET /rss** - Returns the RSS feed (XML format)
- **GET /health** - Health check endpoint (JSON format)

### Example Usage

```bash
# Get RSS feed
curl http://localhost:8080/rss

# Check service health
curl http://localhost:8080/health
```

## 🛠️ Local Development

### Prerequisites
- Python 3.9+

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the scraper directly:**
   ```bash
   python nyt_requests.py
   ```

3. **Run the web server locally:**
   ```bash
   python app.py
   ```

   The service will be available at:
   - RSS Feed: http://localhost:8080/rss
   - Health Check: http://localhost:8080/health

## 🔧 Configuration

### Environment Variables

- `PORT` - Server port (default: 8080)
- `HOST` - Server host (default: 0.0.0.0)

### Docker Environment

```bash
# Set custom port
docker run -d -p 9000:9000 -e PORT=9000 nyt-rss-feed
```

## 📊 Monitoring

### Health Check

The service includes a health endpoint for monitoring:

```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-08T12:00:00Z",
  "service": "nyt-rss-feed"
}
```

### Logs

View container logs:
```bash
# Docker
docker logs nyt-rss-service

# Docker Compose
docker-compose logs -f
```

## 🚨 Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Change port mapping
   docker run -p 8081:8080 nyt-rss-feed
   ```

2. **RSS feed not updating:**
   - Check logs for scraping errors
   - Verify NYT website structure hasn't changed
   - Check internet connectivity

3. **Service not responding:**
   - Verify container is running: `docker ps`
   - Check container logs: `docker logs nyt-rss-service`

### Debug Mode

Run with debug logging:
```bash
docker run -e LOG_LEVEL=DEBUG nyt-rss-feed
```

## 📁 Project Structure

```
nyt/
├── app.py                 # Flask web server
├── nyt_requests.py        # NYT scraper
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container build instructions
├── docker-compose.yml    # Docker Compose configuration
├── docker-run.sh         # Helper script
├── .dockerignore         # Docker build exclusions
├── .gitignore           # Git exclusions
└── README.md            # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🔗 Related

- [New York Times Morning Briefing](https://www.nytimes.com/series/us-morning-briefing)
- [RSS 2.0 Specification](https://cyber.harvard.edu/rss/rss.html)
- [Docker Documentation](https://docs.docker.com/)
