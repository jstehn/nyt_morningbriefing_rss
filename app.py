#!/usr/bin/env python3
"""
Flask web server to serve NYT Morning Briefing RSS feed
"""

from flask import Flask, Response, request, jsonify
import logging
import sys
import datetime
from zoneinfo import ZoneInfo
from nyt_requests import generate_nytimes_morning_briefing_rss

# New York timezone
NY_TZ = ZoneInfo("America/New_York")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
@app.route('/rss')
@app.route('/feed')
@app.route('/nyt-morning-briefing.xml')
def serve_rss():
    """Serve the NYT Morning Briefing RSS feed."""
    try:
        logger.info(f"RSS request from {request.remote_addr} - {request.user_agent}")
        
        # Generate fresh RSS feed
        rss_content = generate_nytimes_morning_briefing_rss()
        
        # Return with proper content type
        return Response(
            rss_content,
            mimetype='application/rss+xml',
            headers={
                'Content-Type': 'application/rss+xml; charset=utf-8',
                'Cache-Control': 'public, max-age=1800',  # Cache for 30 minutes
                'X-Content-Type-Options': 'nosniff'
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating RSS feed: {e}")
        return Response(
            f"Error generating RSS feed: {e}",
            status=500,
            mimetype='text/plain'
        )

@app.route('/health')
def health_check():
    """Health check endpoint for Docker."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now(NY_TZ).isoformat(),
        "service": "nyt-rss-feed"
    })

@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests."""
    return Response("", status=204)

if __name__ == '__main__':
    logger.info("Starting NYT Morning Briefing RSS server...")
    app.run(host='0.0.0.0', port=8080, debug=False)
