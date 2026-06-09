#!/bin/bash
echo "Building project..."

# Install python dependencies
python3 -m pip install -r requirements.txt

# Run collectstatic to compile all static files
echo "Collecting static files..."
python3 ZeroWave/manage.py collectstatic --noinput --clear

# Copy to the output directory that Vercel static build expects
echo "Distributing static files..."
mkdir -p static_collected/static
cp -r ZeroWave/static/* static_collected/static/

echo "Build complete."
