#!/bin/bash

echo "🚀 Starting Legacy Interview App Frontend..."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the React development server
echo "🌐 Starting React development server on http://localhost:3000"
echo "🛑 Press Ctrl+C to stop the server"

npm start
