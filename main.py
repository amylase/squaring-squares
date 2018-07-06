import pulp
from pulp.solvers import PULP_CBC_CMD
import time


def solve(n):
    problem = pulp.LpProblem("TileCovering", pulp.LpMinimize)

    sizes = []
    idx_ranges = []
    for l in range(1, n + 1):
        fr = len(sizes)
        sizes += [l] * l
        to = len(sizes)
        idx_ranges.append((fr, to))
    tile_count = len(sizes)
    field_size = n * (n + 1) // 2
    xs = [pulp.LpVariable("x_{}".format(i), 0, field_size - sizes[i]) for i in range(tile_count)]
    ys = [pulp.LpVariable("y_{}".format(i), 0, field_size - sizes[i]) for i in range(tile_count)]

    # symmetry
    problem += xs[0] <= ys[0]
    problem += ys[0] <= (field_size + 1) // 2

    for l in range(1, n + 1):
        fr, to = idx_ranges[l - 1]
        for gr in range(fr, to):
            for le in range(fr, gr):
                problem += field_size * xs[le] + ys[le] <= field_size * xs[gr] + ys[gr], "tileOrdering_{}_{}".format(le, gr)

    big_m_constant = 2 * field_size
    for j in range(tile_count):
        for i in range(j):
            slacks = [pulp.LpVariable("slack_{}_{}_{}".format(i, j, k), 0) for k in range(4)]
            constraints = [
                (xs[i] + sizes[i], xs[j], slacks[0]),
                (xs[j] + sizes[j], xs[i], slacks[1]),
                (ys[i] + sizes[i], ys[j], slacks[2]),
                (ys[j] + sizes[j], ys[i], slacks[3]),
            ]
            for k, (less, greater, slack) in enumerate(constraints):
                problem += greater - less + slack >= 0, "distinctConstraint_{}_{}_{}".format(i, j, k)
            nonzero_indicators = [pulp.LpVariable("nonzero_{}_{}_{}".format(i, j, k), 0, 1, pulp.LpBinary) for k in range(4)]
            for k in range(4):
                problem += slacks[k] <= big_m_constant * nonzero_indicators[k], "slackNonzeroIndicatorConstraint_{}_{}_{}".format(i, j, k)
            problem += pulp.lpSum(nonzero_indicators) <= 3, "violationConstraint_{}_{}".format(i, j)

    problem += 0
    print(problem)
    problem.writeLP("problem.lp")
    solver = pulp.solvers.PULP_CBC_CMD()

    duration = -time.time()
    result_status = problem.solve(solver)
    duration += time.time()

    print("result_status: {}".format(pulp.LpStatus[result_status]))
    print("duration: {:.4f} [sec]".format(duration))
    print("obtained allocations:")
    for i in range(tile_count):
        print("size {} at ({}, {})".format(sizes[i], xs[i].value(), ys[i].value()))


def main():
    solve(2)


if __name__ == '__main__':
    main()