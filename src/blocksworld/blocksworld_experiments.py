import pathlib
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.domain_base_class import DomainTestBase

from utils import unit_tests, search, experiment_utils
import csv
import logging
from blocksworld import parse_problem_blocks
import json
import tempfile
from subprocess import PIPE, Popen


if sys.version_info.major < 3:
    print("Require Python 3.6 or above")
    sys.exit()
val_kwargs = {"stdout": PIPE,
            "stderr": PIPE}
if sys.version_info.minor >= 7:
    val_kwargs['text']=True
else:
    val_kwargs['universal_newlines']=True


def val(pddl_domain, pddl_problem, plan):
    with tempfile.NamedTemporaryFile() as plan_temp:
        
        open(str(plan_temp.name), 'w', encoding='utf8').write("\n".join(plan))

        process = Popen(["validate", "-vvv", pddl_domain, pddl_problem, str(plan_temp.name)], **val_kwargs)
        stdout, stderr = process.communicate()
        if process.wait() != 0 or len(str(stderr))>0:
            # print("ERROR")
            # print(stderr)
            return False
        else:
            if 'Plan valid' in stdout:
                # print("SUCCESS")
                # print(stdout)
                return True
        # print(stdout)
        return False

def extract_action(s, t):
    """
    s = {'clear': ['a', 'b', 'd'], 'on-table': ['a', 'c', 'd'], 'arm-empty': True, 'holding': None, 'on': [('b', 'c')]}, 
    t = {'clear': ['a', 'd', 'c'], 'on-table': ['a', 'c', 'd'], 'arm-empty': False, 'holding': 'b', 'on': []}, 
    """
    b = t["holding"]
    if b is not None:    
        # pick-up or unstack
        if len(s["on"]) == len(t["on"]) and len(s["on-table"]) == len(t["on-table"]) + 1:
            # pick-up
            return f"(pick-up {b})"
        elif len(s["on"]) == len(t["on"]) + 1 and len(s["on-table"]) == len(t["on-table"]):
            # unstack
            on = [x for x in s["on"] if x not in t["on"]]
            assert(len(on) ==1)
            if on[0][0] == b:
                return f"(unstack {b} {on[0][1]})"
        return None
    b = s["holding"]
    # put-down or stack
    if len(s["on"]) == len(t["on"]) and len(s["on-table"]) == len(t["on-table"]) - 1:
        # put-down
        return f"(put-down {b})"
    elif len(s["on"]) == len(t["on"]) - 1 and len(s["on-table"]) == len(t["on-table"]):
        # stack
        on = [x for x in t["on"] if x not in s["on"]]
        assert(len(on) ==1)
        if on[0][0] == b:
            return f"(stack {b} {on[0][1]})"
    return None

def extract_plan(res):
    return [extract_action(res[i], res[i+1]) for i in range(len(res)-1)]



