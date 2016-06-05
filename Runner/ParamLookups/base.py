from Hardcoded import (get_board_parameters, get_box_parameters,
    get_mouse_parameters)

def get_specific_parameters_from_user_input(user_input):
    """Converts session parameters to specific parameters.
    
    """
    # Convert session parameters into specific parameters
    board_parameters = get_board_parameters(user_input['board'])
    box_parameters = get_box_parameters(user_input['box'])
    mouse_parameters = get_mouse_parameters(user_input['mouse'])    
    
    # Split into C, Python, and build parameters
    specific_parameters = {}
    for param_type in ['C', 'Python', 'build']:
        if param_type not in specific_parameters:
            specific_parameters[param_type] = {}
        
        specific_parameters[param_type].update(box_parameters[param_type])
        specific_parameters[param_type].update(board_parameters[param_type])
        specific_parameters[param_type].update(mouse_parameters[param_type])

    # Check the required ones are present
    for param_name in ['protocol_name', 'script_name', 'serial_port']:
        assert param_name in specific_parameters['build']
    
    # Copy some from 'build' to 'python'
    if 'serial_port' not in specific_parameters['Python']:
        specific_parameters['Python']['serial_port'] = specific_parameters[
            'build']['serial_port']
    if 'box' not in specific_parameters['Python']:
        specific_parameters['Python']['box'] = user_input['box']
    if 'mouse' not in specific_parameters['Python']:
        specific_parameters['Python']['mouse'] = user_input['mouse']
    
    return specific_parameters