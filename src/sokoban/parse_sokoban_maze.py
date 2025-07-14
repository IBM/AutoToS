import re

def parse_pddl_sokoban_from_file(filename):
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
    
    # Extract the init and goal sections
    init_section = extract_section(input_pddl, "(:init", "(:goal")
    goal_section = extract_section(input_pddl, "(:goal", None)
    goal_section = goal_section[:-1].strip()
    
    # Remove the outer 'and' if present in the goal
    if goal_section.startswith('(and'):
        goal_section = goal_section[4:-1].strip()

    # Extract grid positions and determine dimensions
    pos_pattern = r'pos-(\d+)-(\d+)'
    positions = re.findall(pos_pattern, input_pddl)
    max_row = max(int(pos[0]) for pos in positions)
    max_col = max(int(pos[1]) for pos in positions)
    
    # Initialize the 2D array with 0 (free cells)
    grid = [[0 for _ in range(max_col)] for _ in range(max_row)]

    # Extract goal locations
    goal_pattern = r'\(IS-GOAL pos-(\d+)-(\d+)\)'
    goals = re.findall(goal_pattern, input_pddl)
    for goal in goals:
        x, y = int(goal[0])-1, int(goal[1])-1
        grid[x][y] = 2

    # Extract clear positions
    clear_pattern = r'\(clear pos-(\d+)-(\d+)\)'
    clears = re.findall(clear_pattern, input_pddl)
    clear_positions = set((int(clear[0])-1, int(clear[1])-1) for clear in clears)

    at_pattern = r'\(at (.*) pos-(\d+)-(\d+)\)'
    ats = re.findall(at_pattern, input_pddl)
    
    clear_positions |= set((int(a[1])-1, int(a[2])-1) for a in ats)

    init_dict = {}
    for a, b, c in ats:
        if 'player' in a:
            init_dict['at-player'] = (int(b)-1, int(c)-1)
        else:
            if 'at-stone' not in init_dict:
                init_dict['at-stone'] = []
            init_dict['at-stone'].append((int(b)-1, int(c)-1))

    # Determine blocked positions
    all_positions = set((x, y) for x in range(max_row) for y in range(max_col))
    goal_positions = set((int(goal[0])-1, int(goal[1])-1) for goal in goals)
    blocked_positions = all_positions - clear_positions - goal_positions
    for blocked in blocked_positions:
        x, y = blocked
        grid[x][y] = 1

    return init_dict, grid
