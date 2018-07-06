import pulp
from pulp.solvers import PULP_CBC_CMD
import time
from pathlib import Path


class VariableNameGenerator(object):
    def __init__(self):
        self.count = 0

    def get(self):
        ret = hex(self.count)[1:]
        self.count += 1
        return ret


def narrow_prunning(width, length):
    if width == 1:
        return length >= 2
    elif width == 2:
        return length >= 5
    elif width == 3:
        return length >= 11
    else:
        return False


def relation(xl, xu, yl, yu):
    return max(xl, yl) - min(xu, yu)


def get_problem(n, relax=False):
    problem = pulp.LpProblem("TileCovering", pulp.LpMaximize)
    field_size = n * (n + 1) // 2

    indicators = {}
    generator = VariableNameGenerator()
    for size in range(1, n + 1):
        variables = {}
        for x in range(field_size - size + 1):
            for y in range(field_size - size + 1):
                bound_distances = [x, y, field_size - (x + size), field_size - (y + size)]
                if narrow_prunning(min(x for x in bound_distances if x > 0), size):
                    continue
                if size == 1 and min(bound_distances) <= 1:
                    continue
                if size == 1 and (x > y or field_size - y - 1 < y):
                    continue
                variables[x, y] = pulp.LpVariable(generator.get(), 0, 1, pulp.LpContinuous if relax else pulp.LpBinary)
        indicators[size] = variables
        problem += pulp.lpSum(variables.values()) == size

    for x in range(field_size):
        for y in range(field_size):
            variables = []
            for size in range(1, n + 1):
                for rx in range(x - size + 1, x + 1):
                    for ry in range(y - size + 1, y + 1):
                        if (rx, ry) in indicators[size]:
                            variables.append(indicators[size][rx, ry])
            problem += pulp.lpSum(variables) == 1

    problem += 0
    return problem, indicators


def visualize(allocs):
    n = max(size for size, x, y in allocs)
    field_size = n * (n + 1) // 2
    buf = [['.' for _ in range(field_size)] for _ in range(field_size)]

    for size, x, y in allocs:
        print("size {} at ({}, {})".format(size, x, y))
        if size == 1:
            buf[x][y] = 'O'
            continue
        buf[x][y] = '+'
        buf[x][y + size - 1] = '+'
        buf[x + size - 1][y] = '+'
        buf[x + size - 1][y + size - 1] = '+'
        for i in range(1, size - 1):
            buf[x][y + i] = '-'
            buf[x + size - 1][y + i] = '-'
            buf[x + i][y] = '|'
            buf[x + i][y + size - 1] = '|'

    for l in buf:
        print(''.join(l))


def solve(n, relax=False):
    problem, indicators = get_problem(n, relax)
    print(problem)

    solver = pulp.solvers.PULP_CBC_CMD()

    duration = -time.time()
    result_status = problem.solve(solver)
    duration += time.time()

    print("result_status: {}".format(pulp.LpStatus[result_status]))
    print("duration: {:.4f} [sec]".format(duration))

    if relax:
        for size in range(1, n + 1):
            for (x, y), variable in indicators[size].items():
                alloc = variable.value()
                print("size {} at ({}, {}): value = {}".format(size, x, y, alloc))
    else:
        if result_status == pulp.LpStatusOptimal:
            print("obtained allocations:")
            allocs = []
            for size in range(1, n + 1):
                for (x, y), variable in indicators[size].items():
                    alloc = variable.value()
                    if alloc > 0.5:
                        allocs.append((size, x, y))
            visualize(allocs)


def read_sol(path: Path):
    solution = {}
    with path.open() as f:
        for l in f:
            var, val = l.split()
            val = float(val)
            solution[var] = val
    return solution


def visualize_sol(n, path: Path):
    problem, indicators = get_problem(n)
    solution = read_sol(path)
    allocs = []
    for size in range(1, n + 1):
        for (x, y), variable in indicators[size].items():
            alloc = solution[variable.name]
            if alloc > 0.5:
                allocs.append((size, x, y))
    visualize(allocs)


def main():
    solve(6)
    return


if __name__ == '__main__':
    main()