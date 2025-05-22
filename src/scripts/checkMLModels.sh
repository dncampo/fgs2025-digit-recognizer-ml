#!/bin/bash

# List all MLModel entities in the Context Broker
curl -L -G 'http://localhost:1026/ngsi-ld/v1/entities' \
  -d 'type=MLModel' \
  -H 'Accept: application/ld+json' \
  -H 'Link: <https://raw.githubusercontent.com/smart-data-models/dataModel.MachineLearning/master/context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'

