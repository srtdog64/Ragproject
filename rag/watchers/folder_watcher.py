"""
Folder watcher for automatic document ingestion using watchdog
"""
import os
import time
import logging
from pathlib import Path
from typing import Set, Dict, Optional, Callable
from queue import Queue, Empty
from threading import Thread, Event
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

logger = logging.getLogger(__name__)

class DocumentIngestionHandler(FileSystemEventHandler):
    """
    Handler for monitoring document additions to watched folders
    """
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.md', '.txt', '.json', '.docx'}
    FILE_STABLE_TIME = 2.0  # Wait 2 seconds for file to stabilize
    
    def __init__(self, ingest_queue: Queue, watched_folder: str):
        """
        Initialize the handler
        
        Args:
            ingest_queue: Queue for pending ingest tasks
            watched_folder: Path to the watched folder
        """
        super().__init__()
        self.ingest_queue = ingest_queue
        self.watched_folder = Path(watched_folder)
        self.pending_files: Dict[str, float] = {}  # Track file creation times
        self.processed_files: Set[str] = set()  # Avoid duplicate processing
        
        # Start file stability checker thread
        self.stop_event = Event()
        self.checker_thread = Thread(target=self._check_file_stability, daemon=True)
        self.checker_thread.start()
    
    def on_created(self, event):
        """Handle file creation event"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Check if file has supported extension
        if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
            # Add to pending files with current timestamp
            self.pending_files[str(file_path)] = time.time()
            logger.info(f"Detected new file: {file_path.name}")
    
    def _check_file_stability(self):
        """Check if pending files are stable (fully written)"""
        while not self.stop_event.is_set():
            current_time = time.time()
            stable_files = []
            
            # Check each pending file
            for file_path, added_time in list(self.pending_files.items()):
                if current_time - added_time >= self.FILE_STABLE_TIME:
                    # File has been stable for required time
                    if Path(file_path).exists():
                        # Double-check file is fully written by checking size
                        try:
                            size1 = Path(file_path).stat().st_size
                            time.sleep(0.1)
                            size2 = Path(file_path).stat().st_size
                            
                            if size1 == size2 and size1 > 0:
                                stable_files.append(file_path)
                        except (IOError, OSError) as e:
                            logger.debug(f"File not ready yet: {file_path} - {e}")
                            # Reset timer for this file
                            self.pending_files[file_path] = current_time
                    else:
                        # File disappeared, remove from pending
                        stable_files.append(file_path)
            
            # Process stable files
            for file_path in stable_files:
                del self.pending_files[file_path]
                
                if Path(file_path).exists():
                    # Avoid duplicate processing
                    if file_path not in self.processed_files:
                        self.processed_files.add(file_path)
                        
                        # Add to ingest queue
                        self.ingest_queue.put({
                            'type': 'file',
                            'path': file_path,
                            'timestamp': time.time()
                        })
                        
                        logger.info(f"Added to ingest queue: {Path(file_path).name}")
            
            time.sleep(0.5)  # Check every 500ms
    
    def stop(self):
        """Stop the stability checker thread"""
        self.stop_event.set()
        if self.checker_thread.is_alive():
            self.checker_thread.join(timeout=2)


class FolderWatcher:
    """
    Main folder watcher that monitors directories for new documents
    """
    
    def __init__(self, ingest_callback: Optional[Callable] = None):
        """
        Initialize folder watcher
        
        Args:
            ingest_callback: Callback function to process documents
        """
        self.ingest_callback = ingest_callback
        self.ingest_queue = Queue()
        self.observers: Dict[str, Observer] = {}
        self.handlers: Dict[str, DocumentIngestionHandler] = {}
        self.watched_folders: Set[str] = set()
        
        # Processing thread
        self.stop_event = Event()
        self.processing_thread = None
        self.is_running = False
        self.is_processing = False  # Flag to track if we're actively processing
        
        logger.info("FolderWatcher initialized")
    
    def add_folder(self, folder_path: str) -> bool:
        """
        Add a folder to watch list
        
        Args:
            folder_path: Path to folder to watch
            
        Returns:
            True if folder was added successfully
        """
        folder_path = str(Path(folder_path).resolve())
        
        if folder_path in self.watched_folders:
            logger.warning(f"Folder already being watched: {folder_path}")
            return False
        
        if not Path(folder_path).exists():
            logger.error(f"Folder does not exist: {folder_path}")
            return False
        
        if not Path(folder_path).is_dir():
            logger.error(f"Path is not a directory: {folder_path}")
            return False
        
        # Create handler and observer for this folder
        handler = DocumentIngestionHandler(self.ingest_queue, folder_path)
        observer = Observer()
        observer.schedule(handler, folder_path, recursive=True)
        
        # Store references
        self.handlers[folder_path] = handler
        self.observers[folder_path] = observer
        self.watched_folders.add(folder_path)
        
        # Start observer if watcher is running
        if self.is_running:
            observer.start()
        
        logger.info(f"Added folder to watch: {folder_path}")
        return True
    
    def remove_folder(self, folder_path: str) -> bool:
        """
        Remove a folder from watch list
        
        Args:
            folder_path: Path to folder to stop watching
            
        Returns:
            True if folder was removed successfully
        """
        folder_path = str(Path(folder_path).resolve())
        
        if folder_path not in self.watched_folders:
            logger.warning(f"Folder not being watched: {folder_path}")
            return False
        
        # Stop and cleanup observer
        if folder_path in self.observers:
            observer = self.observers[folder_path]
            observer.stop()
            observer.join(timeout=2)
            del self.observers[folder_path]
        
        # Stop handler
        if folder_path in self.handlers:
            self.handlers[folder_path].stop()
            del self.handlers[folder_path]
        
        self.watched_folders.discard(folder_path)
        
        logger.info(f"Removed folder from watch: {folder_path}")
        return True
    
    def start(self):
        """Start watching folders"""
        if self.is_running:
            logger.warning("FolderWatcher is already running")
            return
        
        self.is_running = True
        self.stop_event.clear()
        
        # Start all observers
        for observer in self.observers.values():
            if not observer.is_alive():
                observer.start()
        
        # Start processing thread
        self.processing_thread = Thread(target=self._process_queue, daemon=True)
        self.processing_thread.start()
        
        logger.info(f"Started watching {len(self.watched_folders)} folders")
    
    def stop(self):
        """Stop watching folders"""
        if not self.is_running:
            logger.warning("FolderWatcher is not running")
            return
        
        self.is_running = False
        self.stop_event.set()
        
        # Stop all observers
        for observer in self.observers.values():
            observer.stop()
            observer.join(timeout=2)
        
        # Stop all handlers
        for handler in self.handlers.values():
            handler.stop()
        
        # Stop processing thread
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5)
        
        logger.info("Stopped watching folders")
    
    def _process_queue(self):
        """Process documents from the queue"""
        while not self.stop_event.is_set():
            try:
                # Wait for item with timeout
                item = self.ingest_queue.get(timeout=1)
                
                if item and self.ingest_callback:
                    file_path = item.get('path')
                    if file_path and Path(file_path).exists():
                        self.is_processing = True
                        try:
                            # Call the ingest callback
                            logger.info(f"Processing file: {Path(file_path).name}")
                            self.ingest_callback(file_path)
                            logger.info(f"Successfully processed: {Path(file_path).name}")
                        except Exception as e:
                            logger.error(f"Error processing file {file_path}: {e}")
                        finally:
                            self.is_processing = False
                
                self.ingest_queue.task_done()
                
            except Empty:
                # Queue is empty, continue waiting
                continue
            except Exception as e:
                logger.error(f"Error in processing thread: {e}")
    
    def get_queue_size(self) -> int:
        """Get number of files pending in queue"""
        return self.ingest_queue.qsize()
    
    def is_busy(self) -> bool:
        """Check if watcher is currently processing files"""
        return self.is_processing or self.get_queue_size() > 0
    
    def get_status(self) -> Dict:
        """Get current status of the watcher"""
        return {
            'is_running': self.is_running,
            'is_processing': self.is_processing,
            'queue_size': self.get_queue_size(),
            'watched_folders': list(self.watched_folders),
            'folder_count': len(self.watched_folders)
        }
