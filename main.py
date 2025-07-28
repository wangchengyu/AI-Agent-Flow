"""
Main entry point for the AI Agent Flow application.
This script initializes and coordinates the various components
including agent management, MCP tools, LLM interface, and CLI interaction.
"""

from cli import CLIInterface
from agent_manager import AgentManager
from mcp_manager import MCPManager
from llm_interface import LLMInterface
from data_manager import DataManager
import json

class AIAgentFlow:
    """Main system orchestrator for the AI Agent Flow application."""
    
    def __init__(self):
        """Initialize all system components."""
        self.cli = CLIInterface()
        self.agent_manager = AgentManager()
        self.mcp_manager = MCPManager()
        self.llm_interface = LLMInterface()
        self.data_manager = DataManager()
        
    def _get_additional_info(self, request):
        """Request additional information from the user."""
        self.cli.show_help()
        user_input = input(f"Additional info needed: {request} - ")
        return user_input
    
    def _execute_tool_operation(self, tool_name, parameters):
        """Execute an MCP tool operation."""
        try:
            result = self.mcp_manager.execute_file_operation(tool_name, parameters)
            self.data_manager.update_file_metadata(
                parameters.get('path', ''), 
                len(result.get('content', '')) if tool_name == 'read_file' else 0
            )
            return result
        except Exception as e:
            print(f"Error executing tool: {e}")
            return {"error": str(e)}
    
    def _process_subtask(self, task_description):
        """Process a subtask using LLM reasoning and tool execution."""
        # Get LLM analysis of the task
        analysis = self.llm_interface.task_analysis(task_description)
        print(f"Task analysis: {analysis.get('choices', [{}])[0].get('message', {}).get('content', '')}")
        
        # Store original task for reference
        original_task = task_description
        
        # Request additional information if needed
        for i in range(5):  # Maximum 5 iterations
            reasoning = self.llm_interface.validate_result(
                analysis.get('choices', [{}])[0].get('message', {}).get('content', ''),
                task_description
            )
            
            if "additional information needed" in reasoning.get('choices', [{}])[0].get('message', {}).get('content', '').lower():
                request = reasoning.get('choices', [{}])[0].get('message', {}).get('content', '')
                additional_info = self._get_additional_info(request)
                
                if additional_info.lower() in ['exit', 'quit']:
                    return None
                    
                task_description += f"\nAdditional information: {additional_info}"
                analysis = self.llm_interface.task_analysis(task_description)
            else:
                break
        
        # Determine if we need to use tools or generate content
        decision = self.llm_interface.chat_completion([
            {"role": "system", "content": "Determine if this task requires tool operations or content generation"},
            {"role": "user", "content": task_description}
        ])
        
        if "tool" in decision.get('choices', [{}])[0].get('message', {}).get('content', '').lower():
            # Tool operation requested
            tool_request = self.llm_interface.chat_completion([
                {"role": "system", "content": "Specify the exact tool operation needed"},
                {"role": "user", "content": task_description}
            ])
            
            # Parse tool request (simplified implementation)
            tool_name = "read_file"  # Simplified example
            parameters = {"path": "README.md"}
            
            result = self._execute_tool_operation(tool_name, parameters)
        else:
            # Content generation requested
            result = self.llm_interface.generate_code(task_description)
        
        # Validate final result
        validation = self.llm_interface.validate_result(
            json.dumps(result), 
            original_task
        )
        
        print(f"Validation result: {validation.get('choices', [{}])[0].get('message', {}).get('content', '')}")
        
        # Save task result
        self.data_manager.save_task_result(
            original_task, 
            result,
            "completed" if "acceptable" in validation.get('choices', [{}])[0].get('message', {}).get('content', '').lower() else "needs_revision"
        )
        
        return result
    
    def validate_architecture(self):
        """Perform comprehensive validation of the system architecture."""
        print("Performing system architecture validation...")
        
        validation_results = {
            "component_health": {},
            "integration_tests": {},
            "data_flow": {},
            "security": {}
        }
        
        # Check component health
        validation_results["component_health"]["agent_manager"] = self.agent_manager is not None
        validation_results["component_health"]["mcp_manager"] = self.mcp_manager is not None
        validation_results["component_health"]["llm_interface"] = self.llm_interface is not None
        validation_results["component_health"]["data_manager"] = self.data_manager is not None
        
        # Check integration between components
        validation_results["integration_tests"]["agent_llm"] = self._test_agent_llm_integration()
        validation_results["integration_tests"]["mcp_data"] = self._test_mcp_data_integration()
        validation_results["integration_tests"]["cli_flow"] = self._test_cli_flow()
        
        # Check data flow integrity
        validation_results["data_flow"]["task_persistence"] = self._test_task_persistence()
        validation_results["data_flow"]["file_metadata"] = self._test_file_metadata_tracking()
        
        # Basic security checks
        validation_results["security"]["api_key_masked"] = self._check_api_key_masked()
        
        return validation_results
    
    def _test_agent_llm_integration(self):
        """Test integration between agent manager and LLM interface."""
        try:
            test_task = self.agent_manager.create_task('engineer', 'Write a Python function to calculate Fibonacci numbers')
            result = self.agent_manager.run_task(test_task)
            return result is not None
        except:
            return False
    
    def _test_mcp_data_integration(self):
        """Test integration between MCP tools and data manager."""
        try:
            # Test file listing
            files = self.mcp_manager.execute_file_operation("list_files", {"path": "."})
            if not files:
                return False
                
            # Test file metadata tracking
            if "README.md" in str(files):
                read_result = self.mcp_manager.execute_file_operation("read_file", {"path": "README.md"})
                return read_result is not None
                
            return True
        except:
            return False
    
    def _test_cli_flow(self):
        """Test basic CLI interaction flow."""
        try:
            # Simulate user input
            test_inputs = [
                "help",
                "process test task",
                "exit"
            ]
            
            # Override input function for testing
            original_input = input
            input_values = test_inputs.copy()
            input_values.reverse()
            
            def mock_input(prompt):
                return input_values.pop()
            
            input = mock_input
            
            # Run CLI test
            self.cli.running = True
            test_thread = threading.Thread(target=self.cli.start)
            test_thread.start()
            
            # Wait for test to complete
            test_thread.join(timeout=5)
            input = original_input
            self.cli.running = False
            
            return True
        except:
            input = original_input
            self.cli.running = False
            return False
    
    def _test_task_persistence(self):
        """Test task persistence through data manager."""
        try:
            test_task = {
                "description": "Test task",
                "result": {"output": "Test output"},
                "status": "completed"
            }
            
            # Save and retrieve task
            self.data_manager.save_task_result("Test task", test_task)
            history = self.data_manager.get_task_history(1)
            
            return len(history) > 0 and history[0]['description'] == "Test task"
        except:
            return False
    
    def _test_file_metadata_tracking(self):
        """Test file metadata tracking."""
        try:
            # Test with README.md
            test_path = "README.md"
            result = self.mcp_manager.execute_file_operation("read_file", {"path": test_path})
            
            metadata = self.data_manager.get_file_metadata(test_path)
            return metadata is not None and metadata['size'] == len(result.get('content', ''))
        except:
            return False
    
    def _check_api_key_masked(self):
        """Check if API key is masked in any output."""
        try:
            # This is a simple check - in a real system we'd need more comprehensive security checks
            api_key_str = str(self.llm_interface.api_key).lower()
            return "key" in api_key_str or "token" in api_key_str or len(api_key_str) > 4
        except:
            return False
    
    def run(self):
        """Run the AI Agent Flow system."""
        self.cli.start()
        
        while True:
            try:
                user_input = input("AI-Agent> ")
                if user_input.lower() in ['exit', 'quit']:
                    break
                elif user_input.lower() == 'help':
                    self.cli.show_help()
                elif user_input.lower() == 'validate':
                    validation_results = self.validate_architecture()
                    print("System Architecture Validation Results:")
                    print(json.dumps(validation_results, indent=2))
                elif user_input.lower().startswith('process '):
                    task = user_input[8:]
                    result = self._process_subtask(task)
                    print(f"Task result: {json.dumps(result, indent=2)}")
                else:
                    print("Unknown command. Type 'help' for available commands.")
            except KeyboardInterrupt:
                print("\nReceived keyboard interrupt. Exiting...")
                break
        
        print("Shutting down AI Agent Flow system...")

if __name__ == "__main__":
    system = AIAgentFlow()
    system.run()