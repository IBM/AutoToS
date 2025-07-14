import copy
import io
import time

def pprint(*args, **kwargs):
    output = io.StringIO()
    print(*args, file=output, **kwargs)
    contents = output.getvalue()
    output.close()
    return contents

def reconstruct_plan(s, Closed, state_representation):
    plan = []
    current = s
    while current is not None:
        plan.append(current)
        c = state_representation(current)
        current = Closed[c]
    return plan[::-1]

def bfs(state, successor_states, is_goal, state_representation, verify_successor, perform_checks = True, timeout=600):
    start_time = time.time()
    expansions = 0
    evaluations = 0
    s = state
    error_detected = False
    Q = [tuple((s, None))]
    Closed = dict()
    feedback = ""
    while len(Q) > 0:
        if timeout and time.time() - start_time > timeout:
            feedback += pprint("Timeout occurred during search with the successor function.")
            feedback += pprint("Please provide a different implementation of the successor function.")
            feedback += pprint("Keep the same function signature.")
            break 

        s, parent = Q[0][0], Q[0][1]
        # logging.info("=====================> Expanding", s)
        del Q[0]
        c = state_representation(s)
        if c in Closed:
            continue
        Closed[c] = parent
        try:
            _is_goal = is_goal(s)
        except KeyboardInterrupt:
            feedback += pprint("Goal test function execution took too long.")
            feedback += pprint("Please provide a different implementation of the goal test function.")
            feedback += pprint("Keep the same function signature.")
            break
        if _is_goal:
            plan = reconstruct_plan(s, Closed, state_representation)
            return plan, expansions, evaluations, feedback
        expansions += 1

        if perform_checks:
            before_succ_run = copy.deepcopy(s)
        try:
            successors = successor_states(s)
        except KeyboardInterrupt:
            feedback += pprint("Successor function execution took too long.")
            feedback += pprint("Please provide a different implementation of the successor function.")
            feedback += pprint("Keep the same function signature.")
            break 

        if perform_checks and state_representation(s) != state_representation(before_succ_run):
            #print("Input state changed as a result of applying the successor function.")
            feedback += pprint("Input state should not change as a result of applying the successor function.")
            feedback += pprint("State before successor function applied:", before_succ_run)
            feedback += pprint("State after successor function applied:", s)
            feedback += pprint("Let's think step by step. First, think of the possible reasons why the input state may change as a result of applying the successor function, such as the use of shallow copy.")
            feedback += pprint("Then, provide the complete Python code for the revised successor function that returns a list of successor states and ensure it does not change the input state.") 
            feedback += pprint("Remember how you fixed the previous mistakes, if any. Keep the same function signature.")
            break 

        for t in successors:
            if perform_checks:
                res, succ_feedback = verify_successor(s, t)
                if not res:
                    feedback += pprint(succ_feedback)
                    feedback += pprint("Input state:", s)
                    feedback += pprint("Example wrong successor state:", t)
                    error_detected = True
                    break
            Q.append(tuple((t, s)))
            evaluations += 1
        
        if error_detected:
            break
    return None, expansions, evaluations, feedback


def dfs(state, successor_states, is_goal, state_representation, verify_successor, perform_checks = True, timeout=600):
    start_time = time.time()
    expansions = 0
    evaluations = 0
    s = state
    error_detected = False
    Q = [tuple((s, None))]
    Closed = dict()
    feedback = ""
    while len(Q) > 0:
        if perform_checks and timeout and time.time() - start_time > timeout:
            feedback += pprint("Timeout occurred during search with the successor function.")
            feedback += pprint("Please provide a different implementation of the successor function.")
            feedback += pprint("Keep the same function signature.")
            break 
        # Get the top from the queue
        s, parent = Q[-1][0], Q[-1][1]
        del Q[-1]
        c = state_representation(s)
        if c in Closed:
            continue
        Closed[c] = parent
        
        try:
            _is_goal = is_goal(s)
        except KeyboardInterrupt:
            feedback += pprint("Goal test function execution took too long.")
            feedback += pprint("Please provide a different implementation of the goal test function.")
            feedback += pprint("Keep the same function signature.")
            break
        if _is_goal:
            plan = reconstruct_plan(s, Closed, state_representation)
            return plan, expansions, evaluations, feedback
        expansions += 1

        if perform_checks:
            before_succ_run = copy.deepcopy(s)
        try:
            successors = successor_states(s)
        except KeyboardInterrupt:
            feedback += pprint("Successor function execution took too long.")
            feedback += pprint("Please provide a different implementation of the successor function.")
            feedback += pprint("Keep the same function signature.")
            break         
        #domain independent
        if perform_checks and state_representation(s) != state_representation(before_succ_run):
            # print("Input state changed as a result of applying the successor function.")
            feedback += pprint("Input state should not change as a result of applying the successor function.")
            feedback += pprint("State before successor function applied:", before_succ_run)
            feedback += pprint("State after successor function applied:", s)
            feedback += pprint("Let's think step by step. First, think of the possible reasons why the input state may change as a result of applying the successor function, such as the use of shallow copy.")
            feedback += pprint("Then, provide the complete Python code for the revised successor function that returns a list of successor states and ensure it does not change the input state.") 
            feedback += pprint("Remember how you fixed the previous mistakes, if any. Keep the same function signature.")
            break 

        for t in successors:
            if perform_checks:
                res, succ_feedback = verify_successor(s, t)
                if not res:
                    feedback += pprint(succ_feedback)
                    feedback += pprint("Input state:", s)
                    feedback += pprint("Example wrong successor state:", t)
                    error_detected = True
                    break
            Q.append(tuple((t,s)))
            evaluations += 1
        if error_detected:
            break
    return None, expansions, evaluations, feedback

