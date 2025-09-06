# ui/chat/chat_worker.py
"""
Background worker thread for RAG operations
"""
import requests
import json
import logging
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)

class RagWorkerThread(QThread):
    """
    Worker thread for handling RAG requests with retry logic
    """
    
    responseReceived = Signal(str)
    errorOccurred = Signal(str)
    progressUpdate = Signal(str)
    retryAvailable = Signal(str)  # Signal that retry is available for a question
    
    def __init__(self, server_url: str = "http://localhost:7001"):
        super().__init__()
        self.server_url = server_url
        self.question = ""
        self.k = 5
        self.retry_count = 0
        self.max_retries = 3
    
    def setQuestion(self, question: str, k: int = 5):
        """Set the question to process"""
        self.question = question
        self.k = k
        self.retry_count = 0
    
    def run(self):
        """Execute the RAG request"""
        if not self.question:
            self.errorOccurred.emit("No question provided")
            return
        
        self.progressUpdate.emit("Searching relevant documents...")
        
        try:
            response = requests.post(
                f"{self.server_url}/ask",
                json={"question": self.question, "k": self.k},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', '')
                
                if answer and answer.strip():
                    # Success - emit answer
                    self.responseReceived.emit(answer)
                else:
                    # Empty answer - enable retry
                    error_msg = "No answer generated. The system couldn't find relevant information."
                    self.errorOccurred.emit(error_msg)
                    self.retryAvailable.emit(self.question)
            
            elif response.status_code in [503, 504]:
                # Service temporarily unavailable - auto retry
                if self.retry_count < self.max_retries:
                    self.retry_count += 1
                    self.progressUpdate.emit(f"Service temporarily unavailable. Retrying... ({self.retry_count}/{self.max_retries})")
                    self.msleep(2000)  # Wait 2 seconds
                    self.run()  # Retry
                else:
                    error_msg = f"Service unavailable after {self.max_retries} retries"
                    self.errorOccurred.emit(error_msg)
                    self.retryAvailable.emit(self.question)
            
            elif response.status_code == 422:
                # Bad request - don't retry
                error_msg = f"Invalid request: {response.text}"
                self.errorOccurred.emit(error_msg)
                # No retry for bad requests
            
            else:
                # Other errors - enable manual retry
                error_msg = f"Server error ({response.status_code})"
                self.errorOccurred.emit(error_msg)
                self.retryAvailable.emit(self.question)
                
        except requests.exceptions.Timeout:
            error_msg = "Request timed out. The server might be busy."
            self.errorOccurred.emit(error_msg)
            self.retryAvailable.emit(self.question)
            
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to server. Please check if the server is running."
            self.errorOccurred.emit(error_msg)
            # No retry if server is not running
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.errorOccurred.emit(error_msg)
            self.retryAvailable.emit(self.question)
