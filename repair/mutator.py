import ast
import copy
from typing import Iterable, List

class Marker(ast.NodeTransformer):
    """Mark the target statement."""
    def __init__(self, line_no: int) -> None:
        super().__init__()

        self.line_no = line_no
        self.found = False          # target found?
        self.loop_level = 0         # depth of loop (0 indicates outside loop body)
        self.is_first_stmt = False  # is the first stmt in block?

    def generic_visit(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.stmt) and node.lineno == self.line_no:
            setattr(node, '__target__', (self.loop_level > 0, self.is_first_stmt))
            self.found = True
            return node
        
        # TODO: YOUR CODE HERE
        # The following is the super class implementation. Modify it to maintain
        # `self.loop_level` and `self.is_first_stmt` correctly.
        for field, old_value in ast.iter_fields(node):
            if isinstance(old_value, list):
                new_values = []
                if self.loop_level > 0:
                    if field == "orelse" and len(old_value) > 0:
                        self.loop_level -= 1
                    elif field == "decorator_list" and self.loop_level > 0:
                        self.loop_level -= 1
                i = -1
                for value in old_value:
                    i += 1
                    if field == "body" and i== 0:
                        self.is_first_stmt = True
                    else:
                        self.is_first_stmt = False
                    if isinstance(value, ast.AST):
                        if type(value) in [ast.For, ast.While]:
                            self.loop_level += 1
                        value = self.visit(value)
                        if value is None:
                            continue
                        elif not isinstance(value, ast.AST):
                            new_values.extend(value)
                            continue
                    new_values.append(value)
                old_value[:] = new_values
            elif isinstance(old_value, ast.AST):
                #self.is_first_stmt = True
                new_node = self.visit(old_value)
                if new_node is None:
                    delattr(node, field)
                else:
                    setattr(node, field, new_node)
        return node


def mk_abstract() -> ast.expr:
    """Create an AST for the abstract condition."""
    return ast.Name('__abstract__')

class MutationOperator(ast.NodeTransformer):
    def __init__(self) -> None:
        super().__init__()
        self.mutated = False

class Tighten(MutationOperator):
    """If the target statement is an if-statement, transform its condition by
    conjoining an abstract condition: if c => if c and not __abstract__."""
    # TODO: YOUR CODE HERE
    def visit_If(self, node):
        self.generic_visit(node)
        if (hasattr(node, '__target__')):
            node.test = ast.BoolOp(
                op=ast.And(), 
                values = [node.test, ast.UnaryOp(op=ast.Not(), operand=mk_abstract())])            
            self.mutated = True
        return node    
    pass


class Loosen(MutationOperator):
    """If the target statement is an if-statement, transform its condition by
    disjoining an abstract condition: if c => if c or __abstract__."""
    # TODO: YOUR CODE HERE
    def visit_If(self, node):
        self.generic_visit(node)
        if (hasattr(node, '__target__')):
            node.test = ast.BoolOp(
                op=ast.Or(), 
                values = [node.test, mk_abstract()])
            self.mutated = True
        return node
    pass


class Guard(MutationOperator):
    """Transform the target statement so that it executes only if an abstract condition is false:
    s => if not __abstract__: s."""
    # TODO: YOUR CODE HERE
    def generic_visit(self, node):
        super().generic_visit(node)
        if (hasattr(node, '__target__') and isinstance(node, ast.stmt)):
            node = ast.If(
                test = ast.UnaryOp(op=ast.Not(), operand=mk_abstract()),
                body = node,
                orelse = []
            )
            self.mutated = True
        return node
    pass


class Break(MutationOperator):
    """If the target statement is in loop body, right before it insert a `break` statement that
    executes only if an abstract condition is true, i.e., if __abstract__: break."""
    def __init__(self, required_position: bool) -> None:
        """If `required_position` is `True`, this operation is performed only when the 
        target is the first statement.
        If `required_position` is `False`, this operation is performed only when the 
        target is not the first statement.
        """
        super().__init__()
        self.required_position = required_position

    # TODO: YOUR CODE HERE
    def generic_visit(self, node):
        super().generic_visit(node)
        if (hasattr(node, '__target__') and isinstance(node, ast.stmt)):            
            if self.required_position == True and node.__target__[0] == True and node.__target__[1] == True:
                previous = ast.unparse(node)
                str = f"""
if __abstract__:
    break
{previous}"""
                node = ast.parse(str)
                self.mutated = True
            elif self.required_position == False and node.__target__[0] == True and node.__target__[1] == False:
                previous = ast.unparse(node)
                str = f"""
if __abstract__:
    break
{previous}"""
                node = ast.parse(str)
                self.mutated = True
        return node
    pass

class Mutator:
    """Perform program mutation."""
    def __init__(self, tree: ast.Module, line_no: int, log: bool = False) -> None:
        assert isinstance(tree, ast.Module)
        self.old_tree = tree
        self.log = log
        
        marker = Marker(line_no)
        self.marked_tree = marker.visit(copy.deepcopy(tree))
        assert marker.found

    def apply(self, ops: List[MutationOperator] = None) -> Iterable[ast.Module]:
        if ops is None:
            # in default priority order
            ops = [Tighten(), Loosen(), Break(True), Guard(), Break(False)] 

        for visitor in ops:
            new_tree = visitor.visit(copy.deepcopy(self.marked_tree))
            if self.log:
                print(f'-> {visitor.__class__.__name__}', '✓' if visitor.mutated else '✗')

            if visitor.mutated:
                if self.log:
                    print(ast.unparse(new_tree))

                yield new_tree
