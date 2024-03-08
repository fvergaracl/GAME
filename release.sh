#!/bin/bash

# Check if a tag comment has been provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 \"Tag comment\""
    echo "This script creates and pushes a git tag for the project."
    echo "The version is extracted from pyproject.toml, prefixed with 'v', and used as the tag."
    echo "A comment for the tag must be provided as an argument."
    exit 1
fi

# Store the tag comment
TAG_COMMENT="$1"

# Extract the version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

# Prepare the tag with "v" prefix
TAG="v${VERSION}"

# Create the git tag
git tag -a "${TAG}" -m "${TAG_COMMENT}"

# Push the tag to GitHub
git push origin "${TAG}"
