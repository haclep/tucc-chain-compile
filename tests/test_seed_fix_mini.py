"""Miniature of the C2-equilibrium eigensolve failure and its fix.

Three disconnected blocks, shaped like the real system:
  block A (10 dets)  -- contains the "HF" determinant (index 0).
      Flat diagonal at -74.60, strong couplings: correlation pushes the
      block's ground DEEP, to ~-74.696 (the true global ground).
  blocks B and C (10 dets each) -- EXACT COPIES of each other, so their
      ground states are an exactly degenerate pair at ~-74.66. Their
      lowest diagonal (-74.65) sits BELOW block A's lowest (-74.60).

That is the C2 trap: the lowest DIAGONALS live in the degenerate pair's
blocks, while the lowest EIGENVALUE lives in the HF block. A Davidson
seeded on lowest diagonals can never leave the blocks its seed touches
(H is exactly zero across blocks), so it converges the pair and never
sees the ground.

Run:  python -u test_seed_fix_mini.py
(imports davidson from chaincompile.fastpath if installed, else from a
local fastpath.py copy)
"""
import numpy as np

try:
    from chaincompile.fastpath import davidson
except Exception:
    from fastpath import davidson


# ---------- the toy Hamiltonian ----------------------------------------

def block_A():
    n = 10
    H = np.full((n, n), 0.0)
    np.fill_diagonal(H, -74.60)
    for i in range(n - 1):
        H[i, i + 1] = H[i + 1, i] = 0.05
    H[0, 5] = H[5, 0] = 0.03
    return H


def block_B():
    n = 10
    H = np.zeros((n, n))
    d = np.full(n, -74.64)
    d[0] = -74.65          # unique lowest diagonal of this block
    np.fill_diagonal(H, d)
    for i in range(n - 1):
        H[i, i + 1] = H[i + 1, i] = 0.005
    return H


def assemble(bridge=0.0):
    """30x30 block-diagonal H = A (+) B (+) C, with C an exact copy of
    B; optional tiny 'bridge' coupling between B and C mimicking
    numerical symmetry breaking in dumped integrals."""
    A, B = block_A(), block_B()
    H = np.zeros((30, 30))
    H[0:10, 0:10] = A
    H[10:20, 10:20] = B
    H[20:30, 20:30] = B
    if bridge:
        H[10, 20] = H[20, 10] = bridge   # couples the DOMINANT dets
    return H


class DenseOp:
    """Minimal operator wrapper with the same interface davidson and
    the driver's block walk (_csr_component) consume."""

    def __init__(self, H):
        self.H = H
        self.dim = H.shape[0]
        r, c = np.nonzero(H)
        o = np.argsort(r, kind="stable")
        r, c = r[o], c[o]
        self.indices = c.astype(np.int64)
        self.data = H[r, c]
        self.indptr = np.zeros(self.dim + 1, np.int64)
        np.add.at(self.indptr, r + 1, 1)
        self.indptr = np.cumsum(self.indptr)

    def matvec(self, v):
        return self.H @ np.asarray(v, float)

    def diagonal(self):
        return np.diag(self.H).copy()


def csr_component(indptr, indices, data, seed, thr=1e-10):
    """Verbatim logic of run_big_sd._csr_component."""
    import collections
    seen = {int(seed)}
    dq = collections.deque(seen)
    while dq:
        i = dq.popleft()
        for k in range(indptr[i], indptr[i + 1]):
            if abs(data[k]) <= thr:
                continue
            j = int(indices[k])
            if j not in seen:
                seen.add(j)
                dq.append(j)
    return seen


def seeds_new(diag, hf_index, n_extra=3):
    seeds = [int(hf_index)]
    for j in np.argsort(diag)[:n_extra]:
        if int(j) not in seeds:
            seeds.append(int(j))
    return seeds


def unit_columns(dim, seeds):
    v0 = np.zeros((dim, len(seeds)))
    for r, s in enumerate(seeds):
        v0[s, r] = 1.0
    return v0


def blockweight(v, lo, hi):
    return float(np.linalg.norm(v[lo:hi]))


