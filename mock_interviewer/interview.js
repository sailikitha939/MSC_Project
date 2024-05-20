document.addEventListener('DOMContentLoaded', function() {
    const interviewForm = document.getElementById('interviewForm');
    const resumeInput = document.getElementById('resumeInput');
    const fileName = document.getElementById('fileName');
    const messageInput = document.getElementById('messageInput');
    const messages = document.getElementById('messages');
    const startRecordingButton = document.getElementById('startRecording');

    let mediaRecorder;
    let audioChunks = [];

    // Display the selected file name
    resumeInput.addEventListener('change', function() {
        const file = resumeInput.files[0];
        if (file) {
            fileName.textContent = file.name;
        }
    });

    // Form submission handler
    interviewForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(interviewForm);

        alert('Form submitted successfully!');
    });

    // Send message function
    function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            addMessageToChat('user-message', message);
            messageInput.value = '';
            askQuestion(message);
        }
    }

    // Add message to chat window
    function addMessageToChat(senderClass, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', senderClass);
        messageElement.textContent = message;
        messages.appendChild(messageElement);
        messages.scrollTop = messages.scrollHeight; // Scroll to the bottom
    }

    // Ask question function
    function askQuestion(question) {
        appendTypingIndicator();
        fetch('https://api.example.com/interview', { // Replace with your API endpoint
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question }),
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator();
            addMessageToChat('assistant-message', data.answer);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while fetching the answer.');
            removeTypingIndicator();
        });
    }

    // Append typing indicator
    function appendTypingIndicator() {
        const typingIndicator = document.createElement('div');
        typingIndicator.classList.add('typing-indicator-bubble');
        typingIndicator.setAttribute('id', 'typingIndicator');
        typingIndicator.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        messages.appendChild(typingIndicator);
        messages.scrollTop = messages.scrollHeight;
    }

    // Remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            messages.removeChild(typingIndicator);
        }
    }

    // Start recording function
    startRecordingButton.addEventListener('click', function() {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            startRecordingButton.textContent = 'Record';
        } else {
            startRecording();
            startRecordingButton.textContent = 'Stop Recording';
        }
    });

    // Start recording audio
    function startRecording() {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.start();
                audioChunks = [];

                mediaRecorder.addEventListener('dataavailable', event => {
                    audioChunks.push(event.data);
                });

                mediaRecorder.addEventListener('stop', () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    const audio = new Audio(audioUrl);
                    audio.play();
                });
            }).catch(error => {
                console.error('Error accessing microphone:', error);
            });
    }

    // Attach event listeners to buttons
    document.getElementById('generateFeedback').addEventListener('click', function() {
        // Generate feedback function
        alert('Feedback generated!');
    });

    document.getElementById('goHome').addEventListener('click', function() {
        // Go back to home function
        window.location.href = 'index.html';
    });

    // Attach send message function to send button
    document.querySelector('.send-button').addEventListener('click', sendMessage);

    // Attach enter key event to message input
    messageInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            sendMessage();
        }
    });
});
