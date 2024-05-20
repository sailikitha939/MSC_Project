const apiUrl = 'http://127.0.0.1:8000';

function createMessageElement(text, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message', isUser ? 'user-message' : 'assistant-message');
    const messageText = document.createElement('p');
    messageText.textContent = text;
    messageDiv.appendChild(messageText);
    return messageDiv;
}

function appendMessageToChat(text, isUser) {
    const chatOutput = document.getElementById('chatOutput');
    const messageElement = createMessageElement(text, isUser);
    chatOutput.appendChild(messageElement);
    chatOutput.scrollTop = chatOutput.scrollHeight;
}

function askQuestion() {
  const questionInput = document.getElementById('questionInput');
  const question = questionInput.value.trim();
  if (question !== "") {
      appendMessageToChat(question, true); // Display the user's question
      questionInput.value = ''; // Clear the input field

      // Display typing indicator
      appendTypingIndicator();

      // Simulate fetching answer
      fetch(`${apiUrl}/ask_question/`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ question: question }),
      })
      .then(response => response.json())
      .then(data => {
          removeTypingIndicator(); 
          appendMessageToChat(data.answer || "Could not find an answer.", false); // Display the assistant's answer
      })
      .catch((error) => {
          console.error('Error:', error);
          removeTypingIndicator(); 
          alert("An error occurred while fetching the answer.");
      });
  }
}

function appendTypingIndicator() {
  const chatOutput = document.getElementById('chatOutput');
  const messageDiv = document.createElement('div');
  messageDiv.classList.add('chat-message', 'typing-indicator-bubble'); 
  const typingIndicator = document.createElement('div');
  typingIndicator.classList.add('typing-indicator');
  for (let i = 0; i < 3; i++) {
      const dot = document.createElement('span');
      dot.textContent = '.';
      typingIndicator.appendChild(dot);
  }

  messageDiv.appendChild(typingIndicator); 
  chatOutput.appendChild(messageDiv);
  chatOutput.scrollTop = chatOutput.scrollHeight;
}

function removeTypingIndicator() {
  const typingIndicatorBubble = document.querySelector('.typing-indicator-bubble'); 
  if (typingIndicatorBubble) {
      typingIndicatorBubble.remove();
  }
}
// Function to display default questions
function displayDefaultQuestions() {
  const defaultQuestions = [
      "Hi, How can I help you?",
  ];

  defaultQuestions.forEach((question, index) => {
      setTimeout(() => {
          appendMessageToChat(question, false); 
      }, index * 1000); 
  });
}


window.onload = function() {
  displayDefaultQuestions();
};

document.addEventListener('DOMContentLoaded', (event) => {
  const questionInput = document.getElementById('questionInput');

  questionInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
          e.preventDefault(); 
          askQuestion(); 
      }
  });
});


function renderResponse(response) {
  const answerElement = document.getElementById('answer');
  answerElement.innerHTML = ''; // Clear previous answer


  for (const key in response) {
      const value = response[key];


      const container = document.createElement('div');
      container.classList.add('response-section');


      container.innerHTML = `
          <h3>${formatTitle(key)}</h3>
          <p>${value}</p>
      `;

      answerElement.appendChild(container);
  }
}

// Example usage with a sample response
const sampleResponse = {
  "treatment": "Steroid Tablets",
  "use": "Immediate asthma attack treatment; long-term prevention",
  "benefits": "Helps control symptoms",
  "sideEffects": "Weight gain, mood changes, high blood pressure"
};

renderResponse(sampleResponse);


function formatTitle(key) {
  return key.replace(/([A-Z])/g, ' $1') // Insert space before capital letters
            .replace(/^./, (str) => str.toUpperCase()) // Capitalize the first letter
            .trim();
}


