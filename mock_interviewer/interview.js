document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("interviewForm");
    const fileInput = document.getElementById("resumeInput");
    const fileNameDisplay = document.getElementById("fileName");
    const messageInput = document.getElementById("messageInput");
    const messagesContainer = document.getElementById("messages");
    const sendButton = document.querySelector(".send-button");
    const generateFeedbackButton = document.getElementById("generateFeedback");

    // Typing indicator element
    const typingIndicator = document.createElement("div");
    typingIndicator.classList.add("typing-indicator");
    typingIndicator.innerHTML = `
        <span></span><span></span><span></span>
    `;

    // Create a Polly client
    const polly = new AWS.Polly();

    // Display selected file name
    fileInput.addEventListener("change", function () {
        const allowedExtensions = ['pdf', 'docx', 'txt'];
        const fileName = fileInput.files[0].name;
        const fileExtension = fileName.split('.').pop().toLowerCase();

        if (allowedExtensions.includes(fileExtension)) {
            fileNameDisplay.textContent = fileName;
        } else {
            fileNameDisplay.textContent = "";
            alert("Only PDF, DOCX, and TXT files are allowed.");
            fileInput.value = ""; // Clear the input
        }
    });

    // Handle form submission
    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        const formData = new FormData();
        formData.append("name", document.getElementById("name").value);
        formData.append("role", document.getElementById("role").value);
        formData.append("job_description", document.getElementById("jobDescription").value);
        formData.append("file", fileInput.files[0]);

        console.log("Submitting form with the following data:");
        for (let pair of formData.entries()) {
            console.log(`${pair[0]}: ${pair[1]}`);
        }

        await uploadFile(formData);
    });

    async function uploadFile(formData) {
        try {
            const response = await fetch("http://127.0.0.1:8000/upload", {
                method: "POST",
                body: formData,
            });
    
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, details: ${errorText}`);
            }
    
            const result = await response.json();
            console.log("Upload result:", result);
    
            // Check if the response contains the expected data
            if (result && result.filename) {
                alert("Resume Submitted Successfully, Let's Start the Interview");
            } else {
                throw new Error("Unexpected response format");
            }
        } catch (error) {
            console.error("Error uploading file:", error);
        }
    }
    

    function displayMessage(message, sender) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", sender);
        messageElement.textContent = message;
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function showTypingIndicator() {
        messagesContainer.appendChild(typingIndicator);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function hideTypingIndicator() {
        if (typingIndicator.parentNode) {
            messagesContainer.removeChild(typingIndicator);
        }
    }

    async function sendMessage() {
        const message = messageInput.value;
        if (!message) return;

        displayMessage(message, "user-message");
        messageInput.value = "";

        showTypingIndicator();

        try {
            const response = await fetch("http://127.0.0.1:8000/submit-message", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, details: ${errorText}`);
            }

            const result = await response.json();
            hideTypingIndicator();
            displayMessage(result.message, "assistant-message");
            synthesizeSpeech(result.message);
        } catch (error) {
            hideTypingIndicator();
            console.error("Error sending message:", error);
        }
    }

    async function generateFeedback() {
        showTypingIndicator();

        try {
            const response = await fetch("http://127.0.0.1:8000/generate-feedback", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, details: ${errorText}`);
            }

            const result = await response.json();
            hideTypingIndicator();
            displayMessage(result.feedback, "assistant-message");
            synthesizeSpeech(result.feedback);
        } catch (error) {
            hideTypingIndicator();
            console.error("Error generating feedback:", error);
        }
    }

    function synthesizeSpeech(text) {
        const params = {
            OutputFormat: "mp3",
            Text: text,
            VoiceId: "Joanna" // Choose a Polly voice
        };

        polly.synthesizeSpeech(params, function (err, data) {
            if (err) {
                console.log(err, err.stack);
            } else {
                const uInt8Array = new Uint8Array(data.AudioStream);
                const arrayBuffer = uInt8Array.buffer;
                const blob = new Blob([arrayBuffer], { type: "audio/mpeg" });
                const url = URL.createObjectURL(blob);
                const audio = new Audio(url);
                audio.play();
            }
        });
    }

    sendButton.addEventListener("click", sendMessage);

    // Trigger send message on pressing Enter key
    messageInput.addEventListener("keypress", function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });

    generateFeedbackButton.addEventListener("click", generateFeedback);
});