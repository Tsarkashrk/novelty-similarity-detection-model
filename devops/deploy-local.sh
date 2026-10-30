#!/bin/sh
set -eu

image=${1:?Usage: deploy-local.sh IMAGE}
service=thesis-novelty-api-test
candidate="${service}-candidate-$$"
old_image=

cleanup() {
    docker rm -f "$candidate" >/dev/null 2>&1 || true
}
trap cleanup EXIT

wait_for_api() {
    container=$1
    attempt=0
    while [ "$attempt" -lt 30 ]; do
        if docker exec "$container" python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=2)' >/dev/null 2>&1; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    return 1
}

docker run -d --name "$candidate" "$image" >/dev/null
if ! wait_for_api "$candidate"; then
    echo "Candidate API failed its health check" >&2
    exit 1
fi

if docker inspect "$service" >/dev/null 2>&1; then
    old_image=$(docker inspect --format '{{.Config.Image}}' "$service")
    docker rm -f "$service" >/dev/null
fi

if docker run -d --name "$service" --restart unless-stopped -p 127.0.0.1:8010:8000 "$image" >/dev/null && wait_for_api "$service"; then
    echo "Test API deployed: http://127.0.0.1:8010/health"
    exit 0
fi

echo "Deployment failed; restoring the previous image" >&2
docker rm -f "$service" >/dev/null 2>&1 || true
if [ -n "$old_image" ]; then
    docker run -d --name "$service" --restart unless-stopped -p 127.0.0.1:8010:8000 "$old_image" >/dev/null
    wait_for_api "$service"
fi
exit 1
