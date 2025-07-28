"""
Command Line Interface for the AI Agent Flow system.
Handles user input/output and command routing.
"""

class CLIInterface:
    """Main CLI interface for user interaction."""
    
    def __init__(self):
        """Initialize CLI components."""
        self.running = True
    
    def start(self):
        """Start the CLI interface."""
        print("Starting CLI interface...")
        while self.running:
            try:
                user_input = input("AI-Agent> ")
                if user_input.lower() in ['exit', 'quit']:
                    self.running = False
                elif user_input.lower() == 'help':
                    self.show_help()
                else:
                    self.process_command(user_input)
            except KeyboardInterrupt:
                print("\nReceived keyboard interrupt. Exiting...")
                self.running = False
    
    def show_help(self):
        """Display help information."""
        print("Available commands:")
        print("  help - Show this help message")
        print("  exit - Exit the application")
        print("  process <task> - Process a task")
    
    def process_command(self, command):
        """Process a user command."""
        print(f"Processing command: {command}")
        # Placeholder for command processing logic

if __name__ == "__main__":
    cli = CLIInterface()
    cli.start()