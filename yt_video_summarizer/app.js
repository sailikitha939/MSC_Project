document.getElementById('submitLink').addEventListener('click', function() {
    const youtubeLink = document.getElementById('youtubeLink').value;
    if (!youtubeLink) {
        alert('Please enter a YouTube link.');
        return;
    }

    displayThumbnail(youtubeLink);

    fetch('http://127.0.0.1:8000/process_video', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            youtube_link: youtubeLink
        }),
    })
    .then(response => response.json())
    .then(data => {
        const summaryQuizContainer = document.getElementById('result');
        summaryQuizContainer.innerHTML = '';

        const summary = document.createElement('div');
        summary.innerHTML = `<h2>Summary</h2><p>${data.summary_and_quiz.split('Quiz Questions:')[0].trim()}</p>`;
        summaryQuizContainer.appendChild(summary);

        const quizSection = data.summary_and_quiz.split('Quiz Questions:')[1];
        const quizQuestions = quizSection.split('Answers:')[0].trim().split('\n');
        const quizContainer = document.createElement('div');
        quizContainer.innerHTML = '<h2>Quiz Questions</h2>';

        quizQuestions.forEach((question, index) => {
            const questionElement = document.createElement('p');
            questionElement.innerText = question;
            quizContainer.appendChild(questionElement);
        });

        const answers = quizSection.split('Answers:')[1].trim().split('\n');
        const answersContainer = document.createElement('div');
        answersContainer.innerHTML = '<h2>Answers</h2>';

        answers.forEach((answer, index) => {
            const answerElement = document.createElement('p');
            answerElement.innerText = answer;
            answersContainer.appendChild(answerElement);
        });

        summaryQuizContainer.appendChild(quizContainer);
        summaryQuizContainer.appendChild(answersContainer);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while processing the video.');
    });
});

function displayThumbnail(youtubeLink) {
    let videoId;
    const url = new URL(youtubeLink);
    if (url.hostname === 'youtu.be') {
        videoId = url.pathname.slice(1);
    } else {
        videoId = url.searchParams.get('v');
    }
    const thumbnailUrl = `https://img.youtube.com/vi/${videoId}/0.jpg`;
    document.getElementById('thumbnail').innerHTML = `<img src="${thumbnailUrl}" alt="Video Thumbnail">`;
}
