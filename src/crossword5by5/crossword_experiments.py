import pathlib
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.domain_base_class import DomainTestBase

from utils import unit_tests, search

import csv 
import json
import logging

class Crossword(DomainTestBase):

    def get_initial_successor_prompt(self):
        return """
The task is a 5x5 mini crosswords. A state is a 2D array representing the current puzzle state, where the initial grid is all "None". Note that some of the possible answers are not exactly 5 character long. Given an input of possible answers to horizontal clues and vertical clues, how is the successor state function defined? Please first think step by step. Then provide the successor state function in Python code. 

The possible clues for each row and each column are given separately. Here is an example of possible horizontal and vertical clues:

horizontal_answers = [
        ["tasks", "goals", "plans", "agend", "chores", "works", "deeds", "items", "lists", "brief"],
        ["motor", "power", "drive", "diesel", "steam", "pumps", "crank", "gears", "turbn", "motor"],
        ["grand", "artsy", "showy", "ornate", "fancy", "vain", "proud", "vogue", "swank", "luxus"], 
        ["venue", "salle", "forum", "atria", "lobby", "parls", "court", "malls", "mall", "lobby"], 
        ["jeer", "scoff", "sleer", "deris", "sneer", "scorn", "derid", "gibes", "gibed", "flout"] 
]
vertical_answers = [
        ["amass", "stack", "hoard", "pile", "store", "heaps", "massy", "gathe", "lumps", "mound"],
        ["nilga", "goral", "eland", "lepus", "gazal", "kudu", "oryx", "gnu", "imps", "carb"],
        ["scheme", "design", "ettle", "nettle", "sting", "wiles", "plans", "ideas", "plots", "cocks"], 
        ["spout", "nosle", "snout", "mouth", "nostr", "ports", "inlet", "vents", "outlt", "beaks"], 
        ["drier", "arid", "sere", "parch", "dryer", "wring", "drear", "sear", "pall", "lack"]
]

where horizontal_answers is a list where element i is a list of possible answers to clue in row i, and vertical_answers is a list where element i is a list of possible answers to clue in column i.
"""

    def get_initial_goal_prompt(self):
        return """
Please provide a goal test function in Python ensuring that all cells are not None, all words horizontally are matching at least one of the horizontal answers, and all words vertically match at least one of the vertical answers. The function should receive a state, horizontal_answers, and vertical_answers as before and return True for a goal state and False otherwise.
"""

    def _str(self, state):
        return " ".join(list([str(s) for s in state]))

    def reconstruct_plan(self, s, Closed):
        plan = []
        current = s
        while current is not None:
            plan.append(current)
            c = str(current)
            current = Closed[c]
        return plan[::-1]
    
    def validate_transition_complex(self, s, t):
        def count_none(s):
            ns = 0 
            for r in s:
                ns += len([c for c in r if c is None])
            return ns

        ns = count_none(s)
        nt = count_none(t)

        feedback = ""
        if ns < nt:
            # More unknown
            feedback += search.pprint("Successor state has less filled cells than the parent state.")
        elif ns == nt:
            # Same unknown
            feedback += search.pprint("Successor state has the same number of filled cells as the parent state.")
        elif ns - nt > 5:
            # Way too many less unknown
            feedback += search.pprint("Successor state has more than 5 filled cells more than the parent state.")
        else:
            return True, ""

        feedback += search.pprint("Let's think step by step. First, think what you did wrong.")
        feedback += search.pprint("Then, think of in what ways successor state should be different from the parent state.")
        feedback += search.pprint("Then, provide the complete Python code for the revised successor function that returns a list of successor states.") 
        feedback += search.pprint("Remember how you fixed the previous mistakes, if any. Keep the same function signature.")
        return False, feedback

    
    def test_successor_soundness(self, successor_states, is_goal):
        with open(pathlib.Path(__file__).parent/'unittests.csv', mode ='r')as file:
            csvFile = csv.reader(file)
            next(csvFile, None)  # skip the headers
            for lines in csvFile:
                state = [[None]*5 for _ in range(5)]
                horizontal_answers = json.loads(lines[0])
                vertical_answers = json.loads(lines[1])

                def is_goal_f(state):
                    return is_goal(state, horizontal_answers, vertical_answers)
                
                def successor_states_f(state):
                    return successor_states(state, horizontal_answers, vertical_answers)
                
                res, _, _, feedback = search.dfs(state, successor_states_f, is_goal_f, self._str, self.validate_transition)

                if res is None:
                    if len(feedback) > 0:
                        feedback += search.pprint(f"Horizontal clues: {horizontal_answers}")
                        feedback += search.pprint(f"Vertical clues: {vertical_answers}")
                        return feedback
                    pass
        return feedback

    def model_test_split_eval(self, no_logging=False):
        success = 0
        failure = 0
        total_expansions = 0
        total_evaluations = 0
        with open(pathlib.Path(__file__).parent/'crossworld.csv', mode ='r')as file:
            csvFile = csv.reader(file)
            next(csvFile, None)  # skip the headers
            for lines in csvFile:
                state = [[None]*5 for _ in range(5)]
                horizontal_answers = json.loads(lines[0])
                vertical_answers = json.loads(lines[1])

                def is_goal_f(state):
                    return self.llm_is_goal(state, horizontal_answers, vertical_answers)
                
                def successor_states_f(state):
                    return self.llm_successor_states(state, horizontal_answers, vertical_answers)
                
                res, expansions, evaluations, _ = search.dfs(state, successor_states_f, is_goal_f, self._str, None, perform_checks=False)
                total_expansions += expansions
                total_evaluations += evaluations
                if res == None:
                    failure += 1
                else:
                    success += 1

        if not no_logging:
            logging.info(f"Success: {success}, failure: {failure}, total expansions {total_expansions}, total generated {total_evaluations}")
        str = f"Success: {success}, failure: {failure}, total expansions {total_expansions}, total generated {total_evaluations}"
        return str

    def test_successor_completeness(self, llm_successor_func):
        with open(pathlib.Path(__file__).parent/'crosswords_successors.jsonl', mode='r') as file:
            for data in json.loads(file.read()):
                state = data["state"]
                successors = data["successors"]
                horizontal_answers = data['horizontal_clues']
                vertical_answers = data['vertical_clues']

                def ground_truth_successor_t(state):
                    return successors
                
                def llm_successor_t(state):
                    return llm_successor_func(state, horizontal_answers, vertical_answers)
                
                res, feedback = unit_tests.completeness_check(state, ground_truth_successor_t, llm_successor_t, self._str)

                if not res:
                    feedback += search.pprint(f"Horizontal clues: {horizontal_answers}")
                    feedback += search.pprint(f"Vertical clues: {vertical_answers}")

                    return feedback
                
        return ""
    
    def test_goal_soundness(self, is_goal_func):
        # Load goal states
        with open(pathlib.Path(__file__).parent/'crosswords_goal.jsonl', 'r') as f:
            for data in json.loads(f.read()):
                state = data["state"]
                horizontal_answers = data['horizontal_clues']
                vertical_answers = data['vertical_clues']
                def llms_is_goal(state):
                    return is_goal_func(state, horizontal_answers, vertical_answers)
                feedback = unit_tests.soundness_check([state], [], llms_is_goal)

                if len(feedback) > 0:
                    feedback += search.pprint(f"Horizontal clues: {horizontal_answers}")
                    feedback += search.pprint(f"Vertical clues: {vertical_answers}")
                    return feedback

        # Load non-goal states
        with open(pathlib.Path(__file__).parent/'crosswords_nongoal.jsonl', 'r') as f:
            for data in json.loads(f.read()):
                state = data["state"]
                horizontal_answers = data['horizontal_clues']
                vertical_answers = data['vertical_clues']
                def llms_is_goal(state):
                    return is_goal_func(state, horizontal_answers, vertical_answers)
                feedback = unit_tests.soundness_check([], [state], llms_is_goal)

                if len(feedback) > 0:
                    feedback += search.pprint(f"Horizontal clues: {horizontal_answers}")
                    feedback += search.pprint(f"Vertical clues: {vertical_answers}")
                    return feedback
        
        return ""
    
