# Captions

Are accessed on the admin (frontend) via its own api Endpoint

```javascript
async function saveCaptions(...ids) {
  for (const id of ids) {
    try {
      const response = await fetch(`https://YOURSCHOOL.teachable.com/api/v1/captions?attachment_id=${id}`);
      const data = await response.json();
      
      if (data.captions && data.captions.length > 0) {
        // Create downloadable file
        const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        // Create temporary link and trigger download
        const link = document.createElement('a');
        link.href = url;
        link.download = `captions_${id}.json`;
        document.body.appendChild(link);
        link.click();
        
        // Cleanup
        setTimeout(() => {
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
        }, 100);
      }
    } catch (error) {
      console.error(`Error processing ID ${id}:`, error);
    }
  }
}

// Usage example:
// saveCaptions('12392534', '23456789', '34567890');
```

This function:

1. Accepts multiple IDs as arguments using rest parameters
2. Processes each ID sequentially using a `for...of` loop
3. Fetches data from the API endpoint for each ID
4. Checks if the `captions` array is not empty
5. Triggers a file download dialog with the JSON data when captions exist
6. Includes error handling and proper resource cleanup

Key features:

- Downloads files as JSON with the naming convention `captions_[ID].json`
- Handles both successful and failed requests gracefully
- Automatically cleans up created DOM elements and object URLs
- Processes IDs sequentially to avoid overwhelming the browser

To use it, simply call with your IDs as arguments:

```javascript
saveCaptions('12392534', '23456789', '34567890');
```

Note: This must be run in the context of a web page (like the Chrome DevTools console) where you have proper CORS permissions to access the API endpoint.
