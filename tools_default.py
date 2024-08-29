import os
import io
import unittest

read_file_tool_desc = {
    "name": "read_file",
    "description": "Read the contents of a specified file.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path to the file to be read, including the file name and extension."
            }
        },
        "required": ["file_path"]
    }
}

def read_file_tool(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return content
    except Exception as e:
        return f"An error occurred while reading the file: {e}"

write_file_tool_desc = {
    "name": "write_file",
    "description": "Write data to a specified file.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path to the file to be written to, including the file name and extension."
            },
            "data": {
                "type": "string",
                "description": "The data to be written to the file."
            }
        },
        "required": ["file_path", "data"]
    }
}

def write_file_tool(file_path, data):
    try:
        with open(file_path, 'w') as file:
            file.write(data)
        return f"Data successfully written to {file_path}."
    except Exception as e:
        return f"An error occurred while writing to the file: {e}"


run_file_tool_desc = {
    "name": "run_file",
    "description": "Run a specified Python file and return its output.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path to the Python file to be executed, including the file name and extension."
            }
        },
        "required": ["file_path"]
    }
}

def run_file_tool(file_path):
    try:
        # Capture stdout using os.dupterm
        output_buffer = io.StringIO()
        original_term = os.dupterm(output_buffer)

        # Execute the file
        with open(file_path, 'r') as file:
            exec(file.read(), globals())

        # Restore original terminal and get the captured output
        os.dupterm(original_term)
        output = output_buffer.getvalue()

        output = output[-1024:] # Only take the final part of the output to reduce the tokens
        return output
    except Exception as e:
        import sys
        sys.print_exception(e)
        return f"An error occurred while running the file: {e}"


run_unittest_tool_desc = {
    "name": "run_unittest",
    "description": "Run unittest on a specified test file and return the results.",
    "input_schema": {
        "type": "object",
        "properties": {
            "test_file_path": {
                "type": "string",
                "description": "The path to the test file to be executed, including the file name and extension."
            }
        },
        "required": ["test_file_path"]
    }
}

def run_unittest_tool(test_file_path):
    try:
        import unittest
        import io

        # Load the test module
        test_module_name = test_file_path.split('/')[-1].replace('.py', '')
        test_module = __import__(test_module_name)

        # Capture stdout
        output_buffer = io.StringIO()
        original_term = os.dupterm(output_buffer)

        # Run the tests
        unittest.main(test_module)

        # Restore original terminal and get the captured output
        os.dupterm(original_term)
        output = output_buffer.getvalue()
        
        return f"Unittest results:\n{output}"
    except SystemExit:
        # unittest.main() calls sys.exit(), so we need to catch it
        output = output_buffer.getvalue()
        return f"Unittest results:\n{output}"
    except Exception as e:
        return f"An error occurred while running unittest: {e}"
