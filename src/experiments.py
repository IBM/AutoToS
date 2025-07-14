import time
import argparse
from twentyfourgame.twentyfourgame_experiments import TwentyFourGame
from sokoban.sokoban_experiment import Sokoban
from crossword5by5.crossword_experiments import Crossword
from prontoqa.prontoqa_experiments import Prontoqa
from blocksworld.blocksworld_experiments import Blocksworld



domains = {"24game": TwentyFourGame, "blocks": Blocksworld, "cw": Crossword, "sokoban": Sokoban, "prontoqa": Prontoqa}


def run_domain(args, domain):
    log_folder = f"logs/{args.domain}/{args.model}"
    if args.complex_validation:
        log_folder+="-val"
    else:
        log_folder+="-noval"

    start_time = time.time()
    exp = domain(model_name=args.model, log_folder = log_folder)
    if args.complex_validation:
        try:
            exp.set_use_complex_validator()
        except NotImplementedError as e:
            print(f"A complex validator is not implemented for {args.domain}")
            exit(1)
    
    # Obtain the successor function
    print("Getting the successor function...")
    if exp.obtain_successor_function():
        #Perform the goal iteration
        print("Getting the goal test function...")
        if exp.perform_goal_iteration(exp.get_initial_goal_prompt()):
            # Step 3: Perform the successor completeness and soundness tests
            print("Successor soundness and completeness tests...")
            if exp.successor_completeness_soundness_tests():
                #perform evaluation using the final llm successor function and goal
                exp.model_test_split_eval()
            
    exp.log_all_messages()
    print(f"Finished in {time.time() - start_time} seconds")
    return exp.get_client()

if __name__ == "__main__":            
    parser = argparse.ArgumentParser()

    parser.add_argument('--model', type=str, required=True)
    parser.add_argument('--domain', type=str, choices=list(domains.keys())+ ["all"], required=True)
    parser.add_argument('--complex-validation', action='store_true')
    args = parser.parse_args()

    if args.domain=="all":
        for domain_name in domains.keys():
            print(f"=====================Starting {domain_name}===============")
            domain = domains[domain_name]
            args.domain = domain_name
            client = run_domain(args, domain)
            print(f"=====================Ended {domain}===============")
    else:
        domain = domains[args.domain]
        client = run_domain(args, domain)
    
    