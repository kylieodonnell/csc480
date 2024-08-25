import time
from unittest.mock import MagicMock
from utils.Enums import COLLUMN_STYLE
from buildings.elements.Window import Window

class TransformMock:
    def __init__(self, value=None, rotation=None, flip=None):
        self.value = value
        self.rotation = rotation  # Add the rotation attribute
        self.flip = flip


    def __mul__(self, other):
        return other

    def __le__(self, other):
        if isinstance(other, TransformMock):
            return self.value <= other.value
        return False

    def __ge__(self, other):
        if isinstance(other, TransformMock):
            return self.value >= other.value
        return False

    def __eq__(self, other):
        if isinstance(other, TransformMock):
            return self.value == other.value
        return False

class MockEditor:
    def __init__(self):
        self.blocks_placed = []
        self.transform = TransformMock()  # Replace MagicMock with TransformMock

    def placeBlock(self, position, block):
        self.blocks_placed.append((position, block))

    def placeBlockGlobal(self, position, block, replace):
        self.blocks_placed.append((position, block))

    def pushTransform(self, transform):
        return MagicMock()

    def __mul__(self, other):
        return other
    
class MockWindow:
    def __init__(self):
        self.padding = 0
        self.ypadding = 0
        self.windows = []


class BalconyTest:
    def __init__(self):
        self.rdata = {
            "size": {"min_len": 3, "max_len": 10, "min_width": 3, "max_width": 10, "min_height": 4, "max_height": 6},
            "multiple": {"min_width": 5, "min_gap": 2, "proba": 0},
            "growth": 0.5,
            "details": 0,
            "border_radius": {"none": 5},
            "grounded": 0.5,
            "alternate": 0.5,
            "crossbars": {
                "min_height_for_vertical_crossbar": 5,
                "min_width_for_horizontal_crossbar": 5,
                "vertical_crossbar": 0.5,
                "horizontal_crossbar": 0.5
            }
        }
        self.max_width = 10
        self.max_height = 6
        self.facade_len = 12
        self.facade_height = 10
        self.windows = MockWindow()  # Use the simplified mock window
        self.collumn_style = COLLUMN_STYLE(1)
        self.editor = MockEditor()
        self.materials = ["stone", "wood", "glass", "iron", "brick"]


    def run_functionality_test(self, balcony_class):
        print(f"Running functionality test on {balcony_class.__name__}...")
        balcony = balcony_class(self.rdata, self.max_width, self.windows, self.collumn_style)
        balcony.build(self.editor, self.materials)
        
        print(f"Blocks placed: {self.editor.blocks_placed}")
        print("Functionality test completed.\n")

    def test_individual_components(self, balcony_class, name):
        print(f"Testing individual components of {name}...")

        balcony = balcony_class(self.rdata, self.max_width, self.windows, self.collumn_style)
        structures = balcony.get_structures()
        print(f"Generated structures: {structures}")

        for s in structures:
            balcony.build_border_radius(s)
        print(f"Blocks placed for border radius: {self.editor.blocks_placed}")

        self.editor.blocks_placed = []
        for s in structures:
            balcony.build_details(s)
        print(f"Blocks placed for details: {self.editor.blocks_placed}")

        print("Individual components test completed.\n")

    def measure_execution_time(self, balcony_class, name, iterations=100):
        print(f"Measuring execution time for {name}...")
        start_time = time.time()
        for _ in range(iterations):
            balcony = balcony_class(self.rdata, self.max_width, self.windows, self.collumn_style)
            balcony.build(self.editor, self.materials)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Execution time for {name}: {elapsed_time:.4f} seconds over {iterations} iterations.\n")
        return elapsed_time

    def compare_versions(self, original_class, optimized_class, iterations=100):
        original_time = self.measure_execution_time(original_class, "original", iterations)
        optimized_time = self.measure_execution_time(optimized_class, "optimized", iterations)
        
        improvement = ((original_time - optimized_time) / original_time) * 100
        print(f"Optimized class is {improvement:.2f}% faster than the original class.\n")

if __name__ == "__main__":
    from buildings.elements.Balcony import Balcony as OriginalBalcony
    from buildings.elements.OptimizedBalcony import Balcony as OptimizedBalcony

    tester = BalconyTest()
    num_runs = 0
    while num_runs < 5:
        try:
            tester.run_functionality_test(OriginalBalcony)
        except Exception as e:
            print(f"Error in OriginalBalcony: {e}")
        num_runs += 1
    num_runs = 0
    while num_runs < 5:
        try:
            tester.run_functionality_test(OptimizedBalcony)
        except Exception as e:
            print(f"Error in OptimizedBalcony: {e}")
        num_runs += 1
    
    num_runs = 0
    while num_runs < 5:
        try:
            tester.test_individual_components(OriginalBalcony, "original")
        except Exception as e:
            print(f"Error in OriginalBalcony: {e}")
        num_runs += 1
    num_runs = 0
    while num_runs < 5:
        try:
            tester.test_individual_components(OptimizedBalcony, "optimized")
        except Exception as e:
            print(f"Error in OptimizedBalcony: {e}")
        num_runs += 1

    tester.compare_versions(OriginalBalcony, OptimizedBalcony, iterations=100000)