"""Utility functions for the generator package."""

import sys
import time
import threading


class Spinner:
    """Simple ASCII spinner for showing progress during API calls."""

    def __init__(self, message="🤖 Generating OpenAPI spec"):
        self.message = message
        self.spinning = False
        self.thread = None
        self.spinner_chars = "|/-\\"

    def start(self):
        """Start the spinner in a separate thread."""
        self.spinning = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop the spinner."""
        self.spinning = False
        if self.thread:
            self.thread.join()
        # Clear the line
        sys.stdout.write("\r" + " " * (len(self.message) + 5) + "\r")
        sys.stdout.flush()

    def _spin(self):
        """Internal method to display the spinning animation."""
        i = 0
        while self.spinning:
            char = self.spinner_chars[i % len(self.spinner_chars)]
            sys.stdout.write(f"\r{self.message} {char}")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1


# API key related functions have been removed as they are no longer needed
