import math

class constraint_result:
    def __init__(self, success_count:int, restriction_result:float, assertion_result:float) -> None:
        self.success_count = success_count
        self.restriction_result = restriction_result
        self.assertion_result = assertion_result

    def ok_success_count(self):
        return self.success_count == 2

    def ok_restriction_result(self):
        return self.restriction_result < 0.001

    def ok_assertion_result(self):
        return self.assertion_result < 0.01

class bounds:
    def __init__(self) -> None:
        self.min_x = math.inf
        self.min_y = math.inf
        self.max_x = -math.inf
        self.max_y = -math.inf
        self.empty = True

    def includePoint(self, x:float, y:float) -> None:
        self.min_x = min(self.min_x, x)
        self.min_y = min(self.min_y, y)
        self.max_x = max(self.max_x, x)
        self.max_y = max(self.max_y, y)
        self.empty = False

    def includeBounds(self, other:bounds) -> None:
        if other.empty:
            return
        self.min_x = min(self.min_x, other.min_x)
        self.min_y = min(self.min_y, other.min_y)
        self.max_x = max(self.max_x, other.max_x)
        self.max_y = max(self.max_y, other.max_y)
        self.empty = True

    def __str__(self) -> str:
        return f"{self.min_x} {self.min_y} {self.max_x} {self.max_y}"

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
        return self.command + " " + " ".join([f"{round(p, 4):z.4g}" if type(p) == float else str(p) for p in self.params])

    def getBounds(self, s_x:float, s_y:float) -> bounds:
        p = self.discrete_params
        box = bounds()
        match self.discrete_command:
            case "A":
                r_x = abs(p[0])
                r_y = abs(p[1])
                phi = math.radians(p[2])
                large_arc = p[3]
                arc_side = p[4]
                p2_x = p[5]
                p2_y = p[6]
                cos_phi = math.cos(phi)
                sin_phi = math.sin(phi)

                box.includePoint(s_x, s_y)
                box.includePoint(p2_x, p2_y)
                
                petit_p1_x = (cos_phi * s_x + sin_phi * s_y) / r_x
                petit_p1_y = (cos_phi * s_y - sin_phi * s_x) / r_y
                petit_p2_x = (cos_phi * p2_x + sin_phi * p2_y) / r_x
                petit_p2_y = (cos_phi * p2_y - sin_phi * p2_x) / r_y

                petit_along_x = petit_p2_x - petit_p1_x
                petit_along_y = petit_p2_y - petit_p1_y

                petit_semidist = math.sqrt(petit_along_x ** 2 + petit_along_y ** 2)
                petit_along_x /= petit_semidist
                petit_along_y /= petit_semidist
                petit_semidist /= 2
                r_scale = max(1, petit_semidist)
                petit_ascender = math.sqrt(1 - petit_semidist ** 2) if petit_semidist <= 1 else 0
                if large_arc == arc_side:
                    # go on other side
                    petit_ascender = -petit_ascender
                petit_center_x = petit_p1_x + petit_along_x * petit_semidist - petit_ascender * petit_along_y
                petit_center_y = petit_p1_y + petit_along_y * petit_semidist + petit_ascender * petit_along_x
                petit_center_x *= r_x
                petit_center_y *= r_y

                center_x = cos_phi * petit_center_x - sin_phi * petit_center_y
                center_y = cos_phi * petit_center_y + sin_phi * petit_center_x

                petit_offset_x = cos_phi * r_x
                petit_offset_y = sin_phi * r_y
                petit_offset_len = math.sqrt(petit_offset_x ** 2 + petit_offset_y ** 2)
                petit_offset_x /= petit_offset_len
                petit_offset_y /= petit_offset_len
                petit_offset_x *= -r_x * r_scale
                petit_offset_y *= r_y * r_scale

                offset_x = cos_phi * petit_offset_x - sin_phi * petit_offset_y
                offset_y = cos_phi * petit_offset_y + sin_phi * petit_offset_x

                dot_prod_scale = 1 if arc_side else -1
                
                potential_x = center_x + offset_x
                potential_y = center_y + offset_y

                if ((potential_x - s_x) * petit_along_y - (potential_y - s_y) * petit_along_x) * dot_prod_scale >= 0:
                    box.includePoint(potential_x, potential_y)

                potential_x = center_x - offset_x
                potential_y = center_y - offset_y

                if ((potential_x - s_x) * petit_along_y - (potential_y - s_y) * petit_along_x) * dot_prod_scale >= 0:
                    box.includePoint(potential_x, potential_y)

                petit_offset_x = sin_phi * r_x
                petit_offset_y = cos_phi * r_y
                petit_offset_len = math.sqrt(petit_offset_x ** 2 + petit_offset_y ** 2)
                petit_offset_x /= petit_offset_len
                petit_offset_y /= petit_offset_len
                petit_offset_x *= r_x * r_scale
                petit_offset_y *= r_y * r_scale

                offset_x = cos_phi * petit_offset_x - sin_phi * petit_offset_y
                offset_y = cos_phi * petit_offset_y + sin_phi * petit_offset_x

                potential_x = center_x + offset_x
                potential_y = center_y + offset_y

                if ((potential_x - s_x) * petit_along_y - (potential_y - s_y) * petit_along_x) * dot_prod_scale >= 0:
                    box.includePoint(potential_x, potential_y)

                potential_x = center_x - offset_x
                potential_y = center_y - offset_y
                
                if ((potential_x - s_x) * petit_along_y - (potential_y - s_y) * petit_along_x) * dot_prod_scale >= 0:
                    box.includePoint(potential_x, potential_y)
            case "C":
                a_x = -s_x + 3 * (p[0] - p[2]) + p[4]
                a_y = -s_y + 3 * (p[1] - p[3]) + p[5]
                b_x = 3 * (s_x - 2 * p[0] + p[2])
                b_y = 3 * (s_y - 2 * p[1] + p[3])
                c_x = 3 * (-s_x + p[0])
                c_y = 3 * (-s_y + p[1])
                d_x = s_x
                d_y = s_y

                box.includePoint(s_x, s_y)
                box.includePoint(p[4], p[5] )

                if abs(a_x) >= 10e-4:
                    tx_disc = b_x - 3 * a_x * c_x
                    if tx_disc >= 0:
                        t_x = (-b_x + math.sqrt(tx_disc)) / (3 * a_x)
                        if 0 <= t_x <= 1:
                            box.includePoint(a_x * t_x ** 3 + b_x * t_x ** 2 + c_x * t_x + d_x, a_y * t_x ** 3 + b_y * t_x ** 2 + c_y * t_x + d_y)
                        t_x = (-b_x - math.sqrt(tx_disc)) / (3 * a_x)
                        if 0 <= t_x <= 1:
                            box.includePoint(a_x * t_x ** 3 + b_x * t_x ** 2 + c_x * t_x + d_x, a_y * t_x ** 3 + b_y * t_x ** 2 + c_y * t_x + d_y)
                elif abs(b_x) >= 10e-4:
                    t_x = c_x / (2 * b_x)
                    if 0 <= t_x <= 1:
                        box.includePoint(b_x * t_x ** 2 + c_x * t_x + d_x, b_y * t_x ** 2 + c_y * t_x + d_y)
                
                if abs(a_y) >= 10e-4:
                    ty_disc = b_y - 3 * a_y * c_y
                    if ty_disc >= 0:
                        t_y = (-b_y + math.sqrt(ty_disc)) / (3 * a_y)
                        if 0 <= t_y <= 1:
                            box.includePoint(a_x * t_y ** 3 + b_x * t_y ** 2 + c_x * t_y + d_x, a_y * t_y ** 3 + b_y * t_y ** 2 + c_y * t_y + d_y)
                        t_y = (-b_y - math.sqrt(ty_disc)) / (3 * a_y)
                        if 0 <= t_y <= 1:
                            box.includePoint(a_x * t_y ** 3 + b_x * t_y ** 2 + c_x * t_y + d_x, a_y * t_y ** 3 + b_y * t_y ** 2 + c_y * t_y + d_y)
                elif abs(b_y) >= 10e-4:
                    t_y = c_y / (2 * b_y)
                    if 0 <= t_y <= 1:
                        box.includePoint(b_x * t_y ** 2 + c_x * t_y + d_x, b_y * t_y ** 2 + c_y * t_y + d_y)
            case "L":
                box.includePoint(s_x, s_y)
                box.includePoint(p[0], p[1])
            case "Q":
                box.includePoint(s_x, s_y)
                box.includePoint(p[2], p[3])
                a_x = s_x - 2 * p[0] + p[2]
                a_y = s_y - 2 * p[1] + p[3]
                b_x = 2 * (p[0] - s_x)
                b_y = 2 * (p[1] - s_y)
                c_x = s_x
                c_y = s_y
                if abs(a_x) >= 10e-4:
                    t_x = -b_x / (2 * a_x)
                    if 0 <= t_x <= 1:
                        box.includePoint(a_x * t_x ** 2 + b_x * t_x + c_x, a_y * t_x ** 2 + b_y * t_x + c_y)
                if abs(a_x) >= 10e-4:
                    t_y = -b_y / (2 * a_y)
                    if 0 <= t_y <= 1:
                        box.includePoint(a_x * t_y ** 2 + b_x * t_y + c_x, a_y * t_y ** 2 + b_y * t_y + c_y)
            case _:
                pass
        return box