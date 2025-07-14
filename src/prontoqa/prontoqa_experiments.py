import pathlib
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.domain_base_class import DomainTestBase

import inflect
import json
from utils import search, unit_tests
import logging

class Prontoqa(DomainTestBase):

    def get_initial_successor_prompt(self):
        return """
Logical deduction is performed by applying rules of the form if X then Y to our current knowledge about a world, extending our knowledge with each single rule application. 
A rule if X then Y is applicable if we know X. If a state is defined as our current knowledge of the world, how are successor states defined, given a collection of rules? Please think step by step. Then, provide only the Python implementation for the successor function that receives a state and rules and returns a list of successor states.

Example initial state: {"integer"}
Example rules: [("integer", "real number"), ("integer", "float")]
"""

    def get_initial_goal_prompt(self):
        return """
Provide only the Python function for the goal test function that tests, given a target fact, whether a state is a goal state. 
"""

    def parse_input(self, test_or_eval_flag):
        def get_negation(pred):
            if "not" in pred:
                assert(pred.startswith("not "))
                return pred[4:], False
            return pred, True

        def parse_fact(target):
            arr = target.split(" is ")
            assert(len(arr) == 2)
            obj, pred = arr[0:2]
            positive_lit = True
            assert("not" not in obj)
            pred, positive_lit = get_negation(pred)

            if pred.startswith("a "):
                pred = pred[2:]
            if pred.startswith("an "):
                pred = pred[3:]
            return obj.lower(), pred.lower(), positive_lit

        def _to_singular(word):
            if word in plural_exceptions:
                return word
            ret = p.singular_noun(word)
            if ret == False:
                return word
            return ret

        def parse_rule(rule):
            if rule.startswith("Every "):
                cond, eff = rule[6:].split(" is ")[0:2]
                eff, positive_lit = get_negation(eff)
            elif rule.startswith("Each "):
                cond, eff = rule[5:].split(" is ")[0:2]
                eff, positive_lit = get_negation(eff)
            else:
                cond, eff = rule.split(" are ")[0:2]
                eff, positive_lit = get_negation(eff)
                cond = _to_singular(cond)
                eff = _to_singular(eff)

            if eff.startswith("a "):
                eff = eff[2:]        
            if eff.startswith("an "):
                eff = eff[3:]        
            return cond.lower(), eff.lower(), positive_lit

        def parse_question(data):
            sentences = data['question'].split(". ")
            rules = sentences[:-1]
            init = sentences[-1].replace(".", "")

            target = data['query'].replace("True or false: ", "").replace(".", "")
            init_obj, init_pred, init_lit = parse_fact(init)
            target_obj, target_pred, target_lit = parse_fact(target)
            rule_preds = set()
            for rule in rules:
                cond, eff, lit = parse_rule(rule)
                rule_preds.add(tuple((cond, str("" if lit else "not-") + eff)))
            assert(init_obj == target_obj)
            return init_obj, init_pred, target_pred, target_lit, rule_preds

        p = inflect.engine()
        plural_exceptions = {"carnivorous", "herbivorous"}

        if test_or_eval_flag:
            #then testing for llm successor soundness
            with open(pathlib.Path(__file__).parent/"unittests.json", 'r') as file:
                data = json.loads(file.read())['example_pool']
                for e in data:
                    yield parse_question(e), e["answer"] == 'True' 
        else:
            #then evaluation
            with open(pathlib.Path(__file__).parent/"example_pool.json", 'r') as file:
                data = json.loads(file.read())['example_pool']
                for e in data:
                    yield parse_question(e), e["answer"] == 'True'         

    
    def test_successor_soundness(self, successor_states, is_goal):
        for (init_obj, init_pred, target_pred, target_lit, rule_preds), answer in self.parse_input(test_or_eval_flag = True):
            def successors_func(state):
                return successor_states(state, rule_preds)
            
            def is_goal_t(state):
                return is_goal(state, target_pred)
            def is_goal_f(state):
                return is_goal(state, f"not-{target_pred}")

            state = set()
            state.add(init_pred)

            res, _, _, feedback = search.bfs(state, successors_func, is_goal_t, self._str, self.validate_transition)

            if res is None:
                if len(feedback) > 0:
                    feedback += search.pprint(f"Rules: {rule_preds}")
                    return feedback
                pass
        
        return feedback


    def test_successor_completeness(self, llm_successor_states):
        with open(pathlib.Path(__file__).parent/"prontoqa_successors.jsonl", "r") as f: 
            prontoqa_successors = [json.loads(line) for line in f]
            for d in prontoqa_successors:
                s = set(d["state"])
                rules = [tuple(s) for s in d["rules"]]
                succ = [set(s) for s in d["successors"]]
            
                def successor_states(state):
                    return succ

                def llm_successor_states_t(state):
                    return llm_successor_states(state, rules)
                
                res, feedback = unit_tests.completeness_check(s, successor_states, llm_successor_states_t, self._str)

                if not res:
                    feedback += search.pprint(f"Rules: {rules}")
                    return feedback
                
        return ""

    def test_goal_soundness(self, llm_goal_test):
        with open(pathlib.Path(__file__).parent/"prontoqa_goals.jsonl", "r") as f: 
            goals = [json.loads(line) for line in f]
            for line in goals:
                s = set(line["state"])
                g = line["goal"]
                def goal_check_f(state):
                    return llm_goal_test(state, g)
                
                feedback = unit_tests.soundness_check([s], [], goal_check_f)

                if len(feedback) > 0:
                    feedback += search.pprint(f"Goal: {g}")
                    return feedback
        with open(pathlib.Path(__file__).parent/"prontoqa_non_goals.jsonl", "r") as fn: 
            non_goals = [json.loads(line) for line in fn]
            for line in non_goals:
                s = set(line["state"])
                g = line["goal"]

                def goal_check_f(state):
                    return llm_goal_test(state, g)

                feedback = unit_tests.soundness_check([], [s], goal_check_f)

                if len(feedback) > 0:
                    feedback += search.pprint(f"Goal: {g}")
                    return feedback
                
        return ""

        
    def validate_transition_complex(self, s, t):
        if s == t:
            return True, ""
        elif len(t) - len(s) != 1:
            feedback = search.pprint("Invalid transition: length mismatch - the length of a successor must be one more than the parent.")
            feedback += search.pprint("Let's think step by step. First think through in words why the successor function produced a successor that had a length that was not exactly one more than the parent. Then provide the complete Python code for the revised successor function that ensures the length of a successor is exactly one more than the parent.") 
            feedback += search.pprint("Remember how you fixed the previous mistakes, if any. Keep the same function signature.")
            return False, feedback
        return True, ""
    
    def model_test_split_eval(self, no_logging=False):
        success = 0
        failure = 0
        total_expansions = 0
        total_evaluations = 0

        for (init_obj, init_pred, target_pred, target_lit, rule_preds), answer in self.parse_input(test_or_eval_flag = False):
            def successors_func(state):
                return self.llm_successor_states(state, rule_preds)
            def is_goal_t(state):
                return self.llm_is_goal(state, target_pred)
            def is_goal_f(state):
                return self.llm_is_goal(state, f"not-{target_pred}")

            state =set()
            state.add(init_pred)

            res, expansions, evaluations, _ = search.bfs(state, successors_func, is_goal_t, self._str, None, perform_checks=False)
            total_expansions += expansions
            total_evaluations += evaluations

            if res is not None:
                if answer == target_lit:
                    success += 1
                else:
                    failure += 1
            else:
                res_n, expansions, evaluations, _ = search.bfs(state, successors_func, is_goal_f, self._str, None, perform_checks=False)
                total_expansions += expansions
                total_evaluations += evaluations
                if res_n is not None:
                    if answer != target_lit:
                        success += 1
                    else:
                        failure += 1
                else:
                    failure += 1
        
        if not no_logging:
            logging.info(f"Success: {success}, failure: {failure}, total expansions {total_expansions}, total evaluations {total_evaluations}")    
        str = f"Success: {success}, failure: {failure}, total expansions {total_expansions}, total evaluations {total_evaluations}"
        return str
