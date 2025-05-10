# FIWARE FGS2025 Digit Recognizer

An interactive handwritten digit recognition demo showcasing machine learning integration with FIWARE Smart Data Models and Context Broker.


## Overview

This project demonstrates how machine learning applications can be integrated with FIWARE components to provide smart solutions. The application allows users to:

1. Draw digits on a canvas
2. Train a digit recognition model with user-provided examples
3. Make predictions on newly drawn digits
4. Store all training data and predictions in a FIWARE Context Broker

The project implements NGSI-LD entities and leverages FIWARE's context management capabilities to create a comprehensive ML pipeline.

## Features

- Interactive drawing canvas for digit input
- Digit collection mode for training data acquisition
- Real-time prediction of drawn digits
- Integration with FIWARE Context Broker
- Support for multiple Context Broker implementations (Orion-LD, Scorpio, Stellio)
- NGSI-LD entity creation for ML artifacts (training images, prediction results)

## Architecture

The application consists of:

- A Flask web application serving the frontend and API endpoints
- FIWARE Context Broker for storing entities (training data, predictions, model info)
- Mock ML prediction service (can be replaced with a real TensorFlow model)
- Docker-compose configurations for various FIWARE setups

## FIWARE Integration

The application demonstrates several FIWARE integration patterns:

- **Smart Data Models**: Custom entity types for ML artifacts (TrainingImage, PredictionResult, MLModel)
- **Context Management**: Storing and retrieving ML-related data via Context Broker
- **NGSI-LD API**: Implementing property attributes, relationships, and context information

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.6+
- FIWARE Context Broker (Orion-LD, Scorpio, or Stellio)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/fiware/FGS2025/fgs2025-digit-recognizer-ml.git
   cd fgs2025-digit-recognizer-ml
   ```

2. Set up a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install required dependencies:
   ```
   pip install -r src/requirements.txt
   ```

4. Start the FIWARE Context Broker (choose one):
   ```
   docker-compose -f src/docker-compose/orion-ld.yml up -d
   # OR
   docker-compose -f src/docker-compose/scorpio.yml up -d
   # OR
   docker-compose -f src/docker-compose/stellio.yml up -d
   ```

5. Start the application:
   ```
   cd src
   python app.py
   ```

6. Open your browser and navigate to:
   ```
   http://localhost:5001
   ```

## Usage

### Collecting Digits

1. Navigate to `/collect`
2. Draw a digit on the canvas when prompted
3. Click "Send Digit" to save your drawing
4. Each saved digit creates a `TrainingImage` entity in the Context Broker

### Predicting Digits

1. Navigate to `/predict`
2. Draw a digit on the canvas
3. Select a model from the dropdown
4. Click "Predict Digit" to get a prediction
5. Prediction results are stored as `PredictionResult` entities

## Development

The application uses a mock prediction system by default. To integrate with a real TensorFlow model, modify the `api_predict_digit` function in `app.py`.

### Environment Variables

- `ORION_CB_ENDPOINT`: URL of the FIWARE Context Broker (default: `http://localhost:1026`)

## License

This project is licensed under [AGPL-3.0](LICENSE)

## Related FIWARE Components

- [Orion-LD Context Broker](https://github.com/FIWARE/context.Orion-LD)
- [FIWARE Smart Data Models](https://github.com/smart-data-models/)
- [NGSI-LD Tutorials](https://fiware-tutorials.readthedocs.io/en/latest/)

## Deployment Options

### Running with Flask Development Server

// ... existing code ...

### Deploying with Apache2

To deploy this application on a production server with Apache2:

1. Install the required packages:
   ```
   sudo apt-get update
   sudo apt-get install apache2 libapache2-mod-wsgi-py3 python3-pip python3-venv
   ```

2. Copy the project files to your server (e.g., in `/var/www/fgs2025-digit-recognizer-ml`)

3. Use the provided deployment script:
   ```
   cd /path/to/fgs2025-digit-recognizer-ml
   sudo bash src/deploy.sh
   ```

4. Or manually configure Apache:
   - Create a virtual environment and install requirements
   - Copy `src/digit-recognizer.conf` to `/etc/apache2/sites-available/`
   - Enable the site: `sudo a2ensite digit-recognizer`
   - Restart Apache: `sudo systemctl restart apache2`

5. Update the ServerName in the Apache configuration file to match your domain or server IP.

The application should now be accessible at http://your-server-ip or your configured domain.

> **Note**: Make sure the Context Broker is also properly configured and accessible from the server.