def main():
    H = assemble()
    ev = np.linalg.eigvalsh(H)
    evA = np.linalg.eigvalsh(block_A())
    evB = np.linalg.eigvalsh(block_B())
    print("spectrum check: global ground %.6f (block A %.6f, "
          "pair %.6f x2)" % (ev[0], evA[0], evB[0]))
    assert abs(ev[0] - evA[0]) < 1e-12          # ground lives in A
    assert np.sum(np.isclose(ev, evB[0], atol=1e-12)) == 2  # exact pair
    dg = np.diag(H)
    assert dg.min() == -74.65 and dg[:10].min() == -74.60
    print("trap check: lowest diagonals are in B/C, ground is in A\n")

    op = DenseOp(H)

    # ---- 1. reproduce the failure: the shipped call --------------------
    w, X, nmv = davidson(op, nroots=2, tol=1e-10)
    print("OLD (nroots=2, lowest-diagonal seeds):")
    print("  roots %.8f %.8f  gap %.3e  (%d matvecs)"
          % (w[0], w[1], w[1] - w[0], nmv))
    print("  root-0 weight in A %.3f, B %.3f, C %.3f"
          % (blockweight(X[:, 0], 0, 10), blockweight(X[:, 0], 10, 20),
             blockweight(X[:, 0], 20, 30)))
    assert abs(w[0] - evB[0]) < 1e-8            # converged to the PAIR
    assert w[0] - ev[0] > 0.03                  # ~36 mHa above ground
    assert blockweight(X[:, 0], 0, 10) < 1e-8   # blind to block A
    print("  -> converged the degenerate pair; never saw the ground. "
          "FAILURE REPRODUCED\n")

    # ---- 2. the fix: HF joins the seeds --------------------------------
    sds = seeds_new(op.diagonal(), hf_index=0)
    w2, X2, nmv2 = davidson(op, nroots=len(sds), tol=1e-10,
                            v0=unit_columns(op.dim, sds))
    print("NEW (seeds = HF + 3 lowest diagonals, nroots=%d):" % len(sds))
    print("  roots " + "  ".join("%.8f" % x for x in w2)
          + "  (%d matvecs)" % nmv2)
    assert abs(w2[0] - ev[0]) < 1e-9            # TRUE ground found
    assert blockweight(X2[:, 0], 10, 30) < 1e-7
    print("  -> root 0 is the true ground, pure in block A. FIXED\n")

    # ---- 3. stretched-geometry analog: pair IS the ground --------------
    Hs = assemble()
    Hs[0:10, 0:10] += 0.08 * np.eye(10)         # push block A up
    evs = np.linalg.eigvalsh(Hs)
    ops = DenseOp(Hs)
    w3, X3, _ = davidson(ops, nroots=len(sds), tol=1e-10,
                         v0=unit_columns(ops.dim, sds))
    assert abs(w3[0] - evs[0]) < 1e-9
    # force the worst case for the purity check: an exact 50/50 mixture
    eB = np.linalg.eigh(block_B())[1][:, 0]
    mix = np.zeros(30)
    mix[10:20] = eB / np.sqrt(2)
    mix[20:30] = eB / np.sqrt(2)
    j0 = int(np.argmax(np.abs(mix)))
    comp = csr_component(ops.indptr, ops.indices, ops.data, j0, thr=1e-7)
    mask = np.zeros(30, bool)
    mask[list(comp)] = True
    leak = float(np.linalg.norm(mix[~mask]))
    assert len(comp) == 10 and abs(leak - 1 / np.sqrt(2)) < 1e-12
    proj = np.where(mask, mix, 0.0)
    proj /= np.linalg.norm(proj)
    hv = ops.matvec(proj)
    e_act = float(proj @ hv)
    res = float(np.linalg.norm(hv - e_act * proj))
    print("STRETCHED ANALOG: ground = pair %.8f; 50/50 mixture leak "
          "%.3f -> projected, support 20 -> 10, eigen-residual %.1e"
          % (w3[0], leak, res))
    assert res < 1e-10                          # blocks truly disjoint
    print("  -> leak-triggered projection recovers a pure exact "
          "eigenvector. SAFETY NET WORKS\n")

    # ---- 4. numerical symmetry breaking: 1e-8 bridge -------------------
    Hb = assemble(bridge=1e-8)
    Hb[0:10, 0:10] += 0.08 * np.eye(10)         # pair is the ground
    wb, Ub = np.linalg.eigh(Hb)
    vb = Ub[:, 0]                               # TRUE numerical ground
    gap = wb[1] - wb[0]
    wB, wC = blockweight(vb, 10, 20), blockweight(vb, 20, 30)
    print("BRIDGED (B-C coupling 1e-8, the dumped-integral noise case):")
    print("  exact gap %.3e; true eigenvector weight B %.3f / C %.3f"
          % (gap, wB, wC))
    assert gap >= 1e-9                          # OLD trigger stays silent
    assert min(wB, wC) > 0.4                    # yet it IS a mixture
    opb = DenseOp(Hb)
    j0 = int(np.argmax(np.abs(vb)))
    c7 = csr_component(opb.indptr, opb.indices, opb.data, j0, thr=1e-7)
    c10 = csr_component(opb.indptr, opb.indices, opb.data, j0, thr=1e-10)
    assert len(c7) == 10 and len(c10) == 20     # 1e-10 walk fuses blocks
    mask = np.zeros(30, bool)
    mask[list(c7)] = True
    leak = float(np.linalg.norm(vb[~mask]))
    assert leak > 1e-8                          # NEW trigger fires
    proj = np.where(mask, vb, 0.0)
    proj /= np.linalg.norm(proj)
    hv = opb.matvec(proj)
    e_act = float(proj @ hv)
    res = float(np.linalg.norm(hv - e_act * proj))
    print("  old gap-trigger (<1e-9): SILENT.  new leak-trigger at "
          "1e-7 walk: fires (leak %.3f)" % leak)
    print("  projected eigen-residual %.1e (= the symmetry-breaking "
          "noise scale, the honest price)" % res)
    assert res < 1e-7
    print("  -> mechanism (b)/(c) both handled and REPORTED\n")

    print("ALL MINIATURE CHECKS PASSED")


if __name__ == "__main__":
    main()
