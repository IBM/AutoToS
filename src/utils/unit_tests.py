from .search import pprint
import traceback
import logging


def completeness_check(state, ground_truth_successor_states, llm_successor_states, state_representation):
    ground_truth_successors = ground_truth_successor_states(state)
    try:
        llm_successors = llm_successor_states(state)
    except KeyboardInterrupt:
        feedback = pprint("Successor function execution took too long.")
        feedback += pprint("Please provide a different implementation of the successor function.")
        feedback += pprint("Keep the same function signature.")
        return False, feedback

    set_of_true = set(map(state_representation, ground_truth_successors))
    set_of_llm = set(map(state_representation, llm_successors))
    #print(set_of_llm)
    set_diff = set_of_true - set_of_llm
    #print(set_diff)
    set_diff_successors = [s for s in ground_truth_successors if state_representation(s) in set_diff]
    if len(set_of_true-set_of_llm) > 0:
        feedback = ""
        feedback += pprint(f"Successor function when run on the state {state} failed to produce all successors.")
        feedback += pprint(f"Missing successors are: {set_diff_successors}")
        logging.info(f"Generated successors are {llm_successors} with state representation {set_of_llm}")
        feedback += pprint(f"First think step by step why the successor function failed to produce all successors of the state.")
        feedback += pprint("Then, fix the successor function.")
        feedback += pprint("Remember how you fixed the previous mistakes, if any. Keep the same function signature.")
        return False, feedback
    return True, ""


def soundness_check(goal_states, non_goal_states, is_goal):
    global current_state
    for state in goal_states:
        current_state = state

        try: 
            if not is_goal(state):
                feedback = pprint(f"The goal test function failed on the following input state {state}, incorrectly reporting it as a non-goal state.")
                feedback += pprint(f"First think step by step what it means for a state to be a goal state in this domain. Then think through in words why the goal test function incorrectly reported input state: {state} as a non-goal state. Now, revise the goal test function and ensure it returns true for the input state.")
                feedback += pprint("Remember how you fixed the previous mistakes, if any. Keep the same function signature.")
                return feedback 
        except KeyboardInterrupt:
            feedback = pprint("Goal test function execution took too long.")
            feedback += pprint("Please provide a different implementation of the goal test function.")
            feedback += pprint("Keep the same function signature.")
            return feedback                
        except Exception as e:
            last_traceback = traceback.extract_tb(e.__traceback__)[-1:]
            relevant_trace = traceback.format_list(last_traceback) + [str(e)]
            trace = '\n'.join(relevant_trace)
            feedback = pprint(f"The goal test function failed to execute on the following input state {state}.")
            feedback += pprint(f"The follow exception occurred: {trace}.")
            feedback += pprint("Please rewrite the goal function entirely.")
            feedback += pprint("Remember how you fixed the previous mistakes, if any. Keep the same function signature.")
            return feedback

    for state in non_goal_states:
        current_state = state
        try:
            if is_goal(state):
                feedback = pprint(f"The goal test function failed on the following input state {state}, incorrectly reporting it as a goal state.")
                feedback += pprint(f"First think step by step what it means for a state to be a goal state in this domain. Then think through in words why the goal test function incorrectly reported input state: {state} as a goal state. Now, revise the goal test function and ensure it returns false for the input state.")
                feedback += pprint("Remember how you fixed the previous mistakes, if any. Keep the same function signature.")
                return feedback 
        except KeyboardInterrupt:
            feedback = pprint("Goal test function execution took too long.")
            feedback += pprint("Please provide a different implementation of the goal test function.")
            feedback += pprint("Keep the same function signature.")
            return feedback    
        except Exception as e:
            last_traceback = traceback.extract_tb(e.__traceback__)[-1:]
            relevant_trace = traceback.format_list(last_traceback) + [str(e)]
            trace = '\n'.join(relevant_trace)
            feedback = pprint(f"The goal test function failed to execute on the following input state {state}.")
            feedback += pprint(f"The follow exception occurred: {trace}.")
            feedback += pprint("Please rewrite the goal function entirely.")
            feedback += pprint("Keep the same function signature.")
            return feedback
    return ""