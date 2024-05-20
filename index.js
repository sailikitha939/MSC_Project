const express = require('express');
const path = require('path');

const app = express();
const port = 3000;

// Serve static files from the frontend directory
app.use(express.static(path.join(__dirname, 'frontend')));

// Define a route to handle the root URL ("/")
app.get('/', (req, res) => {
  // Send the index.html file as a response from the frontend directory
  res.sendFile(path.join(__dirname, 'frontend', 'index.html'));
});

// Start the server
app.listen(port, () => {
  console.log(`Server is running at http://localhost:${port}`);
});
