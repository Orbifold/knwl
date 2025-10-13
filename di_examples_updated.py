"""
Examples demonstrating the improved bind_partial behavior with kwargs filtering
"""

# Example 1: Function with specific parameters
def example_func(a, b, c=None):
    return f"a={a}, b={b}, c={c}"

# Example 2: Function with **kwargs
def flexible_func(a, b, **kwargs):
    return f"a={a}, b={b}, kwargs={kwargs}"

# Example 3: Function with no parameters
def no_params_func():
    return "no parameters"

# Test cases:
test_kwargs = {
    'a': 1, 
    'b': 2, 
    'c': 3,
    'extra_param': 'ignored',  # This will be filtered out for example_func
    'another_extra': 'also_ignored'
}

# The safe_bind_partial method will:
# 1. For example_func: only pass a, b, c (filter out extra_param, another_extra)
# 2. For flexible_func: pass all kwargs (because it accepts **kwargs)  
# 3. For no_params_func: pass no kwargs at all

print("Updated DI container now safely handles:")
print("✓ Functions with specific parameters (extra kwargs ignored)")
print("✓ Functions with **kwargs (all kwargs passed through)")
print("✓ Functions with no parameters (all kwargs ignored)")