import pathlib
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.domain_base_class import DomainTestBase

from sokoban import parse_sokoban_maze
from utils import unit_tests, search
import json
import logging




class Sokoban(DomainTestBase):

    def get_initial_successor_prompt(self):
        return """
This domain models the classic Sokoban game, where the robot needs to move around and push stones to specific locations while adhering to the constraints defined by the walls in the maze. 
The maze is defined by a grid of values 0,1, and 2, where 2 means it is a goal location for a stone, 1 means the cell is blocked, and either 0 or 2 means that the cell can be occupied. A cell is clear if it can be occupied, but is not occupied by either the player or any stone.

The actions are:

move: This action moves the player in a specified direction. To perform this action, the target location must be clear and adjacent to player's location. Performing this action will result in the player being at the target location and no longer at the starting location, meaning the starting location is now clear, while the target location is now not clear.

push: This action allows the player to push a stone in a specified direction. To perform this action, the player's location, the stone location, and the target location must line up in the same direction, and the target location must be clear. Performing the action results in player being at the stone's initial location and the stone is at the target location. Further, the player's previous location is clear, while the target location is not clear.

Assume that states are defined by a dictionary with keys at-player and at-stone. 
Here is an example of a state
{'at-player': (4, 4), 'at-stone': [(2, 2), (3, 3)]}
Here is an example of the grid:
[[1, 1, 1, 1, 0, 0, 0, 0], [1, 0, 0, 1, 1, 0, 0, 0], [1, 0, 0, 0, 1, 1, 1, 1], [1, 0, 0, 0, 1, 0, 0, 1], [1, 1, 0, 0, 0, 0, 0, 1], [0, 1, 1, 1, 2, 2, 0, 1], [0, 0, 0, 1, 0, 1, 0, 1], [0, 0, 0, 1, 0, 0, 0, 1], [0, 0, 0, 1, 1, 1, 1, 1]]

Provide a Python implementation of successor states function, receiving a state and a grid and returning a list of immediate successor states.
"""

    def get_initial_goal_prompt(self):
        return """
Provide only the python code that tests whether a state is a goal state for a given goal configuration. Assume that the goal configuration is provided by the 2-dimensional array as before. The function should receive a state and the 2-dimensional array and return True if the state is a goal state and False otherwise.
"""

    def validate_transition_complex(self, s, t):
        # Check that the target state has all objects in different locations
        locations = set(t['at-stone'])
        if len(locations) < len(t['at-stone']):
            feedback = search.pprint("Invalid transition: multiple stones at the same location.")
            feedback += search.pprint("Let's think step by step. First think through in words why the successor function produced a successor that has two stones at the same location. Then provide the complete Python code for the revised successor function that ensures that in all successors all stones are at different locations.") 
            feedback += search.pprint("Remember how you fixed the previous mistakes, if any. Keep the same function signature.")
            return False, feedback
        if t['at-player'] in locations:
            feedback = search.pprint("Invalid transition: a stone and the player are at the same location.")
            feedback += search.pprint("Let's think step by step. First think through in words why the successor function produced a successor that has a stone and the player at the same location. Then provide the complete Python code for the revised successor function that ensures that in all successors the player and the stones are at different locations.") 
            feedback += search.pprint("Remember how you fixed the previous mistakes, if any. Keep the same function signature.")
            return False, feedback
        return True, ""

    def fix_state(self, state):
        if 'at-player' in state:
            state['at-player'] = tuple(state['at-player'])
        if 'at-stone' in state:
            state['at-stone'] = [tuple(pos) for pos in state['at-stone']]
        return state

    def extract_plan(self, res, grid):
        def direction(fx, fy, tx, ty):
            if fx > tx:
                return "dir-left"
            elif fx < tx:
                return "dir-right"
            elif fy > ty:
                return "dir-up"
            else:
                return "dir-down"

        plan = []
        cnt = 1
        stone_ids_by_flocation = {}
        for st in res[0]['at-stone']:
            stone_ids_by_flocation[st] = f"{cnt:02}"
            cnt += 1

        def get_stone_id_by_location(st):
            return stone_ids_by_flocation[st]

        def update_stone_id_by_location(id, fst, tst):
            assert(stone_ids_by_flocation[fst] == id)
            del stone_ids_by_flocation[fst]
            stone_ids_by_flocation[tst] = id

        for i in range(len(res)-1):
            s, t = res[i], res[i+1]
            # Getting an action for the transition
            fstones = set(s['at-stone'])
            tstones = set(t['at-stone'])
            new_stones = tstones - fstones

            fx, fy = s['at-player'] 
            tx, ty = t['at-player']
            dir = direction(fx,fy, tx, ty)

            assert(len(new_stones) <= 1)
            if len(new_stones) == 0:
                # move action
                plan.append(f"(move player-01 pos-{fx+1:02}-{fy+1:02} pos-{tx+1:02}-{ty+1:02} {dir})")
            else:
                # push action
                sx, sy = list(new_stones)[0]
                is_goal = "goal" if grid[sx][sy] == 2 else "nongoal"
                old_stone = list(fstones - tstones)[0]
                stoneid = get_stone_id_by_location(old_stone)
                update_stone_id_by_location(stoneid, old_stone, (sx, sy))
                plan.append(f"(push-to-{is_goal} player-01 stone-{stoneid} pos-{fx+1:02}-{fy+1:02} pos-{tx+1:02}-{ty+1:02} pos-{sx+1:02}-{sy+1:02} {dir})")

        return plan

    def test_successor_soundness(self, llm_successor_states, is_goal, transform_state=None):
        folder = os.path.join(os.path.dirname(__file__), "unittests_instances")
        
        for file in os.listdir(folder):
            if file.endswith(".pddl"):
                file_path = os.path.join(folder, file)
                init, grid = parse_sokoban_maze.parse_pddl_sokoban_from_file(file_path)
                
                def is_goal_f(state):
                    return is_goal(state, grid)
                
                def successor_states_f(state):
                    return llm_successor_states(state, grid)

                res, _, _, feedback = search.bfs(init, successor_states_f, is_goal_f, self._str, self.validate_transition)

                if res is None:
                    if len(feedback) > 0:
                        feedback = search.pprint(f"Error occurred for grid configuration: {grid}") + feedback
                        return feedback

                    # Goal was not found
                    # In all test cases the goal should exist, so we defer to completeness test
                    pass            
        return feedback

    def test_successor_completeness(self, llm_successor_states):
        with open(pathlib.Path(__file__).parent/"sokoban_successors.jsonl", "r") as f:
            sokoban_successors = [json.loads(line) for line in f]
            for d in sokoban_successors:
                s = self.fix_state(d["state"])
                g = self.fix_state(d["grid"])
                succ = [self.fix_state(s) for s in d["successors"]]

                def ground_truth_successor_states(state):
                    return succ
                
                def llm_successor_states_t(state):
                    return llm_successor_states(state, g)

                res, feedback = unit_tests.completeness_check(s, ground_truth_successor_states, llm_successor_states_t, self._str)
                
                if not res:
                    feedback = search.pprint(f"Error occurred for grid configuration: {g}") + feedback
                    return feedback
                
        return ""

    def test_goal_soundness(self, llm_goal_test):
        with open(pathlib.Path(__file__).parent/"sokoban_goals.jsonl", "r") as f:
            goals = [json.loads(line) for line in f]
            for line in goals:
                s = self.fix_state(line["state"])
                g = self.fix_state(line["grid"])

                def goal_check_f(state):
                    return llm_goal_test(state, g)

                feedback = unit_tests.soundness_check([s], [], goal_check_f)

                if len(feedback) > 0:
                    feedback = search.pprint(f"Error occurred for grid configuration: {g}") + feedback
                    return feedback
        
        with open(pathlib.Path(__file__).parent/"sokoban_non_goals.jsonl", "r") as fn:
            non_goals = [json.loads(line) for line in fn]
            for line in non_goals:
                s = self.fix_state(line["state"])
                g = self.fix_state(line["grid"])

                def goal_check_f(state):
                    return llm_goal_test(state, g)

                feedback = unit_tests.soundness_check([], [s], goal_check_f)

                if len(feedback) > 0:
                    feedback = search.pprint(f"Error occurred for grid configuration: {g}") + feedback
                    return feedback
        
        return ""

    def model_test_split_eval(self, no_logging=False):
        success = 0
        failure = 0
        total_expansions = 0
        total_evaluations = 0
        folder = os.path.join(os.path.dirname(__file__), "test_instances")
        costs = json.load(open(pathlib.Path(__file__).parent/"sokoban_optimal_costs.json"))
        for file in os.listdir(folder):
            if file.endswith(".pddl"):
                file_path = os.path.join(folder, file)
                init, grid = parse_sokoban_maze.parse_pddl_sokoban_from_file(file_path)
                cost = costs[file]
                def is_goal_f(state):
                    return self.llm_is_goal(state, grid)
                
                def successor_states_f(state):
                    return self.llm_successor_states(state, grid)

                res, expansions, evaluations, _ = search.bfs(init, successor_states_f, is_goal_f, self._str, None, perform_checks=False)

                total_expansions += expansions
                total_evaluations += evaluations
                if res is None:
                    failure += 1
                    if not no_logging:
                        logging.info(f"File: {file}: Failed to find a goal state")
                else:
                    if cost == len(res) - 1:
                        success += 1
                    else:
                        if not no_logging:
                            logging.info(f"File: {file}: Found solution of length {len(res) - 1}, optimal: {cost}")
                            logging.info(f"Grid {grid}")
                            logging.info(res)
                        failure += 1

            # print(f"Success: {res is not None}, failure: {res is None}, expansions {expansions}, generated {evaluations}")
        if not no_logging:
            logging.info(f"Total success: {success}, failure: {failure}, total expansions {total_expansions}, total generated {total_evaluations}")    
        str = f"Success: {success}, failure: {failure}, total expansions {total_expansions}, total generated {total_evaluations}"
        return str
    