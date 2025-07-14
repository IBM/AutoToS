import re

def parse_pddl_blocks_from_file(filename):
    # Read content from file
    with open(filename, 'r') as file:
        input_pddl = file.read()

    # Helper function to extract contents between markers
    def extract_section(content, start_marker, end_marker):
        start = content.find(start_marker) + len(start_marker)
        if end_marker is not None:
            end = content.find(end_marker, start)
            return content[start:end].strip()
        return content[start:].strip()
    # Helper function to parse the "init" or "goal" sections
    def parse_state(state_str):
        state = {
            "clear": [],
            "on-table": [],
            "arm-empty": False,
            "holding": None,
            "on": []
        }
        
        lines = state_str.splitlines()
        for line in lines:
            line = line.strip().strip('()')
            parts = line.split()
            
            if not parts:
                continue
            
            if parts[0] == 'clear':
                state["clear"].append(parts[1])
            elif parts[0] == 'ontable':
                state["on-table"].append(parts[1])
            elif parts[0] == 'handempty':
                state["arm-empty"] = True
            elif parts[0] == 'holding':
                state["holding"] = parts[1]
            elif parts[0] == 'on':
                state["on"].append((parts[1], parts[2]))
        
        return state

    # Extract the init and goal sections
    init_section = extract_section(input_pddl, "(:init", "(:goal")
    goal_section = extract_section(input_pddl, "(:goal", None)
    goal_section = goal_section[:-1].strip()
    # Remove the outer 'and' if present in the goal
    if goal_section.startswith('(and'):
        goal_section = goal_section[4:-1].strip()

    # print("-----------------------------")
    # print(init_section)
    # print("-----------------------------")
    # print(goal_section)
    # print("-----------------------------")
    # Parse the extracted sections
    init_state = parse_state(init_section)
    goal_state = parse_state(goal_section)

    del goal_state['arm-empty']
    del goal_state['holding']
    
    return init_state, goal_state

