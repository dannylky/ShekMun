const express = require('express');
const cors = require('cors');
const net = require('net');

const app = express();
app.use(cors()); // Allows your frontend to talk to this backend
app.use(express.json());

// Create an API endpoint that the webpage can call
app.post('/api/restart-decoder', (req, res) => {
    const { ipAddress } = req.body;
    
    if (!ipAddress) {
        return res.status(400).json({ error: "IP address is required" });
    }

    const client = new net.Socket();
    client.setTimeout(5000); // 5 second timeout

    // Connect to the Kramer device on Port 5000
    client.connect(5000, ipAddress, () => {
        console.log(`Connected to ${ipAddress}, sending reset command...`);
        client.write('#RESET\r');
    });

    // Listen for the Kramer device's response
    client.on('data', (data) => {
        const responseText = data.toString().trim();
        console.log(`Response: ${responseText}`);
        client.destroy(); // Close the connection
        
        res.json({ success: true, response: responseText });
    });

    // Handle connection errors
    client.on('error', (err) => {
        console.error(`Socket error: ${err.message}`);
        res.status(500).json({ success: false, error: err.message });
    });

    client.on('timeout', () => {
        client.destroy();
        res.status(504).json({ success: false, error: "Connection timed out" });
    });
});

const PORT = 3000;
app.listen(PORT, () => console.log(`Proxy server running on http://localhost:${PORT}`));