#!/bin/bash

# 1. pull all MLModel IDs into a flat list
ENTITY_IDS=$(curl -s -G 'http://localhost:1026/ngsi-ld/v1/entities' \
  -d 'type=MLModel' \
  -H 'Accept: application/ld+json' \
  -H 'Link: <https://raw.githubusercontent.com/smart-data-models/dataModel.MachineLearning/master/context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"' \
  | jq -r '.[].id')

# 2. turn that list into a JSON array
ID_ARRAY=$(printf '%s\n' $ENTITY_IDS | jq -R . | jq -s .)

# 3. post to the batch‐delete endpoint
curl -iX POST 'http://localhost:1026/ngsi-ld/v1/entityOperations/delete' \
  -H 'Content-Type: application/json' \
  --data-raw "$ID_ARRAY"

