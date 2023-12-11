#!/bin/bash
set -e

docker-compose -f docker-compose-dev.yml up -d


if [ "$1" = "--migration" ]; then
    poetry run python3 main.py --env dev --migration
fi

if [ "$1" != "--migration" ]; then
    poetry run python3 main.py --env dev --debug
fi
```