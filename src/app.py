import os
import base64
import uuid
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template, send_from_directory
import requests as fiware_requests # Alias to avoid conflict with flask.request
import numpy as np
from PIL import Image # For image processing if needed, not strictly for mock
import io
import json
app = Flask(__name__)

# --- Configuration ---
IMAGE_STORAGE_PATH = "collected_images"
PREDICTION_STORAGE_PATH = "predicted_images"
# IMPORTANT: Set this environment variable or change the default
ORION_CB_ENDPOINT = os.environ.get("ORION_CB_ENDPOINT", "http://localhost:1026")
# For a MOCK prediction, we don't need a real TF Serving URL
# TF_SERVING_URL = os.environ.get("TF_SERVING_URL", "http://localhost:8501/v1/models/mnist:predict")

# Ensure storage directories exist
for i in range(10):
    os.makedirs(os.path.join(IMAGE_STORAGE_PATH, str(i)), exist_ok=True)
    os.makedirs(os.path.join(PREDICTION_STORAGE_PATH, str(i)), exist_ok=True)

# --- NGSI-LD Context ---
NGSI_LD_CONTEXT = [
    "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"
]
NGSI_LD_HEADERS = {
    "Content-Type": "application/ld+json"
}
NGSI_LD_ACCEPT_HEADERS = {
    "Accept": "application/ld+json"
}


# --- Helper Functions ---
def ping_context_broker():
    """Helper to check if the context broker is available."""
    try:
        response = fiware_requests.get(
            f"{ORION_CB_ENDPOINT}/version",
            headers=NGSI_LD_ACCEPT_HEADERS
        )
        response.raise_for_status()
        return True, response.json()
    except fiware_requests.exceptions.RequestException as e:
        app.logger.error(f"Failed to ping context broker: {e}")
        return False, {"error": str(e)}

def query_entities(entity_type=None, limit=1000, offset=0):
    """Helper to query entities by type from Orion."""
    try:
        query_params = {"limit": limit, "offset": offset}
        if entity_type:
            query_params["type"] = entity_type
            
        response = fiware_requests.get(
            f"{ORION_CB_ENDPOINT}/ngsi-ld/v1/entities",
            params=query_params,
            headers=NGSI_LD_ACCEPT_HEADERS
        )
        response.raise_for_status()
        return response.json()
    except fiware_requests.exceptions.RequestException as e:
        app.logger.error(f"Failed to query entities: {e}")
        return []

def create_ngsi_ld_entity(entity_payload):
    """Helper to create an entity in Orion."""
    URL_ENDPOINT = f"{ORION_CB_ENDPOINT}/ngsi-ld/v1/entities"
    print(f"URL_ENDPOINT: {URL_ENDPOINT}\n")
    print(f"entity_payload: {json.dumps(entity_payload, indent=2)}\n")
    print(f"NGSI_LD_HEADERS: {NGSI_LD_HEADERS}\n")

    
    try:
        response = fiware_requests.post(
            URL_ENDPOINT,
            json=entity_payload,
            headers=NGSI_LD_HEADERS
        )
        response.raise_for_status()
        app.logger.info(f"Successfully created entity: {entity_payload.get('id')}")
        return True, response
    except fiware_requests.exceptions.RequestException as e:
        app.logger.error(f"Failed to create entity {entity_payload.get('id')} in CB: {e}. Response: {e.response.text if e.response else 'No response'}")
        return False, e.response


def update_ngsi_ld_entity_attrs(entity_id, attrs_payload):
    """Helper to update attributes of an entity in Orion."""
    try:
        # Using application/json for partial attribute update here for simplicity
        # application/merge-patch+json is also an option
        headers = {"Content-Type": "application/json"}
        response = fiware_requests.patch(
            f"{ORION_CB_ENDPOINT}/ngsi-ld/v1/entities/{entity_id}/attrs",
            json=attrs_payload,
            headers=headers # No Link header needed for simple attribute update
        )
        response.raise_for_status()
        app.logger.info(f"Successfully updated attributes for entity: {entity_id}")
        return True, response
    except fiware_requests.exceptions.RequestException as e:
        app.logger.error(f"Failed to update attributes for {entity_id} in CB: {e}. Response: {e.response.text if e.response else 'No response'}")
        return False, e.response


def get_ngsi_ld_entity(entity_id):
    """Helper to get an entity from Orion."""
    try:
        response = fiware_requests.get(
            f"{ORION_CB_ENDPOINT}/ngsi-ld/v1/entities/{entity_id}",
            headers=NGSI_LD_ACCEPT_HEADERS
        )
        response.raise_for_status()
        return response.json()
    except fiware_requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return None # Entity not found
        app.logger.error(f"HTTP error getting entity {entity_id}: {e}")
        raise
    except fiware_requests.exceptions.RequestException as e:
        app.logger.error(f"Error getting entity {entity_id}: {e}")
        raise

