#!/bin/bash

# Insert a new MLModel entity with the specified attributes
curl -iX POST 'http://localhost:1026/ngsi-ld/v1/entities' \
  -H 'Content-Type: application/ld+json' \
  --data-raw '{
    "id": "urn:ngsi-ld:MLModel:HandwrittenDigitPrediction",
    "type": "MLModel",
    "algorithm": "CNN",
    "description": "Predicts the handwritten digit",
    "dockerImage": "No docker image",
    "inputAttributes": ["imagePath", "size"],
    "name": "Handwritten digit prediction",
    "outputAttributes": ["predictedDigit", "confidence"],
    "version": 1,
    "@context": [
      "https://raw.githubusercontent.com/smart-data-models/dataModel.MachineLearning/master/context.jsonld"
    ]
  }'

