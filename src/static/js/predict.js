document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('drawing-canvas');
    const ctx = canvas.getContext('2d');
    const clearButton = document.getElementById('clear-button');
    const predictButton = document.getElementById('predict-button');
    const modelSelect = document.getElementById('model-select');
    const modelLoadingStatus = document.getElementById('model-loading-status');

    const predictionResultContainer = document.getElementById('prediction-result-container');
    const predictedDigitSpan = document.getElementById('predicted-digit');
    const confidenceScoreSpan = document.getElementById('confidence-score');
    const confidenceBarsDiv = document.getElementById('confidence-bars');
    const predictFeedbackMessage = document.getElementById('predict-feedback-message');


    let drawing = false;

    // Canvas setup
    ctx.lineWidth = 15; // Thickness of the line
    ctx.lineCap = 'round';
    ctx.strokeStyle = 'black';

    // Fetch available models from the API
    async function loadModels() {
        try {
            modelLoadingStatus.textContent = 'Loading models...';
            const response = await fetch('/api/models');
            if (!response.ok) {
                throw new Error('Failed to fetch models');
            }
            
            const models = await response.json();
            
            // Clear the existing options
            modelSelect.innerHTML = '';
            
            // Add each model as an option
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.name;
                if (model.description) {
                    option.title = model.description;
                }
                modelSelect.appendChild(option);
            });
            
            modelLoadingStatus.textContent = models.length > 1 ? 
                `${models.length} models loaded` : 
                'Default mock model loaded';
        } catch (error) {
            console.error('Error loading models:', error);
            modelLoadingStatus.textContent = 'Error loading models. Using default mock model.';
            
            // Ensure there's at least the default model
            modelSelect.innerHTML = '<option value="mock" selected>Mock model by default</option>';
        }
    }

    function getMousePos(canvasDom, event) {
        const rect = canvasDom.getBoundingClientRect();
        const scaleX = canvasDom.width / rect.width;
        const scaleY = canvasDom.height / rect.height;
         if (event.touches && event.touches.length > 0) {
            return {
                x: (event.touches[0].clientX - rect.left) * scaleX,
                y: (event.touches[0].clientY - rect.top) * scaleY
            };
        }
        return {
            x: (event.clientX - rect.left) * scaleX,
            y: (event.clientY - rect.top) * scaleY
        };
    }

    function startDrawing(e) {
        e.preventDefault();
        drawing = true;
        const pos = getMousePos(canvas, e);
        ctx.beginPath();
        ctx.moveTo(pos.x, pos.y);
    }

    function draw(e) {
        e.preventDefault();
        if (!drawing) return;
        const pos = getMousePos(canvas, e);
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();
    }

    function stopDrawing() {
        if (!drawing) return;
        drawing = false;
        ctx.beginPath();
    }

    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseleave', stopDrawing);

    canvas.addEventListener('touchstart', startDrawing);
    canvas.addEventListener('touchmove', draw);
    canvas.addEventListener('touchend', stopDrawing);


    function clearCanvas() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        predictionResultContainer.style.display = 'none';
        predictFeedbackMessage.textContent = '';
    }

    function displayConfidenceBars(confidencesArray) { // confidencesArray is [0.1, 0.05, ..., 0.8, ...]
        confidenceBarsDiv.innerHTML = ''; // Clear previous bars
        confidencesArray.forEach((confidence, digit) => {
            const barWrapper = document.createElement('div');
            barWrapper.className = 'confidence-bar-wrapper';

            const label = document.createElement('span');
            label.className = 'confidence-bar-label';
            label.textContent = `${digit}:`;

            const barOuter = document.createElement('div');
            barOuter.className = 'confidence-bar-outer';

            const barInner = document.createElement('div');
            barInner.className = 'confidence-bar-inner';
            const percentage = (confidence * 100);
            barInner.style.width = `${percentage}%`;
            // barInner.textContent = `${percentage.toFixed(1)}%`; // Text inside bar

            const percentageText = document.createElement('span');
            percentageText.className = 'confidence-bar-percentage';
            percentageText.textContent = `${percentage.toFixed(1)}%`;


            barOuter.appendChild(barInner);
            barWrapper.appendChild(label);
            barWrapper.appendChild(barOuter);
            barWrapper.appendChild(percentageText);
            confidenceBarsDiv.appendChild(barWrapper);
        });
    }


    async function predictDigit() {
        // Create a temporary 28x28 canvas for resizing
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = 28;
        tempCanvas.height = 28;
        const tempCtx = tempCanvas.getContext('2d');
        tempCtx.drawImage(canvas, 0, 0, canvas.width, canvas.height, 0, 0, 28, 28);
        const imageDataUrl = tempCanvas.toDataURL('image/png');

        predictButton.disabled = true;
        predictFeedbackMessage.textContent = 'Predicting...';
        predictFeedbackMessage.style.color = 'blue';
        predictionResultContainer.style.display = 'none';

        // Get the selected model
        const selectedModelId = modelSelect.value;

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    imageDataB64: imageDataUrl,
                    modelId: selectedModelId,
                    timestamp: new Date().toISOString()
                }),
            });

            const result = await response.json();
            predictButton.disabled = false;

            if (response.ok) {
                predictedDigitSpan.textContent = result.predicted_label;
                confidenceScoreSpan.textContent = result.confidence.toFixed(2);
                displayConfidenceBars(result.all_confidences);
                predictionResultContainer.style.display = 'block';
                predictFeedbackMessage.textContent = 'Prediction complete!';
                predictFeedbackMessage.style.color = 'green';
            } else {
                predictFeedbackMessage.textContent = `Error: ${result.error || 'Failed to get prediction.'}`;
                predictFeedbackMessage.style.color = 'red';
            }
        } catch (error) {
            console.error('Error predicting digit:', error);
            predictFeedbackMessage.textContent = 'Network error. Please try again.';
            predictFeedbackMessage.style.color = 'red';
            predictButton.disabled = false;
        }
    }

    clearButton.addEventListener('click', clearCanvas);
    predictButton.addEventListener('click', predictDigit);

    // Initial setup
    clearCanvas();
    loadModels(); // Load available models when the page loads
});