# --- Routes ---
@app.route('/')
def home():
    return """
    <h1>Digit Recognition App</h1>
    <p><a href="/collect">Collect Digits</a></p>
    <p><a href="/predict">Predict Digits</a></p>
    """

@app.route('/collect')
def collect_page():
    return render_template('collect.html')

@app.route('/predict')
def predict_page():
    return render_template('predict.html')

@app.route('/api/models', methods=['GET'])
def api_get_models(type="MLModel"):
    """Get available ML models from the Context Broker."""
    models = query_entities(entity_type=type)
    
    # Format models for the frontend
    formatted_models = []
    
    # Always include the default mock model
    formatted_models.append({
        "id": "mock",
        "name": "Mock model by default",
        "description": "Random prediction generator"
    })
    
    # Add models from the context broker if any
    for model in models:
        model_id = model.get("id", "").split(":")[-1]  # Extract ID after last colon
        model_name = model.get("name", {}).get("value", f"Model {model_id}")
        model_desc = model.get("description", {}).get("value", "")
        
        formatted_models.append({
            "id": model_id,
            "name": model_name,
            "description": model_desc
        })
    
    return jsonify(formatted_models)

@app.route('/api/collect', methods=['POST'])
def api_collect_digit():
    try:
        data = request.get_json()
        label_str = data.get('label')
        image_data_b64 = data.get('imageDataB64')
        client_timestamp_str = data.get('timestamp', datetime.now(timezone.utc).isoformat())

        if label_str is None or image_data_b64 is None:
            return jsonify({"error": "Missing label or image data"}), 400

        try:
            label = int(label_str)
            if not (0 <= label <= 9):
                raise ValueError("Label out of range")
        except ValueError:
            return jsonify({"error": "Invalid label, must be an integer 0-9"}), 400

        # 1. Decode and Save Image
        header, encoded = image_data_b64.split(",", 1)
        image_binary = base64.b64decode(encoded)

        image_id = str(uuid.uuid4())
        filename = f"{image_id}.png"
        # Relative path for storage, construct full path for saving
        relative_image_path = os.path.join(str(label), filename)
        full_image_path_on_disk = os.path.join(IMAGE_STORAGE_PATH, relative_image_path)

        with open(full_image_path_on_disk, "wb") as f:
            f.write(image_binary)

        # This URL will be served by our Flask app for local testing
        image_url_served_by_app = f"/images/{str(label)}/{filename}"

        # 2. Create NGSI-LD Entity for TrainingImage
        entity_id = f"urn:ngsi-ld:TrainingImage:{image_id}"
        training_image_payload = {
            "id": entity_id,
            "type": "TrainingImage",
            "label": {"type": "Property", "value": label},
            "imageUrl": {"type": "Property", "value": image_url_served_by_app},
            "createdAt": {"type": "Property", "value": {"@type": "DateTime", "@value": client_timestamp_str}},
            "storagePath": {"type": "Property", "value": full_image_path_on_disk}, # Internal reference
            "@context": NGSI_LD_CONTEXT
        }

        success, _ = create_ngsi_ld_entity(training_image_payload)
        if not success:
            # Potentially delete the saved image if CB update fails, or mark for retry
            # os.remove(full_image_path_on_disk) # Example cleanup
            return jsonify({"error": "Failed to create TrainingImage entity in Context Broker"}), 500

        # 3. Update DatasetSummary entity
        dataset_summary_id = f"urn:ngsi-ld:DatasetSummary:digit_{label}"
        existing_summary = get_ngsi_ld_entity(dataset_summary_id)

        now_iso = datetime.now(timezone.utc).isoformat()
        if existing_summary:
            current_count = existing_summary.get("sampleCount", {}).get("value", 0)
            new_count = current_count + 1
            summary_attrs_payload = {
                "sampleCount": {"type": "Property", "value": new_count},
                "lastUpdatedAt": {"type": "Property", "value": {"@type": "DateTime", "@value": now_iso}}
            }
            update_success, _ = update_ngsi_ld_entity_attrs(dataset_summary_id, summary_attrs_payload)
            if not update_success:
                app.logger.warning(f"Failed to update DatasetSummary {dataset_summary_id}, but TrainingImage was created.")
        else:
            summary_payload_to_create = {
                "id": dataset_summary_id,
                "type": "DatasetSummary",
                "digitValue": {"type": "Property", "value": label},
                "sampleCount": {"type": "Property", "value": 1},
                "createdAt": {"type": "Property", "value": {"@type": "DateTime", "@value": now_iso}},
                "lastUpdatedAt": {"type": "Property", "value": {"@type": "DateTime", "@value": now_iso}},
                "@context": NGSI_LD_CONTEXT
            }
            create_success, _ = create_ngsi_ld_entity(summary_payload_to_create)
            if not create_success:
                app.logger.warning(f"Failed to create DatasetSummary {dataset_summary_id}, but TrainingImage was created.")

        return jsonify({"message": f"Digit {label} received and stored.", "imageId": image_id, "entityId": entity_id}), 201

    except Exception as e:
        app.logger.error(f"Error in /api/collect: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500


@app.route('/api/predict', methods=['POST'])
def api_predict_digit():
    try:
        data = request.get_json()
        image_data_b64 = data.get('imageDataB64')
        model_id = data.get('modelId', 'mock')  # Default to mock if not provided

        if not image_data_b64:
            return jsonify({"error": "Missing image data"}), 400

        # 1. Decode the image data
        header, encoded = image_data_b64.split(",", 1)
        image_binary = base64.b64decode(encoded)

        # 2. Generate a unique ID for this prediction
        prediction_id = str(uuid.uuid4())

        # For this example, we are NOT processing the image or using a real model.
        # We will return a MOCK prediction.
        mock_confidences = np.random.rand(10).astype(float)
        mock_confidences = mock_confidences / np.sum(mock_confidences) # Normalize to sum to 1 (like softmax)

        predicted_label = int(np.argmax(mock_confidences))
        confidence = float(np.max(mock_confidences))
        all_confidences_list = mock_confidences.tolist()

        # 3. Save the drawn image to the predictions folder
        filename = f"{prediction_id}.png"
        relative_image_path = os.path.join(str(predicted_label), filename)
        full_image_path_on_disk = os.path.join(PREDICTION_STORAGE_PATH, relative_image_path)

        with open(full_image_path_on_disk, "wb") as f:
            f.write(image_binary)

        # Image URL that will be served by our Flask app
        image_url_served_by_app = f"/predictions/{relative_image_path}"

        # 4. Create a PredictionResult entity in the Context Broker
        now_iso = datetime.now(timezone.utc).isoformat()
        prediction_entity_id = f"urn:ngsi-ld:PredictionResult:{prediction_id}"
        
        prediction_entity = {
            "id": prediction_entity_id,
            "type": "PredictionResult",
            "predictedLabel": {"type": "Property", "value": predicted_label},
            "confidence": {"type": "Property", "value": confidence},
            "allConfidences": {"type": "Property", "value": all_confidences_list},
            "imageUrl": {"type": "Property", "value": image_url_served_by_app},
            "storagePath": {"type": "Property", "value": full_image_path_on_disk},
            "createdAt": {"type": "Property", "value": {"@type": "DateTime", "@value": now_iso}},
            "modelId": {"type": "Property", "value": model_id},
            "@context": NGSI_LD_CONTEXT
        }
        
        # Save to Context Broker
        success, _ = create_ngsi_ld_entity(prediction_entity)
        if not success:
            app.logger.warning(f"Failed to create PredictionResult entity {prediction_entity_id}, but prediction was made.")

        return jsonify({
            "predicted_label": predicted_label,
            "confidence": round(confidence * 100, 2),
            "all_confidences": all_confidences_list,
            "prediction_id": prediction_id,
            "entity_id": prediction_entity_id
        }), 200

    except Exception as e:
        app.logger.error(f"Error in /api/predict: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500


# Route to serve collected images (for `imageUrl` in NGSI-LD entity)
@app.route('/images/<path:filename_with_subdir>')
def serve_collected_image(filename_with_subdir):
    # filename_with_subdir will be like "0/image_id.png"
    return send_from_directory(IMAGE_STORAGE_PATH, filename_with_subdir)

# Route to serve prediction images
@app.route('/predictions/<path:filename_with_subdir>')
def serve_prediction_image(filename_with_subdir):
    return send_from_directory(PREDICTION_STORAGE_PATH, filename_with_subdir)


if __name__ == '__main__':
    # Ping the context broker on startup 
    ping_result, ping_info = ping_context_broker()
    print(f"Context broker ping result: {ping_result}")
    print(f"Context broker info: {json.dumps(ping_info, indent=2)}")
    
    # Make sure debug is False in production
    app.run(debug=True, host='0.0.0.0', port=5001)
