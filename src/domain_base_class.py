import logging
import os
import sys
import io
import traceback
from abc import ABC, abstractmethod
from datetime import datetime

from utils import experiment_utils

from dotenv import load_dotenv
from openai import OpenAI



class DomainTestBase(ABC):
    
    def __init__(self, model_name, log_folder):
        # make sure you have a .env file under genai root with
        load_dotenv()
        self.use_complex_validator = False
        sysmsg = """You are Python coding assistant. Help me generate my Python functions based on the task descriptions. Please always generate only a single function and keep all imports in it. If you need to define any additional functions, define them as inner functions. Do not generate examples of how to invoke the function. Please do not add any print statements outside the function. Provide the complete function and do not include any ellipsis notation."""
        self.model_id = model_name

        self.client = OpenAI(api_key=os.getenv("API_KEY"), base_url=os.getenv("API_BASE_URL","http://0.0.0.0:4000"))
        self.messages = [
                {"role": "system", "content": sysmsg}
                ]

        self.max_goal_iterations = 10
        self.max_succ_iterations = 10
        self.goal_iterations = 0
        self.succ_iterations = 0
        self.llm_successor_states = None
        self.llm_is_goal = None
        self.conversation_id = None

        # Create logs
        self.log_directory = f'./{log_folder}_logs'
        os.makedirs(self.log_directory, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file_path = os.path.join(self.log_directory, f'script_log_{timestamp}.txt')
        self.setup_logging()
        self.num_input_tokens = 0
        self.num_output_tokens = 0

    def get_client(self):
        return self.client
    
    def prompt_model(self, prompt):

        self.messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=self.messages
            )        
        self.num_input_tokens += response.usage.prompt_tokens
        self.num_output_tokens += response.usage.completion_tokens
        resp = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": resp})

        return resp 


    def log_all_messages(self):
        logging.info("======================= Model messages =======================")
        logging.info(self.messages)
        logging.info("======================= Model messages end =======================")
        logging.info(f"Number of tokens, input: {self.num_input_tokens}, output: {self.num_output_tokens}")

    def setup_logging(self):
        if not logging.getLogger().hasHandlers():
            file_formatter = logging.Formatter('%(message)s')
            file_handler = logging.FileHandler(self.log_file_path)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(file_formatter)
            file_handler.addFilter(experiment_utils.HTTPRequestFilter())

            console_handler = logging.StreamHandler()
            console_handler.addFilter(experiment_utils.HTTPRequestFilter())

            logging.getLogger().setLevel(logging.INFO)
            logging.getLogger().addHandler(file_handler)
            logging.getLogger().addHandler(console_handler)

    def _str(self, state):
        if isinstance(state, dict):
            # return str(state)
            res = ""
            for key, val in state.items():
                if isinstance(val, list):
                    val = sorted(val)
                res += str(key) + ":" + str(val)
            return res
            # return str(state)
        return " ".join(sorted(list([str(s) for s in state])))
    
    def set_use_complex_validator(self):
        self.use_complex_validator = True

    def validate_transition(self, s, t):
        if self.use_complex_validator:
            return self.validate_transition_complex(s, t)
        return True, ""
    
    @abstractmethod
    def test_successor_soundness(self, llm_successor_states, llm_is_goal):
        pass

    @abstractmethod
    def test_successor_completeness(self, llm_successor_states):
        pass

    @abstractmethod
    def test_goal_soundness(self, llm_is_goal):
        pass

    @abstractmethod
    def model_test_split_eval(self, no_logging=False):
        pass

    @abstractmethod
    def get_initial_successor_prompt(self):
        pass

    @abstractmethod
    def get_initial_goal_prompt(self):
        pass

    @abstractmethod
    def validate_transition_complex(self, s, t):
        pass
    
    def run_tests(self, llm_successor_states, llm_is_goal, test_type):
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout

        feedback = ""
        res = ""
        try:
            if test_type == 'goal_soundness_test':
                res += self.test_goal_soundness(llm_is_goal)
            elif test_type == 'successor_soundness_test':
                res += self.test_successor_soundness(llm_successor_states, llm_is_goal)
            elif test_type == 'successor_completeness_test':
                res += self.test_successor_completeness(llm_successor_states)
        except Exception as e:
            last_traceback = traceback.extract_tb(e.__traceback__)[-1:]
            relevant_trace = traceback.format_list(last_traceback) + [str(e)]
            if test_type == 'goal_soundness_test':
                trace = "\n".join(relevant_trace)
                feedback = f'The following exception was produced when testing the goal function: \n {trace}. Please fix this exception in the goal function.'
            elif test_type == 'successor_soundness_test' or test_type == 'successor_completeness_test':
                trace = "\n".join(relevant_trace)
                feedback = f"The following exception was produced when testing the successor function: \n{trace}. Please fix this exception in the successor function."

        feedback = new_stdout.getvalue() + feedback + res
        sys.stdout = old_stdout
        return feedback
    

    def obtain_successor_function(self):
        self.succ_iterations = 0
        feedback = self.get_initial_successor_prompt()
        while self.succ_iterations < self.max_succ_iterations:
            if self.succ_iterations == 0:
                logging.info("User:")
                logging.info(feedback)

            response_text = self.prompt_model(feedback)
            logging.info("Model:")
            logging.info(response_text)

            self.llm_successor_states, successor_code, response_feedback = experiment_utils.get_from_text_by_keyword(response_text, 'successor')
            if self.llm_successor_states:
                logging.info("========= Extracted code: =========")
                logging.info(successor_code)
                logging.info("===================================") 
                break

            if response_feedback:
                # Syntax error
                feedback = f"The code contains syntax error: {response_feedback}\nPlease fix the error. Please provide only the complete Python function that returns a list of successor states for a state."
            else:
                feedback = "Could not extract the function from your response. Please provide only the complete Python function that returns a list of successor states for a state."
            self.succ_iterations += 1
            if self.succ_iterations >= self.max_succ_iterations:
                logging.info("Maximum iterations reached for extracting a successor function. Process stopped.")
                return False

        return True


    def perform_goal_iteration(self, _feedback):
        feedback = _feedback
        while self.goal_iterations < self.max_goal_iterations:

            # if self.goal_iterations == 0:
            logging.info("User:")
            logging.info(feedback)
            response_text = self.prompt_model(feedback)

            logging.info("Model:")
            logging.info(response_text)
            self.llm_is_goal, goal_code, response_feedback = experiment_utils.get_from_text_by_keyword(response_text, 'goal')
            if self.llm_is_goal:
                logging.info("========= Extracted code: =========")
                logging.info(goal_code)
                logging.info("===================================") 
            else:

                if response_feedback:
                    # Syntax error
                    feedback = f"The code contains syntax error: {response_feedback}\nPlease fix the error. Please provide only the complete Python function that tests whether a given state is already a goal state."
                else:
                    feedback = "Could not extract the function from your response. Please provide only the complete Python function that tests whether a given state is already a goal state."
                self.goal_iterations += 1
                continue

            feedback = self.run_tests(None, self.llm_is_goal, 'goal_soundness_test')

            if feedback == "":
                logging.info("Goal Soundness Test Passed")
                return True

            # logging.info(f'Current feedback: {feedback}')
            self.goal_iterations += 1
            if self.goal_iterations >= self.max_goal_iterations:
                logging.info("Maximum number of iterations reached for goal soundness test. Process stopped.")
                return False

            logging.info(f"Goal Iteration {self.goal_iterations} - Goal Soundness Test")
        

    def successor_completeness_soundness_tests(self):
        logging.info(f"Soundness test")
        while self.succ_iterations < self.max_succ_iterations:
            #print(f"succ_iterations: {succ_iterations}")

            if self.succ_iterations > 0:
                logging.info(f"Successor Iteration {self.succ_iterations}")
                logging.info("User:")
                logging.info(feedback)

                response_text = self.prompt_model(feedback)

                logging.info("Model:")
                logging.info(response_text)
                self.llm_successor_states, successor_code, response_feedback = experiment_utils.get_from_text_by_keyword(response_text, 'successor')
                if self.llm_successor_states:
                    logging.info("========= Extracted code: =========")
                    logging.info(successor_code)
                    logging.info("===================================") 
                else:
                    if response_feedback:
                        # Syntax error
                        feedback = f"The code contains syntax error: {response_feedback}\nPlease fix the error. Please provide only the complete Python function that returns a list of successor states for a state."
                    else:
                        feedback = "Could not extract the function from your response. Please provide only the complete Python function that returns a list of successor states for a state."
                    self.succ_iterations += 1
                    if self.succ_iterations >= self.max_succ_iterations:
                        logging.info("Maximum iterations reached for completeness test. Process stopped.")
                        return False
                    continue

            feedback = self.run_tests(self.llm_successor_states, self.llm_is_goal, 'successor_soundness_test')
            if feedback == "":
                logging.info("Successor States Soundness Test Passed")
            else:
                if "Please fix the goal test function." in feedback:
                    logging.info(f"Successor Iteration {self.succ_iterations} - Restarting function extraction")
                    self.perform_goal_iteration(feedback)
                
                self.succ_iterations += 1
                if self.succ_iterations >= self.max_succ_iterations:
                    logging.info("Maximum iterations reached for completeness test. Process stopped.")
                    return False
                continue

            logging.info(f"Completeness test")

            feedback = self.run_tests(self.llm_successor_states, self.llm_is_goal, 'successor_completeness_test')
            if feedback == "":
                logging.info("Successor Completeness Test Passed")
                return True
            
            self.succ_iterations += 1
            if self.succ_iterations >= self.max_succ_iterations:
                logging.info("Maximum iterations reached for completeness test. Process stopped.")
                return False

        return False


