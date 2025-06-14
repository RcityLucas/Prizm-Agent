#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unified SurrealDB API Server

Uses the new unified storage system for dialogue management and agent interactions.
"""
import os
import sys
import json
import logging
import uuid
import asyncio
from datetime import datetime
from json import JSONEncoder

# Add project root to Python path
import pathlib
root_dir = str(pathlib.Path(__file__).absolute().parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import and initialize the centralized configuration system
from rainbow_agent.config import load_config, config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration (this will also load environment variables from .env)
load_config()

# Import Flask and other dependencies after configuration is loaded
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from rainbow_agent.storage.config import get_surreal_config
from rainbow_agent.storage.unified_dialogue_storage import UnifiedDialogueStorage
from rainbow_agent.core.dialogue_manager import DialogueManager
from rainbow_agent.api.unified_routes import api as unified_blueprint

# Custom JSON encoder for handling special types
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return JSONEncoder.default(self, obj)

# Create Flask app
app = Flask(__name__)
app.json_encoder = CustomJSONEncoder
CORS(app, resources={r"/*": {"origins": config.app.cors_origins}})

# Initialize storage system
logger.info(f"Initializing storage system with SurrealDB at {config.surreal.url}")
storage = UnifiedDialogueStorage()

# Initialize dialogue manager
logger.info("Initializing dialogue manager")
dialogue_manager = DialogueManager(storage)

# Register blueprints
app.register_blueprint(unified_blueprint, url_prefix='/api/v1')

# Root endpoint
@app.route('/')
def index():
    return jsonify({
        "status": "ok",
        "message": "Rainbow Agent API Server",
        "version": "1.0.0"
    })

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    })

# Static files (for web UI)
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Main entry point
if __name__ == '__main__':
    host = config.app.host
    port = config.app.port
    debug = config.app.debug
    
    logger.info(f"Starting server on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
