#!/usr/bin/env python
"""
RAG System Main Entry Point - Cross-Platform Version
Works on both Windows and Linux/Mac
"""
import os
import sys
import time
import subprocess
import signal
import argparse
import logging
import platform
from pathlib import Path
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGSystemLauncher:
    """Manages the RAG system components - Cross-platform"""
    
    def __init__(self):
        self.server_process: Optional[subprocess.Popen] = None
        self.ui_process: Optional[subprocess.Popen] = None
        self.project_root = Path(__file__).parent
        self.is_windows = platform.system() == "Windows"
        self.is_linux = platform.system() == "Linux"
        self.is_mac = platform.system() == "Darwin"
        
        logger.info(f"Platform detected: {platform.system()}")
        
    def check_environment(self):
        """Check if environment is properly set up"""
        # Check for .env file
        env_file = self.project_root / ".env"
        if not env_file.exists():
            logger.warning(" .env file not found!")
            
            sample_file = self.project_root / ".env.sample"
            if sample_file.exists():
                logger.error("Please copy .env.sample to .env and add your API keys")
                if self.is_linux or self.is_mac:
                    logger.info("Run: cp .env.sample .env")
                else:
                    logger.info("Run: copy .env.sample .env")
                return False
            else:
                logger.error(".env.sample not found! Cannot proceed.")
                return False
        
        # Check for required directories
        required_dirs = ["config", "rag", "server", "ui"]
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                logger.error(f"Required directory '{dir_name}' not found!")
                return False
        
        # Check for config files
        config_file = self.project_root / "config" / "config.yaml"
        if not config_file.exists():
            logger.error("config/config.yaml not found!")
            return False
            
        return True
    
    def get_python_executable(self):
        """Get the correct Python executable path"""
        if self.is_windows:
            # Check if we're in a virtual environment
            venv_python = self.project_root / "venv" / "Scripts" / "python.exe"
            if venv_python.exists():
                return str(venv_python)
        else:  # Linux/Mac
            venv_python = self.project_root / "venv" / "bin" / "python"
            if venv_python.exists():
                return str(venv_python)
        
        # Fallback to system Python
        return sys.executable
    
    def start_server(self, port: int = 7001):
        """Start the FastAPI server - Cross-platform version"""
        logger.info("Starting RAG server...")
        
        server_script = self.project_root / "run_server.py"
        if not server_script.exists():
            logger.error("run_server.py not found!")
            return False
        
        python_exe = self.get_python_executable()
        logger.debug(f"Using Python: {python_exe}")
        
        try:
            # Platform-specific process creation
            if self.is_windows:
                # Windows: Create new console window
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                self.server_process = subprocess.Popen(
                    [python_exe, str(server_script)],
                    cwd=str(self.project_root),
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    startupinfo=startupinfo
                )
            else:
                # Linux/Mac: Run in background with proper signal handling
                self.server_process = subprocess.Popen(
                    [python_exe, str(server_script)],
                    cwd=str(self.project_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid if not self.is_windows else None
                )
            
            # Wait for server to be ready
            logger.info(f"Waiting for server to start on port {port}...")
            
            # Check if server is responding
            server_ready = False
            max_attempts = 15
            
            for attempt in range(max_attempts):
                time.sleep(2)
                
                # Check if process is still running
                if self.server_process.poll() is not None:
                    logger.error("Server process terminated unexpectedly")
                    return False
                
                # Try to connect to server
                try:
                    import requests
                    response = requests.get(f"http://localhost:{port}/health", timeout=1)
                    if response.status_code == 200:
                        server_ready = True
                        logger.info(f"Server started successfully on http://localhost:{port}")
                        break
                except:
                    logger.debug(f"Attempt {attempt + 1}/{max_attempts}: Server not ready yet...")
                    continue
            
            if not server_ready:
                logger.warning("Server is taking longer than expected to start...")
                logger.info("Proceeding anyway - server may still be initializing")
                
            return True
                
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    def start_ui(self):
        """Start the Qt UI application - Cross-platform"""
        logger.info("Starting Qt UI...")
        
        ui_script = self.project_root / "qt_app.py"
        if not ui_script.exists():
            logger.error("qt_app.py not found!")
            return False
        
        python_exe = self.get_python_executable()
        
        try:
            if self.is_windows:
                # Windows: Normal process (Qt creates its own window)
                self.ui_process = subprocess.Popen(
                    [python_exe, str(ui_script)],
                    cwd=str(self.project_root)
                )
            else:
                # Linux/Mac: Run with proper display handling
                env = os.environ.copy()
                
                # Ensure DISPLAY is set for X11 (Linux)
                if self.is_linux and 'DISPLAY' not in env:
                    env['DISPLAY'] = ':0'
                
                self.ui_process = subprocess.Popen(
                    [python_exe, str(ui_script)],
                    cwd=str(self.project_root),
                    env=env
                )
            
            # Check if UI started successfully
            time.sleep(2)
            if self.ui_process.poll() is None:
                logger.info("Qt UI started successfully")
                return True
            else:
                logger.error("UI process terminated unexpectedly")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start UI: {e}")
            return False
    
    def stop_all(self):
        """Stop all running processes - Cross-platform"""
        logger.info("Stopping all processes...")
        
        # Stop UI
        if self.ui_process and self.ui_process.poll() is None:
            logger.info("Stopping UI...")
            if self.is_windows:
                self.ui_process.terminate()
            else:
                self.ui_process.terminate()
            try:
                self.ui_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ui_process.kill()
        
        # Stop server
        if self.server_process and self.server_process.poll() is None:
            logger.info("Stopping server...")
            if self.is_windows:
                self.server_process.terminate()
            else:
                # On Linux/Mac, terminate the process group
                try:
                    os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
                except:
                    self.server_process.terminate()
            
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                if self.is_windows:
                    self.server_process.kill()
                else:
                    try:
                        os.killpg(os.getpgid(self.server_process.pid), signal.SIGKILL)
                    except:
                        self.server_process.kill()
        
        logger.info("All processes stopped")
    
    def run_server_only(self):
        """Run only the server"""
        if not self.check_environment():
            return 1
        
        if not self.start_server():
            return 1
        
        logger.info("Server is running. Press Ctrl+C to stop.")
        try:
            # Keep running until interrupted
            while True:
                if self.server_process.poll() is not None:
                    logger.error("Server stopped unexpectedly")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nShutdown signal received...")
            self.stop_all()
        
        return 0
    
    def run_ui_only(self):
        """Run only the UI (assumes server is already running)"""
        if not self.check_environment():
            return 1
        
        # Check if server is running
        import requests
        try:
            response = requests.get("http://localhost:7001/health", timeout=2)
            if response.status_code != 200:
                logger.warning("Server health check failed. Is the server running?")
        except:
            logger.warning("Cannot connect to server at http://localhost:7001")
            logger.info("Please start the server first with: python main.py --server")
            return 1
        
        if not self.start_ui():
            return 1
        
        logger.info("UI is running. Close the window or press Ctrl+C to stop.")
        try:
            # Wait for UI to close
            self.ui_process.wait()
        except KeyboardInterrupt:
            logger.info("\nShutdown signal received...")
            self.stop_all()
        
        return 0
    
    def run_all(self):
        """Run both server and UI"""
        if not self.check_environment():
            return 1
        
        # Start server
        if not self.start_server():
            return 1
        
        # Give server time to fully initialize
        time.sleep(3)
        
        # Start UI
        if not self.start_ui():
            self.stop_all()
            return 1
        
        logger.info("="*60)
        logger.info("RAG System is running!")
        logger.info("Server: http://localhost:7001")
        logger.info("UI: Qt application window")
        logger.info("Press Ctrl+C to stop all components")
        logger.info("="*60)
        
        try:
            # Monitor both processes
            while True:
                # Check if UI closed
                if self.ui_process and self.ui_process.poll() is not None:
                    logger.info("UI closed by user")
                    break
                
                # Check if server crashed
                if self.server_process and self.server_process.poll() is not None:
                    logger.error("Server crashed unexpectedly!")
                    break
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\nShutdown signal received...")
        
        self.stop_all()
        return 0

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="RAG System Launcher - Cross-Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py              # Run both server and UI
  python main.py --server     # Run server only
  python main.py --ui         # Run UI only (server must be running)
  python main.py --help       # Show this help

Platform: """ + platform.system() + """
Python: """ + sys.version.split()[0]
    )
    
    parser.add_argument(
        "--server", 
        action="store_true",
        help="Run server only"
    )
    parser.add_argument(
        "--ui", 
        action="store_true",
        help="Run UI only (requires server to be running)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7001,
        help="Server port (default: 7001)"
    )
    
    args = parser.parse_args()
    
    # ASCII Art Banner
    print(f"""
    ╔═══════════════════════════════════════╗
    ║     RAG System Launcher v2.0          ║
    ║   Retrieval-Augmented Generation      ║
    ║       Platform: {platform.system():20} ║
    ╚═══════════════════════════════════════╝
    """)
    
    launcher = RAGSystemLauncher()
    
    # Handle signals properly for each platform
    def signal_handler(sig, frame):
        logger.info("\nReceived interrupt signal...")
        launcher.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    if not launcher.is_windows:
        signal.signal(signal.SIGTERM, signal_handler)
    
    # Determine what to run
    if args.server:
        return launcher.run_server_only()
    elif args.ui:
        return launcher.run_ui_only()
    else:
        return launcher.run_all()

if __name__ == "__main__":
    sys.exit(main())
