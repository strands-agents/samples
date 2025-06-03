import React, { useState } from 'react';
import { 
  Button, 
  TextField, 
  Box, 
  Typography, 
  Paper, 
  CircularProgress,
  Container,
  List,
  ListItem,
  Divider
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MarkdownRenderer from "./MarkdownRenderer.js";

const StreamingResponseComponent = () => {
  const [prompt, setPrompt] = useState('');
  const [responses, setResponses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!prompt.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://CdkStr-Agent-MtRX6gHtMjIR-941229847.us-east-1.elb.amazonaws.com/assistant-streaming', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      });

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let responseText = '';

      // Read the streaming response
      while (true) {
        const { value, done } = await reader.read();
        
        if (done) {
          break;
        }
        
        // Decode the chunk and add it to the response text
        const chunk = decoder.decode(value, { stream: true });
        responseText += chunk;
        
        // Add the current response to the array
        setResponses(prev => {
          // Replace the last response if it's from the current prompt,
          // otherwise add a new response
          const newResponses = [...prev];
          if (newResponses.length > 0 && newResponses[newResponses.length - 1].prompt === prompt) {
            newResponses[newResponses.length - 1].response = responseText;
          } else {
            newResponses.push({ prompt, response: responseText });
          }
          return newResponses;
        });
      }
      
      // Reset prompt after successful submission
      setPrompt('');
    } catch (err) {
      console.error('Error fetching response:', err);
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Paper elevation={3} sx={{ p: 3, my: 3 }}>
        <Typography variant="h5" gutterBottom>
          Streaming API Response
        </Typography>
        
        <Box component="form" onSubmit={handleSubmit} sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              rows={2}
              variant="outlined"
              label="Enter your prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={loading}
              sx={{ mb: 1 }}
            />
            <Button 
              variant="contained" 
              color="primary"
              type="submit"
              disabled={loading || !prompt.trim()}
              sx={{ mt: 1, height: 40 }}
              endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
            >
              {loading ? 'Sending...' : 'Send'}
            </Button>
          </Box>
        </Box>

        {error && (
          <Paper elevation={0} sx={{ p: 2, mb: 2, bgcolor: 'error.light', color: 'error.contrastText' }}>
            <Typography>{error}</Typography>
          </Paper>
        )}

        <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
          Responses
        </Typography>
        
        {responses.length > 0 ? (
          <List>
            {responses.map((item, index) => (
              <React.Fragment key={index}>
                <ListItem sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                  <Typography variant="subtitle1" fontWeight="bold" sx={{ mb: 1 }}>
                    Prompt: {item.prompt}
                  </Typography>
                  <Typography component="div" variant="body1">
                    
                    <MarkdownRenderer content={item.response} />
                  </Typography>
                </ListItem>
                {index < responses.length - 1 && <Divider component="li" />}
              </React.Fragment>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No responses yet. Enter a prompt and click "Send" to get started.
          </Typography>
        )}
      </Paper>
    </Container>
  );
};

export default StreamingResponseComponent;