class Blocksworld(DomainTestBase):
    def get_initial_successor_prompt(self):
        return """
I am playing with a set of blocks where I need to arrange the blocks into stacks. Here are the actions I can do
   Pick up a block from the table
   Put down a block on the table
   Unstack a block from on top of another block
   Stack a block on top of another block

   I have the following restrictions on my actions:
   I can only pick up or unstack one block at a time.
   I can only pick up or unstack a block if my hand is empty.
   I can only pick up a block if the block is on the table and the block is clear. A block is clear if the block has no other blocks on top of it and if the block is not picked up.
   I can only unstack a block from on top of another block if the block I am unstacking was really on top of the other block.
   I can only unstack a block from on top of another block if the block I am unstacking is clear.
   Once I pick up a block, I am holding the block and it is no longer clear and no longer on the table. 
   Once I unstack from on top of another block, I am holding the block and it is no longer clear. Instead, the other block becomes clear.   

   I can only put down a block that I am holding.
   I can only stack a block on top of another block if I am holding the block being stacked.
   I can only stack a block on top of another block if the block onto which I am stacking the block is clear.
   Once I put down a block, my hand becomes empty, the block becomes clear, and it is now on the table.
   Once I stack a block on top of another block, the block on top becomes clear and the block under it is no longer clear.
If a state is defined by a dictionary of following predicates "clear block", "on-table block", "arm-empty", "holding block", and "on block1 block2", how are successor states defined? 
Here is an example of the initial state:
Init: {'clear': ['b'], 'on-table': ['d'], 'arm-empty': True, 'holding': None, 'on': [('a', 'c'), ('b', 'a'), ('c', 'd')]}
Please provide only the Python code for the successor function that returns a list of successor states.
"""

    def get_initial_goal_prompt(self):
        return """
Provide only the python code that tests whether a state is a goal state. The goal specifies a partial state, the facts that must be true in any full goal state. Assume that the goal configuration is provided in the same dictionary format. 
Here's an example goal specification:
Goal: {'clear': [], 'on-table': [], 'on': [('b', 'c'), ('d', 'b')]}
"""

    def fix_state(self, state):
        state["on"] = [tuple(x) for x in state["on"]]
        return state
    

    def validate_transition_complex(self, parent, state):
        """
        Verifies the correctness of a state.
        - state: a dictionary representing the state.
        - blocks: a set of all block identifiers.
        Returns True if the state is valid, False otherwise.
        """
        # seen_blocks = set()
        arm_empty = state['arm-empty']
        holding_block = state['holding']

        #there can only one block on top of another, x on y then not x on z and not z on y if so.

        # \# in clear should the same as the \# on the table ie holding block then this block should not be clear
        feedback = ""
        if holding_block:
            if arm_empty:
                feedback += search.pprint("If holding a block then the arm cannot be empty")
                return False, feedback
            # seen_blocks.add(holding_block)
        elif not arm_empty:
            feedback += search.pprint("If not holding a block then the arm must be empty.")
            return False, feedback

        if len(state.get('clear')) != len(state.get('on-table')):
            feedback += search.pprint("Each tower has the bottom block on the table and the top block clear.")
            feedback += search.pprint("Therefore, the number of clear blocks should be the same as the number of blocks on the table.")
            feedback += search.pprint("The number of elements in the clear list is not the same as the number of elements in the on-table list.")
            feedback += search.pprint("Reminder: Once I pick up a block, I am holding the block and it is no longer clear and no longer on the table.")
            feedback += search.pprint("Once I unstack from on top of another block, I am holding the block and it is no longer clear. Instead, the other block becomes clear.")
            feedback += search.pprint("Once I put down a block, my hand becomes empty, the block becomes clear, and it is now on the table.")
            feedback += search.pprint("Once I stack a block on top of another block, the block on top becomes clear and the block under it is no longer clear.")

            feedback += search.pprint("Let's think step by step. First, think of how applying each action changes which blocks are clear.")
            feedback += search.pprint("Then, think of how applying each action changes which blocks are on the table.")
            feedback += search.pprint("Then, provide the complete Python code for the revised successor function that returns a list of successor states.") 
            feedback += search.pprint("Remember how you fixed the previous mistakes, if any. Keep the same function signature.")
            return False, feedback

        # Ensure all blocks are accounted for

        return True, ""

    def test_successor_soundness(self, llm_successor_states, llm_is_goal):
        with open(pathlib.Path(__file__).parent/'unittests.csv', mode='r') as file:
            csvFile = csv.reader(file)
            for lines in csvFile:
                fname = lines[0]
                cost = int(lines[1])

                init, goal = parse_problem_blocks.parse_pddl_blocks_from_file(pathlib.Path(__file__).parent/fname)
                                    
                def is_goal_f(state):
                    return llm_is_goal(state, goal)

                res, _, _, feedback = search.bfs(init, llm_successor_states, is_goal_f, self._str, self.validate_transition)

                if res is None:
                    if len(feedback) > 0:
                        return feedback

                    # Goal was not found
                    # In all test cases the goal should exist, so we defer to completeness test
                    pass
        return feedback



    def model_test_split_eval(self, no_logging=False):
        success = 0
        failure = 0
        total_expansions = 0
        total_evaluations = 0
        cnt = 0
        with open(pathlib.Path(__file__).parent/'solutions.csv', mode='r') as file:
            csvFile = csv.reader(file)
            for lines in csvFile:
                fname = lines[0]
                cost = int(lines[1])

                init, goal = parse_problem_blocks.parse_pddl_blocks_from_file(pathlib.Path(__file__).parent/fname)
                                    
                def is_goal_f(state):
                    return self.llm_is_goal(state, goal)

                res, expansions, evaluations, _ = search.bfs(init, self.llm_successor_states, is_goal_f, self._str, verify_successor=None, perform_checks=False, timeout=2)
                cnt +=1
                total_expansions += expansions
                total_evaluations += evaluations

                if res == None:
                    failure += 1
                    continue
                plan = extract_plan(res)
                if None in plan:
                    failure += 1
                    continue
                if not val(pathlib.Path(__file__).parent/"domain.pddl", pathlib.Path(__file__).parent/fname, plan):
                    if not no_logging:
                        logging.info(f"Failed to validate the plan for problem {fname}")
                        logging.info(plan)
                    failure += 1
                    continue

                if cost == (len(res) - 1):
                    success += 1
                else:
                    if not no_logging:
                        logging.info(f"Plan not optimal: {len(res) - 1}, optimal cost: {cost}")
                        logging.info(plan)
                    failure += 1
        if not no_logging:
            logging.info(f"Success: {success}, failure: {failure}, total expansions {total_expansions}, total generated {total_evaluations}")
        str = f"Success: {success}, failure: {failure}, total expansions {total_expansions}, total generated {total_evaluations}"
        return str

    def test_successor_completeness(self, llm_successor_states):
        successors_examples = experiment_utils.load_from_jsonl_nonlist(pathlib.Path(__file__).parent/'blocks_successors.jsonl')
        
        for d in successors_examples:
            s = d["state"]
            succ = [self.fix_state(state) for state in d["successors"]]

            def successor_states_f(state):
                return succ

            s = self.fix_state(s)

            res, feedback = unit_tests.completeness_check(s, successor_states_f, llm_successor_states, self._str)
            if not res:
                return feedback
        return ""
    
    def test_goal_soundness(self, llm_goal_test):
        with open(pathlib.Path(__file__).parent/"blocks_goals.jsonl", "r") as f: 
            goals = json.loads(f.read())
            for line in goals:
                s = line["state"]
                g = line["goal"]

                s = self.fix_state(s)
                g = self.fix_state(g)
                
                def goal_check_f(state):
                    return llm_goal_test(state, g)
                
                feedback = unit_tests.soundness_check([s], [], goal_check_f)
                if len(feedback) > 0:
                    feedback += search.pprint(f"Goal: {g}")
                    return feedback
                
        with open(pathlib.Path(__file__).parent/"blocks_non_goals.jsonl", "r") as fn: 
            non_goals = json.loads(fn.read())

            for line in non_goals:
                s = line["state"]
                g = line["goal"]
                s = self.fix_state(s)
                g = self.fix_state(g)

                def goal_check_f(state):
                    return llm_goal_test(state, g)

                feedback = unit_tests.soundness_check([], [s], goal_check_f)
                if len(feedback) > 0:
                    feedback += search.pprint(f"Goal: {g}")
                    return feedback
        
        return ""

