import math
import pathlib
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.domain_base_class import DomainTestBase
from utils import unit_tests, search, experiment_utils
import csv
import logging
from itertools import permutations


class TwentyFourGame(DomainTestBase):


    def get_initial_successor_prompt(self):
        return """
The 24 Game is a mathematical card game in which the objective is to find a way to manipulate four integers so that the end result is 24. The game is played with a list of four numbers, and the player must use all four numbers exactly once, using any combination of addition, subtraction, multiplication, or division, to arrive at the number 24. If a state is defined by a list of numbers (4 or less), how are successor states defined? Please think step by step. Then, provide only the Python function that returns a list of successor states for an input state.

Here is an example of an initial state:
[6, 6, 2, 1]
"""

    def get_initial_goal_prompt(self):
        return """
Provide only the python code that tests whether a state is a goal state. 
Example goal state: [24]
Example non-goal state: [24,1]
"""

    def validate_transition_complex(self, s, t):
        if len(s) - len(t) != 1:
            feedback = search.pprint("Invalid transformation: length mismatch - the length of a successor must be one less than the parent.")
            feedback += search.pprint("Let's think step by step. First think through in words why the successor function produced a successor that had a length that was not exactly one less than the parent. Then provide the complete Python code for the revised successor function that ensures the length of a successor is exactly one less than the parent.") 
            feedback += search.pprint("Remember how you fixed the previous mistakes, if any. Keep the same function signature.")
            return False, feedback
        return True, ""

    def test_successor_soundness(self, llm_successor_states, llm_is_goal):
        with open(pathlib.Path(__file__).parent/'unittests.csv', mode='r') as file:
            csvFile = csv.reader(file)
            next(csvFile, None)  # skip the headers
            for lines in csvFile:
                state = [int(a) for a in lines[1].split(" ")]

                res, _, _, feedback = search.bfs(state, llm_successor_states, llm_is_goal, self._str, self.validate_transition)
                if res is None:
                    if len(feedback) > 0:
                        return feedback

                    # Goal was not found
                    # In all test cases the goal should exist, so we defer to completeness test
                    pass
                elif res[-1] == [24]:
                    assert(len(feedback) == 0)
                    continue
                    # valid, reason = self.validate_state_sequence(res)
                    # if not valid:
                    #     reason += search.pprint("Please fix the successor function")
                    #     return reason
                else:
                    # This case means that the llm_is_goal did not recognize the state res[-1] as non-goal (reported as goal)
                    assert(len(feedback) == 0)
                    feedback = search.pprint(f"The goal test function failed on the following input state {res[-1]}, incorrectly reporting it as a goal state.")
                    feedback += search.pprint("Please fix the goal test function.")
                    return feedback

        return feedback

    def test_successor_completeness(self, llm_successor_states):
        successors_examples = experiment_utils.load_from_jsonl(pathlib.Path(__file__).parent/'24game_successors.jsonl')
    
        instance_successor_dict = {tuple(state): successors for state, successors in successors_examples}
        
        # Define the function to get ground truth successors from the loaded data
        def get_ground_truth_successor_states(state):
            state_tuple = tuple(sorted(state))
            return instance_successor_dict.get(state_tuple, [])
        
        # Perform the completeness check for each state in the examples
        for state in instance_successor_dict.keys():
            res, feedback = unit_tests.completeness_check(list(state), get_ground_truth_successor_states, llm_successor_states, self._str)
            if not res:
                return feedback
        return ""

    def test_goal_soundness(self, llm_is_goal):
        # Load the examples from the JSONL files
        goal_states = experiment_utils.load_from_jsonl(pathlib.Path(__file__).parent/'24game_goals.jsonl')
        non_goal_states = experiment_utils.load_from_jsonl(pathlib.Path(__file__).parent/'24game_non_goals.jsonl')
        
        # Perform the soundness check
        return unit_tests.soundness_check(goal_states, non_goal_states, llm_is_goal)

    def model_test_split_eval(self, no_logging=False):
        success = 0
        failure = 0
        total_expansions = 0
        total_evaluations = 0
        with open(pathlib.Path(__file__).parent/'model_test.csv', mode='r') as file:
            csvFile = csv.reader(file)
            next(csvFile, None) 
            for lines in csvFile:
                state = [int(a) for a in lines[1].split(" ")]
                solvable = int(lines[6]) == 1
                res, expansions, evaluations, _ = search.bfs(state, self.llm_successor_states, self.llm_is_goal, self._str, None, perform_checks=False)
                total_expansions += expansions
                total_evaluations += evaluations
                if res is not None:
                    if res[-1] == [24] and solvable:
                        valid, reason = self.validate_solution(res)
                        if valid:
                            success += 1
                            if not no_logging:
                                logging.info(f"State {state} solved.")
                        else:
                            failure += 1
                            if not no_logging:
                                logging.info(f"State {state} solution invalid: {reason}, {res}")
                    else:
                        failure += 1
                        if not no_logging:
                            logging.info(f"State {state} solved incorrectly: {res}")
                else:
                    if solvable:
                        failure += 1
                        if not no_logging:
                            logging.info(f"State {state} not solved")
                    else:
                        success += 1
        if not no_logging:
            logging.info(f"Success: {success}, failure: {failure}, total expansions {total_expansions}, total generated {total_evaluations}")
        str = f"Success: {success}, failure: {failure}, total expansions {total_expansions}, total generated {total_evaluations}"
        return str

    def validate_transition_full(self, s, t):
        def ms(s):
            res = {}
            for x in s:
                if x not in res:
                    res[x] = 0
                res[x] += 1
            return res
        def ms_minus(s, t):
            res = {}
            for x, c in s.items():
                res[x] = max(c - t.get(x, 0), 0)
            return res
        def ms_to_list(s):
            res = []
            for x, c in s.items():
                for i in range(c):
                    res.append(x)
            return res

        if len(s) - len(t) != 1:
            return False, "Invalid transformation: length mismatch"
        
        mss = ms(s)
        mst = ms(t)
        f_nums = ms_to_list(ms_minus(mss, mst))
        t_nums = ms_to_list(ms_minus(mst, mss))
        if len(t_nums) == 0 and len(f_nums) == 1:
            x = f_nums[0]
            # Check if x op y = y 
            if math.isclose(x, 0, abs_tol = 0.001) or math.isclose(x, 1, abs_tol = 0.001):
                return True, None
            other = ms_to_list(ms_minus(mss, ms([x])))
            for y in other:
                if math.isclose(x, 2*y, abs_tol = 0.001) or math.isclose(x, y*y, abs_tol = 0.001):
                    return True, None
            return False, "No valid operation found to transform state"
        assert(len(f_nums) == 2)
        assert(len(t_nums) == 1)
        x, y = f_nums[0], f_nums[1]
        z = t_nums[0]
        if math.isclose(x+y, z, abs_tol = 0.001) or math.isclose(x-y, z, abs_tol = 0.001) or \
            math.isclose(y-x, z, abs_tol = 0.001) or math.isclose(x*y, z, abs_tol = 0.001) or \
                (y != 0 and math.isclose(x / y, z, abs_tol = 0.001)) or \
                (x != 0 and math.isclose(y / x, z, abs_tol = 0.001)):
            return True, None        
        return False, "No valid operation found to transform state"

    def validate_solution(self, plan):
        if not plan or plan[-1] != [24]:
            return False, "Final state is not [24]"
        
        for i in range(len(plan) - 1):
            s = plan[i]
            t = plan[i + 1]
            valid, reason = self.validate_transition_full(s, t)
            if not valid:
                reason += search.pprint("Input state", s)
                reason += search.pprint("Successor state", t)
                # reason += "First explain in words why the successor function produced this invalid transformation. Then fix the successor function."
                return False, reason
        
        return True, None
    