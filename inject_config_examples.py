"""
Examples demonstrating the updated inject_config decorator with param_name support
"""

from knwl.di import inject_config

# Example 1: Standard usage (parameter names match config key endings)
@inject_config('api.host', 'api.port')
def start_server_standard(host=None, port=None):
    """Config values injected to 'host' and 'port' parameters"""
    print(f"Starting server on {host}:{port}")

# Example 2: Custom parameter name for single config key
@inject_config('api.host', param_name='server_address')
def start_server_custom(server_address=None):
    """Config value 'api.host' injected to 'server_address' parameter"""
    print(f"Starting server on {server_address}")

# Example 3: Custom parameter name with override
@inject_config('database.connection_string', param_name='db_url', 
               override={'database': {'connection_string': 'sqlite:///test.db'}})
def connect_to_db(db_url=None):
    """Config value injected with custom parameter name and override"""
    print(f"Connecting to database: {db_url}")

# Example 4: Multiple config keys (param_name not allowed)
@inject_config('llm.model', 'llm.temperature')
def setup_llm(model=None, temperature=None):
    """Multiple config values injected to matching parameter names"""
    print(f"Setting up LLM: {model} with temperature {temperature}")

# Example 5: Error case - param_name with multiple keys would raise ValueError
# @inject_config('api.host', 'api.port', param_name='server_config')  # This would fail!

if __name__ == "__main__":
    print("Examples of inject_config with param_name:")
    print("\n1. Standard usage:")
    # start_server_standard()  # Would inject from config
    
    print("\n2. Custom parameter name:")
    # start_server_custom()  # Would inject api.host to server_address
    
    print("\n3. Custom parameter with override:")
    # connect_to_db()  # Would use override value
    
    print("\n4. Multiple config keys:")
    # setup_llm()  # Would inject both model and temperature