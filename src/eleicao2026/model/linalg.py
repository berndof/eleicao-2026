"""Álgebra linear mínima e utilidades numéricas (somente biblioteca padrão)."""
import math


def solve(A, b):
    """Resolve A x = b por eliminação de Gauss-Jordan com pivoteamento parcial."""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        pv = M[c][c]
        if abs(pv) < 1e-12:
            continue
        for j in range(c, n + 1):
            M[c][j] /= pv
        for r in range(n):
            if r != c and M[r][c] != 0:
                f = M[r][c]
                for j in range(c, n + 1):
                    M[r][j] -= f * M[c][j]
    return [M[i][n] for i in range(n)]


def wls(X, y, w, ridge=1e-6):
    """Mínimos quadrados ponderados com um ridge mínimo (não aplicado ao intercepto)."""
    p = len(X[0])
    A = [[0.0] * p for _ in range(p)]
    b = [0.0] * p
    for xi, yi, wi in zip(X, y, w):
        for a in range(p):
            xa = xi[a] * wi
            b[a] += xa * yi
            Aa = A[a]
            for c in range(p):
                Aa[c] += xa * xi[c]
    for a in range(1, p):
        A[a][a] += ridge * A[a][a] + 1e-9
    return solve(A, b)


def dot(x, beta):
    return sum(a * b for a, b in zip(x, beta))


def logit(p):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return math.log(p / (1 - p))


def expit(z):
    return 1 / (1 + math.exp(-z))


def wquant(vals, weights, qs):
    """Quantis ponderados (qs em [0,1])."""
    idx = sorted(range(len(vals)), key=lambda i: vals[i])
    tot = sum(weights)
    out, cum, j = [], 0.0, 0
    qs = sorted(qs)
    for i in idx:
        cum += weights[i]
        while j < len(qs) and cum / tot >= qs[j]:
            out.append(vals[i])
            j += 1
    while len(out) < len(qs):
        out.append(vals[idx[-1]])
    return out
