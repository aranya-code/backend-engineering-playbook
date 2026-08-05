#!/bin/sh
# Simple health check script to verify the API is responsive.
# The --fail flag ensures curl exits with a non-zero status if the HTTP request fails.
curl --fail http://localhost:8000/health
