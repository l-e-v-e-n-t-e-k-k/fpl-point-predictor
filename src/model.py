# src/model.py


# Matrix helper functions

def mat_transpose(A):
    return list(map(list, zip(*A)))

def mat_mul(A, B):
    # A: n×m, B: m×k -> n×k
    n = len(A)
    m = len(A[0])
    k = len(B[0])
    out = [[0.0] * k for _ in range(n)]
    for i in range(n):
        for j in range(k):
            s = 0.0
            for t in range(m):
                s += A[i][t] * B[t][j]
            out[i][j] = s
    return out

def mat_vec_mul(A, v):
    # A: n×m, v: m -> n
    n = len(A)
    m = len(A[0])
    out = [0.0] * n
    for i in range(n):
        s = 0.0
        for j in range(m):
            s += A[i][j] * v[j]
        out[i] = s
    return out

def gauss_jordan_solve(A, b):
    """
    Megoldja A x = b-t Gauss–Jordan eliminacioval
    A: n×n, b: n
    """
    n = len(A)
    # augmented matrix
    M = [A[i][:] + [b[i]] for i in range(n)]

    for col in range(n):
        # pivot kereses
        pivot = col
        for r in range(col, n):
            if abs(M[r][col]) > abs(M[pivot][col]):
                pivot = r
        if abs(M[pivot][col]) < 1e-12:
            raise ValueError("Singular matrix (nem invertálható).")

        # sorcsere
        M[col], M[pivot] = M[pivot], M[col]

        # pivot sor normalizálás
        piv_val = M[col][col]
        for c in range(col, n + 1):
            M[col][c] /= piv_val

        # kinullazas
        for r in range(n):
            if r == col:
                continue
            factor = M[r][col]
            if factor == 0:
                continue
            for c in range(col, n + 1):
                M[r][c] -= factor * M[col][c]

    return [M[i][n] for i in range(n)]

# Linear Regression (Normal Equation)
class LinearRegression:

    def __init__(self):
        self.w = None

    def fit(self, X, y):
        # w = (X^T X)^-1 X^T y
        Xt = mat_transpose(X)
        XtX = mat_mul(Xt, X)               # p×p
        Xty = mat_vec_mul(Xt, y)           # p
        self.w = gauss_jordan_solve(XtX, Xty)   # p 

    def predict_row(self, x):
        if self.w is None:
            raise ValueError("Model nincs betanítva.")
        return sum(xj * wj for xj, wj in zip(x, self.w))

    def predict(self, X):
        if self.w is None:
            raise ValueError("Model nincs betanítva.")
        return [self.predict_row(x) for x in X]
#
# def predict(X, w):
#   return [sum(xj * wj for xj, wj in zip(x, w)) for x in X]

# def predict_row(x, w):
#    return sum(xj * wj for xj, wj in zip(x, w))

#  predict_batch(X, w):
#    return [predict_row(x, w) for x in X]

class MeanBaseline:

    def __init__(self):
        self.mean_value = None

    def fit(self, X, y):
        if not y:
            raise ValueError("Ures target")
        self.mean_value = sum(y) / len(y)

    def predict(self, X):
        if self.mean_value is None:
            raise ValueError("Model nincs betanitva")
        return [self.mean_value for _ in X]
