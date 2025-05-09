document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('drawing-canvas');
    const ctx = canvas.getContext('2d');
    const clearButton = document.getElementById('clear-button');
    const sendButton = document.getElementById('send-button');
    const digitPrompt = document.getElementById('digit-prompt');
    const feedbackMessage = document.getElementById('feedback-message');
    const nextDigitButton = document.getElementById('next-digit-button');

    let drawing = false;
    let currentDigitToDraw = null;

    // Canvas setup
    ctx.lineWidth = 15; // line thickness, canvas size 280x280 -> 28x28
    ctx.lineCap = 'round';
    ctx.strokeStyle = 'black';

    function getMousePos(canvasDom, event) {
        const rect = canvasDom.getBoundingClientRect();
        const scaleX = canvasDom.width / rect.width;
        const scaleY = canvasDom.height / rect.height;
        if (event.touches && event.touches.length > 0) {
             // Handle touch events
            return {
                x: (event.touches[0].clientX - rect.left) * scaleX,
                y: (event.touches[0].clientY - rect.top) * scaleY
            };
        }
        // Handle mouse events
        return {
            x: (event.clientX - rect.left) * scaleX,
            y: (event.clientY - rect.top) * scaleY
        };
    }

    function startDrawing(e) {
        e.preventDefault(); // Prevent scrolling on touch
        drawing = true;
        const pos = getMousePos(canvas, e);
        ctx.beginPath();
        ctx.moveTo(pos.x, pos.y);
    }

    function draw(e) {
        e.preventDefault(); // Prevent scrolling on touch
        if (!drawing) return;
        const pos = getMousePos(canvas, e);
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();
    }

    function stopDrawing() {
        if (!drawing) return;
        drawing = false;
        ctx.beginPath(); // Reset path to avoid connecting next line
    }

    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseleave', stopDrawing); // Stop drawing if mouse leaves canvas

    canvas.addEventListener('touchstart', startDrawing);
    canvas.addEventListener('touchmove', draw);
    canvas.addEventListener('touchend', stopDrawing);


    function clearCanvas() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        feedbackMessage.textContent = '';
    }

    function promptNewDigit() {
        currentDigitToDraw = Math.floor(Math.random() * 10);
        digitPrompt.textContent = currentDigitToDraw;
        clearCanvas();
        sendButton.disabled = false;
        nextDigitButton.style.display = 'none';
        feedbackMessage.textContent = '';
        feedbackMessage.style.color = 'black';
    }

    async function sendDigit() {
        if (currentDigitToDraw === null) {
            feedbackMessage.textContent = 'No digit prompted yet.';
            feedbackMessage.style.color = 'red';
            return;
        }

        // Create a temporary 28x28 canvas for resizing
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = 28;
        tempCanvas.height = 28;
        const tempCtx = tempCanvas.getContext('2d');

        // --- Image Preprocessing similar to MNIST ---
        // 1. Draw the 280x280 image onto the 28x28 canvas (scales down)
        tempCtx.drawImage(canvas, 0, 0, canvas.width, canvas.height, 0, 0, 28, 28);


        // When the model is trained on images like MNIST (white digit, black background),
        // I'd need to invert the colors here or on the server.
        // For now, I send it as drawn (black on white background from canvas).
        // The server-side Python mock doesn't care, but a real model would.

        const imageDataUrl = tempCanvas.toDataURL('image/png');

        sendButton.disabled = true;
        feedbackMessage.textContent = 'Sending...';
        feedbackMessage.style.color = 'blue';

        try {
            const response = await fetch('/api/collect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    label: currentDigitToDraw,
                    imageDataB64: imageDataUrl,
                    timestamp: new Date().toISOString()
                }),
            });

            const result = await response.json();

            if (response.ok) {
                feedbackMessage.textContent = `Success: ${result.message || 'Digit submitted!'}`;
                feedbackMessage.style.color = 'green';
                nextDigitButton.style.display = 'inline-block';
            } else {
                feedbackMessage.textContent = `Error: ${result.error || 'Failed to submit digit.'}`;
                feedbackMessage.style.color = 'red';
                sendButton.disabled = false; // Re-enable if failed
            }
        } catch (error) {
            console.error('Error sending digit:', error);
            feedbackMessage.textContent = 'Network error. Please try again.';
            feedbackMessage.style.color = 'red';
            sendButton.disabled = false; // Re-enable on network error
        }
    }

    clearButton.addEventListener('click', clearCanvas);
    sendButton.addEventListener('click', sendDigit);
    nextDigitButton.addEventListener('click', promptNewDigit);

    // Initial setup
    promptNewDigit();
});


