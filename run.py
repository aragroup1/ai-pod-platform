"""
Railway-compatible server entry point
Handles PORT environment variable correctly
"""
import os
import uvicorn

if __name__ == "__main__":
    # Get PORT from environment, Railway sets this automatically
    port = int(os.getenv("PORT", 8000))
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
