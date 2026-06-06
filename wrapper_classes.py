class constraint_result:
    def __init__(self, success_count:int, restriction_result:float, assertion_result:float) -> None:
        self.success_count = success_count
        self.restriction_result = restriction_result
        self.assertion_result = assertion_result

class curve_data:
    def __init__(self, command:str, params:list[float], debug:bool) -> None:
        self.command = command
        self.params = params
        self.discrete_command:str = command
        self.discrete_params = params
        self.debug = debug
    
    def carry_over(self):
        self.discrete_command = self.command
        self.discrete_params = [*self.params]

    def __str__(self) -> str:
        return self.command + " " + " ".join([f"{p:z.4g}" if type(p) == float else str(p) for p in self.params])