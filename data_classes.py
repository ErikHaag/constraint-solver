from dataclasses import dataclass, field

@dataclass
class definition_model:
    name: str
    definition: str
    delayed: bool = field(default=False)

@dataclass
class constraint_model:
    variables:list[str]
    assertions: list[str]
    restrictions: list[str] = field(default_factory=list)

@dataclass
class curve_model:
    type: str
    params: str = field(default="")
    debug: bool = field(default=False)

@dataclass
class input_data_model:
    output : str
    dump : str
    definitions: list[definition_model]
    constraits: list[constraint_model]
    curves: list[curve_model]
    minX:float
    minY:float
    width:float
    height:float

    @staticmethod
    def from_dict(obj):
        return input_data_model(
            output = obj.get("output"),
            dump = obj.get("dump", ""),
            definitions = [definition_model(**i) for i in obj.get("definitions")],
            constraits = [constraint_model(**i) for i in obj.get("constraints")],
            curves = [curve_model(**i) for i in obj.get("curves")],
            minX = obj.get("minX", 0),
            minY = obj.get("minY", 0),
            width = obj.get("width", 100),
            height = obj.get("height", 100)
        )
